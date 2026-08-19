"""
Echo — FastAPI Server & Telemetry Hub

Serves the Echo web UI (login + dashboard SPA), provides authenticated REST APIs for
user management, emergency contact pairing, system control, and Telegram deep-link
webhook handling. Broadcasts real-time audio telemetry over WebSockets.
"""

import asyncio
import json
import logging
import os
import threading
import time
from typing import Dict, List, Optional, Set

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import numpy as np

from auth import hash_password, verify_password, create_access_token, decode_access_token
import database as db

# Configure logging
logger = logging.getLogger("EchoServer")

# ── Initialize FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(title="Echo — Acoustic Hazard Detection Platform", version="3.0.0")


# ── WebSocket Connection Manager ────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.latest_telemetry: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active: {len(self.active_connections)}")
        if self.latest_telemetry:
            try:
                await websocket.send_json(self.latest_telemetry)
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        self.latest_telemetry = message
        if not self.active_connections:
            return
        dead = set()
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.add(conn)
        for d in dead:
            self.active_connections.discard(d)


manager = ConnectionManager()


# ── Global Engine State ─────────────────────────────────────────────────────────

ENGINE_STATE = {
    "ingestion": None,
    "classifier": None,
    "firewall": None,
    "temporal_buffer": None,
    "agent": None,
    "simulation_queue": None,
    "total_chunks": 0,
    "start_time": time.time(),
    "mic_enabled": True,
}

# ── Static Files ────────────────────────────────────────────────────────────────

DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "dashboard")
app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")


# ── Pydantic Request Models ─────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class SettingsUpdateRequest(BaseModel):
    mic_enabled: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    theme: Optional[str] = None

class ContactCreateRequest(BaseModel):
    contact_name: str

class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    city: Optional[str] = None


# ── Auth Dependency ─────────────────────────────────────────────────────────────

async def get_current_user(request: Request) -> dict:
    """Extract and verify JWT from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.get_user_by_id(payload["user_id"])
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Page Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_login_page():
    """Serve the login/signup page."""
    return FileResponse(os.path.join(DASHBOARD_DIR, "login.html"))


@app.get("/app")
async def serve_dashboard():
    """Serve the main dashboard SPA (requires client-side auth check)."""
    return FileResponse(os.path.join(DASHBOARD_DIR, "index.html"))


# ── Auth Endpoints ──────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register_user(body: RegisterRequest):
    """Register a new user account with bcrypt-encrypted password."""
    if len(body.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if "@" not in body.email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    existing = await db.get_user_by_username(body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    hashed = hash_password(body.password)
    user = await db.create_user(username=body.username, email=body.email, password_hash=hashed)
    token = create_access_token(user_id=user["id"], username=user["username"])

    return JSONResponse({
        "status": "registered",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user["display_name"],
        },
    })


@app.post("/api/auth/login")
async def login_user(body: LoginRequest):
    """Authenticate user credentials and return a JWT token."""
    user = await db.get_user_by_username(body.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user_id=user["id"], username=user["username"])
    return JSONResponse({
        "status": "authenticated",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user["display_name"],
        },
    })


@app.get("/api/auth/me")
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile and settings."""
    settings = await db.get_user_settings(user["id"])
    return JSONResponse({
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "display_name": user["display_name"],
            "created_at": user["created_at"],
        },
        "settings": {
            "mic_enabled": bool(settings["mic_enabled"]) if settings else True,
            "notifications_enabled": bool(settings["notifications_enabled"]) if settings else True,
            "theme": settings["theme"] if settings else "light",
            "location": settings["location_descriptor"] if settings else "My Home",
        },
    })


# ── Profile Endpoints ───────────────────────────────────────────────────────────

