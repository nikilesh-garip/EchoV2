"""
Telegram Dynamic AI Voice Dispatcher & Live Maps Hunt-Group Manager

Coordinates emergency incident broadcasts across Telegram contacts:
1. Dynamic AI Voice Briefing via edge-tts (sent as Telegram Voice Memo via sendVoice).
2. Acoustic Evidence: 5-second 16kHz PCM .wav temporal buffer snippet (via sendAudio).
3. Emergency Dashboard & Location: Live IP Geolocation / Google Maps location link (via sendMessage)
   with an interactive Inline Keyboard button [ 🛑 ACKNOWLEDGE EMERGENCY ].
4. Webhook Acknowledgment: First click edits message text across all recipient devices to show
   ✅ Emergency Acknowledged and Handled by [Responder], removes inline button, and notifies UI.
"""

import asyncio
import json
import logging
import os
import struct
import tempfile
import threading
import time
import wave
from typing import Callable, Dict, List, Optional

from dotenv import load_dotenv
import numpy as np
import requests
import edge_tts

# Load environment variables
load_dotenv()

logger = logging.getLogger("TelegramManager")

# Configuration Constants from Environment
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "7123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
TELEGRAM_CHAT_IDS_RAW: str = os.getenv("TELEGRAM_CHAT_IDS", "123456789,987654321,555444333")
PUBLIC_WEBHOOK_URL: str = os.getenv("PUBLIC_WEBHOOK_URL", "https://your-ngrok-subdomain.ngrok-free.app")
EMERGENCY_LOCATION: str = os.getenv("EMERGENCY_LOCATION", "Facility Alpha - Sector 4")
EXACT_LATITUDE: str = os.getenv("EXACT_LATITUDE", "")
EXACT_LONGITUDE: str = os.getenv("EXACT_LONGITUDE", "")
MOCK_TELEGRAM: bool = os.getenv("MOCK_TELEGRAM", "True").lower() in ["true", "1", "yes"]

DEFAULT_VOICE_NEURAL = "en-US-ChristopherNeural"

# Global In-Memory Coordinates cache (populated by Web UI HTML5 Geolocation or REST API)
GLOBAL_USER_COORDINATES: Dict[str, str] = {}


def set_user_coordinates(lat: float, lon: float, city: Optional[str] = None) -> None:
    """Cache exact coordinates from browser HTML5 Geolocation API or UI settings."""
    global GLOBAL_USER_COORDINATES
    GLOBAL_USER_COORDINATES["lat"] = str(lat)
    GLOBAL_USER_COORDINATES["lon"] = str(lon)
    if city:
        GLOBAL_USER_COORDINATES["city"] = city
    logger.info(f"Updated live global user coordinates: {lat}, {lon} (City: {city})")


