"""
Acoustic Firewall Module - Milestone 3

Eliminates false positives caused by laptop/device speaker media playback (e.g. YouTube,
movies, music, gaming) through dual-stream acoustic echo correlation and simultaneous
target classification.

Suppression Decision Logic:
- Analyzes simultaneous Microphone and Speaker Loopback chunks.
- Computes normalized cross-correlation (rho) via FFT.
- If Mic detects a hazard (Fire Alarm, Gunshot, Explosion, Glass Shatter, Baby Cry) AND
  Speaker loopback is actively playing correlated audio or the same hazard sound:
    -> Flags event as SUPPRESSED_MEDIA_PLAYBACK (False Positive prevented!)
    -> Blocks temporal hazard buffer from incrementing.
- If Mic detects a hazard BUT Speaker loopback is silent/uncorrelated:
    -> Flags event as CONFIRMED_AMBIENT_HAZARD (Real-world threat)
    -> Temporal buffer increments and validates sustained hazard.
"""

import logging
from typing import Dict, Optional, Tuple

import numpy as np
from scipy import signal

from yamnet_classifier import (
    CONFIDENCE_THRESHOLD,
    CRITICAL_SOUNDS,
    WARNING_SOUNDS,
    YAMNetClassifier,
)

logger = logging.getLogger("AcousticFirewall")

# Threshold Constants
SPEAKER_ACTIVE_RMS_THRESHOLD: float = 0.005  # -46 dBFS minimum for active media
CROSS_CORRELATION_THRESHOLD: float = 0.35   # Normalized correlation threshold for acoustic echo
SPEAKER_HAZARD_THRESHOLD: float = 0.40      # YAMNet target confidence threshold on loopback


def compute_normalized_cross_correlation(
    sig1: np.ndarray,
    sig2: np.ndarray,
) -> float:
    """
    Compute maximum normalized cross-correlation between two 1D audio signals.

    Args:
        sig1: Microphone 1D float32 array
        sig2: Speaker Loopback 1D float32 array

    Returns:
        float: Normalized cross-correlation coefficient in [0.0, 1.0]
    """
    norm1 = np.linalg.norm(sig1)
    norm2 = np.linalg.norm(sig2)

    if norm1 < 1e-6 or norm2 < 1e-6:
        return 0.0

    # FFT-based cross correlation (O(N log N))
    correlation = signal.correlate(sig1, sig2, mode="full", method="fft")
    max_corr = np.max(np.abs(correlation))
    normalized_corr = float(max_corr / (norm1 * norm2))

    return min(1.0, normalized_corr)


