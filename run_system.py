"""
Echo — Acoustic Intelligence Platform Launcher

Orchestrates:
1. SQLite Database Initialization (users, contacts, settings).
2. Hardware Dual-Audio Ingestion (Microphone + Speaker Loopback).
3. Google YAMNet Edge AI Classifier.
4. Acoustic Firewall Media Suppression Engine.
5. 5-Frame Rolling Temporal Buffer & Validation Gate.
6. Security Agent with Policy Enforcement, Refractory Debouncing, and Telegram Bot Hunt-Group.
7. FastAPI Auth Server + WebSocket Real-Time Dashboard (http://localhost:8000).
"""

import argparse
import asyncio
import collections
import logging
import queue
import signal
import sys
import threading
import time
from typing import Optional

import numpy as np
import uvicorn

from acoustic_firewall import AcousticFirewall
from agent_orchestrator import AntigravitySecurityAgent
from audio_ingestion import (
    DEFAULT_CHUNK_SAMPLES,
    DEFAULT_SAMPLE_RATE,
    DualAudioIngestion,
    calculate_rms,
    rms_to_dbfs,
)
from server import ENGINE_STATE, app, manager
from telegram_manager import TelegramHuntGroupManager
from yamnet_classifier import (
    CONFIDENCE_THRESHOLD,
    CRITICAL_SOUNDS,
    REQUIRED_CONSECUTIVE_FRAMES,
    WARNING_SOUNDS,
    TemporalHazardBuffer,
    YAMNetClassifier,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("EchoLauncher")

# Main Asyncio Event Loop reference for WebSocket broadcasting
main_event_loop: Optional[asyncio.AbstractEventLoop] = None


def audio_ai_pipeline_worker(
    ingestion: DualAudioIngestion,
    classifier: YAMNetClassifier,
    firewall: AcousticFirewall,
    temporal_buffer: TemporalHazardBuffer,
    agent: AntigravitySecurityAgent,
    sim_queue: queue.Queue,
    stop_event: threading.Event,
    confidence_thresh: float,
) -> None:
    """
    Background worker executing continuous dual-stream audio capture,
    edge AI classification, acoustic firewall evaluation, Antigravity Agent policy dispatch,
    and WebSocket telemetry broadcast.
    """
    logger.info("Audio AI Pipeline worker thread started.")
    chunk_idx = 0

    # Rolling window of raw audio arrays (5 frames = ~4.875s) for incident .wav export
    raw_audio_buffer = collections.deque(maxlen=5)

    with ingestion:
        while not stop_event.is_set():
            try:
                # 0. Check mic toggle — if paused, emit silence telemetry
                if not ENGINE_STATE.get("mic_enabled", True):
                    time.sleep(0.975)  # Match chunk cadence
                    chunk_idx += 1
                    ENGINE_STATE["total_chunks"] = chunk_idx
                    silence_packet = {
                        "chunk_index": chunk_idx,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "mic_enabled": False,
                        "mic_rms": 0.0, "spk_rms": 0.0, "mic_dbfs": -96.0, "spk_dbfs": -96.0,
                        "mic_device_name": "Paused", "speaker_name": "Paused",
                        "top_prediction": {"class_name": "Paused", "confidence": 0.0},
                        "target_scores": {}, "firewall": {"cross_correlation": 0.0, "is_suppressed": False, "suppressed_total": 0, "confirmed_total": 0},
                        "temporal_buffer": [], "gate_qualifying_count": 0,
                        "alert_state": "PAUSED", "active_hazard": None,
                        "agent_state": agent.get_agent_state() if agent else {},
                    }
                    if main_event_loop and main_event_loop.is_running():
                        asyncio.run_coroutine_threadsafe(manager.broadcast(silence_packet), main_event_loop)
                    continue

                # 1. Read simultaneous audio chunks
                mic_chunk, spk_chunk = ingestion.read_chunk(timeout=2.0)

                # Check if simulation queue has an injected test waveform
                try:
                    sim_chunk = sim_queue.get_nowait()
                    if sim_chunk is not None:
                        mic_chunk = sim_chunk
                        logger.info("Injected simulated ambient hazard chunk into mic pipeline.")
                except queue.Empty:
                    pass

                chunk_idx += 1
                ENGINE_STATE["total_chunks"] = chunk_idx

                # Cache raw audio chunk in rolling audio buffer
                raw_audio_buffer.append(mic_chunk.copy())
                if len(raw_audio_buffer) > 0:
                    combined_audio = np.concatenate(list(raw_audio_buffer), axis=0)
                    agent.update_latest_audio(combined_audio)

                # 2. Compute loopback & mic RMS metrics
                mic_rms = calculate_rms(mic_chunk)
                spk_rms = calculate_rms(spk_chunk)
                mic_db = rms_to_dbfs(mic_rms)
                spk_db = rms_to_dbfs(spk_rms)

                # 3. Run Google YAMNet AI inference on Microphone chunk
                top_class, top_score, mic_target_scores, _ = classifier.predict(mic_chunk)

                # 4. Evaluate Acoustic Firewall (media suppression check)
                fw_result = firewall.evaluate_streams(
                    mic_chunk=mic_chunk,
                    spk_chunk=spk_chunk,
                    mic_top_class=top_class,
                    mic_top_score=top_score,
                    mic_target_scores=mic_target_scores,
                    spk_rms=spk_rms,
                )

                fw_result["suppressed_total"] = firewall.suppressed_count
                fw_result["confirmed_total"] = firewall.confirmed_hazard_count

                # 5. Update Temporal Buffer
                is_suppressed = fw_result.get("is_suppressed", False)
                if is_suppressed:
                    suppressed_scores = {k: 0.0 for k in mic_target_scores}
                    temporal_buffer.append(
                        chunk_idx=chunk_idx,
                        top_class=top_class,
                        top_score=top_score,
                        target_scores=suppressed_scores,
                    )
                    if temporal_buffer.buffer:
                        temporal_buffer.buffer[-1]["is_suppressed"] = True
                else:
                    temporal_buffer.append(
                        chunk_idx=chunk_idx,
                        top_class=top_class,
                        top_score=top_score,
                        target_scores=mic_target_scores,
                    )
                    if temporal_buffer.buffer:
                        temporal_buffer.buffer[-1]["is_suppressed"] = False

                # 6. Evaluate Validation Gate
                detected_hazards = temporal_buffer.evaluate_gate()

                alert_state = "NORMAL"
                active_hazard = None
                qualifying_count = 0

                if detected_hazards:
                    active_hazard = detected_hazards[0]
                    qualifying_count = active_hazard.get("count", 0)
                    if "CRITICAL" in active_hazard.get("tier", ""):
                        alert_state = "CRITICAL"
                    else:
                        alert_state = "WARNING"

                    # 7. Invoke Antigravity Security Agent (Policy Enforcement & Telegram Escalation)
                    if not is_suppressed:
                        agent_action = agent.dispatch_hazard_event(active_hazard)
                        if agent_action.get("action") == "COOLDOWN_SUPPRESSED":
                            pass
                        elif agent_action.get("action") not in ["COOLDOWN_ACTIVE"]:
                            logger.info(f"Agent Dispatched Action: {agent_action}")

                else:
                    for frame in temporal_buffer.buffer:
                        for target in WARNING_SOUNDS + CRITICAL_SOUNDS:
                            if frame.get("target_scores", {}).get(target, 0.0) >= confidence_thresh:
                                qualifying_count = max(qualifying_count, 1)

                # Get Agent Telemetry State
                agent_telemetry = agent.get_agent_state()

                # 8. Assemble Telemetry Packet
                packet = {
                    "chunk_index": chunk_idx,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "mic_enabled": True,
                    "mic_rms": float(mic_rms),
                    "spk_rms": float(spk_rms),
                    "mic_dbfs": float(mic_db),
                    "spk_dbfs": float(spk_db),
                    "mic_device_name": getattr(ingestion, "mic_device_info", {}).get("name", "Active Microphone") if hasattr(ingestion, "mic_device_info") and ingestion.mic_device_info else "Active Microphone",
                    "speaker_name": getattr(ingestion, "speaker_name", "Default Speaker"),
                    "top_prediction": {
                        "class_name": top_class,
                        "confidence": float(top_score),
                    },
                    "target_scores": {k: float(v) for k, v in mic_target_scores.items()},
                    "firewall": fw_result,
                    "temporal_buffer": [
                        {
                            "slot": i + 1,
                            "chunk_idx": item.get("chunk_idx", 0),
                            "class_name": item.get("top_class", "-"),
                            "confidence": float(item.get("top_score", 0.0)),
                            "is_target": any(
                                item.get("target_scores", {}).get(k, 0.0) >= 0.40
                                for k in WARNING_SOUNDS + CRITICAL_SOUNDS
                            ),
                            "is_suppressed": item.get("is_suppressed", False),
                        }
                        for i, item in enumerate(temporal_buffer.buffer)
                    ],
                    "gate_qualifying_count": qualifying_count,
                    "alert_state": alert_state,
                    "active_hazard": active_hazard,
                    "agent_state": agent_telemetry,
                }

                # 9. Broadcast over WebSocket to connected clients
                if main_event_loop and main_event_loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(packet),
                        main_event_loop,
                    )

                # Terminal telemetry log
                fw_badge = "[SUPPRESSED]" if is_suppressed else ("[THREAT!]" if detected_hazards else "[CLEAR]")
                countdown_info = ""
                if agent_telemetry.get("active_countdown"):
                    cd = agent_telemetry["active_countdown"]
                    countdown_info = f" | [ESCALATING: {cd['remaining_seconds']}s]"

                tg_info = ""
                if agent_telemetry.get("telegram", {}).get("active_alert"):
                    tga = agent_telemetry["telegram"]["active_alert"]
                    tg_info = f" | [TG: {tga['status']}]"

                print(
                    f"#{chunk_idx:<5} | {time.strftime('%H:%M:%S')} | Mic: {top_class[:20]:<20} ({top_score*100:>4.1f}%) | "
                    f"Spk RMS: {spk_rms:0.4f} (rho: {fw_result['cross_correlation']:.2f}) | {fw_badge} | Gate: {alert_state}{countdown_info}{tg_info}",
                    flush=True,
                )

                if detected_hazards and not is_suppressed:
                    for hazard in detected_hazards:
                        print(temporal_buffer.format_alert_banner(hazard), flush=True)

            except queue.Empty:
                continue
            except Exception as e:
                if not stop_event.is_set():
                    logger.error(f"Error in processing loop: {e}", exc_info=True)

    logger.info("Audio AI Pipeline worker thread terminated cleanly.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AegisAudio - Telegram Interactive Hunt-Group Launcher"
    )
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")
    parser.add_argument("--confidence-thresh", type=float, default=CONFIDENCE_THRESHOLD, help="Hazard threshold (default: 0.85)")
    args = parser.parse_args()

    print("\n" + "=" * 96)
    print(f"{'ECHO — ACOUSTIC INTELLIGENCE PLATFORM':^96}")
    print(f"{'Telegram Bot Hunt-Group + Acoustic Firewall + Auth Engine':^96}")
    print(f"Dashboard URL: http://{args.host}:{args.port} | Sample Rate: {DEFAULT_SAMPLE_RATE} Hz | Chunk: {DEFAULT_CHUNK_SAMPLES} samples")
    print("=" * 96 + "\n")

    # 0. Initialize Database
    import database as db_module
    logger.info("Initializing SQLite database...")
    asyncio.get_event_loop().run_until_complete(db_module.init_db()) if not asyncio.get_event_loop().is_running() else None

    # 1. Initialize Subsystems
    logger.info("Initializing Google YAMNet Model...")
    classifier = YAMNetClassifier()
    classifier.load_model()

    logger.info("Initializing Acoustic Firewall...")
    firewall = AcousticFirewall(classifier=classifier)

    logger.info("Initializing 5-Frame Rolling Temporal Buffer...")
    temporal_buffer = TemporalHazardBuffer(
        maxlen=5,
        threshold=args.confidence_thresh,
        required_frames=REQUIRED_CONSECUTIVE_FRAMES,
    )

    logger.info("Initializing Telegram Interactive Hunt-Group Manager...")
    telegram_mgr = TelegramHuntGroupManager()

    logger.info("Initializing Security Agent...")
    agent = AntigravitySecurityAgent(telegram_manager=telegram_mgr)

    logger.info("Initializing Dual Audio Ingestion Engine...")
    ingestion = DualAudioIngestion(
        sample_rate=DEFAULT_SAMPLE_RATE,
        chunk_samples=DEFAULT_CHUNK_SAMPLES,
    )

    sim_queue: queue.Queue = queue.Queue()

    # Save to global engine state for REST APIs
    ENGINE_STATE["ingestion"] = ingestion
    ENGINE_STATE["classifier"] = classifier
    ENGINE_STATE["firewall"] = firewall
    ENGINE_STATE["temporal_buffer"] = temporal_buffer
    ENGINE_STATE["agent"] = agent
    ENGINE_STATE["simulation_queue"] = sim_queue

    # 2. Launch Background Audio AI Processing Thread
    stop_event = threading.Event()
    pipeline_thread = threading.Thread(
        target=audio_ai_pipeline_worker,
        args=(
            ingestion,
            classifier,
            firewall,
            temporal_buffer,
            agent,
            sim_queue,
            stop_event,
            args.confidence_thresh,
        ),
        name="AudioAIPipelineWorker",
        daemon=True,
    )
    pipeline_thread.start()

    # 3. Setup Signal Handlers
    def shutdown_signal_handler(sig, frame):
        logger.info("Shutdown signal received. Stopping services...")
        stop_event.set()
        ingestion.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_signal_handler)
    signal.signal(signal.SIGTERM, shutdown_signal_handler)

    # 4. Start Uvicorn Web Server
    global main_event_loop

    class StandaloneServer(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    config = uvicorn.Config(
        app=app,
        host=args.host,
        port=args.port,
        log_level="warning",
        access_log=False,
    )
    server = StandaloneServer(config=config)

    async def serve():
        global main_event_loop
        main_event_loop = asyncio.get_running_loop()
        # Initialize database tables before serving
        await db_module.init_db()
        await server.serve()

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        stop_event.set()
        ingestion.stop()
        logger.info("Echo System shutdown complete.")


if __name__ == "__main__":
    main()
