from fastapi import APIRouter, Query
from app.database import db

router = APIRouter()

# get all employees
@router.get("/getallusers")
async def get_all_employees():
    employees_collection = db["employees"]
    employees = []
    async for emp in employees_collection.find():
        emp["_id"] = str(emp["_id"])
        employees.append(emp)
    return employees

# get employees by department
@router.get("/getuserbydepart")
async def get_employees_by_department(department: str = Query(...)):
    employees_collection = db["employees"]
    employees = []
    async for emp in employees_collection.find({"department": department}):
        emp["_id"] = str(emp["_id"])
        employees.append(emp)
    return employees

# get total user count
@router.get("/gettotaluser")
async def get_total_user_count():
    employees_collection = db["employees"]
    count = await employees_collection.count_documents({})
    return {"total_users": count}

# get user count by department
@router.get("/getusercountbydepart")
async def get_user_count_by_department(department: str = Query(...)):
    employees_collection = db["employees"]
    count = await employees_collection.count_documents({"department": department})
    return {"department": department, "user_count": count}