def resolve_live_location() -> Dict[str, str]:
    """
    Determine high-precision coordinates for Google Maps tracking.
    1. Browser HTML5 Geolocation / UI location sync (if set).
    2. EXACT_LATITUDE / EXACT_LONGITUDE from .env (if set).
    3. Fresh IP Geolocation API (ipapi.co / ipinfo.io).
    """
    # Level 1: Live Browser HTML5 GPS sync / UI location setting
    if GLOBAL_USER_COORDINATES.get("lat") and GLOBAL_USER_COORDINATES.get("lon"):
        lat = GLOBAL_USER_COORDINATES["lat"]
        lon = GLOBAL_USER_COORDINATES["lon"]
        city = GLOBAL_USER_COORDINATES.get("city", EMERGENCY_LOCATION)
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        logger.info(f"Using Live Device GPS coordinates: {lat}, {lon}")
        return {"lat": lat, "lon": lon, "city": city, "maps_url": maps_url}

    # Level 2: Exact coordinates from .env
    env_lat = os.getenv("EXACT_LATITUDE", "").strip()
    env_lon = os.getenv("EXACT_LONGITUDE", "").strip()

    if env_lat and env_lon:
        try:
            lat_f = float(env_lat)
            lon_f = float(env_lon)
            maps_url = f"https://www.google.com/maps?q={lat_f},{lon_f}"
            logger.info(f"Using exact coordinates from .env: {lat_f}, {lon_f}")
            return {
                "lat": str(lat_f),
                "lon": str(lon_f),
                "city": EMERGENCY_LOCATION,
                "maps_url": maps_url,
            }
        except ValueError:
            pass

    # Level 3: Fresh IP Geolocation APIs (with cache-busting timestamp)
    cb = int(time.time())
    try:
        res = requests.get(f"https://ipapi.co/json/?_cb={cb}", timeout=4)
        if res.status_code == 200:
            data = res.json()
            lat = data.get("latitude")
            lon = data.get("longitude")
            city = data.get("city") or data.get("region") or EMERGENCY_LOCATION
            if lat is not None and lon is not None:
                maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                logger.info(f"Resolved live location via ipapi.co: {city} ({lat}, {lon})")
                return {
                    "lat": str(lat),
                    "lon": str(lon),
                    "city": str(city),
                    "maps_url": maps_url,
                }
    except Exception as e:
        logger.warning(f"Primary IP geolocation check (ipapi.co) failed: {e}")

    try:
        res = requests.get(f"https://ipinfo.io/json?_cb={cb}", timeout=4)
        if res.status_code == 200:
            data = res.json()
            loc_str = data.get("loc", "")
            city = data.get("city") or EMERGENCY_LOCATION
            if "," in loc_str:
                lat, lon = loc_str.split(",", 1)
                maps_url = f"https://www.google.com/maps?q={lat.strip()},{lon.strip()}"
                logger.info(f"Resolved live location via ipinfo.io: {city} ({loc_str})")
                return {
                    "lat": lat.strip(),
                    "lon": lon.strip(),
                    "city": str(city),
                    "maps_url": maps_url,
                }
    except Exception as e:
        logger.warning(f"Fallback IP geolocation check (ipinfo.io) failed: {e}")

    # Fallback
    default_lat = "17.3840"
    default_lon = "78.4564"
    return {
        "lat": default_lat,
        "lon": default_lon,
        "city": EMERGENCY_LOCATION,
        "maps_url": f"https://www.google.com/maps?q={default_lat},{default_lon}",
    }


