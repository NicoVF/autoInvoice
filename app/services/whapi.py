import os
import requests
from app.logger import loggerWhappi

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WHAPI_URL = os.environ.get("WHAPI_URL")
WHAPI_TOKEN = os.environ.get("WHAPI_TOKEN")


def setup_whapi_webhook():
    try:
        base_url = WHAPI_URL
        token = WHAPI_TOKEN
        bot_url = WEBHOOK_URL + "whapi/events"

        if not token or not bot_url:
            loggerWhappi.warning("WHAPI_TOKEN or BOT_URL not defined. Webhook was not configured.")
            return False

        endpoint = f"{base_url}/settings"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "webhooks": [
                {
                    "url": bot_url,
                    "events": [{"type": "messages", "method": "post"}],
                    "mode": "method"
                }
            ]
        }
        loggerWhappi.info(f"Setting Whapi webhook to: {bot_url}")
        response = requests.patch(endpoint, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            loggerWhappi.info(f"Webhook successfully configured: {bot_url}")
            return True
        else:
            loggerWhappi.error(
                f"Failed to configure webhook "
                f"({response.status_code}): {response.text}"
            )
            return False
    except requests.exceptions.Timeout:
        loggerWhappi.error("⏳ Timeout while configuring webhook (Whapi.Cloud took too long to respond).")
        return False
    except requests.exceptions.RequestException as e:
        loggerWhappi.error(f"Request error while configuring webhook: {e}")
        return False
    except Exception as e:
        loggerWhappi.error(f"Unexpected exception while configuring webhook: {e}")
        return False


def send_text_message(chat_id, text, reply_to=None):
    headers = {"Authorization": f"Bearer {WHAPI_TOKEN}", "Content-Type": "application/json"}
    payload = {"to": chat_id, "body": text}
    if reply_to:
        payload["quoted"] = reply_to
    try:
        resp = requests.post(f"{WHAPI_URL}messages/text", json=payload, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        loggerWhappi.error(f"Unexpected error sending message to {chat_id}: {e}")
    return None
