from agent.state import AgentState
from utils.loggings import get_logger
from database.db import get_client
from services.scoring_service import scoring_func
logger = get_logger(__name__)
sup_client = get_client()

async def scoring_node(state: AgentState):
   try: 
    "This node is the one responsible for the scoring of the lead"
    
    email = state.lead_email
    
    response = sup_client.table("Leads").select("*").eq("email", email).execute()
    size = response.data[0]["size"]
    industry = response.data[0]["industry"]
    source = response.data[0]["source"]
    
    logger.info(f"lead scoring for {email} has started")
    result = scoring_func(size, industry, source)
    
    score = result["lead_score"]
    priority = result["lead_priority"]
    
    sup_client.table("Leads").update({"lead_score": score, "priority": priority}).eq("email", email).execute()
    logger.info(f"The lead with email '{email}' score and priority has been updated successfuly")
    state.lead_score = score
    state.lead_priority = priority
    
    return state
   except Exception as e:
       logger.error(f"scoring failed, {str(e)}")
    
    