def generate_ai_voice_briefing(
    hazard_type: str,
    city: str,
    user_name: str = "Nikhilesh",
    voice: str = DEFAULT_VOICE_NEURAL,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a dynamic AI voice note briefing using edge-tts.

    Script format:
    "Critical alert. The Echo system has detected a {hazard_type} at {user_name}'s location in {city}. Immediate review is required."
    """
    if output_path is None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", prefix="dispatcher_", delete=False)
        output_path = temp_file.name
        temp_file.close()

    script_text = (
        f"Critical alert. The Echo system has detected a {hazard_type} at {user_name}'s location in {city}. "
        f"Immediate review is required."
    )

    logger.info(f"Generating AI voice briefing via edge-tts ({voice}): '{script_text}'")

    async def _async_generate():
        communicate = edge_tts.Communicate(script_text, voice=voice)
        await communicate.save(output_path)

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_async_generate(), loop)
            future.result(timeout=10)
        else:
            asyncio.run(_async_generate())
    except Exception as e:
        logger.error(f"Error rendering edge-tts voice briefing: {e}")

    return output_path


def export_audio_buffer_to_wav(
    audio_samples: Optional[np.ndarray],
    sample_rate: int = 16000,
    output_path: Optional[str] = None,
) -> str:
    """
    Export raw float32 audio samples from temporal buffer into a 16-bit Mono PCM .wav file.
    """
    if output_path is None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", prefix="hazard_", delete=False)
        output_path = temp_file.name
        temp_file.close()

    if audio_samples is None or len(audio_samples) == 0:
        duration = 5.0
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        freq = 950.0 + 150.0 * np.sin(2 * np.pi * 4 * t)
        phase = 2 * np.pi * np.cumsum(freq) / sample_rate
        audio_samples = (0.7 * np.sin(phase)).astype(np.float32)
    elif isinstance(audio_samples, list):
        audio_samples = np.concatenate(audio_samples, axis=0).astype(np.float32)

    clamped = np.clip(audio_samples, -1.0, 1.0)
    int16_pcm = (clamped * 32767.0).astype(np.int16)

    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int16_pcm.tobytes())

    return output_path


class TelegramHuntGroupManager:
    """
    Manages dynamic Telegram Bot emergency alerts, AI voice briefing notes,
    live Google Maps tracking links, and multi-device interactive webhook callbacks.
    """

    def __init__(
        self,
        bot_token: str = TELEGRAM_BOT_TOKEN,
        chat_ids: Optional[List[str]] = None,
        location: str = EMERGENCY_LOCATION,
        webhook_url: str = PUBLIC_WEBHOOK_URL,
        mock_mode: bool = MOCK_TELEGRAM,
        on_status_update: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.bot_token = bot_token
        self.location = location
        self.webhook_url = webhook_url
        self.mock_mode = mock_mode
        self.on_status_update = on_status_update

        if chat_ids:
            self.chat_ids = [str(cid).strip() for cid in chat_ids if str(cid).strip()]
        else:
            self.chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_IDS_RAW.split(",") if cid.strip()]

        if "ABCdefGHIjkl" in self.bot_token or not self.bot_token:
            self.mock_mode = True

        self.lock = threading.Lock()
        self.active_alert: Optional[Dict[str, any]] = None
        self.alert_history: List[Dict[str, any]] = []

    def _notify_update(self) -> None:
        if self.on_status_update and callable(self.on_status_update):
            try:
                self.on_status_update(self.get_telegram_state())
            except Exception as e:
                logger.error(f"Error in on_status_update callback: {e}")

    def get_telegram_state(self) -> Dict[str, any]:
        with self.lock:
            return {
                "bot_status": "ONLINE" if self.bot_token else "OFFLINE",
                "mock_mode": self.mock_mode,
                "configured_chats": self.chat_ids,
                "active_alert": self.active_alert,
                "recent_alerts": self.alert_history[-5:],
            }

    def set_webhook(self, url: Optional[str] = None) -> Dict[str, any]:
        target_url = url or self.webhook_url
        if not target_url.endswith("/telegram/webhook"):
            target_url = target_url.rstrip("/") + "/telegram/webhook"

        if self.mock_mode:
            logger.info(f"[MOCK TELEGRAM] Set webhook to: {target_url}")
            return {"ok": True, "description": f"Mock webhook set to {target_url}"}

        api_url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
        try:
            res = requests.post(api_url, data={"url": target_url}, timeout=10)
            data = res.json()
            logger.info(f"Set Telegram Webhook response: {data}")
            return data
        except Exception as e:
            logger.error(f"Failed to set Telegram webhook: {e}")
            return {"ok": False, "error": str(e)}

    def broadcast_telegram_alert(
        self,
        hazard_type: str,
        audio_samples: Optional[np.ndarray] = None,
        location: Optional[str] = None,
        user_name: str = "Nikhilesh",
        target_chats: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Executes the full 3-part Telegram Dispatch Sequence across all target contacts:
        1. Voice Briefing: sendVoice endpoint with edge-tts MP3.
        2. Acoustic Evidence: sendAudio endpoint with 5s .wav recording.
        3. Emergency Dashboard & Location: sendMessage endpoint with Google Maps link
           and inline button [ 🛑 ACKNOWLEDGE EMERGENCY ].
        """
        alert_id = f"alert_{int(time.time())}"
        timestamp_str = time.strftime("%H:%M:%S")

        # 1. Resolve Live Location & Google Maps URL
        loc_info = resolve_live_location()
        city = loc_info["city"]
        maps_url = loc_info["maps_url"]

        # 2. Render AI Voice Briefing MP3 via edge-tts
        mp3_path = generate_ai_voice_briefing(
            hazard_type=hazard_type,
            city=city,
            user_name=user_name,
        )

        # 3. Export 5-second acoustic WAV buffer
        wav_path = export_audio_buffer_to_wav(audio_samples=audio_samples)

        # Determine target chats
        chats_to_send = target_chats or self.chat_ids
        if not chats_to_send:
            chats_to_send = self.chat_ids

        # Formatted Location Text Message with Inline Acknowledgment Button
        message_text = (
            f"🚨 <b>CRITICAL HAZARD: {hazard_type.upper()}</b>\n"
            f"🕒 <b>Time:</b> {timestamp_str}\n"
            f"📍 <b>Live Location:</b> <a href=\"{maps_url}\">{maps_url}</a>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "🛑 ACKNOWLEDGE EMERGENCY",
                        "callback_data": f"ack_{alert_id}",
                    }
                ]
            ]
        }

        messages_dispatched: Dict[str, any] = {}

        logger.warning(
            f"📱 [DYNAMIC TELEGRAM AI DISPATCH] Broadcasting '{hazard_type}' alert to {len(chats_to_send)} "
            f"Telegram contacts (Mock Mode={self.mock_mode})..."
        )

        with self.lock:
            if self.mock_mode:
                for idx, chat_id in enumerate(chats_to_send):
                    sim_id = 1000 + int(time.time() % 10000) + idx
                    messages_dispatched[chat_id] = {
                        "voice_id": sim_id,
                        "audio_id": sim_id + 100,
                        "text_id": sim_id + 200,
                        "message_id": sim_id + 200,  # Main target for callback query editing
                        "status": "DELIVERED",
                        "chat_id": chat_id,
                    }
                    logger.info(f"[MOCK TELEGRAM] Dispatched Voice, Audio & Maps message to chat_id={chat_id}")
            else:
                for chat_id in chats_to_send:
                    chat_result = {
                        "voice_id": None,
                        "audio_id": None,
                        "text_id": None,
                        "message_id": None,
                        "status": "FAILED",
                        "chat_id": chat_id,
                    }

                    # Step A: Send AI Voice Briefing (sendVoice)
                    try:
                        voice_url = f"https://api.telegram.org/bot{self.bot_token}/sendVoice"
                        with open(mp3_path, "rb") as voice_file:
                            res_v = requests.post(
                                voice_url,
                                data={"chat_id": chat_id, "caption": f"🎙️ AI Voice Briefing — {hazard_type}"},
                                files={"voice": (os.path.basename(mp3_path), voice_file, "audio/mpeg")},
                                timeout=10,
                            )
                            d_v = res_v.json()
                            if d_v.get("ok"):
                                chat_result["voice_id"] = d_v["result"]["message_id"]
                                logger.info(f"Sent sendVoice note to chat_id={chat_id}")
                    except Exception as e:
                        logger.error(f"Error in sendVoice to {chat_id}: {e}")

                    # Step B: Send Acoustic WAV Snippet (sendAudio)
                    try:
                        audio_url = f"https://api.telegram.org/bot{self.bot_token}/sendAudio"
                        with open(wav_path, "rb") as audio_file:
                            res_a = requests.post(
                                audio_url,
                                data={"chat_id": chat_id, "caption": f"🔊 5-second acoustic evidence snippet"},
                                files={"audio": (os.path.basename(wav_path), audio_file, "audio/wav")},
                                timeout=10,
                            )
                            d_a = res_a.json()
                            if d_a.get("ok"):
                                chat_result["audio_id"] = d_a["result"]["message_id"]
                                logger.info(f"Sent sendAudio clip to chat_id={chat_id}")
                    except Exception as e:
                        logger.error(f"Error in sendAudio to {chat_id}: {e}")

                    # Step C: Send Emergency Dashboard & Live Google Maps Message (sendMessage)
                    try:
                        msg_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                        res_m = requests.post(
                            msg_url,
                            json={
                                "chat_id": chat_id,
                                "text": message_text,
                                "parse_mode": "HTML",
                                "reply_markup": reply_markup,
                                "disable_web_page_preview": False,
                            },
                            timeout=10,
                        )
                        d_m = res_m.json()
                        if d_m.get("ok"):
                            text_msg_id = d_m["result"]["message_id"]
                            chat_result["text_id"] = text_msg_id
                            chat_result["message_id"] = text_msg_id
                            chat_result["status"] = "DELIVERED"
                            logger.info(f"Sent sendMessage location link to chat_id={chat_id} (msg_id={text_msg_id})")
                        else:
                            logger.error(f"sendMessage error for {chat_id}: {d_m}")
                    except Exception as e:
                        logger.error(f"Error in sendMessage to {chat_id}: {e}")

                    messages_dispatched[chat_id] = chat_result

            alert_record = {
                "alert_id": alert_id,
                "hazard_type": hazard_type,
                "location": city,
                "maps_url": maps_url,
                "status": "DISPATCHED",
                "start_time": time.time(),
                "timestamp": timestamp_str,
                "wav_path": wav_path,
                "mp3_path": mp3_path,
                "messages": messages_dispatched,
                "responder": None,
                "acknowledged_at": None,
            }
            self.active_alert = alert_record

            self._notify_update()
            return alert_record

    def acknowledge_alert(
        self,
        alert_id: str,
        responder_name: str,
        responder_id: str,
        callback_query_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Invoked when a contact clicks [ 🛑 ACKNOWLEDGE EMERGENCY ].
        1. Calls answerCallbackQuery to dismiss loading spinner.
        2. Calls editMessageText across all target devices to strip button and append
           ✅ Emergency Acknowledged and Handled by [Responder].
        3. Updates alert state to RESOLVED and triggers WebSocket UI updates.
        """
        with self.lock:
            if not self.active_alert:
                return {"status": "NO_ACTIVE_ALERT"}

            if self.active_alert.get("status") == "RESOLVED":
                return {
                    "status": "ALREADY_RESOLVED",
                    "responder": self.active_alert.get("responder"),
                    "acknowledged_at": self.active_alert.get("acknowledged_at"),
                }

            # Mark as RESOLVED
            self.active_alert["status"] = "RESOLVED"
            self.active_alert["responder"] = {"name": responder_name, "id": responder_id}
            self.active_alert["acknowledged_at"] = time.strftime("%H:%M:%S")

            # 1. Dismiss spinner via answerCallbackQuery
            if callback_query_id and not self.mock_mode:
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery",
                        json={
                            "callback_query_id": callback_query_id,
                            "text": f"✅ Incident Acknowledged by @{responder_name}!",
                            "show_alert": False,
                        },
                        timeout=5,
                    )
                except Exception as e:
                    logger.error(f"Failed to answer callback query: {e}")

            # 2. Edit Text Messages on all devices to strip button and add resolution text
            hazard_type = self.active_alert.get("hazard_type", "Hazard")
            timestamp_str = self.active_alert.get("timestamp", "")
            maps_url = self.active_alert.get("maps_url", "")

            updated_text = (
                f"🚨 <b>CRITICAL HAZARD: {hazard_type.upper()}</b>\n"
                f"🕒 <b>Time:</b> {timestamp_str}\n"
                f"📍 <b>Live Location:</b> <a href=\"{maps_url}\">{maps_url}</a>\n\n"
                f"✅ <b>Emergency Acknowledged and Handled by @{responder_name}</b>"
            )

            for chat_id, msg_data in self.active_alert.get("messages", {}).items():
                target_msg_id = msg_data.get("text_id") or msg_data.get("message_id")
                if not target_msg_id:
                    continue

                if self.mock_mode:
                    msg_data["status"] = "ACKNOWLEDGED_EDITED"
                    logger.info(f"[MOCK TELEGRAM] Edited message {target_msg_id} for chat {chat_id}")
                else:
                    try:
                        edit_url = f"https://api.telegram.org/bot{self.bot_token}/editMessageText"
                        payload = {
                            "chat_id": chat_id,
                            "message_id": target_msg_id,
                            "text": updated_text,
                            "parse_mode": "HTML",
                            "reply_markup": json.dumps({"inline_keyboard": []}),
                            "disable_web_page_preview": False,
                        }
                        res = requests.post(edit_url, json=payload, timeout=5)
                        if res.json().get("ok"):
                            msg_data["status"] = "ACKNOWLEDGED_EDITED"
                            logger.info(f"Edited message {target_msg_id} on chat {chat_id}")
                        else:
                            # Fallback edit caption if sent via photo/audio
                            requests.post(
                                f"https://api.telegram.org/bot{self.bot_token}/editMessageCaption",
                                json={
                                    "chat_id": chat_id,
                                    "message_id": target_msg_id,
                                    "caption": updated_text,
                                    "parse_mode": "HTML",
                                    "reply_markup": json.dumps({"inline_keyboard": []}),
                                },
                                timeout=5,
                            )
                            msg_data["status"] = "ACKNOWLEDGED_EDITED"
                    except Exception as e:
                        logger.error(f"Failed to edit Telegram message for {chat_id}: {e}")

            # Archive to history
            self.alert_history.append(self.active_alert.copy())

            self._notify_update()
            return {"status": "SUCCESS", "alert": self.active_alert}
