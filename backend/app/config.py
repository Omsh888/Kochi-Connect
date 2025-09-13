# Load ENV variables, constants like SCOPES

import os
from dotenv import load_dotenv

load_dotenv()
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.file"
]
