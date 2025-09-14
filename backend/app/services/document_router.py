from app.database import db
from typing import Dict, List
from bson import ObjectId



async def auto_assign_document(document_id: str):
    """Auto-assign document to appropriate department staff"""
    try:
        # Get summary to find department
        summary = await db["summary"].find_one({"document_id": document_id})
        
        if summary and summary.get("department"):
            department = summary["department"]
            staff_id = await document_router.assign_document(document_id, department)
            return staff_id
        else:
            print(f"⚠️ No department found for document {document_id}")
            return None
            
    except Exception as e:
        print(f"❌ Document auto-assign error: {e}")
        return None



class DocumentRouter:
    def __init__(self):
        self.department_counters: Dict[str, int] = {}
    
    async def get_department_staff(self, department: str) -> List[dict]:
        """Get all staff members for a department"""
        staff = await db["employees"].find(
            {"department": department, "role": 2}
        ).to_list(None)
        return staff
    
    async def get_next_staff(self, department: str) -> str:
        """Round-robin assignment for department staff - returns _id"""
        # Get all staff in this department
        staff = await self.get_department_staff(department)
        
        if not staff:
            return "unassigned"  # Fallback if no staff found
        
        # Initialize or get counter for this department
        if department not in self.department_counters:
            self.department_counters[department] = 0
        
        # Get next staff in round-robin
        current_index = self.department_counters[department]
        next_staff = staff[current_index % len(staff)]
        
        # Update counter for next time
        self.department_counters[department] = (current_index + 1) % len(staff)
        
        return str(next_staff["_id"])  # Return staff _id
    
    async def assign_document(self, document_id: str, department: str):
        """Assign document to appropriate staff member using _id"""
        try:
            staff_id = await self.get_next_staff(department)
            
            if staff_id == "unassigned":
                print(f"⚠️ No staff found for department {department}")
                return None
            
            # Update document with assigned staff _id
            await db["document"].update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"assigned_to": staff_id, "status": "assigned"}}
            )
            
            # Get staff details for logging
            staff = await db["employees"].find_one({"_id": ObjectId(staff_id)})
            staff_name = staff["name"] if staff else "Unknown"
            
            print(f"📄 Document {document_id} assigned to {staff_name} ({staff_id}) for {department}")
            return staff_id
            
        except Exception as e:
            print(f"❌ Error assigning document: {e}")
            return None

# Global router instance
document_router = DocumentRouter()