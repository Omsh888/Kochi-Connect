# to run this file --> (python app/auth/auth_setup.py) AND  file after successful authentication
# which is used by main.py to access Google APIs

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

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

if __name__ == "__main__":
    generate_token()
