"""
YAMNet Audio Classification and Temporal Hazard Buffer Module - Milestone 2

Integrates Google's pre-trained YAMNet model (via TensorFlow Hub) for real-time
acoustic inference on 16kHz float32 mono audio chunks, coupled with a 5-frame
rolling temporal buffer to suppress transient false positives.
"""

import collections
import csv
import logging
import os
import urllib.request
from typing import Dict, List, Optional, Tuple

import numpy as np

# Configure logging
logger = logging.getLogger("YAMNetClassifier")

# Target Threat Categories
WARNING_SOUNDS: List[str] = ["Glass", "Shatter", "Crying baby"]
CRITICAL_SOUNDS: List[str] = ["Gunshot, gunfire", "Fire alarm", "Explosion"]
CONFIDENCE_THRESHOLD: float = 0.85
REQUIRED_CONSECUTIVE_FRAMES: int = 3
BUFFER_MAX_LEN: int = 5

# URL for YAMNet Class Map if offline/fallback needed
YAMNET_CLASS_MAP_URL: str = (
    "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"
)
YAMNET_HUB_URL: str = "https://tfhub.dev/google/yamnet/1"


class YAMNetClassifier:
    """
    Wraps TensorFlow Hub Google YAMNet model for inference on 16kHz float32 audio chunks.
    """

    def __init__(self, model_url: str = YAMNET_HUB_URL) -> None:
        self.model_url = model_url
        self.model = None
        self.class_names: List[str] = []
        self.target_class_indices: Dict[str, List[int]] = {}
        self._is_loaded = False

    def load_model(self) -> None:
        """Load YAMNet model from TensorFlow Hub and initialize class mapping."""
        if self._is_loaded:
            return

        logger.info(f"Loading Google YAMNet model from {self.model_url}...")
        # Suppress TensorFlow verbose C++ warnings
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
        import tensorflow as tf
        import tensorflow_hub as hub

        # Load YAMNet model
        self.model = hub.load(self.model_url)
        logger.info("YAMNet model loaded successfully.")

        # Load class map
        self._load_class_map()
        self._resolve_target_classes()
        self._is_loaded = True

    def _load_class_map(self) -> None:
        """Extract or download class names mapping (0-520)."""
        class_map_path = None

        # 1. Check if model provides class map path
        try:
            if hasattr(self.model, "class_map_path"):
                raw_path = self.model.class_map_path().numpy()
                if isinstance(raw_path, bytes):
                    class_map_path = raw_path.decode("utf-8")
                else:
                    class_map_path = str(raw_path)
                logger.info(f"Found model class map at: {class_map_path}")
        except Exception as e:
            logger.debug(f"Could not retrieve class_map_path directly from model: {e}")

        # 2. If not found or inaccessible, use local cached CSV or download
        if not class_map_path or not os.path.exists(class_map_path):
            local_csv = os.path.join(os.path.dirname(__file__), "yamnet_class_map.csv")
            if not os.path.exists(local_csv):
                logger.info("Downloading yamnet_class_map.csv...")
                try:
                    urllib.request.urlretrieve(YAMNET_CLASS_MAP_URL, local_csv)
                except Exception as e:
                    logger.error(f"Failed to download yamnet class map: {e}")
                    raise
            class_map_path = local_csv

        # Parse CSV
        self.class_names = []
        with open(class_map_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # skip header: index,mid,display_name
            for row in reader:
                if len(row) >= 3:
                    self.class_names.append(row[2].strip('"'))
                elif len(row) == 2:
                    self.class_names.append(row[1].strip('"'))

        logger.info(f"Loaded {len(self.class_names)} YAMNet acoustic classes.")

    def _resolve_target_classes(self) -> None:
        """Map target sound names (WARNING & CRITICAL) to YAMNet class index lists."""
        all_targets = WARNING_SOUNDS + CRITICAL_SOUNDS
        self.target_class_indices = {}

        for target in all_targets:
            target_lower = target.lower()
            matching_indices = []
            for idx, name in enumerate(self.class_names):
                name_lower = name.lower()
                # Check exact match or substring match (e.g. 'crying baby' in 'Baby cry, infant cry' or 'Crying, sobbing')
                if name_lower == target_lower:
                    matching_indices.append(idx)
                elif target_lower in name_lower:
                    matching_indices.append(idx)
                elif target_lower == "crying baby" and any(k in name_lower for k in ["baby cry", "crying", "infant cry"]):
                    matching_indices.append(idx)
                elif target_lower == "shatter" and any(k in name_lower for k in ["shatter", "glass", "smash"]):
                    matching_indices.append(idx)
                elif target_lower == "glass" and "glass" in name_lower:
                    matching_indices.append(idx)

            self.target_class_indices[target] = matching_indices
            matched_names = [self.class_names[i] for i in matching_indices]
            logger.info(f"Target '{target}' mapped to indices: {matching_indices} ({matched_names})")

    def predict(self, audio_chunk: np.ndarray) -> Tuple[str, float, Dict[str, float], np.ndarray]:
        """
        Run YAMNet inference on a 16kHz float32 mono audio chunk.

        Args:
            audio_chunk: 1D numpy array of float32 samples in [-1.0, 1.0]

        Returns:
            Tuple:
              - top_class (str): Display name of top predicted class
              - top_score (float): Confidence score of top predicted class [0.0, 1.0]
              - target_scores (Dict[str, float]): Scores for each target sound category
              - mean_scores (np.ndarray): Full 521-class probability distribution
        """
        if not self._is_loaded:
            self.load_model()

        # Ensure float32 1D numpy array
        waveform = audio_chunk.astype(np.float32)
        if waveform.ndim > 1:
            waveform = waveform.flatten()

        # YAMNet inference: returns (scores, embeddings, spectrogram)
        scores, _, _ = self.model(waveform)
        # Average frame scores across the 0.975s chunk window
        mean_scores = np.mean(scores.numpy(), axis=0)

        # Top prediction
        top_idx = int(np.argmax(mean_scores))
        top_class = self.class_names[top_idx] if top_idx < len(self.class_names) else f"Class_{top_idx}"
        top_score = float(mean_scores[top_idx])

        # Target scores
        target_scores: Dict[str, float] = {}
        for target, indices in self.target_class_indices.items():
            if indices:
                # Take maximum score among matching ontology categories
                target_score = float(np.max(mean_scores[indices]))
            else:
                target_score = 0.0
            target_scores[target] = target_score

        return top_class, top_score, target_scores, mean_scores


class TemporalHazardBuffer:
    """
    Rolling temporal buffer (deque maxlen=5) implementing the validation gate
    to suppress transient acoustic noise and validate persistent hazards.
    """

    def __init__(
        self,
        maxlen: int = BUFFER_MAX_LEN,
        threshold: float = CONFIDENCE_THRESHOLD,
        required_frames: int = REQUIRED_CONSECUTIVE_FRAMES,
    ) -> None:
        self.maxlen = maxlen
        self.threshold = threshold
        self.required_frames = required_frames
        self.buffer = collections.deque(maxlen=maxlen)

    def append(
        self,
        chunk_idx: int,
        top_class: str,
        top_score: float,
        target_scores: Dict[str, float],
    ) -> None:
        """Add a frame inference result to the rolling buffer."""
        record = {
            "chunk_idx": chunk_idx,
            "top_class": top_class,
            "top_score": top_score,
            "target_scores": target_scores,
        }
        self.buffer.append(record)

    def evaluate_gate(self) -> List[Dict[str, any]]:
        """
        Evaluate the validation gate across all frames in the buffer.

        Condition:
          If a specific target class in WARNING_SOUNDS or CRITICAL_SOUNDS has
          confidence > threshold in at least required_frames (>= 3 out of 5),
          return hazard detection details.

        Returns:
            List of detected hazard events:
            [
              {
                "tier": "CRITICAL HAZARD" | "WARNING HAZARD",
                "class_name": str,
                "max_confidence": float,
                "avg_confidence": float,
                "count": int,
                "total_frames": int
              }
            ]
        """
        detected_hazards = []
        if not self.buffer:
            return detected_hazards

        total_frames = len(self.buffer)
        all_targets = [
            ("CRITICAL HAZARD", c) for c in CRITICAL_SOUNDS
        ] + [
            ("WARNING HAZARD", w) for w in WARNING_SOUNDS
        ]

        for tier, target in all_targets:
            # Count frames where confidence exceeds threshold
            frame_scores = [
                frame["target_scores"].get(target, 0.0)
                for frame in self.buffer
            ]
            qualifying_scores = [s for s in frame_scores if s > self.threshold]
            qualifying_count = len(qualifying_scores)

            if qualifying_count >= self.required_frames:
                detected_hazards.append({
                    "tier": tier,
                    "class_name": target,
                    "max_confidence": max(qualifying_scores),
                    "avg_confidence": sum(qualifying_scores) / qualifying_count,
                    "count": qualifying_count,
                    "total_frames": total_frames,
                })

        return detected_hazards

    def format_alert_banner(self, hazard: Dict[str, any]) -> str:
        """Generate a massive, highly visible hazard alert banner for the console."""
        tier = hazard["tier"]
        class_name = hazard["class_name"]
        max_conf_pct = hazard["max_confidence"] * 100.0
        avg_conf_pct = hazard["avg_confidence"] * 100.0
        count = hazard["count"]
        total = hazard["total_frames"]

        banner_width = 86
        title_text = f"[!] [{tier}] DETECTED: {class_name.upper()} [!]"
        details_text = f"Confidence: {max_conf_pct:.1f}% (Avg: {avg_conf_pct:.1f}%) | Consistency: {count}/{total} frames in temporal buffer"

        border_char = "=" if "CRITICAL" in tier else "-"
        box = [
            "\n+" + border_char * (banner_width - 2) + "+",
            "| " + f"{title_text:^{banner_width - 4}}" + " |",
            "| " + f"{details_text:^{banner_width - 4}}" + " |",
            "+" + border_char * (banner_width - 2) + "+\n",
        ]
        return "\n".join(box)