class AcousticFirewall:
    """
    Intelligent Acoustic Firewall inspecting dual streams to suppress media false alarms.
    """

    def __init__(
        self,
        classifier: YAMNetClassifier,
        spk_active_thresh: float = SPEAKER_ACTIVE_RMS_THRESHOLD,
        cross_corr_thresh: float = CROSS_CORRELATION_THRESHOLD,
        spk_hazard_thresh: float = SPEAKER_HAZARD_THRESHOLD,
    ) -> None:
        self.classifier = classifier
        self.spk_active_thresh = spk_active_thresh
        self.cross_corr_thresh = cross_corr_thresh
        self.spk_hazard_thresh = spk_hazard_thresh

        self.total_evaluations: int = 0
        self.suppressed_count: int = 0
        self.confirmed_hazard_count: int = 0

    def evaluate_streams(
        self,
        mic_chunk: np.ndarray,
        spk_chunk: np.ndarray,
        mic_top_class: str,
        mic_top_score: float,
        mic_target_scores: Dict[str, float],
        spk_rms: float,
    ) -> Dict[str, any]:
        """
        Evaluate simultaneous Mic and Speaker streams through the Acoustic Firewall.

        Args:
            mic_chunk: 1D float32 mono array (15600 samples)
            spk_chunk: 1D float32 mono array (15600 samples)
            mic_top_class: Top classification from YAMNet for Mic
            mic_top_score: Confidence for top Mic class
            mic_target_scores: Dict of scores for WARNING/CRITICAL target sounds
            spk_rms: RMS volume level of Speaker loopback

        Returns:
            Dict containing firewall decision telemetry:
            {
                "status": "CLEAR" | "SUPPRESSED_MEDIA_PLAYBACK" | "CONFIRMED_AMBIENT_HAZARD",
                "is_suppressed": bool,
                "hazard_detected": bool,
                "detected_target": Optional[str],
                "target_tier": Optional[str],
                "mic_confidence": float,
                "spk_confidence": float,
                "cross_correlation": float,
                "spk_active": bool,
                "reason": str
            }
        """
        self.total_evaluations += 1

        # Check if Mic detects any target hazard
        all_targets = [
            ("CRITICAL", c) for c in CRITICAL_SOUNDS
        ] + [
            ("WARNING", w) for w in WARNING_SOUNDS
        ]

        detected_target = None
        target_tier = None
        max_mic_hazard_score = 0.0

        for tier, target in all_targets:
            score = mic_target_scores.get(target, 0.0)
            if score > max_mic_hazard_score:
                max_mic_hazard_score = score
            if score >= CONFIDENCE_THRESHOLD:
                detected_target = target
                target_tier = tier
                break

        # If top class itself is in target classes even if individual threshold varied
        if not detected_target:
            for tier, target in all_targets:
                if target.lower() in mic_top_class.lower() and mic_top_score >= 0.70:
                    detected_target = target
                    target_tier = tier
                    max_mic_hazard_score = mic_top_score
                    break

        hazard_detected = detected_target is not None

        # Compute cross-correlation
        cross_corr = compute_normalized_cross_correlation(mic_chunk, spk_chunk)
        spk_active = spk_rms >= self.spk_active_thresh

        spk_top_class = "Silence"
        spk_top_score = 0.0
        spk_target_score = 0.0

        # If loopback is active or a hazard was detected in mic, run YAMNet on speaker chunk
        if spk_active or hazard_detected:
            try:
                (
                    spk_top_class,
                    spk_top_score,
                    spk_target_scores,
                    _,
                ) = self.classifier.predict(spk_chunk)
                if detected_target:
                    spk_target_score = spk_target_scores.get(detected_target, 0.0)
            except Exception as e:
                logger.debug(f"Speaker classification skipped: {e}")

        # Suppression Decision Gate
        is_suppressed = False
        status = "CLEAR"
        reason = "Acoustic baseline clear"

        if hazard_detected:
            # Condition 1: Speaker is playing the same hazard category
            spk_playing_hazard = spk_active and (
                spk_target_score >= self.spk_hazard_thresh
                or (detected_target and detected_target.lower() in spk_top_class.lower())
            )

            # Condition 2: High cross-correlation (acoustic echo of media stream)
            spk_correlated = spk_active and (cross_corr >= self.cross_corr_thresh)

            if spk_playing_hazard or spk_correlated:
                is_suppressed = True
                status = "SUPPRESSED_MEDIA_PLAYBACK"
                self.suppressed_count += 1
                if spk_playing_hazard:
                    reason = f"Speaker loopback contains '{detected_target}' ({spk_target_score*100:.1f}%)"
                else:
                    reason = f"High cross-correlation ({cross_corr:.2f}) with active speaker stream"
                logger.info(
                    f"Acoustic Firewall [SUPPRESSED]: {detected_target} prevented from media playback. Reason: {reason}"
                )
            else:
                is_suppressed = False
                status = "CONFIRMED_AMBIENT_HAZARD"
                self.confirmed_hazard_count += 1
                reason = f"Real-world ambient acoustic threat: '{detected_target}' ({max_mic_hazard_score*100:.1f}%)"
                logger.warning(
                    f"Acoustic Firewall [CONFIRMED]: {target_tier} '{detected_target}' detected in room!"
                )
        else:
            status = "CLEAR"
            reason = "Normal acoustic background"

        return {
            "status": status,
            "is_suppressed": is_suppressed,
            "hazard_detected": hazard_detected,
            "detected_target": detected_target,
            "target_tier": target_tier,
            "mic_confidence": float(max_mic_hazard_score if hazard_detected else mic_top_score),
            "spk_confidence": float(spk_target_score),
            "cross_correlation": float(cross_corr),
            "spk_active": bool(spk_active),
            "spk_top_class": spk_top_class,
            "reason": reason,
        }
