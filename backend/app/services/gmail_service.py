from googleapiclient.discovery import build
from app.auth.auth import get_gmail_credentials

def get_gmail_service():
    creds = get_gmail_credentials()
    return build("gmail", "v1", credentials=creds)
