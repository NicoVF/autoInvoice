import os
from app.services.spreadsheet import append_row_to_sheet
from app.business.groups import get_group_commission, get_group_expected_cbu, get_group_expected_name, \
    get_group_expected_alias, get_group_expected_cuit
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
        data.get("alias") or "",
        data.get("receiver_cuit") or "",
        data.get("operation_id") or "",
        data.get("bank") or "",
        "❌ Pendiente",
        data.get("notes") or "",
    ]
    return append_row_to_sheet(SPREADSHEET_ID, SPREADSHEET_SHEET_GENERAL, row)


def handle_invoice(chat_id, message_id, file_url, file_type, chat_name, from_me=False):
    try:
        parsed = parse_invoice(chat_name, file_url, file_type)
        if not parsed:
            send_text_message(chat_id, "❌ Error al leer el comprobante.", reply_to=message_id)
            return

        amount = parsed.get("amount") or 0
        if amount <= 0:
            return

        sender_cvu = parsed.get("sender_cvu")
        if from_me and (expected_cbu := get_group_expected_cbu(chat_name)) and sender_cvu and sender_cvu == expected_cbu:
            parsed["amount"] = -abs(amount)
            parsed["notes"] = "💸 Comprobante enviado (egreso)"
            append_invoice_row(parsed, chat_name)
            return

        receiver_cvu = parsed.get("receiver_cvu")
        receiver_alias = parsed.get("receiver_alias")
        receiver_name = parsed.get("receiver_name")
        receiver_cuit = parsed.get("receiver_cuit")
        expected_cbu = get_group_expected_cbu(chat_name)
        expected_alias = get_group_expected_alias(chat_name)
        expected_name = get_group_expected_name(chat_name)
        expected_cuit = get_group_expected_cuit(chat_name)
        loggerApp.info(expected_alias)
        loggerApp.info(receiver_alias)
        summary = build_summary(parsed)
        match_reasons = []
        if expected_cbu and receiver_cvu and receiver_cvu == expected_cbu:
            match_reasons.append("CBU")
        if expected_alias and receiver_alias and receiver_alias == expected_alias:
            match_reasons.append("Alias")
        if expected_cuit and receiver_cuit and receiver_cuit == expected_cuit:
            match_reasons.append("Cuit")
        if expected_name and receiver_name and receiver_name == expected_name:
            match_reasons.append("Nombre")
        if match_reasons:
            parsed["notes"] = f"✅ Comprobante aprobado por {', '.join(match_reasons)}"
        else:
            parsed["notes"] = "❌ Comprobante rebotado ❌"
            send_text_message(chat_id, f"❌ Comprobante rebotado ❌\n\n{summary}", reply_to=message_id)
            append_invoice_row(parsed, chat_name)
            return
        text_amount_with_commission = ""
        if commission := get_group_commission(chat_name):
            final_amount = amount - (amount * commission / 100)
            text_amount_with_commission = (
                f"\n\n💰 *Monto a liquidar:* *${format_arg_amount(final_amount)}*")
        send_text_message(chat_id, f"{summary}{text_amount_with_commission}", reply_to=message_id)
        append_invoice_row(parsed, chat_name)
    except Exception as e:
        loggerApp.exception(f"Error in handle_invoice: {e}")
        send_text_message(chat_id, "⚠️ Error interno al procesar el comprobante.", reply_to=message_id)
