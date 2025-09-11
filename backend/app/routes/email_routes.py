# from typing import List
# import base64
# from fastapi import APIRouter
# from datetime import datetime
# from app.services.gmail_service import get_gmail_service
# from app.services.drive_service import upload_to_drive
# from app.database import db
# from app.models.schemas import Document_Base_Create, Attachment
# import uuid

# emails_collection = db["document"]
# router = APIRouter()

# def parse_message(service, msg_id: str) -> dict:
#     message = service.users().messages().get(userId="me", id=msg_id).execute()
#     payload = message.get("payload", {})
#     headers = payload.get("headers", [])

#     subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
#     sender = next((h["value"] for h in headers if h["name"] == "From"), "unknown")
#     snippet = message.get("snippet", "")
#     timestamp = int(message["internalDate"]) / 1000
#     received_at = datetime.fromtimestamp(timestamp)

#     attachments_info: list[Attachment] = []
#     if "parts" in payload:
#         for part in payload["parts"]:
#             filename = part.get("filename")
#             body = part.get("body", {})
#             if filename and "attachmentId" in body:
#                 att_id = body["attachmentId"]
#                 att = service.users().messages().attachments().get(
#                     userId="me", messageId=msg_id, id=att_id
#                 ).execute()
#                 data = att.get("data")
#                 file_bytes = base64.urlsafe_b64decode(data.encode("UTF-8"))
#                 link = upload_to_drive(filename, file_bytes)
#                 attachments_info.append(Attachment(filename=filename, drive_link=link))

#     return {
#         "gmail_id": msg_id,                        # 👈 store Gmail ID
#         "text_id": str(uuid.uuid4()),
#         "sender": sender,
#         "subject": subject,
#         "extracted_text": snippet,
#         "created_at": received_at,
#         "source": "gmail",
#         "status": "open",
#         "attachments": attachments_info
#     }


# @router.get("/fetch-emails")
# def fetch_emails(limit: int = 5):
#     service = get_gmail_service()
#     results = service.users().messages().list(userId="me", maxResults=limit).execute()
#     messages = results.get("messages", [])
#     stored = []

#     for m in messages:
#         data = parse_message(service, m["id"])

#         # ✅ Check by gmail_id instead of text_id
#         if not documents_collection.find_one({"gmail_id": data["gmail_id"]}):
#             email = Document_Base_Create(**data)
#             doc = email.dict(by_alias=True)
#             doc["stored_at"] = datetime.utcnow()
#             documents_collection.insert_one(doc)
#             stored.append(doc)

#     return {"inserted": len(stored), "emails": stored}


import base64
import uuid
from datetime import datetime
from fastapi import APIRouter
from app.services.gmail_service import get_gmail_service
from app.services.drive_service import upload_to_drive
from app.database import db
from app.models.schemas import Document_Base_Create, Attachment

router = APIRouter()
documents_collection = db["document"]   # 👈 FIXED

def parse_message(service, msg_id: str) -> dict:
    """Fetch mail + attachments and map to Document schema"""
    message = service.users().messages().get(userId="me", id=msg_id).execute()
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "unknown")
    snippet = message.get("snippet", "")
    timestamp = int(message["internalDate"]) / 1000
    received_at = datetime.fromtimestamp(timestamp)

    attachments_info: list[Attachment] = []
    if "parts" in payload:
        for part in payload["parts"]:
            filename = part.get("filename")
            body = part.get("body", {})
            if filename and "attachmentId" in body:
                att_id = body["attachmentId"]
                att = service.users().messages().attachments().get(
                    userId="me", messageId=msg_id, id=att_id
                ).execute()
                data = att.get("data")
                file_bytes = base64.urlsafe_b64decode(data.encode("UTF-8"))
                link = upload_to_drive(filename, file_bytes)
                attachments_info.append(Attachment(filename=filename, drive_link=link))

    return {
        "text_id": msg_id,   # 👈 use gmail id here
        "submitted_by": sender,
        "subject": subject,
        "extracted_text": snippet,   # 👈 storing snippet as extracted_text
        "created_at": received_at,
        "source": "gmail",
        "status": "open",
        "attachments": [att.dict() for att in attachments_info],
    }

@router.get("/fetch-emails")
def fetch_emails(limit: int = 5):
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", maxResults=limit).execute()
    messages = results.get("messages", [])
    stored = []

    print(f"📨 Found {len(messages)} messages in Gmail API")

    for m in messages:
        data = parse_message(service, m["id"])
        print(f"➡️ Processing message with text_id={data['text_id']} subject={data['subject']}")

        existing = documents_collection.find_one({"text_id": data["text_id"]})
        if existing:
            print(f"⚠️ Skipping duplicate message {data['text_id']}")
            continue

        try:
            email = Document_Base_Create(**data)
            doc = email.dict(by_alias=True)
            doc["stored_at"] = datetime.utcnow()

            result = documents_collection.insert_one(doc)
            print(f"✅ Inserted doc with MongoDB _id={result.inserted_id}")

            stored.append(doc)
        except Exception as e:
            print(f"❌ Error inserting message {data['text_id']}: {e}")
            print("   Data was:", data)

    return {"inserted": len(stored), "emails": stored}
