import os
import requests
from app.logger import loggerWhappi

WHAPI_URL = os.environ.get("WHAPI_URL")
WHAPI_TOKEN = os.environ.get("WHAPI_TOKEN")


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
