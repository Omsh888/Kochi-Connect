import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from app.auth.auth import get_gmail_credentials

def get_drive_service():
    creds = get_gmail_credentials()
    return build("drive", "v3", credentials=creds)

def upload_to_drive(file_name: str, file_bytes: bytes, mime_type="application/octet-stream") -> str:
    service = get_drive_service()
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)
    file_metadata = {"name": file_name}

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    # make public link
    service.permissions().create(
        fileId=file["id"],
        body={"role": "reader", "type": "anyone"}
    ).execute()

    return file["webViewLink"]
