from fastapi import APIRouter
from app.services.gmail_webhook import router as webhook_router

router = APIRouter()

# Include both old and new routes
router.include_router(webhook_router, prefix="/gmail", tags=["gmail"])

# Keep your existing fetch-emails endpoint for manual use
@router.get("/fetch-emails")
async def fetch_emails(limit: int = 5):
    """Manual email fetching (backup)"""
    from app.services.gmail_webhook import get_gmail_service, process_single_email
    
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", maxResults=limit).execute()
    messages = results.get("messages", [])
    stored = []

    for m in messages:
        doc = await process_single_email(m["id"])
        if doc:
            stored.append(doc)

    return {"inserted": len(stored), "emails": stored}