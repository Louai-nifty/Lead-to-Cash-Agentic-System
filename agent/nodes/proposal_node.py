from utils.loggings import get_logger
from database.db import get_client
from agent.state import AgentState
from datetime import datetime, timedelta
from services.proposal_service import proposal_generator
from tools.notification import slack_notification_tool
from config import proposals_channel_id
logger = get_logger(__name__)
sup_client = get_client()

async def proposal_node(state: AgentState):
    try:
        email = state.lead_email
        headcount = state.headcount
        deal_size = state.deal_size
        assigned_to = state.assigned_to
        rep_name = state.rep_name
        rep_email = state.rep_email
        lead_id = state.lead_id
        
        proposal = proposal_generator(email, headcount, deal_size, assigned_to, rep_name, rep_email, lead_id)
        
        lead_details = sup_client.table("Leads").select("lead_name", "company").eq("email", email).execute().data[0]
        
        lead_name = lead_details["lead_name"]
        company_name = lead_details["company"]
        
        pdf_url = proposal["pdf_url"]
        template = proposal["template"]
        
        
        message = f"""Proposal Ready for Review {rep_name}
                    Lead: {lead_name} | {company_name}
                    Template: {template}
                    Deal Size: ${deal_size}

                    Review & Send: {pdf_url}"""
                    
        block_content = 
        
        await slack_notification_tool.ainvoke({"channel": proposals_channel_id, "text": message, "blocks": })

        
        return state
    except Exception as e:
        logger.error(f"Proposal node failed, {str(e)}")
        






async def proposal_send_node(state: AgentState):
    try:
     return state
    except Exception as e:
        logger.error(f"Proposal failed to be sent to lead {str(e)}")