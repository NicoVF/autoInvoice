import os
from flask import Blueprint, request, jsonify
from app.logger import loggerWhappi
from app.routes.spreadsheet import ALLOWED_GROUPS_CACHE, get_group_commission
from app.services.whapi import send_text_message
from app.business.invoice_parser import parse_invoice, build_summary, format_arg_amount
from app.services.spreadsheet import append_invoice_row


whapi_bp = Blueprint('whapi', __name__)
EXPECTED_RECEIVER_CVU = os.getenv("EXPECTED_RECEIVER_CVU")


@whapi_bp.route("/whapi/events", methods=["POST"])
def whapi_events():
    data = request.json
    loggerWhappi.info(data)
    messages = data.get("messages", [])
    for msg in messages:
        if msg["from_me"]:
            continue
        chat_id = msg.get("chat_id", "")
        chat_name = msg.get("chat_name", "")
        msg_type = msg.get("type", "")
        message_id = msg.get("id")
        text = msg.get("text", {}).get("body", "")

        if not (chat_id.endswith("@g.us") and any(g["name"] == chat_name for g in ALLOWED_GROUPS_CACHE["groups"])):
            loggerWhappi.info(f"Message ignored from non-authorized chat: {chat_name}")
            continue

        if msg_type == "document" and msg.get("document", {}).get("mime_type") == "application/pdf":
            handle_invoice(chat_id, message_id, msg["document"]["link"], "pdf", chat_name)

        elif msg_type == "image":
            handle_invoice(chat_id, message_id, msg["image"]["link"], "image", chat_name)

    return jsonify({"status": "received", "data": data})


def handle_invoice(chat_id, message_id, file_url, file_type, chat_name):
    parsed = parse_invoice(file_url, file_type=file_type)
    if not parsed:
        send_text_message(chat_id, "❌ Error al leer el comprobante.", reply_to=message_id)
        return
    amount = parsed.get("amount")
    if not amount or amount == 0:
        return
    receiver_cvu = parsed.get("receiver_cvu")
    summary = build_summary(parsed)
    if EXPECTED_RECEIVER_CVU and receiver_cvu and receiver_cvu != EXPECTED_RECEIVER_CVU:
        send_text_message(chat_id, f"❌ Comprobante rebotado ❌\n\n{summary}", reply_to=message_id)
    else:
        if commission := get_group_commission(chat_name):
            amount = parsed.get("amount") or 0
            amount_with_commission = amount - (amount * commission / 100)
            text_amount_with_commission = (
                f"\n\n💰 *Monto a liquidar:* *${format_arg_amount(amount_with_commission)}*")
        else:
            text_amount_with_commission = ""
        send_text_message(chat_id, f"{summary}{text_amount_with_commission}", reply_to=message_id)
    append_invoice_row(parsed, chat_name)
