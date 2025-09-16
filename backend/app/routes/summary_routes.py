from fastapi import APIRouter, Query
from app.database import db

router = APIRouter()
summary_collection = db["summary"]

# get all data from summary and document collections
@router.get("/getalldata")
async def get_all_data():
    # Summary collection data
    summary_docs = []
    async for doc in summary_collection.find():
        doc["_id"] = str(doc["_id"])
        summary_docs.append(doc)

    # Document collection data
    document_collection = db["document"]
    document_docs = []
    async for doc in document_collection.find():
        doc["_id"] = str(doc["_id"])
        document_docs.append(doc)

    return {
        "summary": summary_docs,
        "document": document_docs
    }

# get department counts
@router.get("/getdepartscount")
async def get_department_counts():
    pipeline = [
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
    result = []
    async for doc in summary_collection.aggregate(pipeline):
        result.append(doc)
    return result

# get documents by department
@router.get("/getdocsbydepart")
async def get_by_department(department: str = Query(...)):
    docs = []
    async for doc in summary_collection.find({"department": department}):
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs
