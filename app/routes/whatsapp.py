import os
from flask import Blueprint, request, jsonify
from app.logger import loggerApp
from app.business.groups import ALLOWED_GROUPS_CACHE, get_group_balance
from app.services.whapi import get_chat_id, send_text_message
from app.business.invoice_parser import format_arg_amount

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


@whatsapp_bp.route("/whatsapp/notify_rejected_invoices", methods=["POST"])
def notify_rejected_invoices():
    token = request.headers.get("apikey")
    if token != WHATSAPP_APIKEY:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.get_json()
        group_name = data.get("group_name")
        amount = data.get("amount")
        date = data.get("date")
        hour = data.get("hour")

        if not group_name or not amount or not date:
            return jsonify({"error": "Missing required fields (group_name, amount, date)"}), 400

        groups = ALLOWED_GROUPS_CACHE.get("groups", [])
        group = next((g for g in groups if g["name"].lower() == group_name.lower()), None)
        if not group:
            loggerApp.warning(f"Group not found: {group_name}")
            return jsonify({"error": f"Group not found '{group_name}'"}), 404
        chat_id = get_chat_id(chat_name=group_name, chat_type="group")
        if not chat_id:
            loggerApp.warning(f"Whapi ChatID not found: {group_name}")
            raise ValueError("Whapi ChatID not found")
        message = f"❌ Comprobante rechazado ❌\n\n💸 Monto: *${format_arg_amount(amount)}*\n📅 Fecha: {date}\n🕒 Hora: {hour}\n\n" \
                  f"Te recordamos que para habilitar la transacción necesitamos que reclames con el banco."
        send_text_message(chat_id, message)
        loggerApp.info({"status": "ok", "group": group_name, "chat_id": chat_id, "message": message})
        return jsonify({
            "status": "ok",
            "group": group_name,
            "chat_id": chat_id,
            "message": message
        }), 200
    except Exception as e:
        loggerApp.error(f"Error in send_daily_balance: {e}")
    return jsonify({"error": str(e)}), 500
