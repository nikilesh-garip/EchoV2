"""
Telegram Webhook Setup Utility Script

Configures the public webhook URL with the Telegram Bot API so that when users
click the [ 🛑 ACKNOWLEDGE EMERGENCY ] inline button in Telegram, Telegram sends
the callback query directly to your FastAPI server (/telegram/webhook).

Usage:
    python setup_telegram_webhook.py --url https://your-domain.ngrok-free.app
"""

import argparse
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def setup_webhook(bot_token: str, public_url: str) -> None:
    if not bot_token or "ABCdefGHIjkl" in bot_token:
        print("[-] Error: Please provide a valid TELEGRAM_BOT_TOKEN in .env or via arguments.")
        return

    # Ensure webhook endpoint path is appended
    webhook_endpoint = public_url.rstrip("/")
    if not webhook_endpoint.endswith("/telegram/webhook"):
        webhook_endpoint += "/telegram/webhook"

    print(f"[*] Registering Telegram Webhook with Telegram API...")
    print(f"    Bot Token: {bot_token[:10]}...{bot_token[-5:]}")
    print(f"    Webhook URL: {webhook_endpoint}")

    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    try:
        response = requests.post(api_url, data={"url": webhook_endpoint}, timeout=10)
        data = response.json()
        if data.get("ok"):
            print(f"[+] Success! Telegram Webhook successfully set to: {webhook_endpoint}")
            print(f"    Description: {data.get('description')}")
        else:
            print(f"[-] Telegram API Error: {data}")
    except Exception as e:
        print(f"[-] Network Exception while setting webhook: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set Telegram Bot Webhook URL")
    parser.add_argument(
        "--url",
        type=str,
        default=os.getenv("PUBLIC_WEBHOOK_URL", "https://your-ngrok-subdomain.ngrok-free.app"),
        help="Public HTTPS URL (e.g. ngrok / localtunnel URL)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        help="Telegram Bot Token",
    )
    args = parser.parse_args()

    setup_webhook(bot_token=args.token, public_url=args.url)
