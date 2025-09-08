from pydantic import BaseModel,EmailStr,Field
from typing import Optional,List  
from datetime import datetime


# Employess Schemasss

class EmployeeBase(BaseModel):
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

class DocumentText(BaseModel):
    text_id: str
    extracted_text: str
    created_at: datetime   

class DocumentText_Response(DocumentText):
    text_id:str
    created_at:datetime



#Document schemas

class DocumenBase(BaseModel):
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

class SummaryBase(BaseModel):
    document_id: str
    role: str
    summary_text: str

class SummaryCreate(SummaryBase):
    pass


class SummaryResponse(SummaryBase):
    id:str
    created_at:datetime



#compliance flag schemas

class ComplianceFlagBase(BaseModel):
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

class NotificationBase(BaseModel):
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
