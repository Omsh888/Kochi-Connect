from fastapi import APIRouter
from app.database import db

router = APIRouter()
summary_collection = db["summary"]

@router.get("/getdocs")
async def get_all_docs():
    docs = []
    async for doc in summary_collection.find():
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs

@router.get("/getdepartscount")
async def get_department_counts():
    pipeline = [
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
    result = []
    async for doc in summary_collection.aggregate(pipeline):
        result.append(doc)
    return result
