from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class AgentState(BaseModel):
    lead_email: EmailStr
    lead_domain: str
    enriched_data: Optional[dict] = None
    status: Optional[str] = None
    lead_score: Optional[int] = None
    lead_priority: Optional[str] = None
    headcount: Optional[int] = None
    rep_email : Optional[EmailStr] = None
    rep_name: Optional[str] = None
    assigned_to: Optional[str] = None
    company: Optional[str] = None
    
    manager_name: Optional[str] = None
    approval_decision: Optional[str] = None
    deal_size: Optional[int] = None