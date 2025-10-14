import os
import threading
from flask import Blueprint, request, jsonify
from app.services.spreadsheet import fetch_groups_from_sheets
from app.logger import loggerGSpreadsheet


spreadsheet_bp = Blueprint("spreadsheet", __name__)
SPREADSHEET_APIKEY = os.environ.get("SPREADSHEET_APIKEY")
ALLOWED_GROUPS_CACHE = {"groups": []}
CACHE_LOCK = threading.Lock()


@spreadsheet_bp.route("/spreadsheet/groups", methods=["POST"])
def sync_spreadsheet():
    token = request.headers.get("apikey")
    if token != SPREADSHEET_APIKEY:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        update_allowed_groups()
        groups = ALLOWED_GROUPS_CACHE["groups"]
        return jsonify({"status": "ok", "count": len(groups), "groups": groups})
    except Exception as e:
        loggerGSpreadsheet.error({"status": "error", "msg": str(e)})
        return jsonify({"status": "error", "msg": str(e)}), 500


def update_allowed_groups():
    with CACHE_LOCK:
        groups = fetch_groups_from_sheets()
        ALLOWED_GROUPS_CACHE["groups"].clear()
        ALLOWED_GROUPS_CACHE["groups"].extend(groups)
    loggerGSpreadsheet.info(f"Groups updated: {len(groups)} - {groups}")


def get_group_commission(chat_name):
    for g in ALLOWED_GROUPS_CACHE["groups"]:
        if g["name"] == chat_name:
            return g["commission"]
    return None
