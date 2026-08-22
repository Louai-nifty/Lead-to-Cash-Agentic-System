from pydantic.v1 import NoneStrBytes
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class AgentState(BaseModel):
    # From the Ingestion

    lead_email: Optional[EmailStr] = None
    lead_domain: Optional[str] = None

    
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
    rep_level: Optional[str] = None
    assigned_to: Optional[str] = None #the rep_id 
    manager_name: Optional[str] = None
    approval_decision: Optional[str] = None
    deal_size: Optional[int] = None
    
    
    proposal_pdf_url: Optional[str] = None
    proposal_status: Optional[str] = None
    proposal_send_trigger: Optional[bool] = None


    lead_name: Optional[str] = None
    company_name: Optional[str] = None
    status: Optional[str] = None


    invoice_id: Optional[str] = None
    invoice_url: Optional[str] = None

    error_message: Optional[str] = None