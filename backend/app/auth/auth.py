from datetime import datetime
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import SCOPES
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import EmployeeBase, EmployeeResponse, LoginRequest
from app.database import db

def get_gmail_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # ✅ AFTER REFRESH, ENSURE SCOPES ARE PRESERVED
            if hasattr(creds, 'scopes') and set(creds.scopes) != set(SCOPES):
                creds.scopes = SCOPES
                # ✅ UPDATE TOKEN FILE WITH CORRECT SCOPES
                update_token_file_scopes(creds)
        else:
            raise Exception("⚠️ token.json missing or invalid. Re-authenticate.")
    return creds

def update_token_file_scopes(creds):
    """Update token.json file with correct scopes"""
    try:
        if os.path.exists("token.json"):
            with open("token.json", "r") as token_file:
                token_data = json.load(token_file)
            
            # Update scopes in token data
            token_data['scopes'] = SCOPES
            
            # Write back to file
            with open("token.json", "w") as token_file:
                json.dump(token_data, token_file, indent=2)
                
            print("✅ Token file scopes updated")
    except Exception as e:
        print(f"❌ Error updating token scopes: {e}")

router = APIRouter()

@router.post("/login", response_model=EmployeeResponse)
async def login(login_data: LoginRequest):
    """
    Login API that checks email and password
    Returns EmployeeResponse if credentials are correct
    """
    # Find employee by email directly in MongoDB collection
    employee = await db.employees.find_one({"email": login_data.email})
    
    # Check if employee exists
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found with this email"
        )
    
    # Check if password matches (plain text comparison)
    if login_data.password != employee.get("password", ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Convert MongoDB document to EmployeeResponse
    return EmployeeResponse(
        id=str(employee["_id"]),
        name=employee["name"],
        email=employee["email"],
        department=employee["department"],
        role=employee["role"],
        phone=employee.get("phone"),  # Use .get() for optional fields
        created_at=employee.get("created_at", datetime.now())
    )