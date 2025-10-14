import os
from app.services.spreadsheet import append_row_to_sheet
from app.business.groups import get_group_commission, get_group_expected_cbu
from app.services.whapi import send_text_message
from app.business.invoice_parser import parse_invoice, build_summary, format_arg_amount
from app.logger import loggerApp


SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SPREADSHEET_SHEET_GENERAL = os.environ["SPREADSHEET_SHEET_GENERAL"]


def append_invoice_row(data, group_name):
    row = [
        data.get("date") or "",
        data.get("time") or "",
        group_name or "",
        data.get("amount") or "",
        data.get("sender_name") or "",
        data.get("sender_cuit") or "",
        data.get("sender_cvu") or "",
        data.get("receiver_name") or "",
        data.get("receiver_cvu") or "",
        data.get("receiver_cuit") or "",
        data.get("operation_id") or "",
        data.get("bank") or "",
        "❌ Pendiente",
        data.get("notes") or "",
    ]
    return append_row_to_sheet(SPREADSHEET_ID, SPREADSHEET_SHEET_GENERAL, row)


def handle_invoice(chat_id, message_id, file_url, file_type, chat_name):
    try:
        parsed = parse_invoice(file_url, file_type=file_type)
        if not parsed:
            send_text_message(chat_id, "❌ Error al leer el comprobante.", reply_to=message_id)
            return

        amount = parsed.get("amount") or 0
        if amount <= 0:
            return

        receiver_cvu = parsed.get("receiver_cvu")
        summary = build_summary(parsed)
        if (expected_cbu := get_group_expected_cbu(chat_name)) and receiver_cvu and receiver_cvu != expected_cbu:
            parsed["notes"] = "❌ Comprobante rebotado ❌"
            send_text_message(chat_id, f"❌ Comprobante rebotado ❌\n\n{summary}", reply_to=message_id)
            append_invoice_row(parsed, chat_name)
            return
        if commission := get_group_commission(chat_name):
            final_amount = amount - (amount * commission / 100)
            text_amount_with_commission = (
                f"\n\n💰 *Monto a liquidar:* *${format_arg_amount(final_amount)}*")
        else:
            text_amount_with_commission = ""
        send_text_message(chat_id, f"{summary}{text_amount_with_commission}", reply_to=message_id)
        append_invoice_row(parsed, chat_name)
    except Exception as e:
        loggerApp.exception(f"Error in handle_invoice: {e}")
        send_text_message(chat_id, "⚠️ Error interno al procesar el comprobante.", reply_to=message_id)
