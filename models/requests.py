from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class FormSubmission(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the lead, required field")
    email: EmailStr = Field (..., description="Email of the lead, required field")
    phone_number: Optional[str] = Field(None, description="Phone number is optional")
    company_name: str = Field(..., min_length=1, description="Company name of the lead, required field")
    job_title: str = Field(..., min_length=1, description="Job title of the lead, required field")
    message: str = Field(..., min_length=1, description="Message from the lead, can include specific requirements or questions")


class EmailSubmission(BaseModel):
    from_email: EmailStr = Field(..., description="Email address of the sender, required field")
    subject_line: str = Field(..., min_length=1, description="Subject of the email, required field")
    email_body: str = Field(..., min_length=1, description="Body of the email, required field")
