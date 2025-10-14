from app.services import gspread_client
from app.logger import loggerGSpreadsheet
import os


SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SPREADSHEET_SHEET_GROUPS = os.environ["SPREADSHEET_SHEET_GROUPS"]
SPREADSHEET_SHEET_GENERAL = os.environ["SPREADSHEET_SHEET_GENERAL"]
SPREADSHEET_GROUPS_NAMES_COLUMN = int(os.environ["SPREADSHEET_GROUPS_NAMES_COLUMN"])
SPREADSHEET_GROUPS_ACTIVE_COLUMN = int(os.environ["SPREADSHEET_GROUPS_ACTIVE_COLUMN"])
SPREADSHEET_GROUPS_COMMISSION = int(os.environ["SPREADSHEET_GROUPS_COMMISSION"])


def fetch_groups_from_sheets():
    sheet = gspread_client.open_by_key(SPREADSHEET_ID).worksheet(SPREADSHEET_SHEET_GROUPS)
    names = sheet.col_values(SPREADSHEET_GROUPS_NAMES_COLUMN)
    active = sheet.col_values(SPREADSHEET_GROUPS_ACTIVE_COLUMN)
    commissions = sheet.col_values(SPREADSHEET_GROUPS_COMMISSION)
    groups = []
    for name, is_active, commission in zip(names[1:], active[1:], commissions[1:]):
        name = name.strip()
        if not name or is_active.upper() != "TRUE":
            continue
        try:
            commission_value = float(commission.replace(",", ".").replace("%", ""))
        except (ValueError, AttributeError):
            commission_value = None

        groups.append({
            "name": name,
            "commission": commission_value
        })

    return groups


def append_invoice_row(data, group_name):
    try:
        sheet = gspread_client.open_by_key(SPREADSHEET_ID).worksheet(SPREADSHEET_SHEET_GENERAL)
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
            "❌ Pendiente"
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        loggerGSpreadsheet.info(f"✅ Row appended to 'General' (Group: {group_name}, Bank: {data.get('bank')}, OpID: {data.get('operation_id')})")
        return True
    except Exception as e:
        loggerGSpreadsheet.error(f"❌ Failed to write data to Google Sheet: {e}")
        return False
