"""
Antigravity Security Agent & Native OS Alerting Engine - Milestone 4 & 5 (Telegram Refactor)

An autonomous security agent governing real-time acoustic threat policy enforcement,
Refractory Period debouncing (60s/120s), native OS desktop notifications via notifypy,
Human-in-the-Loop 10-second countdowns, and Telegram Bot Interactive Hunt-Group incident dispatch.
"""

import asyncio
import logging
import os
import threading
import time
from typing import Callable, Dict, List, Optional

import numpy as np
from notifypy import Notify

from telegram_manager import TelegramHuntGroupManager
from yamnet_classifier import CRITICAL_SOUNDS, WARNING_SOUNDS

logger = logging.getLogger("AntigravityAgent")

# Policy Severity & Refractory Period Definitions
TIER_WARNING = "WARNING"
TIER_CRITICAL = "CRITICAL"
WARNING_COOLDOWN: float = 60.0    # 60 seconds refractory period for Warning tier
CRITICAL_COOLDOWN: float = 120.0  # 120 seconds refractory period for Critical tier
COUNTDOWN_DURATION_SECONDS: int = 10


def trigger_os_popup(
    title: str,
    message: str,
    severity: str = TIER_WARNING,
    sound_type: Optional[str] = None,
) -> bool:
    """
    Trigger a native OS desktop notification banner (Windows / macOS / Linux) using notify-py.

    Args:
        title: Notification header title
        message: Notification body description
        severity: "WARNING" or "CRITICAL"
        sound_type: Optional sound effect trigger

    Returns:
        bool: True if dispatched successfully
    """
    try:
        notification = Notify()
        notification.title = title
        notification.message = message
        notification.application_name = "AegisAudio Security Engine"
        notification.urgency = "critical" if severity == TIER_CRITICAL else "normal"

        # Dispatch non-blocking
        notification.send(block=False)
        logger.info(f"Native OS Notification dispatched: [{severity}] {title} - {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch native OS notification: {e}")
        return False


