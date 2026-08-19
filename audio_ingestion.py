"""
Enterprise Audio Detection System - Milestone 2: Dual Audio Ingestion with Edge AI & Temporal Buffer

Captures microphone audio (via PyAudio) and system speaker loopback (via SoundCard) concurrently.
Runs Google YAMNet classification on the microphone stream and evaluates a 5-frame rolling
temporal buffer to validate sustained threats (Fire Alarm, Gunshot, Explosion, Glass Shatter, Crying Baby).

Data Specifications:
- Sample Rate: 16000 Hz
- Channels: Mono (1 channel)
- Data Type: float32, normalized in [-1.0, 1.0]
- Chunk Size: 15600 samples (0.975 seconds per chunk)
- Loopback: Stereo capture (channels=2) downmixed to Mono (1 channel) via NumPy mean
- AI Model: Google YAMNet (521 AudioSet classes)
- Temporal Buffer: deque maxlen=5, validation gate >= 3/5 frames with confidence > 0.85
"""

import argparse
import logging
import queue
import signal
import sys
import threading
import time
from typing import Optional, Tuple

import numpy as np
import pyaudio
import soundcard as sc

from yamnet_classifier import (
    CONFIDENCE_THRESHOLD,
    CRITICAL_SOUNDS,
    REQUIRED_CONSECUTIVE_FRAMES,
    WARNING_SOUNDS,
    TemporalHazardBuffer,
    YAMNetClassifier,
)

# Ensure UTF-8 output encoding across Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configuration Constants
DEFAULT_SAMPLE_RATE: int = 16000
DEFAULT_CHUNK_SAMPLES: int = 15600  # 0.975 seconds @ 16kHz
MIC_CHANNELS: int = 1
SPEAKER_CHANNELS: int = 2  # WASAPI requires stereo loopback, downmixed to mono
DTYPE = np.float32

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AudioIngestion")


def calculate_rms(audio_chunk: np.ndarray) -> float:
    """
    Calculate the Root Mean Square (RMS) volume level of an audio chunk.

    Args:
        audio_chunk: 1D numpy array of float32 samples in [-1.0, 1.0]

    Returns:
        float: RMS value in range [0.0, 1.0]
    """
    if audio_chunk is None or audio_chunk.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio_chunk, dtype=np.float64))))


def rms_to_dbfs(rms_value: float) -> float:
    """
    Convert linear RMS value [0.0, 1.0] to decibels relative to full scale (dBFS).
    """
    if rms_value <= 1e-7:
        return -100.0
    return float(20.0 * np.log10(rms_value))


def create_meter_bar(rms_value: float, length: int = 10) -> str:
    """
    Generate an ASCII visual volume bar for terminal telemetry.
    """
    scaled = min(1.0, rms_value * 3.0)
    filled_length = int(np.clip(scaled, 0.0, 1.0) * length)
    return "#" * filled_length + "-" * (length - filled_length)


