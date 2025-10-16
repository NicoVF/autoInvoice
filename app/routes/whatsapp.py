import os
from flask import Blueprint, request, jsonify
from app.logger import loggerApp
from app.business.groups import ALLOWED_GROUPS_CACHE, get_group_balance
from app.services.whapi import get_chat_id, send_text_message


whatsapp_bp = Blueprint("whatsapp", __name__)
WHATSAPP_APIKEY = os.environ.get("WHATSAPP_APIKEY")


@whatsapp_bp.route("/whatsapp/send_daily_balance", methods=["POST"])
def send_daily_balance():
    token = request.headers.get("apikey")
    if token != WHATSAPP_APIKEY:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        groups = ALLOWED_GROUPS_CACHE.get("groups", [])
        results = []
        for group in groups:
            group_name = group["name"]
            try:
                chat_id = get_chat_id(chat_name=group_name, chat_type="group")
                if not chat_id:
                    loggerApp.warning(f"Whapi ChatID not found: {group_name}")
                    raise ValueError("Whapi ChatID not found")
                balance = get_group_balance(group_name)
                if balance is None:
                    raise ValueError("Balance not found")
                send_text_message(chat_id, f"👋 Buen día!\nTu saldo disponible al día de hoy es: ${balance} ✅")
                results.append({"group": group_name, "balance": balance, "status": "sent", "chat_id": chat_id})
            except Exception as e:
                loggerApp.error(f"Failed to send message to '{group_name}': {e}")
                results.append({"group": group_name, "status": "error", "error": str(e)})
        loggerApp.info({"status": "ok", "results": results})
        return jsonify({"status": "ok", "results": results}), 200
    except Exception as e:
        loggerApp.error(f"Error in send_daily_balance: {e}")
    return jsonify({"error": str(e)}), 500
