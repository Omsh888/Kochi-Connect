from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

async def startup_db_client():
    try:
        await client.admin.command("ping")
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print("❌ Could not connect to MongoDB:", e)
        raise e