class AntigravitySecurityAgent:
    """
    Autonomous Security Agent enforcing hazard policies, Refractory Period debouncing,
    Human-in-the-Loop countdown workflows, OS desktop alerts, and Telegram Interactive Hunt-Groups.
    """

    SYSTEM_INSTRUCTION = """
    You are the AegisAudio Antigravity Security Agent responsible for real-time acoustic hazard policy enforcement.
    You evaluate validated acoustic events from the YAMNet temporal validation gate, enforce refractory debouncing periods
    (60s for Warning, 120s for Critical) to prevent alert fatigue, manage Human-in-the-Loop escalation countdowns,
    execute native OS desktop notifications, and dispatch autonomous Telegram Bot Interactive Hunt-Groups with 5-second
    audio clips and first-responder inline acknowledgment upon timeout escalation.
    """

    def __init__(
        self,
        on_state_change: Optional[Callable[[], None]] = None,
        telegram_manager: Optional[TelegramHuntGroupManager] = None,
    ) -> None:
        self.on_state_change = on_state_change
        self.lock = threading.Lock()

        # Telegram Interactive Hunt-Group Engine
        self.telegram_manager = telegram_manager or TelegramHuntGroupManager(
            on_status_update=lambda state: self._notify_state_change(),
        )

        # Active countdown & escalation state
        self.active_countdown: Optional[Dict[str, any]] = None
        self.countdown_timer_task: Optional[threading.Timer] = None
        self.current_tier: str = "NORMAL"

        # Cached latest audio samples from buffer for incident audio attachment
        self.latest_audio_samples: Optional[np.ndarray] = None

        # Refractory Period Debouncing State: last_alert_times = {sound_class: timestamp}
        self.last_alert_times: Dict[str, float] = {}

        # Decision & Action Audit Log
        self.action_history: List[Dict[str, any]] = []

    def _notify_state_change(self) -> None:
        if self.on_state_change:
            try:
                self.on_state_change()
            except Exception:
                pass

    def update_latest_audio(self, samples: np.ndarray) -> None:
        """Store the latest audio window so it can be exported to .wav upon escalation."""
        self.latest_audio_samples = samples

    def dispatch_telegram_alert(
        self,
        hazard_type: str,
        audio_samples: Optional[np.ndarray] = None,
        location: Optional[str] = None,
        target_chats: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Tool: Broadcast emergency AI voice briefing, audio clip, and Google Maps live location to Telegram contacts.
        """
        samples = audio_samples if audio_samples is not None else self.latest_audio_samples
        return self.telegram_manager.broadcast_telegram_alert(
            hazard_type=hazard_type,
            audio_samples=samples,
            location=location,
            target_chats=target_chats,
        )

    def dispatch_hazard_event(
        self,
        hazard_event: Dict[str, any],
    ) -> Dict[str, any]:
        """
        Evaluate incoming confirmed hazard from the temporal validation gate with Refractory Period debouncing.

        Args:
            hazard_event:
                {
                    "tier": "CRITICAL HAZARD" | "WARNING HAZARD",
                    "class_name": str,
                    "max_confidence": float,
                    "avg_confidence": float,
                    "count": int,
                    "total_frames": int
                }

        Returns:
            Dict containing agent action response.
        """
        class_name = hazard_event.get("class_name", "Unknown Hazard")
        tier_raw = hazard_event.get("tier", "")
        max_conf = hazard_event.get("max_confidence", 0.95)
        count = hazard_event.get("count", 3)
        total = hazard_event.get("total_frames", 5)

        now = time.time()
        last_time = self.last_alert_times.get(class_name, 0.0)

        # Policy Severity Routing
        is_critical = any(c.lower() == class_name.lower() or class_name.lower() in c.lower() for c in CRITICAL_SOUNDS) or "CRITICAL" in tier_raw
        cooldown_period = CRITICAL_COOLDOWN if is_critical else WARNING_COOLDOWN

        with self.lock:
            # Check Refractory Cooldown
            elapsed = now - last_time
            if elapsed < cooldown_period:
                remaining = int(cooldown_period - elapsed)
                tier_label = TIER_CRITICAL if is_critical else TIER_WARNING
                logger.info(f"[COOLDOWN] Suppressing duplicate {class_name} alert ({remaining}s remaining in {tier_label} refractory period).")
                return {
                    "action": "COOLDOWN_SUPPRESSED",
                    "tier": tier_label,
                    "class_name": class_name,
                    "remaining_seconds": remaining,
                    "popup_sent": False,
                    "message": f"[COOLDOWN] Suppressing duplicate {class_name} alert ({remaining}s remaining)",
                }

            # Update alert timestamp
            self.last_alert_times[class_name] = now

            if is_critical:
                return self._handle_critical_tier(class_name, max_conf, count, total)
            else:
                return self._handle_warning_tier(class_name, max_conf, count, total)

    def _handle_warning_tier(
        self,
        class_name: str,
        confidence: float,
        count: int,
        total: int,
    ) -> Dict[str, any]:
        """Handle Tier 1 Warning (Glass shatter, Crying baby)."""
        self.current_tier = TIER_WARNING
        title = f"⚠️ [WARNING HAZARD] {class_name.upper()}"
        message = f"Acoustic signature detected ({confidence*100:.1f}% conf, {count}/{total} frames). Monitor area."

        # Trigger native desktop popup
        popup_sent = trigger_os_popup(title, message, severity=TIER_WARNING)

        action_record = {
            "timestamp": time.strftime("%H:%M:%S"),
            "tier": TIER_WARNING,
            "class_name": class_name,
            "confidence": confidence,
            "action": "OS_POPUP_DISPATCHED",
            "details": f"Warning notification sent ({count}/{total} frames)",
            "popup_sent": popup_sent,
        }
        self.action_history.insert(0, action_record)
        if len(self.action_history) > 50:
            self.action_history.pop()

        logger.info(f"Agent Policy Enforced: [WARNING] {class_name} -> Dispatched native notification.")
        return action_record

    def _handle_critical_tier(
        self,
        class_name: str,
        confidence: float,
        count: int,
        total: int,
    ) -> Dict[str, any]:
        """Handle Tier 2 Critical (Fire alarm, Gunshot, Explosion) with Human-in-the-Loop countdown."""
        self.current_tier = TIER_CRITICAL
        title = f"🚨 [CRITICAL HAZARD] {class_name.upper()} DETECTED!"
        message = f"Confirmed room hazard ({confidence*100:.1f}% conf). ESCALATING IN {COUNTDOWN_DURATION_SECONDS}s — Check Dashboard to abort."

        # Trigger immediate high-priority native desktop popup
        popup_sent = trigger_os_popup(title, message, severity=TIER_CRITICAL)

        # Cancel any existing active countdown
        if self.countdown_timer_task:
            self.countdown_timer_task.cancel()

        # Initialize Human-in-the-Loop countdown state
        start_time = time.time()
        self.active_countdown = {
            "hazard": class_name,
            "confidence": float(confidence),
            "start_time": start_time,
            "duration": COUNTDOWN_DURATION_SECONDS,
            "status": "ESCALATING",
        }

        # Schedule escalation completion callback
        self.countdown_timer_task = threading.Timer(
            COUNTDOWN_DURATION_SECONDS,
            self._on_escalation_completed,
            args=[class_name, confidence],
        )
        self.countdown_timer_task.start()

        action_record = {
            "timestamp": time.strftime("%H:%M:%S"),
            "tier": TIER_CRITICAL,
            "class_name": class_name,
            "confidence": confidence,
            "action": "COUNTDOWN_INITIATED",
            "details": f"Critical countdown started ({COUNTDOWN_DURATION_SECONDS}s window to abort)",
            "popup_sent": popup_sent,
        }
        self.action_history.insert(0, action_record)
        if len(self.action_history) > 50:
            self.action_history.pop()

        logger.warning(
            f"Agent Policy Enforced: [CRITICAL] {class_name} -> Initiated 10s Human-in-the-Loop countdown."
        )
        return action_record

    def _on_escalation_completed(self, class_name: str, confidence: float) -> None:
        """Invoked when the 10-second countdown expires without human abort: Dispatches Telegram Hunt-Group."""
        with self.lock:
            if self.active_countdown and self.active_countdown.get("status") == "ESCALATING":
                self.active_countdown["status"] = "ESCALATED_CONFIRMED"
                logger.error(
                    f"Agent Escalation Triggered: [EMERGENCY ACTION] Critical hazard '{class_name}' confirmed by timeout. Dispatching Telegram Interactive Hunt-Group..."
                )

                # Send follow-up escalated OS banner
                trigger_os_popup(
                    title=f"🚨 [EMERGENCY ESCALATION] {class_name.upper()}",
                    message="Escalation protocol ACTIVE: Dispatching Telegram emergency alerts with audio clip.",
                    severity=TIER_CRITICAL,
                )

                # Execute Telegram Hunt Group broadcast
                tg_result = self.dispatch_telegram_alert(hazard_type=class_name)

                self.action_history.insert(0, {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "tier": TIER_CRITICAL,
                    "class_name": class_name,
                    "confidence": confidence,
                    "action": "TELEGRAM_ALERT_DISPATCHED",
                    "details": f"Operator timeout reached (10s). Broadcasted alert + audio to {len(self.telegram_manager.chat_ids)} Telegram contacts.",
                    "alert_id": tg_result.get("alert_id"),
                    "popup_sent": True,
                })
                if len(self.action_history) > 50:
                    self.action_history.pop()

    def cancel_alert(self, reason: str = "Operator Abort via Dashboard") -> Dict[str, any]:
        """
        Human-in-the-Loop Cancellation: User clicked Cancel or pressed Spacebar.
        Cancels active countdown, logs false positive, and suppresses further escalation.
        """
        with self.lock:
            if self.countdown_timer_task:
                self.countdown_timer_task.cancel()
                self.countdown_timer_task = None

            hazard_name = self.active_countdown.get("hazard", "Unknown") if self.active_countdown else "Threat"
            self.active_countdown = None
            self.current_tier = "NORMAL"

            # Apply refractory cooldown
            self.last_alert_times[hazard_name] = time.time()

            action_record = {
                "timestamp": time.strftime("%H:%M:%S"),
                "tier": "ABORTED",
                "class_name": hazard_name,
                "confidence": 0.0,
                "action": "OPERATOR_ABORTED_FALSE_POSITIVE",
                "details": f"Escalation aborted by human operator. Reason: {reason}",
                "popup_sent": False,
            }
            self.action_history.insert(0, action_record)
            if len(self.action_history) > 50:
                self.action_history.pop()

            logger.info(f"Agent Action: Alert escalation for '{hazard_name}' aborted by operator.")
            return action_record

    def get_agent_state(self) -> Dict[str, any]:
        """Get current agent telemetry state for WebSocket broadcast."""
        with self.lock:
            countdown_data = None
            if self.active_countdown:
                elapsed = time.time() - self.active_countdown["start_time"]
                remaining = max(0.0, self.active_countdown["duration"] - elapsed)
                countdown_data = {
                    "hazard": self.active_countdown["hazard"],
                    "confidence": self.active_countdown["confidence"],
                    "remaining_seconds": round(remaining, 1),
                    "duration": self.active_countdown["duration"],
                    "status": self.active_countdown["status"],
                }

            telegram_state = self.telegram_manager.get_telegram_state()

            return {
                "agent_status": "ONLINE",
                "current_tier": self.current_tier,
                "active_countdown": countdown_data,
                "telegram": telegram_state,
                "recent_actions": self.action_history[:10],
            }
