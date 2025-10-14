import threading
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.routes.spreadsheet import spreadsheet_bp
from app.routes.whapi import whapi_bp
from app.business.groups import update_allowed_groups
from app.logger import loggerApp
from app.services.whapi import setup_whapi_webhook


load_dotenv()


def create_app():
    def _init_groups():
        try:
            update_allowed_groups()
        except Exception as e:
            loggerApp.error(f"❌ Error updating groups: {e}")

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(whapi_bp)
    app.register_blueprint(spreadsheet_bp)
    threading.Thread(target=_init_groups, daemon=True).start()
    threading.Thread(target=setup_whapi_webhook, daemon=True).start()
    return app


