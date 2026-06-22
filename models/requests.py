from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class TallyFields(BaseModel):
    key: str
    label: str
    type: str
    value: str

class TallyData(BaseModel):
    formName: str
    createdAt: str
    submissionPdfUrl: str
    fields: List[TallyFields] # The hierarchy comes here, it's when you pass the nested level model
    
class WebhookPayload(BaseModel):
    data: TallyData # The hierarchy comes here, it's when you pass the nested level model


class EmailSubmission(BaseModel):
    from_email: EmailStr = Field(..., description="Email address of the sender, required field")
    subject_line: str = Field(..., min_length=1, description="Subject of the email, required field")
    email_body: str = Field(..., min_length=1, description="Body of the email, required field")
