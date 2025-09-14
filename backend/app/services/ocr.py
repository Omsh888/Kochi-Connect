from fastapi import FastAPI, BackgroundTasks,HTTPException
from pymongo import MongoClient
from datetime import datetime
import requests
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
from app.database import db
from app.models.schemas import SummaryCreate,DocumentBase;
import json,re
import google.generativeai as genai
from langdetect import detect
import os
from dotenv import load_dotenv


load_dotenv()
app = FastAPI()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")



DEPARTMENTS = [
    "Operations: Daily train operations, station management, incident reports, rostering",
    "Engineering & Maintenance: Engineering drawings, maintenance job cards, design changes, depot activities",
    "Rolling Stock (Electrical & Mechanical): Train availability, condition monitoring, IoT-based diagnostics",
    "Signalling & Communication: Signal failures, communication breakdowns, trackside equipment faults",
    "Passenger Services: Ticketing, overcrowding, cleanliness, accessibility issues",
    "Safety & Security: Theft, harassment, security system failures, emergency response",
    "Water & Sanitation: Drinking water, washroom maintenance, sewage issues"
]
PRIORITY =[
    "High","Medium","Low"
]
document_collec = db['document']
summary_collec = db['summary']

def get_direct_google_drive_url(file_url: str) -> str:
    match = re.search(r"https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)/view", file_url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return file_url


def extract_text_from_file(file_url: str, file_type: str) -> str:
    try:
        file_url = get_direct_google_drive_url(file_url)
        print("",file_url)
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        file_bytes = response.content

        extracted_text = ""

        if file_type == 'pdf':
            images = convert_from_bytes(file_bytes, dpi=150)
            for img in images:
                text = pytesseract.image_to_string(img, lang='eng')
                extracted_text += text + "\n"
        elif file_type in ['jpg', 'jpeg', 'png']:
            img = Image.open(io.BytesIO(file_bytes))
            extracted_text = pytesseract.image_to_string(img, lang='eng')
        else:
            extracted_text = "Unsupported file type"

        return extracted_text

    except Exception as e:
        print(f"OCR extraction failed for {file_url}: {str(e)}")
        return ""
    

async def process_text(text_user:str)->dict:
    lang = detect(text_user)
    translated_text = text_user if lang == "en" else "Translated English Text"  # Replace with IndicTrans2 later
    
    # 2. Summarization + Classification
    prompt = f"""
    You are an assistant for processing citizen complaints.
    1. Summarize the following complaint in 2-3 concise sentences.
    2. Classify it into one of these departments:
    3. Also assign the priority.

    {chr(10).join(DEPARTMENTS)}

    {chr(10).join(PRIORITY)}

    Complaint:
    {translated_text}

    Respond in JSON format like this:
    {{
      "summary": "...",
      "department": "...",
      "priority":"..."
    }}
    """
    
    response =  gemini_model.generate_content(prompt)
    raw_output = response.text or response.candidates[0].content.parts[0].text
    
    # Extract clean JSON
    try:
        result = json.loads(raw_output)
    except:
        match = re.search(r"\{.*\}", raw_output, re.S)
        if match:
            result = json.loads(match.group())
        else:
            result = {"summary": raw_output.strip(), 
                      "department": "Unclassified",
                      "priority":""}
    
    return result

async def process_document(text_id:str)->dict:
    # print(f"DEBUG process_document started for text_id={text_id}")
    document = await document_collec.find_one({"text_id": text_id})
    # print("---------------------",document)
    if not document:
        print(f"Document {text_id} not found.")
        return

    user_text = document.get('extracted_text', '')
    attachments = document.get('attachments', [])

    attachment_text_combined = ""

    for att in attachments:
        file_url = att.get("file_url")
        file_type = att.get('file_type')

        if file_url and file_type:
            text =  extract_text_from_file(file_url, file_type)
            attachment_text_combined += text + "\n"
        
    rlt = await process_text(user_text)

    print("--------",rlt.get("priority",""))
    record = ({
        "document_id": text_id,
        "department": rlt.get("department",""),
        "priority":rlt.get("priority",""),
        "user_text":user_text,
        "summary": rlt.get("summary",""),
        "attachment_text": attachment_text_combined,
        "created_at": datetime.utcnow()
    })
    
    summary_collec.insert_one(record)
    
    # print("----------",record)
    return record


# @app.post("/process_document")
# async def process_document_api(doc:DocumentBase,background_tasks: BackgroundTasks = None):
#     try:
#         if background_tasks:
#             # run in background so API responds immediately
#             background_tasks.add_task(process_document, doc.id)
#             return {"status": "processing", "document_id": doc.id}
#         else:
#             # run synchronously
#             result = process_document(doc.id,doc.text_id)
#             # print("--------------",result)
#             if not result:
#                 raise HTTPException(status_code=404, detail="Document not found")
#             return {"status": "success", "data": result}
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e)) 

