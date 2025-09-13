import os
import json
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

# import os
# from google.oauth2.credentials import Credentials
# from google.auth.transport.requests import Request
# from app.config import SCOPES

# def get_gmail_credentials():
#     creds = None
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             raise Exception("⚠️ token.json missing or invalid. Re-authenticate.")
#     return creds
