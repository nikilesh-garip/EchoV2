"""
Echo — SQLite Database Layer

Manages user accounts, emergency contacts with Telegram deep-link pairing tokens,
and per-user settings. All operations are async via aiosqlite.
"""

import aiosqlite
import logging
import os
import secrets
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("EchoDB")

DATABASE_PATH: str = os.getenv("DATABASE_PATH", "echo.db")


async def get_db() -> aiosqlite.Connection:
    """Open and return an aiosqlite connection with row_factory enabled."""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    """Create all tables if they don't already exist."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                mic_enabled INTEGER DEFAULT 1,
                notifications_enabled INTEGER DEFAULT 1,
                theme TEXT DEFAULT 'light',
                location_descriptor TEXT DEFAULT 'My Home',
                latitude REAL DEFAULT NULL,
                longitude REAL DEFAULT NULL,
                location_updated_at REAL DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS emergency_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                contact_name TEXT NOT NULL,
                pairing_token TEXT UNIQUE NOT NULL,
                telegram_chat_id TEXT DEFAULT NULL,
                telegram_username TEXT DEFAULT NULL,
                status TEXT DEFAULT 'PENDING',
                created_at REAL NOT NULL,
                verified_at REAL DEFAULT NULL
            );
        """)
        await db.commit()
        logger.info(f"Echo database initialized at '{DATABASE_PATH}'.")
    finally:
        await db.close()


# ── User CRUD ───────────────────────────────────────────────────────────────────

async def create_user(username: str, email: str, password_hash: str) -> Dict[str, Any]:
    """Insert a new user and create their default settings row."""
    now = time.time()
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO users (username, email, password_hash, display_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, email, password_hash, username, now, now),
        )
        user_id = cursor.lastrowid
        await db.execute(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (user_id,),
        )
        await db.commit()
        return {"id": user_id, "username": username, "email": email, "display_name": username, "created_at": now}
    finally:
        await db.close()


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, username, email, display_name, created_at, updated_at FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_user_display_name(user_id: Optional[int] = None) -> str:
    """Fetch user display_name or username for dynamic emergency message personalization."""
    db = await get_db()
    try:
        if user_id is not None:
            cursor = await db.execute("SELECT display_name, username FROM users WHERE id = ?", (user_id,))
        else:
            cursor = await db.execute("SELECT display_name, username FROM users ORDER BY id ASC LIMIT 1")
        row = await cursor.fetchone()
        if row:
            d = dict(row)
            return d.get("display_name") or d.get("username") or "User"
        return "User"
    finally:
        await db.close()


async def update_user_profile(user_id: int, display_name: str = None, email: str = None, location: str = None) -> bool:
    db = await get_db()
    try:
        updates = []
        params = []
        if display_name is not None:
            updates.append("display_name = ?")
            params.append(display_name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if updates:
            updates.append("updated_at = ?")
            params.append(time.time())
            params.append(user_id)
            await db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)

        if location is not None:
            await db.execute("UPDATE user_settings SET location_descriptor = ? WHERE user_id = ?", (location, user_id))

        await db.commit()
        return True
    finally:
        await db.close()


async def change_password(user_id: int, new_password_hash: str) -> bool:
    db = await get_db()
    try:
        await db.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (new_password_hash, time.time(), user_id))
        await db.commit()
        return True
    finally:
        await db.close()


