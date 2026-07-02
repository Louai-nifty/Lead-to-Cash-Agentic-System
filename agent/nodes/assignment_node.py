# this "assignment" node or phase, will have messages being sent, and HITL, also AI to do the estimated value of the deal
# Estimated value of the deal, Assignment to reps, messages sent to reps or managers, HITL, database updated

from agent.state import AgentState
from utils.loggings import get_logger
from database.db import get_client

sup_client = get_client()
logger = get_logger(__name__)

async def assignment_node(state: AgentState):
    "The node responsible for the assignment stage of the lead"
    try:
        score = state.lead_score
        priority = state.lead_priority
        email = state.lead_email
        
        if score < 50:
            sup_client.table("Leads").update({"status": "rejected"}).eq("email", email).execute()
        
        elif score >= 50 and score < 80:
            Rep = sup_client.table("Users").select("id").eq("role", "Junior_Rep").eq("leads_assigned_atm", 0).execute().data[0]
            Rep_id = Rep["id"]
            Rep_email = Rep["email"]
            assigned_to = Rep["lead_assigned_atm"]
            
            sup_client.table("Users").update({"leads_assigned_atm": assigned_to + 1}).eq("id", Rep_id).execute()
            sup_client.table("Leads").update({"status": "assigned", "assigned_rep_id": Rep_id}).eq("email", email).execute()
        
        
        
        
        return state
        
    except Exception as e:
        logger.error(f"Assignment failed for {state.lead_email}: {str(e)}")

