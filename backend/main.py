from fastapi import FastAPI,HTTPException,BackgroundTasks
from app.database import startup_db_client
from app.routes import email_routes,document_routes
from app.services.ocr import process_document,process_text
from app.models.schemas import DocumentBase
from fastapi.concurrency import run_in_threadpool
import json,re
import os
from dotenv import load_dotenv
from app.database import db
from app.auth.auth import router as auth_router

load_dotenv()

app = FastAPI()


app.include_router(document_routes.router, tags=["documents"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
document_collec = db['document']


app.include_router(email_routes.router)
@app.post("/process_document")
async def process_document_api(doc:DocumentBase):
    try:
        # print('----------',doc.text_id)
        record = await process_document(doc.text_id)
        print("DEBUG record type:", type(record))  # Should print: <class 'dict'>
        print(record)

        if not record:
            raise HTTPException(status_code=404, detail="Document processing failed")

        return {
            "status": "success",
            "data": {
                "document_id": record.get("document_id"),
                "department": record.get("department"),
                "priority":record.get("priority"),
                "user_text": record.get("user_text"),
                "summary": record.get("summary"),
                "attachment_text": record.get("attachment_text"),
                "created_at": record.get("created_at").isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    


@app.get("/")
def home():
    return {"message": "Gmail + Drive + Mongo integration running ✅"}

@app.on_event("startup")
async def startup_db():
    await startup_db_client()