async def get_user_settings(user_id: int) -> Optional[Dict[str, Any]]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def update_user_settings(user_id: int, mic_enabled: bool = None, notifications_enabled: bool = None, theme: str = None) -> bool:
    db = await get_db()
    try:
        updates = []
        params = []
        if mic_enabled is not None:
            updates.append("mic_enabled = ?")
            params.append(1 if mic_enabled else 0)
        if notifications_enabled is not None:
            updates.append("notifications_enabled = ?")
            params.append(1 if notifications_enabled else 0)
        if theme is not None:
            updates.append("theme = ?")
            params.append(theme)
        if updates:
            params.append(user_id)
            await db.execute(f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?", params)
            await db.commit()
        return True
    finally:
        await db.close()


async def update_user_location(user_id: int, latitude: float, longitude: float, city: Optional[str] = None) -> bool:
    db = await get_db()
    try:
        now = time.time()
        updates = ["latitude = ?", "longitude = ?", "location_updated_at = ?"]
        params = [latitude, longitude, now]
        if city:
            updates.append("location_descriptor = ?")
            params.append(city)
        params.append(user_id)
        await db.execute(f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?", params)
        await db.commit()
        return True
    finally:
        await db.close()


async def get_latest_user_location() -> Optional[Dict[str, Any]]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT latitude, longitude, location_descriptor, location_updated_at FROM user_settings WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY location_updated_at DESC LIMIT 1")
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


# ── Emergency Contacts CRUD ─────────────────────────────────────────────────────

def generate_pairing_token() -> str:
    """Generate a URL-safe unique pairing token (Telegram deep-link payload constraint: A-Za-z0-9_-)."""
    return secrets.token_urlsafe(24)


async def create_contact(user_id: int, contact_name: str) -> Dict[str, Any]:
    """Create a new pending emergency contact with a unique pairing token."""
    token = generate_pairing_token()
    now = time.time()
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO emergency_contacts (user_id, contact_name, pairing_token, status, created_at) VALUES (?, ?, ?, 'PENDING', ?)",
            (user_id, contact_name, token, now),
        )
        contact_id = cursor.lastrowid
        await db.commit()
        return {
            "id": contact_id,
            "user_id": user_id,
            "contact_name": contact_name,
            "pairing_token": token,
            "telegram_chat_id": None,
            "telegram_username": None,
            "status": "PENDING",
            "created_at": now,
        }
    finally:
        await db.close()


async def get_contacts_for_user(user_id: int) -> List[Dict[str, Any]]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM emergency_contacts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_all_verified_contacts() -> List[Dict[str, Any]]:
    """Return all verified contacts across all users (for alert dispatch)."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM emergency_contacts WHERE status = 'VERIFIED' AND telegram_chat_id IS NOT NULL")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_verified_contacts_for_user(user_id: int) -> List[Dict[str, Any]]:
    """Return verified contacts for a specific user."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM emergency_contacts WHERE user_id = ? AND status = 'VERIFIED' AND telegram_chat_id IS NOT NULL",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_active_target_chats(user_id: Optional[int] = None) -> List[str]:
    """
    Get target Telegram chat IDs for emergency dispatch.
    Prioritizes verified contacts in the database for the given user (or all users).
    Only falls back to TELEGRAM_CHAT_IDS from .env if no verified contacts exist in the DB.
    """
    if user_id is not None:
        contacts = await get_verified_contacts_for_user(user_id)
    else:
        contacts = await get_all_verified_contacts()

    db_chats = [
        str(c["telegram_chat_id"]).strip()
        for c in contacts
        if c.get("telegram_chat_id") and str(c["telegram_chat_id"]).strip()
    ]
    if db_chats:
        # Return unique DB verified contacts
        return list(dict.fromkeys(db_chats))

    # Fallback to .env only if zero verified contacts exist in DB
    env_chats_str = os.getenv("TELEGRAM_CHAT_IDS", "")
    env_chats = [cid.strip() for cid in env_chats_str.split(",") if cid.strip()]
    return env_chats


async def verify_contact_by_token(pairing_token: str, telegram_chat_id: str, telegram_username: str = None) -> Optional[Dict[str, Any]]:
    """Pair a Telegram user to a pending contact via deep-link token."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM emergency_contacts WHERE pairing_token = ?", (pairing_token,))
        row = await cursor.fetchone()
        if not row:
            return None
        contact = dict(row)
        if contact["status"] == "VERIFIED":
            return contact  # Already verified

        now = time.time()
        await db.execute(
            "UPDATE emergency_contacts SET telegram_chat_id = ?, telegram_username = ?, status = 'VERIFIED', verified_at = ? WHERE id = ?",
            (telegram_chat_id, telegram_username, now, contact["id"]),
        )
        await db.commit()

        contact["telegram_chat_id"] = telegram_chat_id
        contact["telegram_username"] = telegram_username
        contact["status"] = "VERIFIED"
        contact["verified_at"] = now
        return contact
    finally:
        await db.close()


async def delete_contact(contact_id: int, user_id: int) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM emergency_contacts WHERE id = ? AND user_id = ?", (contact_id, user_id))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()

