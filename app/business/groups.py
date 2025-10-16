import os
import threading
from app.logger import loggerApp
from app.services.spreadsheet import fetch_rows_from_sheet, sheet_exists


ALLOWED_GROUPS_CACHE = {"groups": []}
CACHE_LOCK = threading.Lock()

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SPREADSHEET_SHEET_GROUPS = os.environ["SPREADSHEET_SHEET_GROUPS"]
SPREADSHEET_GROUPS_NAMES_COLUMN = int(os.environ["SPREADSHEET_GROUPS_NAMES_COLUMN"])
SPREADSHEET_GROUPS_ACTIVE_COLUMN = int(os.environ["SPREADSHEET_GROUPS_ACTIVE_COLUMN"])
SPREADSHEET_GROUPS_COMMISSION = int(os.environ["SPREADSHEET_GROUPS_COMMISSION"])
SPREADSHEET_GROUPS_EXPECTED_CBU = int(os.environ["SPREADSHEET_GROUPS_EXPECTED_CBU"])
SPREADSHEET_GROUPS_EXPECTED_ALIAS = int(os.environ["SPREADSHEET_GROUPS_EXPECTED_ALIAS"])
SPREADSHEET_GROUPS_EXPECTED_CUIT = int(os.environ["SPREADSHEET_GROUPS_EXPECTED_CUIT"])
SPREADSHEET_GROUPS_EXPECTED_NAME = int(os.environ["SPREADSHEET_GROUPS_EXPECTED_NAME"])
SPREADSHEET_COLUMN_GROUPS_TODAY_AVAILABLE_BALANCE = int(os.environ["SPREADSHEET_COLUMN_GROUPS_TODAY_AVAILABLE_BALANCE"])
SPREADSHEET_ROW_GROUPS_TODAY_AVAILABLE_BALANCE = int(os.environ["SPREADSHEET_ROW_GROUPS_TODAY_AVAILABLE_BALANCE"])


def update_allowed_groups():
    try:
        rows = fetch_rows_from_sheet(SPREADSHEET_ID, SPREADSHEET_SHEET_GROUPS, [
                SPREADSHEET_GROUPS_NAMES_COLUMN,
                SPREADSHEET_GROUPS_ACTIVE_COLUMN,
                SPREADSHEET_GROUPS_COMMISSION,
                SPREADSHEET_GROUPS_EXPECTED_CBU,
                SPREADSHEET_GROUPS_EXPECTED_ALIAS,
                SPREADSHEET_GROUPS_EXPECTED_CUIT,
                SPREADSHEET_GROUPS_EXPECTED_NAME,
            ], has_headers=True)
        groups = []
        for name, is_active, commission, expected_cbu, expected_alias, expected_cuit, expected_name in rows:
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
                "expected_cbu": expected_cbu,
                "expected_alias": expected_alias,
                "expected_cuit": expected_cuit,
                "expected_name": expected_name
            })
        with CACHE_LOCK:
            ALLOWED_GROUPS_CACHE["groups"].clear()
            ALLOWED_GROUPS_CACHE["groups"].extend(groups)
        loggerApp.info(f"Groups updated: {len(groups)} - {groups}")
        return groups
    except Exception as e:
        loggerApp.exception(f"❌ Error updating groups: {e}")
        return []


def get_group_balance(group_name):
    try:
        if not sheet_exists(SPREADSHEET_ID, group_name):
            loggerApp.warning(f"Sheet not found for group '{group_name}'")
            raise Exception(f"Sheet not found for group '{group_name}'")
        column_cell = SPREADSHEET_COLUMN_GROUPS_TODAY_AVAILABLE_BALANCE
        row_cell = SPREADSHEET_ROW_GROUPS_TODAY_AVAILABLE_BALANCE
        values = fetch_rows_from_sheet(SPREADSHEET_ID, group_name, [column_cell], has_headers=False)
        if not values or not values[0] or not values[0][0]:
            loggerApp.warning(f"No balance found in {group_name}! {chr(64 + column_cell)}{row_cell}")
            return None
        raw_value = str(values[0][row_cell - 1]).strip()
        try:
            balance = raw_value.replace(".", "X").replace(",", ".").replace("X", ",").replace("$", "").strip()
            balance = balance if float(balance.replace(".", "").replace(",", ".").strip()) > 0 else "0,00"          ## Si es negativo, enviamos 0
        except ValueError:
            loggerApp.warning(f"Invalid balance format in {group_name}!{column_cell}{row_cell}: '{raw_value}'")
            return None
        loggerApp.info(f"Balance for '{group_name}': {balance}")
        return balance
    except Exception as e:
        loggerApp.error(f"Error fetching balance for '{group_name}': {e}")
        return None


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


def get_group_expected_alias(chat_name):
    for g in ALLOWED_GROUPS_CACHE["groups"]:
        if g["name"] == chat_name:
            return g["expected_alias"].lower().strip()
    return None


def get_group_expected_name(chat_name):
    for g in ALLOWED_GROUPS_CACHE["groups"]:
        if g["name"] == chat_name:
            return g["expected_name"].lower().strip()
    return None


def get_group_expected_cuit(chat_name):
    for g in ALLOWED_GROUPS_CACHE["groups"]:
        if g["name"] == chat_name:
            return re.sub(r"[-\s]", "", g["expected_cuit"])
    return None