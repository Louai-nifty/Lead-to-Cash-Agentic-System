from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class AgentState(BaseModel):
    lead_email: EmailStr
    lead_domain: str
    enriched_data: dict
    status: str 