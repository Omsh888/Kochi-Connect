from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema


# --- Custom ObjectId Type ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema()
        )

    @classmethod
    def validate(cls, v: Any):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, _handler):
        return {"type": "string", "example": "64f8a61c7f1b2c3d4e5f6789"}


# --- Base Mongo Model ---
class MongoModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")

    model_config = {
        "populate_by_name": True,   # replaces allow_population_by_field_name
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


# --- Employee Schemas ---
class EmployeeBase(MongoModel):
    __collection__ = "employees"

    name: str
    email: EmailStr
    department: str
    role: str
    password: str
    phone: Optional[str]


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime


# --- Document Text ---
class Attachment(BaseModel):
    filename: str
    drive_link: str


class DocumentBase(MongoModel):
    __collection__ = "document"
    text_id: str
    sender: str     #email/phone no.
    subject: str
    extracted_text: str
    created_at: datetime
    source:str
    status:str="open"
    priority:Optional[str]
    assigned_to:Optional[str]
    attachments: List[Attachment] = []

class Document_Base_Create(DocumentBase):
    pass

class Document_Base_Response(DocumentBase):
    text_id: str
    created_at: datetime



# --- Summary Schemas ---
class SummaryBase(MongoModel):
    __collection__ = "summary"
    document_id: str
    department: str
    summary_text: str


class SummaryCreate(SummaryBase):
    pass


class SummaryResponse(SummaryBase):
    id: str
    created_at: datetime


# --- Compliance Flag Schemas ---
class ComplianceFlagBase(MongoModel):
    __collection__ = "compliance_flag"
    document_id: str
    flag_type: str
    deadline: datetime
    status: str


class ComplianceFlagCreate(ComplianceFlagBase):
    pass


class ComplianceFlagResponse(ComplianceFlagBase):
    id: str
    created_at: datetime


# --- Notification Schemas ---
class NotificationBase(MongoModel):
    __collection__ = "notifications"

    employee_id: str
    document_id: str
    summary_id: Optional[str]
    delivery_channel: str
    status: str


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: str
    delivered_at: datetime
