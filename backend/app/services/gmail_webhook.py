import base64
import os
import json
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.database import db
from app.models.schemas import Document_Base_Create, Attachment
from app.services.drive_service import upload_to_drive

router = APIRouter()
documents_collection = db["document"]

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Get authenticated Gmail service"""
    creds = None
    # Load credentials from token.json
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

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

    attachments_info = []
    if "parts" in payload:
        for part in payload["parts"]:
            filename = part.get("filename")
            body = part.get("body", {})
            if filename and "attachmentId" in body:
                try:
                    att_id = body["attachmentId"]
                    att = service.users().messages().attachments().get(
                        userId="me", messageId=msg_id, id=att_id
                    ).execute()
                    data = att.get("data")
                    file_bytes = base64.urlsafe_b64decode(data.encode("UTF-8"))
                    
                    # Upload to Drive and get URL
                    drive_url = upload_to_drive(filename, file_bytes)
                    
                    # ✅ FIXED: Better file extension extraction
                    if '.' in filename:
                        file_extension = filename.split('.')[-1].lower().strip()
                        # Remove any query parameters or special characters
                        file_extension = file_extension.split('?')[0].split('#')[0]
                    else:
                        file_extension = 'unknown'
                    
                    # Create attachment object with new schema
                    attachment = {
                        "file_url": drive_url,
                        "file_type": file_extension
                    }
                    attachments_info.append(attachment)
                    
                    print(f"📎 Attachment processed: {filename} -> {file_extension}")
                    
                except Exception as e:
                    print(f"⚠️ Attachment error for {filename}: {e}")
                    # Try to extract extension even if upload fails
                    file_extension = 'unknown'
                    if filename and '.' in filename:
                        file_extension = filename.split('.')[-1].lower().strip()
                    
                    fallback_attachment = {
                        "file_url": f"error_uploading_{filename}",
                        "file_type": file_extension
                    }
                    attachments_info.append(fallback_attachment)

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

async def process_single_email(msg_id: str):
    """Process and store a single email"""
    service = get_gmail_service()
    data = parse_message(service, msg_id)
    
    # Check if email already exists
    existing = await documents_collection.find_one({"text_id": data["text_id"]})
    if existing:
        print(f"⚠️ Duplicate message {data['text_id']}, skipping")
        return None

    try:
        # Create document using your schema
        email = Document_Base_Create(**data)
        doc = email.model_dump(by_alias=True, exclude_none=True)
        doc["stored_at"] = datetime.utcnow()

        # Insert into MongoDB
        result = await documents_collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        
        print(f"✅ New email stored: {data['subject']}")
        return doc
        
    except Exception as e:
        print(f"❌ Error processing message {data['text_id']}: {e}")
        return None

# Store the last history ID to track new emails
async def get_last_history_id():
    config = await db["gmail_config"].find_one({"key": "last_history_id"})
    return config["value"] if config else None

async def update_last_history_id(history_id: str):
    await db["gmail_config"].update_one(
        {"key": "last_history_id"},
        {"$set": {"value": history_id}},
        upsert=True
    )

async def process_new_emails():
    """Process emails since last history ID"""
    print("🔍 Starting to process new emails...")
    service = get_gmail_service()
    last_history_id = await get_last_history_id()
    
    print(f"📊 Last history ID from DB: {last_history_id}")
    
    if not last_history_id:
        # First time setup, get current history ID
        profile = service.users().getProfile(userId='me').execute()
        last_history_id = profile['historyId']
        await update_last_history_id(last_history_id)
        print(f"📋 Initial history ID set: {last_history_id}")
        return []

    try:
        # Get history since last check
        print(f"📨 Fetching history since ID: {last_history_id}")
        history = service.users().history().list(
            userId='me',
            startHistoryId=last_history_id,
            historyTypes=['messageAdded']
        ).execute()
        
        print(f"📈 History response keys: {list(history.keys())}")
        
        new_emails = []
        history_records = history.get('history', [])
        print(f"📊 Found {len(history_records)} history records")
        
        for i, history_record in enumerate(history_records):
            messages = history_record.get('messages', [])
            print(f"📝 Record {i+1}: {len(messages)} messages")
            for message in messages:
                if message['id'] not in new_emails:
                    new_emails.append(message['id'])
        
        print(f"🎯 Total new emails to process: {len(new_emails)}")
        
        # Process new emails
        processed_emails = []
        for msg_id in new_emails:
            print(f"📧 Processing message: {msg_id}")
            doc = await process_single_email(msg_id)
            if doc:
                processed_emails.append(doc)
        
        # Update last history ID
        if 'historyId' in history:
            new_history_id = history['historyId']
            await update_last_history_id(new_history_id)
            print(f"💾 Updated history ID to: {new_history_id}")
        
        print(f"✅ Processed {len(processed_emails)} new emails")
        return processed_emails
        
    except Exception as e:
        print(f"❌ Error processing history: {e}")
        import traceback
        traceback.print_exc()
        return []


@router.post("/gmail-webhook")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """Simple webhook that always processes emails"""
    try:
        print("📨 Gmail webhook received - Processing emails...")
        
        # Always process emails regardless of data format
        background_tasks.add_task(process_new_emails)
        
        return {
            "status": "processing", 
            "message": "Emails are being processed in background"
        }
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"status": "error", "message": str(e)}

# @router.post("/gmail-webhook")
# async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
#     """Webhook endpoint for Gmail push notifications with auto-update"""
#     try:
#         print("📨 Gmail webhook received!")
        
#         # Get JSON data
#         body = await request.json()
#         print(f"📦 Raw JSON body: {json.dumps(body, indent=2)}")
        
#         # Google ka actual data format find karo
#         history_id = None
        
#         # Case 1: Direct historyId in decoded data
#         if 'message' in body and 'data' in body['message']:
#             try:
#                 decoded_data = base64.b64decode(body['message']['data']).decode('utf-8')
#                 webhook_data = json.loads(decoded_data)
#                 print(f"🔓 Decoded webhook data: {webhook_data}")
                
#                 if 'historyId' in webhook_data:
#                     history_id = webhook_data['historyId']
#             except:
#                 pass
        
#         # Case 2: HistoryId directly in body
#         if not history_id and 'historyId' in body:
#             history_id = body['historyId']
        
#         # Case 3: Check subscription info
#         if not history_id and 'subscription' in body:
#             # Agar historyId nahi mila, tab bhi process karo
#             print("ℹ️ No historyId found, but processing anyway")
#             background_tasks.add_task(process_new_emails)
#             return {"status": "processing_auto"}
        
#         if history_id:
#             print(f"🔄 New history ID received: {history_id}")
#             background_tasks.add_task(process_new_emails)
#             return {
#                 "status": "processing", 
#                 "historyId": history_id,
#                 "message": "Emails are being processed in background"
#             }
#         else:
#             # Fallback: Process anyway
#             print("ℹ️ No historyId found, processing emails anyway")
#             background_tasks.add_task(process_new_emails)
#             return {"status": "processing_fallback"}
        
#     except Exception as e:
#         print(f"❌ Webhook error: {e}")
#         import traceback
#         traceback.print_exc()
#         return {"status": "error", "message": str(e)}

@router.get("/setup-gmail-watch")
async def setup_gmail_watch():
    """Setup Gmail push notifications with detailed debugging"""
    try:
        print("🚀 Starting Gmail watch setup...")
        
        # Get Gmail service
        service = get_gmail_service()
        print("✅ Gmail service initialized")
        
        # Your Google Cloud Pub/Sub topic (UPDATE WITH YOUR ACTUAL PROJECT ID)
        topic_name = "projects/kochi-connect-471411/topics/gmail-notifications"
        print(f"📋 Using topic: {topic_name}")
        
        watch_request = {
            'labelIds': ['INBOX'],
            'topicName': topic_name,
            'labelFilterAction': 'include'
        }
        
        print("📨 Sending watch request to Gmail API...")
        response = service.users().watch(userId='me', body=watch_request).execute()
        print("✅ Gmail watch request successful")
        
        # Extract response details
        history_id = response['historyId']
        expiration = response.get('expiration', 'Not provided')
        
        print(f"📊 Response - History ID: {history_id}")
        print(f"📊 Response - Expiration: {expiration}")
        
        # Update last history ID in database
        await update_last_history_id(history_id)
        print("💾 History ID stored in database")
        
        # Get current profile to verify
        profile = service.users().getProfile(userId='me').execute()
        print(f"👤 Gmail Profile - Email: {profile.get('emailAddress')}")
        print(f"👤 Gmail Profile - Current History ID: {profile.get('historyId')}")
        
        return {
            "status": "watching",
            "historyId": history_id,
            "expiration": expiration,
            "topic": topic_name,
            "userEmail": profile.get('emailAddress'),
            "message": "Gmail watch setup successfully. New emails will be sent to webhook."
        }
        
    except Exception as e:
        print(f"❌ Gmail watch setup failed: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # Detailed error analysis
        error_msg = str(e)
        if "topicNotFound" in error_msg:
            error_detail = "Pub/Sub topic not found. Create it in Google Cloud Console."
        elif "permission" in error_msg.lower():
            error_detail = "Permission denied. Check Gmail API permissions."
        elif "authentication" in error_msg.lower():
            error_detail = "Authentication failed. Check OAuth credentials."
        else:
            error_detail = "Unknown error. Check Google Cloud setup."
        
        print(f"💡 Suggested fix: {error_detail}")
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Watch setup failed",
                "message": str(e),
                "suggestion": error_detail,
                "help": "Ensure Pub/Sub topic exists and Gmail API is enabled"
            }
        )

@router.get("/check-watch-status")
async def check_watch_status():
    """Check current Gmail watch status"""
    try:
        service = get_gmail_service()
        
        # Get current profile to check history ID
        profile = service.users().getProfile(userId='me').execute()
        
        # Get last stored history ID from database
        last_history_id = await get_last_history_id()
        
        return {
            "status": "success",
            "current_history_id": profile.get('historyId'),
            "last_stored_history_id": last_history_id,
            "email_address": profile.get('emailAddress'),
            "messages_total": profile.get('messagesTotal'),
            "threads_total": profile.get('threadsTotal')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/check-new-emails")
async def check_new_emails():
    """Manual trigger to check for new emails"""
    new_emails = await process_new_emails()
    return {"new_emails": len(new_emails), "emails": new_emails}

@router.get("/manual-fetch-emails")
async def manual_fetch_emails(limit: int = 5):
    """Manual email fetching (backup)"""
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", maxResults=limit).execute()
    messages = results.get("messages", [])
    stored = []

    for m in messages:
        doc = await process_single_email(m["id"])
        if doc:
            stored.append(doc)

    return {"inserted": len(stored), "emails": stored}
