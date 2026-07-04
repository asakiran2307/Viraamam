"""Telegram notification service for new orders."""
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

def send_telegram_notification(order_id: int, amount: float, items_summary: str):
    """Send a notification to the admin's Telegram chat."""
    bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    chat_id = current_app.config.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.warning("Telegram bot token or chat ID not configured. Skipping notification.")
        return False

    message = (
        f"🚨 *New Order Received!* 🚨\n\n"
        f"📦 *Order ID:* #{order_id}\n"
        f"💰 *Amount Paid:* ₹{amount:.2f}\n"
        f"🛒 *Items:*\n{items_summary}\n\n"
        f"Check the admin dashboard for more details."
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Telegram notification sent for order #{order_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False
