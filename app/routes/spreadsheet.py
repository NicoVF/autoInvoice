import os
from flask import Blueprint, request, jsonify
from app.logger import loggerGSpreadsheet
from app.business.groups import ALLOWED_GROUPS_CACHE, update_allowed_groups


spreadsheet_bp = Blueprint("spreadsheet", __name__)
SPREADSHEET_APIKEY = os.environ.get("SPREADSHEET_APIKEY")


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
