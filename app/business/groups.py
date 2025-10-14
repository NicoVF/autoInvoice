import os
import threading
from app.logger import loggerApp
from app.services.spreadsheet import fetch_rows_from_sheet

ALLOWED_GROUPS_CACHE = {"groups": []}
CACHE_LOCK = threading.Lock()

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SPREADSHEET_SHEET_GROUPS = os.environ["SPREADSHEET_SHEET_GROUPS"]
SPREADSHEET_GROUPS_NAMES_COLUMN = int(os.environ["SPREADSHEET_GROUPS_NAMES_COLUMN"])
SPREADSHEET_GROUPS_ACTIVE_COLUMN = int(os.environ["SPREADSHEET_GROUPS_ACTIVE_COLUMN"])
SPREADSHEET_GROUPS_COMMISSION = int(os.environ["SPREADSHEET_GROUPS_COMMISSION"])
SPREADSHEET_GROUPS_EXPECTED_CBU = int(os.environ["SPREADSHEET_GROUPS_EXPECTED_CBU"])


def update_allowed_groups():
    try:
        rows = fetch_rows_from_sheet(SPREADSHEET_ID, SPREADSHEET_SHEET_GROUPS, [
                SPREADSHEET_GROUPS_NAMES_COLUMN,
                SPREADSHEET_GROUPS_ACTIVE_COLUMN,
                SPREADSHEET_GROUPS_COMMISSION,
                SPREADSHEET_GROUPS_EXPECTED_CBU,
            ], has_headers=True)
        groups = []
        for name, is_active, commission, expected_cbu in rows:
            name = name.strip()
            if not name or is_active.upper() != "TRUE":
                continue
            try:
                commission_value = float(
                    commission.replace(",", ".").replace("%", "")
                )
            except (ValueError, AttributeError):
                commission_value = None
            groups.append({
                "name": name,
                "commission": commission_value,
                "expected_cbu": expected_cbu
            })
        with CACHE_LOCK:
            ALLOWED_GROUPS_CACHE["groups"].clear()
            ALLOWED_GROUPS_CACHE["groups"].extend(groups)
        loggerApp.info(f"Groups updated: {len(groups)} - {groups}")
        return groups
    except Exception as e:
        loggerApp.exception(f"❌ Error updating groups: {e}")
        return []


def get_group_commission(chat_name):
    for g in ALLOWED_GROUPS_CACHE["groups"]:
        if g["name"] == chat_name:
            return g["commission"]
    return None


def get_group_expected_cbu(chat_name):
    for g in ALLOWED_GROUPS_CACHE["groups"]:
        if g["name"] == chat_name:
            return g["expected_cbu"]
    return None
