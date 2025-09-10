from pydantic import BaseModel,EmailStr,Field
from typing import Optional,List  
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class MongoModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")

    class Config:
        allow_population_by_field_name = True  # let us use "id" or "_id"
        arbitrary_types_allowed = True         # allow ObjectId in models
        json_encoders = {ObjectId: str}        # convert ObjectId → str in responses
# Employess Schemasss


class EmployeeBase(MongoModel):
    __collection__ = "employees"

    name:str
    email:EmailStr
    department: str
    role: str
    password:str


class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    id:str
    created_at: datetime


#Document text

class DocumentText(MongoModel):
    text_id: str
    extracted_text: str
    created_at: datetime   

class DocumentText_Response(DocumentText):
    text_id:str
    created_at:datetime



#Document schemas

class DocumenBase(MongoModel):
    __collection__ = "document"
    title: str
    file_path: str
    source: str
    language: str


class DocumentCreate(DocumenBase):
    pass


class DocumentResponse(DocumenBase):
    id: str
    uploaded_at: datetime
    document_text: Optional[DocumentText]




#Summary Schemas   

class SummaryBase(MongoModel):
    __collection__ = "summary"
    document_id: str
    role: str
    summary_text: str

class SummaryCreate(SummaryBase):
    pass


class SummaryResponse(SummaryBase):
    id:str
    created_at:datetime



#compliance flag schemas

class ComplianceFlagBase(MongoModel):
    __collection__ = "compliance_flag"
    document_id: str
    flag_type: str
    deadline: datetime
    status: str

class ComplianceFlagCreate(ComplianceFlagBase):
    pass

class ComplianceFlagResponse(ComplianceFlagBase):
    id:str
    created_at: datetime


#Notification Schemas

class NotificationBase(MongoModel):
    __collection__ = "notifications"

    employee_id:str
    document_id: str
    summary_id: Optional[str]
    delivery_channel: str
    status: str

class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id:str
    delivered_at:datetime
