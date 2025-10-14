import threading

from flask import Flask
from flask_cors import CORS
from app.routes.spreadsheet import spreadsheet_bp, update_allowed_groups
from app.routes.whapi import whapi_bp
from dotenv import load_dotenv


load_dotenv()


def create_app():
    def _init_groups():
        try:
            update_allowed_groups()
        except Exception as e:
            app.logger.error(f"❌ Error updating groups: {e}")

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(whapi_bp)
    app.register_blueprint(spreadsheet_bp)
    threading.Thread(target=_init_groups, daemon=True).start()
    return app


