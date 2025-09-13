import base64
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter
from app.services.gmail_service import get_gmail_service
from app.services.drive_service import upload_to_drive
from app.database import db
from app.models.schemas import Document_Base_Create, Attachment

router = APIRouter()
documents_collection = db["document"] 


def parse_message(service, msg_id: str) -> dict:
    """Fetch Gmail message and map to Document schema"""
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
        "text_id": msg_id,
        "sender": sender,
        "subject": subject,
        "extracted_text": snippet,
        "created_at": received_at,
        "source": "gmail",
        "status": "open",
        "priority": None,
        "assigned_to": None,
        "attachments": attachments_info
    }
@router.get("/fetch-emails")
async def fetch_emails(limit: int = 5):
    """Fetch latest Gmail emails and store in MongoDB"""
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", maxResults=limit).execute()
    messages = results.get("messages", [])
    stored = []

    print(f"📨 Found {len(messages)} messages in Gmail API")

    for m in messages:
        data = parse_message(service, m["id"])
        print(f"➡️ Processing Gmail message text_id={data['text_id']} subject={data['subject']}")

        existing = await documents_collection.find_one({"text_id": data["text_id"]})
        if existing:
            print(f"⚠️ Duplicate message {data['text_id']} already exists, skipping")
            continue

        try:
            email = Document_Base_Create(**data)
            doc = email.model_dump(by_alias=True, exclude_none=True)
            doc["stored_at"] = datetime.utcnow()

            result = await documents_collection.insert_one(doc)
            print(f"✅ Inserted doc with MongoDB _id={result.inserted_id}")

            # Convert ObjectId to string for JSON serialization
            doc["_id"] = str(result.inserted_id)
            stored.append(doc)
            
        except Exception as e:
            print(f"❌ Error inserting message {data['text_id']}: {e}")
            print("   Data was:", data)

    return {"inserted": len(stored), "emails": stored}