from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:
        return core_schema.general_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v, _info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema: core_schema.CoreSchema, _handler: Any) -> JsonSchemaValue:
        return {"type": "string"}


class MongoModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default_factory=PyObjectId)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True,
    )

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


class DocumentBase(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    text_id: str
    sender: str
    subject: str
    extracted_text: str
    created_at: datetime
    source: str
    status: str = "open"
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    attachments: Optional[List[Attachment]] = []

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True,
    )

class Document_Base_Create(DocumentBase):
    pass

class Document_Base_Response(DocumentBase):
    pass

# class Document_Base_Response(DocumentBase):
#     text_id: str
#     created_at: datetime



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
