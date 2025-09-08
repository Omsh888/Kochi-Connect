from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
