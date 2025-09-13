# to run this file --> (python app/auth/auth_setup.py)
# which is used by main.py to access Google APIs

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.file"
]

def generate_token():
    creds = None

    # Step 1: Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    # Step 2: Save token.json for future use
    with open("token.json", "w") as token_file:
        token_file.write(creds.to_json())

    print("✅ token.json generated successfully!")

def fix_token_scopes():
    """Fix scopes in existing token.json file"""
    try:
        if os.path.exists("token.json"):
            with open("token.json", "r") as token_file:
                token_data = json.load(token_file)
            
            # Update scopes to ensure they are correct
            token_data['scopes'] = SCOPES
            
            # Write back to file
            with open("token.json", "w") as token_file:
                json.dump(token_data, token_file, indent=2)
                
            print("✅ Token scopes fixed successfully!")
            return True
        else:
            print("❌ token.json not found. Run generate_token() first.")
            return False
    except Exception as e:
        print(f"❌ Error fixing token scopes: {e}")
        return False

if __name__ == "__main__":
    # ✅ SIMPLE: Always fix existing token first, if exists
    if os.path.exists("token.json"):
        print("🔄 Fixing existing token scopes...")
        fix_token_scopes()
    else:
        print("🆕 Generating new token...")
        generate_token()