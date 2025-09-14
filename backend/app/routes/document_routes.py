from fastapi import APIRouter
from app.services.document_router import document_router,auto_assign_document

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/test-assignment/{document_id}")
async def test_document_assignment(document_id: str):
    """Test document assignment manually"""
    result = await auto_assign_document(document_id)
    return {"assigned_to": result, "document_id": document_id}

@router.get("/department-staff/{department}")
async def get_department_staff(department: str):
    """Get all staff in a department"""
    staff = await document_router.get_department_staff(department)
    return {"department": department, "staff_count": len(staff), "staff": staff}