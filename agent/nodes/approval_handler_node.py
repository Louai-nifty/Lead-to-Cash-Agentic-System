from utils.loggings import get_logger
from database.db import get_client
from agent.state import AgentState
from services.routing_service import routing_func
from agent.tools.notification import slack_notification_tool
from config import assignment_channel_id
from langgraph.types import interrupt

logger = get_logger(__name__)
sup_client = get_client()

async def approval_handler_node(state: AgentState):
    logger.info(
        "Approval handler entered for lead %s with decision %s",
        state.lead_email,
        state.approval_decision,
    )

    if state.status in {"approved", "rejected"}:
        logger.info("Approval already handled for lead %s; skipping duplicate execution", state.lead_email)
        return state

    decision = state.approval_decision
    if decision is None:
        decision = interrupt(
            {
                "lead_email": state.lead_email,
                "deal_size": state.deal_size,
                "manager_name": state.manager_name,
            }
        )
        state.approval_decision = decision

    lead_email = state.lead_email
    deal_size = state.deal_size
    manager_name = state.manager_name
    if decision == "approve":
        logger.info(f"Lead with email '{lead_email}' has been approved by Manager {manager_name}.")
        
        sup_client.table("Leads").update({"status": "approved"}).eq("email", lead_email).execute()
        
        score = 90
        routing = routing_func(score, lead_email)
        rep_name = routing["assigned_rep_name"]
        rep_email = routing["assigned_to"]
        
        lead_details = sup_client.table("Leads").select("*").eq("email", lead_email).execute().data[0]
        lead_name = lead_details["lead_name"]
        lead_role = lead_details["role"]
        lead_source = lead_details["source"]
        lead_message = lead_details["message"]
        lead_company = lead_details["company"]
        
        message = f"""New Lead Assigned to you {rep_name}
                                Name: {lead_name} | Role: {lead_role}
                                Company: Lead's company name: {lead_company}
                                Email: {lead_email}
                                Deal Size: The deal size was estimated at: ${deal_size}
                                Source: Where the lead came from: {lead_source}
                                Their Message: {lead_message}

                                Please reach out and schedule an initial conversation. 
                                (This lead has been approved by Manager {manager_name} and assigned to you for follow-up.)
                        """
        
        await slack_notification_tool.ainvoke({"channel": assignment_channel_id, "text": message, "webhook_type": "approval"})
        
        logger.info(f"Lead with email '{lead_email}' has been assigned to Rep '{rep_name}' after approval from Manager {manager_name}.")
        
        state.approval_decision = "approved"
        return state
    
    elif decision == "reject":
        logger.info(f"Lead with email '{lead_email}' has been rejected by Manager {manager_name}.")
        
        sup_client.table("Leads").update({"status": "rejected"}).eq("email", lead_email).execute()
        
        message = f"""Lead Rejected by Manager {manager_name}
                                Lead Email: {lead_email}
                                Deal Size: The deal size was estimated at: ${deal_size}
                                (This lead has been rejected by Manager {manager_name} and will not be pursued further.)
                        """
        
        await slack_notification_tool.ainvoke({"channel": assignment_channel_id, "text": message, "webhook_type": "approval"})
        
        logger.info(f"Lead with email '{lead_email}' has been marked as rejected after Manager's decision.")
        state.approval_decision = "rejected"
        return state