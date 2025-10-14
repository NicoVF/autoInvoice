from flask import Blueprint, request, jsonify
from app.logger import loggerWhappi
from app.business.groups import ALLOWED_GROUPS_CACHE
from app.business.invoices import handle_invoice


whapi_bp = Blueprint('whapi', __name__)


@whapi_bp.route("/whapi/events", methods=["POST"])
def whapi_events():
    try:
        data = request.get_json(force=True, silent=True) or {}
        loggerWhappi.info(data)
        messages = data.get("messages", [])
        for msg in messages:
            try:
                if msg["from_me"]:
                    continue
                chat_id = msg.get("chat_id", "")
                chat_name = msg.get("chat_name", "")
                msg_type = msg.get("type", "")
                message_id = msg.get("id")

                if not (chat_id.endswith("@g.us") and any(g["name"] == chat_name for g in ALLOWED_GROUPS_CACHE["groups"])):
                    loggerWhappi.info(f"Message ignored from non-authorized chat: {chat_name}")
                    continue

                if msg_type == "document" and msg.get("document", {}).get("mime_type") == "application/pdf":
                    handle_invoice(chat_id, message_id, msg["document"]["link"], "pdf", chat_name)

                elif msg_type == "image":
                    handle_invoice(chat_id, message_id, msg["image"]["link"], "image", chat_name)

            except Exception as e:
                loggerWhappi.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({"status": "received", "data": data})
    except Exception as e:
        loggerWhappi.exception(f"Fatal error in /whapi/events: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
