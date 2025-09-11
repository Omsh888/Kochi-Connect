import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import SCOPES

def get_gmail_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("⚠️ token.json missing or invalid. Re-authenticate.")
    return creds
