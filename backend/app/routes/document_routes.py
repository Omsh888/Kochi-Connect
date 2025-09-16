
from fastapi import APIRouter, Query
from app.database import db

router = APIRouter()

# get document count by source
@router.get("/getdocscountbysrc")
async def get_docs_count_by_source(source: str = Query(...)):
	document_collection = db["document"]
	count = await document_collection.count_documents({"source": source})
	return {"source": source, "count": count}

# get monthly status count for a year
@router.get("/getmonthlystatuscount")
async def get_monthly_status_count(year: int = Query(...)):
	document_collection = db["document"]
	pipeline = [
		{"$addFields": {"year": {"$year": "$createdAt"}, "month": {"$month": "$createdAt"}}},
		{"$match": {"year": year}},
		{"$group": {"_id": "$status", "count": {"$sum": 1}}}
	]
	result = []
	async for doc in document_collection.aggregate(pipeline):
		result.append({"status": doc["_id"], "count": doc["count"]})
	return result

# get status count for a specific year and month
@router.get("/getmonthstatuscountbymonth")
async def get_monthly_status_count_by_month(year: int = Query(...), month: int = Query(...)):
	document_collection = db["document"]
	pipeline = [
		{"$addFields": {"year": {"$year": "$createdAt"}, "month": {"$month": "$createdAt"}}},
		{"$match": {"year": year, "month": month}},
		{"$group": {"_id": "$status", "count": {"$sum": 1}}}
	]
	result = []
	async for doc in document_collection.aggregate(pipeline):
		result.append({"status": doc["_id"], "count": doc["count"]})
	return result