@app.put("/api/profile")
async def update_profile(body: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    await db.update_user_profile(user_id=user["id"], display_name=body.display_name, email=body.email, location=body.location)
    return JSONResponse({"status": "updated"})


@app.put("/api/profile/password")
async def change_password(body: PasswordChangeRequest, user: dict = Depends(get_current_user)):
    full_user = await db.get_user_by_username(user["username"])
    if not verify_password(body.old_password, full_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    new_hash = hash_password(body.new_password)
    await db.change_password(user["id"], new_hash)
    return JSONResponse({"status": "password_changed"})


@app.get("/api/profile/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    settings = await db.get_user_settings(user["id"])
    return JSONResponse({"settings": dict(settings) if settings else {}})


@app.put("/api/profile/settings")
async def update_settings(body: SettingsUpdateRequest, user: dict = Depends(get_current_user)):
    await db.update_user_settings(
        user_id=user["id"],
        mic_enabled=body.mic_enabled,
        notifications_enabled=body.notifications_enabled,
        theme=body.theme,
    )
    # Propagate mic toggle to engine state
    if body.mic_enabled is not None:
        ENGINE_STATE["mic_enabled"] = body.mic_enabled
    return JSONResponse({"status": "settings_updated"})


@app.post("/api/location/update")
async def update_location(request: Request, body: LocationUpdateRequest):
    """Sync high-precision coordinates from HTML5 browser Geolocation or UI."""
    from telegram_manager import set_user_coordinates
    set_user_coordinates(lat=body.latitude, lon=body.longitude, city=body.city)

    # Save to SQLite database
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            payload = decode_access_token(token)
            if payload:
                await db.update_user_location(user_id=payload["user_id"], latitude=body.latitude, longitude=body.longitude, city=body.city)
    except Exception as e:
        logger.warning(f"Could not persist user location to DB: {e}")

    return JSONResponse({
        "status": "location_synced",
        "latitude": body.latitude,
        "longitude": body.longitude,
        "maps_url": f"https://www.google.com/maps?q={body.latitude},{body.longitude}",
    })


# ── Emergency Contact Endpoints ─────────────────────────────────────────────────

TELEGRAM_BOT_USERNAME = "my_hunt_group_bot"  # Must match your bot's @username

@app.get("/api/contacts")
async def list_contacts(user: dict = Depends(get_current_user)):
    contacts = await db.get_contacts_for_user(user["id"])
    result = []
    for c in contacts:
        deep_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={c['pairing_token']}"
        result.append({
            "id": c["id"],
            "contact_name": c["contact_name"],
            "status": c["status"],
            "telegram_username": c.get("telegram_username"),
            "telegram_chat_id": c.get("telegram_chat_id"),
            "deep_link": deep_link,
            "created_at": c["created_at"],
            "verified_at": c.get("verified_at"),
        })
    return JSONResponse({"contacts": result})


@app.post("/api/contacts")
async def create_new_contact(body: ContactCreateRequest, user: dict = Depends(get_current_user)):
    if not body.contact_name.strip():
        raise HTTPException(status_code=400, detail="Contact name cannot be empty")
    contact = await db.create_contact(user_id=user["id"], contact_name=body.contact_name.strip())
    deep_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={contact['pairing_token']}"
    return JSONResponse({
        "status": "created",
        "contact": {
            "id": contact["id"],
            "contact_name": contact["contact_name"],
            "status": contact["status"],
            "deep_link": deep_link,
            "pairing_token": contact["pairing_token"],
        },
    })


@app.delete("/api/contacts/{contact_id}")
async def remove_contact(contact_id: int, user: dict = Depends(get_current_user)):
    success = await db.delete_contact(contact_id=contact_id, user_id=user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return JSONResponse({"status": "deleted"})


# ── System Control ──────────────────────────────────────────────────────────────

@app.post("/api/system/toggle-mic")
async def toggle_mic(user: dict = Depends(get_current_user)):
    ENGINE_STATE["mic_enabled"] = not ENGINE_STATE["mic_enabled"]
    await db.update_user_settings(user_id=user["id"], mic_enabled=ENGINE_STATE["mic_enabled"])
    return JSONResponse({"mic_enabled": ENGINE_STATE["mic_enabled"]})


@app.get("/api/status")
async def get_status():
    uptime = time.time() - ENGINE_STATE["start_time"]
    ingestion = ENGINE_STATE.get("ingestion")
    firewall = ENGINE_STATE.get("firewall")
    agent = ENGINE_STATE.get("agent")
    agent_state = agent.get_agent_state() if agent else {}

    return JSONResponse({
        "status": "ONLINE",
        "mic_enabled": ENGINE_STATE["mic_enabled"],
        "uptime_seconds": round(uptime, 1),
        "total_chunks_processed": ENGINE_STATE["total_chunks"],
        "active_websocket_clients": len(manager.active_connections),
        "audio_hardware": {
            "mic_device": ingestion.mic_device_info.get("name", "Active Microphone") if hasattr(ingestion, "mic_device_info") and ingestion.mic_device_info else "Active Microphone",
            "speaker_device": getattr(ingestion, "speaker_name", "Default Speaker"),
            "sample_rate": 16000,
            "chunk_samples": 15600,
        },
        "firewall_stats": {
            "suppressed_media_count": getattr(firewall, "suppressed_count", 0),
            "confirmed_threat_count": getattr(firewall, "confirmed_hazard_count", 0),
        },
        "agent_state": agent_state,
    })


# ── Existing Alert / Telegram Endpoints ─────────────────────────────────────────

@app.post("/api/cancel-alert")
async def cancel_alert():
    agent = ENGINE_STATE.get("agent")
    if agent:
        result = agent.cancel_alert(reason="Operator cancelled via Dashboard")
        return JSONResponse({"status": "aborted", "action_record": result})
    return JSONResponse({"status": "error", "message": "Agent not initialized"}, status_code=500)


@app.post("/api/trigger-alert")
async def trigger_alert(hazard: str = "Fire alarm", tier: str = "CRITICAL"):
    agent = ENGINE_STATE.get("agent")
    if agent:
        event = {
            "tier": f"{tier.upper()} HAZARD",
            "class_name": hazard,
            "max_confidence": 0.96,
            "avg_confidence": 0.94,
            "count": 4,
            "total_frames": 5,
        }
        res = agent.dispatch_hazard_event(event)
        return JSONResponse({"status": "dispatched", "result": res})
    return JSONResponse({"status": "error", "message": "Agent not initialized"}, status_code=500)


@app.post("/api/trigger-telegram")
async def trigger_telegram_endpoint(hazard: str = "Fire alarm", location: Optional[str] = None):
    agent = ENGINE_STATE.get("agent")
    if agent and hasattr(agent, "dispatch_telegram_alert"):
        # Fetch verified emergency contacts from database
        verified_contacts = await db.get_all_verified_contacts()
        verified_chats = [c["telegram_chat_id"] for c in verified_contacts if c.get("telegram_chat_id")]
        
        # Combine with environment configured chat IDs
        env_chats = [cid.strip() for cid in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()]
        all_chats = list(dict.fromkeys(verified_chats + env_chats))
        
        res = agent.dispatch_telegram_alert(hazard_type=hazard, location=location, target_chats=all_chats if all_chats else None)
        return JSONResponse({"status": "telegram_dispatched", "alert_record": res})
    return JSONResponse({"status": "error", "message": "Agent telegram manager not initialized"}, status_code=500)


@app.post("/api/test-telegram-ack")
async def test_telegram_ack_endpoint(
    responder_name: str = "SecurityChief_Alex",
    responder_id: str = "987654321",
):
    agent = ENGINE_STATE.get("agent")
    if agent and hasattr(agent, "telegram_manager"):
        active_alert = agent.telegram_manager.active_alert
        alert_id = active_alert.get("alert_id", "latest") if active_alert else "latest"
        res = agent.telegram_manager.acknowledge_alert(
            alert_id=alert_id,
            responder_name=responder_name,
            responder_id=responder_id,
        )
        # Broadcast WS event
        await manager.broadcast({"event": "TELEGRAM_ACKNOWLEDGED", "responder": responder_name, "alert_id": alert_id})
        return JSONResponse({"status": "acknowledged", "result": res})
    return JSONResponse({"status": "error", "message": "Agent telegram manager not initialized"}, status_code=500)


# ── Telegram Webhook (Callback Queries + Deep-Link /start Pairing) ──────────────

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Handles two types of Telegram updates:
    1. callback_query: When a contact clicks [ 🛑 ACKNOWLEDGE EMERGENCY ]
    2. message with /start <token>: Deep-link pairing for emergency contacts
    """
    try:
        payload = await request.json()
        logger.info(f"Telegram webhook update: {json.dumps(payload)[:500]}")

        # ── Handle callback_query (alert acknowledgment) ────────────
        callback_query = payload.get("callback_query")
        if callback_query:
            callback_id = callback_query.get("id")
            callback_data = callback_query.get("data", "")
            from_user = callback_query.get("from", {})
            responder_name = from_user.get("username") or from_user.get("first_name") or "TelegramUser"
            responder_id = str(from_user.get("id", "0"))
            alert_id = callback_data.replace("ack_", "")

            agent = ENGINE_STATE.get("agent")
            if agent and hasattr(agent, "telegram_manager"):
                ack_res = agent.telegram_manager.acknowledge_alert(
                    alert_id=alert_id,
                    responder_name=responder_name,
                    responder_id=responder_id,
                    callback_query_id=callback_id,
                )
                logger.info(f"Alert {alert_id} acknowledged by @{responder_name}")
                return JSONResponse({"ok": True, "result": ack_res})

        # ── Handle /start <token> (deep-link contact pairing) ───────
        message = payload.get("message", {})
        text = message.get("text", "")
        if text.startswith("/start "):
            parts = text.split(" ", 1)
            if len(parts) == 2:
                pairing_token = parts[1].strip()
                chat_id = str(message.get("chat", {}).get("id", ""))
                from_user = message.get("from", {})
                tg_username = from_user.get("username", "")
                tg_first_name = from_user.get("first_name", "User")

                contact = await db.verify_contact_by_token(
                    pairing_token=pairing_token,
                    telegram_chat_id=chat_id,
                    telegram_username=tg_username or tg_first_name,
                )

                # Send confirmation message back to the user in Telegram
                import requests as http_requests
                from dotenv import load_dotenv
                load_dotenv()
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

                if contact:
                    confirm_text = f"✅ You've been paired as an emergency contact for **Echo**!\n\nContact name: **{contact['contact_name']}**\n\nYou will receive emergency audio alerts if a hazard is detected."
                    status_msg = "paired"
                else:
                    confirm_text = "❌ Invalid or expired pairing link. Please ask for a new link from the Echo dashboard."
                    status_msg = "invalid_token"

                try:
                    http_requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": chat_id, "text": confirm_text, "parse_mode": "Markdown"},
                        timeout=5,
                    )
                except Exception as e:
                    logger.error(f"Failed to send pairing confirmation: {e}")

                logger.info(f"Deep-link pairing: token={pairing_token[:8]}... chat_id={chat_id} -> {status_msg}")
                return JSONResponse({"ok": True, "status": status_msg})

        return JSONResponse({"ok": True, "status": "no_action_needed"})

    except Exception as e:
        logger.error(f"Error in telegram_webhook: {e}", exc_info=True)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ── Test Sound Injection ────────────────────────────────────────────────────────

@app.post("/api/test-sound")
async def trigger_test_sound(mode: str = "media_suppress"):
    import soundcard as sc

    if mode == "media_suppress":
        def play_speaker_test():
            try:
                spk = sc.default_speaker()
                sr = 48000
                duration = 2.0
                t = np.linspace(0, duration, int(sr * duration), endpoint=False)
                freq = 950.0 + 150.0 * np.sin(2 * np.pi * 4 * t)
                phase = 2 * np.pi * np.cumsum(freq) / sr
                tone = (0.5 * np.sin(phase)).astype(np.float32)
                stereo = np.column_stack((tone, tone))
                spk.play(stereo, samplerate=sr)
            except Exception as e:
                logger.error(f"Error in test sound playback: {e}")
        threading.Thread(target=play_speaker_test, daemon=True).start()
        return {"status": "success", "message": "Triggered test tone."}

    elif mode == "ambient_hazard":
        sim_queue = ENGINE_STATE.get("simulation_queue")
        if sim_queue is not None:
            for _ in range(3):
                sr = 16000
                t = np.linspace(0, 15600 / sr, 15600, endpoint=False)
                freq = 950.0 + 150.0 * np.sin(2 * np.pi * 4 * t)
                phase = 2 * np.pi * np.cumsum(freq) / sr
                alarm_chunk = (0.6 * np.sin(phase) + 0.1 * np.sin(2 * phase)).astype(np.float32)
                sim_queue.put(alarm_chunk)
            return {"status": "success", "message": "Injected 3 hazard frames."}
        return {"status": "error", "message": "Simulation queue not initialized."}

    return {"status": "error", "message": f"Unknown mode: {mode}"}


# ── WebSocket Telemetry ─────────────────────────────────────────────────────────

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """Real-time telemetry WebSocket. Optionally validates JWT from query param."""
    # Allow unauthenticated connections for now (token validation is optional)
    if token:
        payload = decode_access_token(token)
        if payload is None:
            await websocket.close(code=4001)
            return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "cancel_alert":
                agent = ENGINE_STATE.get("agent")
                if agent:
                    agent.cancel_alert(reason="WebSocket cancel event")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket terminated: {e}")
        manager.disconnect(websocket)
