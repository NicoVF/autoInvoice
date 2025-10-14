import json
import os
import gspread
from google.cloud import vision
from google.oauth2.service_account import Credentials


def init_cloud_vision():
    credentials = Credentials.from_service_account_info(json.loads(os.environ["CREDENTIALS_JSON"]))
    return vision.ImageAnnotatorClient(credentials=credentials)


def init_gspread():
    creds = Credentials.from_service_account_info(
        json.loads(os.environ["CREDENTIALS_JSON"]),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
        ],
    )
    return gspread.authorize(creds)


gspread_client = init_gspread()
cloud_vision_client = init_cloud_vision()

