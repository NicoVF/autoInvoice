from app.services import gspread_client
from app.logger import loggerGSpreadsheet


def fetch_rows_from_sheet(spreadsheet_id, sheet_name, columns, has_headers=True, as_dict=False, keys=None):
    """
    Fetch rows from a Google Sheet using column indices.

    Args:
        spreadsheet_id (str): Google Spreadsheet ID.
        sheet_name (str): Name of the worksheet/tab.
        columns (list[int]): 1-based column numbers to extract.
        has_headers (bool): Whether the first row contains headers (skip it). Default: True.
        as_dict (bool): If True, returns a list of dictionaries.
        keys (list[str]): Optional list of keys to use when as_dict=True.

    Returns:
        list[list[str]] or list[dict]: Extracted data.
    """
    sheet = gspread_client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    all_values = sheet.get_all_values()
    if not all_values:
        return []
    start_index = 1 if has_headers else 0
    data = []
    for row in all_values[start_index:]:
        selected = [
            row[i - 1].strip() if len(row) >= i and row[i - 1] else ""
            for i in columns
        ]
        data.append(selected)
    if as_dict:
        if not keys:
            # Generate generic keys if none provided
            keys = [f"col_{i}" for i in columns]
        return [dict(zip(keys, row)) for row in data]
    return data


def append_row_to_sheet(spreadsheet_id, sheet_name, values, value_input_option="USER_ENTERED"):
    """
    Appends a new row to a Google Sheet.

    Args:
        spreadsheet_id (str): Google Spreadsheet ID.
        sheet_name (str): Name of the worksheet/tab.
        values (list): List of values to append.
        value_input_option (str): "RAW" or "USER_ENTERED". Default: "USER_ENTERED".

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        sheet = gspread_client.open_by_key(spreadsheet_id).worksheet(sheet_name)
        sheet.append_row(values, value_input_option=value_input_option)
        loggerGSpreadsheet.info(f"Row appended to '{sheet_name}': {values}")
        return True
    except Exception as e:
        loggerGSpreadsheet.error(f"Failed to append row to '{sheet_name}': {e}")
        return False


def get_spreadsheet_metadata(spreadsheet_id):
    try:
        spreadsheet = gspread_client.open_by_key(spreadsheet_id)
        metadata = {
            "sheets": [
                {"properties": {"title": ws.title, "id": ws.id}}
                for ws in spreadsheet.worksheets()
            ]
        }
        return metadata
    except Exception as e:
        loggerGSpreadsheet.error(f"Error getting spreadsheet metadata: {e}")
        return {"sheets": []}


def sheet_exists(spreadsheet_id: str, sheet_name: str) -> bool:
    try:
        metadata = get_spreadsheet_metadata(spreadsheet_id)
        sheet_names = [s["properties"]["title"] for s in metadata.get("sheets", [])]
        exists = sheet_name in sheet_names
        if not exists:
            loggerGSpreadsheet.warning(f"Sheet not found: '{sheet_name}'")
        return exists
    except Exception as e:
        loggerGSpreadsheet.error(f"Error checking sheet existence: {e}")
        return False