class DualAudioIngestion:
    """
    Manages concurrent ingestion of microphone and speaker loopback audio streams.
    """

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        chunk_samples: int = DEFAULT_CHUNK_SAMPLES,
        queue_maxsize: int = 10,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_samples = chunk_samples
        self.queue_maxsize = queue_maxsize

        self.running = threading.Event()
        self.mic_queue: queue.Queue = queue.Queue(maxsize=queue_maxsize)
        self.spk_queue: queue.Queue = queue.Queue(maxsize=queue_maxsize)

        # PyAudio components
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        self.mic_stream: Optional[pyaudio.Stream] = None
        self.mic_device_index: Optional[int] = None
        self.mic_is_fallback: bool = False

        # SoundCard components
        self.loopback_mic: Optional[sc.Microphone] = None
        self.speaker_name: str = "Unknown"

        # Worker threads
        self.mic_thread: Optional[threading.Thread] = None
        self.spk_thread: Optional[threading.Thread] = None

    def initialize_devices(self) -> None:
        """Discover and validate audio input and output devices."""
        logger.info("Initializing audio hardware interfaces...")

        # 1. Initialize PyAudio for Microphone
        self.pyaudio_instance = pyaudio.PyAudio()
        try:
            default_mic_info = self.pyaudio_instance.get_default_input_device_info()
            self.mic_device_index = default_mic_info.get("index")
            self.mic_device_info = default_mic_info
            logger.info(
                f"Default Microphone: [{self.mic_device_index}] {default_mic_info.get('name')}"
            )
        except Exception as e:
            logger.warning(f"Default input device query returned: {e}")
            # Scan across all host APIs for candidate input devices
            candidate_index = None
            for i in range(self.pyaudio_instance.get_device_count()):
                dev = self.pyaudio_instance.get_device_info_by_index(i)
                if dev.get("maxInputChannels", 0) > 0:
                    candidate_index = i
                    break
            self.mic_device_index = candidate_index
            if self.mic_device_index is not None:
                dev_info = self.pyaudio_instance.get_device_info_by_index(self.mic_device_index)
                self.mic_device_info = dev_info
                logger.info(f"Using candidate input device: [{self.mic_device_index}] {dev_info.get('name')}")
            else:
                logger.warning("No physical microphone device found; running in simulated input mode for microphone channel.")
                self.mic_device_info = {"name": "Simulated Microphone", "index": -1}
                self.mic_is_fallback = True

        # 2. Initialize SoundCard for Speaker Loopback
        try:
            default_spk = sc.default_speaker()
            self.speaker_name = default_spk.name
            logger.info(f"Default Speaker: {self.speaker_name}")

            # Locate corresponding loopback microphone in soundcard
            loopback_mics = [m for m in sc.all_microphones(include_loopback=True) if m.isloopback]
            if loopback_mics:
                matching = [m for m in loopback_mics if default_spk.name in m.name]
                self.loopback_mic = matching[0] if matching else loopback_mics[0]
            else:
                self.loopback_mic = sc.get_microphone(id=str(default_spk.name), include_loopback=True)

            logger.info(f"Speaker Loopback Interface: {self.loopback_mic.name}")
        except Exception as e:
            logger.error(f"Failed to initialize speaker loopback device: {e}")
            raise

    def _mic_capture_worker(self) -> None:
        """
        Background worker thread: Captures microphone audio using PyAudio.
        If no physical hardware endpoint is connected, generates synchronized frames.
        """
        logger.info("Microphone capture thread started.")
        opened_stream = False

        if not self.mic_is_fallback and self.pyaudio_instance is not None:
            try:
                self.mic_stream = self.pyaudio_instance.open(
                    format=pyaudio.paFloat32,
                    channels=MIC_CHANNELS,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=self.mic_device_index,
                    frames_per_buffer=self.chunk_samples,
                )
                opened_stream = True
                logger.info("PyAudio microphone stream successfully opened.")
            except Exception as e:
                logger.warning(
                    f"Direct PyAudio stream open failed ({e}). Falling back to synchronized silence generator for Mic."
                )
                self.mic_is_fallback = True

        frame_duration = self.chunk_samples / self.sample_rate

        while self.running.is_set():
            t_start = time.time()
            mic_array = None

            if opened_stream and self.mic_stream is not None:
                try:
                    raw_data = self.mic_stream.read(
                        self.chunk_samples,
                        exception_on_overflow=False,
                    )
                    mic_array = np.frombuffer(raw_data, dtype=DTYPE)
                except Exception as e:
                    if self.running.is_set():
                        logger.error(f"Error reading PyAudio stream: {e}")
                    mic_array = None

            if mic_array is None:
                # Synchronized silence generator for simulated/unplugged mic environments
                mic_array = np.zeros(self.chunk_samples, dtype=DTYPE)
                elapsed = time.time() - t_start
                sleep_time = max(0.0, frame_duration - elapsed)
                time.sleep(sleep_time)

            # Ensure strict shape and float32 dtype
            if mic_array.shape[0] != self.chunk_samples:
                mic_array = np.resize(mic_array, self.chunk_samples).astype(DTYPE)

            # Enqueue chunk
            try:
                self.mic_queue.put(mic_array, block=True, timeout=1.0)
            except queue.Full:
                try:
                    _ = self.mic_queue.get_nowait()
                    self.mic_queue.put_nowait(mic_array)
                except queue.Empty:
                    pass

        logger.info("Microphone capture thread stopped.")

    def _speaker_capture_worker(self) -> None:
        """
        Background worker thread: Captures speaker loopback audio using SoundCard.
        Captures in stereo (channels=2) to satisfy WASAPI, then downmixes to mono.
        """
        logger.info("Speaker loopback capture thread started.")
        try:
            with self.loopback_mic.recorder(
                samplerate=self.sample_rate,
                channels=SPEAKER_CHANNELS,
                blocksize=self.chunk_samples,
            ) as spk_recorder:
                logger.info("SoundCard loopback recorder opened successfully.")
                while self.running.is_set():
                    try:
                        # Record stereo chunk: shape (chunk_samples, 2), float32
                        stereo_chunk = spk_recorder.record(numframes=self.chunk_samples)

                        # Downmix Stereo -> Mono (average across channels)
                        mono_chunk = np.mean(stereo_chunk, axis=1, dtype=np.float32)

                        # Ensure float32 and shape (chunk_samples,)
                        if mono_chunk.dtype != np.float32:
                            mono_chunk = mono_chunk.astype(np.float32)

                        # Enqueue chunk
                        try:
                            self.spk_queue.put(mono_chunk, block=True, timeout=1.0)
                        except queue.Full:
                            try:
                                _ = self.spk_queue.get_nowait()
                                self.spk_queue.put_nowait(mono_chunk)
                            except queue.Empty:
                                pass

                    except Exception as e:
                        if self.running.is_set():
                            logger.error(f"Error during speaker loopback capture: {e}")
                        break

        except Exception as e:
            logger.error(f"Failed to open speaker loopback stream: {e}")
        finally:
            logger.info("Speaker loopback capture thread stopped.")

    def start(self) -> None:
        """Start concurrent audio capture streams."""
        if self.running.is_set():
            logger.warning("Audio ingestion service is already running.")
            return

        self.initialize_devices()
        self.running.set()

        self.mic_thread = threading.Thread(
            target=self._mic_capture_worker,
            name="MicCaptureWorker",
            daemon=True,
        )
        self.spk_thread = threading.Thread(
            target=self._speaker_capture_worker,
            name="SpkCaptureWorker",
            daemon=True,
        )

        self.mic_thread.start()
        self.spk_thread.start()
        logger.info("Dual audio ingestion threads launched successfully.")

    def read_chunk(self, timeout: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Retrieve synchronized audio chunks from both Mic and Speaker streams.

        Args:
            timeout: Maximum wait time in seconds for each queue.

        Returns:
            Tuple[np.ndarray, np.ndarray]: (mic_chunk, spk_chunk)
            Both chunks are 1D arrays of shape (15600,) with dtype float32 in [-1.0, 1.0].
        """
        # Drain backlog if one queue drifted ahead due to OS thread scheduling
        while self.mic_queue.qsize() > 3:
            try:
                _ = self.mic_queue.get_nowait()
            except queue.Empty:
                break
        while self.spk_queue.qsize() > 3:
            try:
                _ = self.spk_queue.get_nowait()
            except queue.Empty:
                break

        mic_chunk = self.mic_queue.get(block=True, timeout=timeout)
        spk_chunk = self.spk_queue.get(block=True, timeout=timeout)

        # Assert data constraints
        assert mic_chunk.dtype == np.float32, f"Mic dtype {mic_chunk.dtype} is not float32"
        assert spk_chunk.dtype == np.float32, f"Spk dtype {spk_chunk.dtype} is not float32"
        assert mic_chunk.shape == (self.chunk_samples,), f"Mic shape {mic_chunk.shape} != ({self.chunk_samples},)"
        assert spk_chunk.shape == (self.chunk_samples,), f"Spk shape {spk_chunk.shape} != ({self.chunk_samples},)"

        return mic_chunk, spk_chunk

    def stop(self) -> None:
        """Gracefully stop all capture streams and release audio resources."""
        if not self.running.is_set():
            return

        logger.info("Stopping dual audio ingestion...")
        self.running.clear()

        # Join worker threads
        if self.mic_thread and self.mic_thread.is_alive():
            self.mic_thread.join(timeout=1.5)
        if self.spk_thread and self.spk_thread.is_alive():
            self.spk_thread.join(timeout=1.5)

        # Close PyAudio stream & terminate instance
        if self.mic_stream:
            try:
                self.mic_stream.stop_stream()
                self.mic_stream.close()
            except Exception as e:
                logger.debug(f"Error closing mic stream: {e}")
            self.mic_stream = None

        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except Exception as e:
                logger.debug(f"Error terminating PyAudio: {e}")
            self.pyaudio_instance = None

        logger.info("Audio ingestion resources released cleanly.")

    def __enter__(self) -> "DualAudioIngestion":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


def run_monitoring_loop(
    max_chunks: Optional[int] = None,
    confidence_thresh: float = CONFIDENCE_THRESHOLD,
) -> None:
    """
    Run the continuous ingestion loop with real-time YAMNet AI classification,
    temporal rolling buffer validation, and side-by-side terminal telemetry.

    Args:
        max_chunks: Optional maximum number of chunks to process before exiting.
        confidence_thresh: Threshold for validation gate hazard classification.
    """
    # 1. Initialize AI Model and Temporal Buffer
    classifier = YAMNetClassifier()
    classifier.load_model()

    temporal_buffer = TemporalHazardBuffer(
        maxlen=5,
        threshold=confidence_thresh,
        required_frames=REQUIRED_CONSECUTIVE_FRAMES,
    )

    # 2. Initialize Ingestion Engine
    ingestion = DualAudioIngestion(
        sample_rate=DEFAULT_SAMPLE_RATE,
        chunk_samples=DEFAULT_CHUNK_SAMPLES,
    )

    # Register clean shutdown signal handlers
    def handle_signal(sig, frame):
        logger.info("Termination signal received. Exiting...")
        ingestion.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print("\n" + "=" * 98)
    print(f"{'ENTERPRISE AUDIO DETECTION SYSTEM - MILESTONE 2':^98}")
    print(f"{'Google YAMNet Edge AI Classification + Rolling Temporal Hazard Validation':^98}")
    print(f"Sample Rate: {DEFAULT_SAMPLE_RATE} Hz | Chunk: {DEFAULT_CHUNK_SAMPLES} samples ({DEFAULT_CHUNK_SAMPLES / DEFAULT_SAMPLE_RATE:.3f}s) | Buffer: 5 frames (>=3 frames > {int(confidence_thresh*100)}%)")
    print("=" * 98)
    print(f"{'Chunk':<7} | {'Time':<8} | {'Microphone AI Prediction':<38} | {'Speaker Volume (RMS)':<25} | {'Gate'}")
    print(f"{'-'*7}-+-{'-'*8}-+-{'-'*38}-+-{'-'*25}-+-{'-'*6}")

    chunk_idx = 0
    with ingestion:
        try:
            while ingestion.running.is_set():
                if max_chunks is not None and chunk_idx >= max_chunks:
                    logger.info(f"Reached specified limit of {max_chunks} chunks.")
                    break

                try:
                    mic_chunk, spk_chunk = ingestion.read_chunk(timeout=3.0)
                except queue.Empty:
                    logger.warning("Queue timeout: Waiting for audio frames...")
                    continue

                chunk_idx += 1

                # 1. Run YAMNet AI inference on Microphone audio
                top_class, top_score, target_scores, _ = classifier.predict(mic_chunk)

                # 2. Append to rolling temporal buffer & evaluate gate
                temporal_buffer.append(chunk_idx, top_class, top_score, target_scores)
                detected_hazards = temporal_buffer.evaluate_gate()

                # 3. Calculate Speaker loopback RMS
                spk_rms = calculate_rms(spk_chunk)
                spk_db = rms_to_dbfs(spk_rms)
                spk_bar = create_meter_bar(spk_rms, length=8)

                timestamp_str = time.strftime("%H:%M:%S")

                # Format display columns
                ai_display = f"{top_class[:26]:<26} ({top_score*100:>4.1f}%)"
                spk_display = f"RMS: {spk_rms:0.4f} [{spk_bar}]"
                gate_status = "ALERT" if detected_hazards else "OK"

                print(
                    f"#{chunk_idx:<6} | {timestamp_str:<8} | {ai_display:<38} | {spk_display:<25} | {gate_status}",
                    flush=True,
                )

                # 4. If Hazard Gate triggers, print massive visible alert
                if detected_hazards:
                    for hazard in detected_hazards:
                        alert_banner = temporal_buffer.format_alert_banner(hazard)
                        print(alert_banner, flush=True)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
        finally:
            print("-" * 98)
            print(f"Total Chunks Processed: {chunk_idx}")
            print("=" * 98 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Milestone 2: Dual Audio Ingestion with YAMNet & Temporal Buffer"
    )
    parser.add_argument(
        "--num-chunks",
        type=int,
        default=None,
        help="Number of chunks to capture before exiting (default: infinite until Ctrl+C)",
    )
    parser.add_argument(
        "--confidence-thresh",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help=f"Confidence threshold for hazard validation gate (default: {CONFIDENCE_THRESHOLD})",
    )
    args = parser.parse_args()

    run_monitoring_loop(
        max_chunks=args.num_chunks,
        confidence_thresh=args.confidence_thresh,
    )


if __name__ == "__main__":
    main()
