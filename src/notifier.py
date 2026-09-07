import requests
from typing import Dict, Any


def send_notification(config: Dict[str, Any], title: str, message: str) -> None:
    """Send notification via Telegram or generic Webhook based on config."""
    noti_cfg = config.get("notifications", {})
    if not noti_cfg.get("enabled", False):
        return

    noti_type = noti_cfg.get("type", "webhook").lower()
    text = f"*{title}*\n{message}"

    try:
        if noti_type == "telegram":
            tg_cfg = noti_cfg.get("telegram", {})
            bot_token = tg_cfg.get("bot_token")
            chat_id = tg_cfg.get("chat_id")
            if bot_token and chat_id:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": f"<b>{title}</b>\n<pre>{message}</pre>",
                    "parse_mode": "HTML"
                }
                requests.post(url, json=payload, timeout=10)
        elif noti_type in ("discord", "webhook"):
            webhook_url = noti_cfg.get("webhook_url")
            if webhook_url:
                payload = {
                    "content": f"**{title}**\n{message}"
                }
                requests.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        print(f"[Notifier Error] Failed to send notification: {e}")
