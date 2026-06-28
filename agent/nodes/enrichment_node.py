from agent.tools.enrich import enrichment_tool
from agent.state import AgentState
from database.db import get_client
from utils.loggings import get_logger

sup_client = get_client()
logger = get_logger(__name__)

async def enrichment_node(state: AgentState):
    "The node responsible for the enrichment stage"
    try:
        domain = state.lead_domain
        email = state.lead_email
        
        logger.info(f"Enrich lead: {email}")
        enrichment_result = await enrichment_tool.ainvoke({"lead_domain": domain})
        
        company_info = {
            "industry": enrichment_result["data"]["category"]["industry"],
            "size": enrichment_result["data"]["metrics"]["employees"],
            "revenue": enrichment_result["data"]["metrics"]["annualRevenue"],
            "location" : enrichment_result["data"]["geo"]["city"]
        }
        
        sup_client.table("Leads").update(company_info).eq("email", email).execute()
        
        logger.info("Lead Enrichment Completed")
        
        state.enriched_data = company_info
        return state
    
    except Exception as e:
        logger.error(f"Enrichment failed for {email}: {str(e)}")
        state.status = "failed"
        return state