from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class AgentState(BaseModel):
    # From the Ingestion
    lead_email: EmailStr
    lead_domain: str
    
    # From the Enrichment
    enriched_data: Optional[dict] = None
    
    # From the Scoring
    lead_score: Optional[int] = None
    lead_priority: Optional[str] = None
    headcount: Optional[int] = None
    company: Optional[str] = None
    lead_id: Optional[str] = None
    
    # From the Assignment & Routing
    rep_email : Optional[EmailStr] = None
    rep_name: Optional[str] = None
    assigned_to: Optional[str] = None #the rep_id 
    manager_name: Optional[str] = None
    approval_decision: Optional[str] = None
    deal_size: Optional[int] = None
    
    
    
    proposal_send_trigger: Optional[bool] = None
    status: Optional[str] = None