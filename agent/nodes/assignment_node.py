from agent.state import AgentState
from utils.loggings import get_logger
from database.db import get_client
from services.routing_service import routing_func
from tools.notification import slack_notification_tool
from config import assignment_channel_id, approval_channel_id

sup_client = get_client()
logger = get_logger(__name__)

async def assignment_node(state: AgentState):
    "The node responsible for the assignment stage of the lead"
    try:
        score = state.lead_score
        priority = state.lead_priority
        email = state.lead_email
        headcount = state.headcount
        
        routing = routing_func(score, priority, email)
        
        routing_level = routing["to_what_level"]
        lead_details = sup_client.table("Leads").select("*").eq("email", email).execute().data
        lead_name = lead_details["lead_name"]
        lead_role = lead_details["role"]
        lead_source = lead_details["source"]
        lead_message = lead_details["message"]
        lead_company = lead_details["company"]
            
        
        if routing_level == "Junior_Rep":
            logger.info(f"Lead with email '{email}' has been assigned to a Junior Rep")
            message = f"""New Lead Assigned to You

                Contact: {lead_name} | {lead_role}
                Company: {lead_company}
                Lead's Email: {email}

                Source: The lead came from {lead_source}
                Their Message: {lead_message}

                Please reach out and schedule an initial conversation at your earliest convenience.
                """
            await slack_notification_tool.ainvoke({"channel": assignment_channel_id, "text": message})
            
            Rep_name = routing["assigned_rep_name"]
            
            logger.info(f"Notification sent to Junior Rep '{Rep_name}' for lead with email '{email}'")
            
            state.assigned_to = routing["assigned_rep_id"]
            state.rep_email = routing["assigned_to"]
            state.company = lead_company
            
            return state
        
        elif routing_level == "Senior_Rep":
            logger.info(f"Lead with email '{email}' has been assigned to a Senior Rep")
            
            if headcount >= 1000:
                deal_size = 15000
            elif headcount >= 200:
                deal_size = 10000
            elif headcount >= 50:
                deal_size = 5000
            else:
                deal_size = 2000
                
            if deal_size < 10000:
                message = f"""New Lead Assigned to You

                Contact: {lead_name} | {lead_role}
                Company: {lead_company}
                Lead's Email: {email}

                Source: The lead came from {lead_source}
                Their Message: {lead_message}

                Please reach out and schedule an initial conversation at your earliest convenience.
                """
                await slack_notification_tool.ainvoke({"channel": assignment_channel_id, "text": message})
                
                Rep_name = routing["assigned_rep_name"]
            
                logger.info(f"Notification sent to Senior Rep '{Rep_name}' for lead with email '{email}'")
                
                state.assigned_to = routing["assigned_rep_id"]
                state.rep_email = routing["assigned_to"]
                state.company = lead_company
                
                return state
            else:
                logger.info(f"Lead deal size is greater than $10,000, sending to manager for approval")
                logger.info(f"Waiting for manager approval for lead with email '{email}'...")
                
                lead_id = lead_details["id"]
                
                message = f"""New Lead Assigned
                                Name: {lead_name} | Role: {lead_role}
                                Company: Lead's company name: {lead_company}
                                Email: {email}
                                Deal Size: The deal size was estimated at: ${deal_size}
                                Source: Where the lead came from: {lead_source}

                                Please reach out and schedule an initial conversation.
                        """
                block_content = [
                                    {
                                        "type": "section",
                                        "text": {
                                            "type": "mrkdwn",
                                            "text": message
                                        }
                                    },
                                    {
                                        "type": "actions",
                                        "elements": [
                                            {
                                                "type": "button",
                                                "text": {"type": "plain_text", "text": "Approve"},
                                                "value": f"approve_{state.id}",
                                                "action_id": "approve_lead"
                                            },
                                            {
                                                "type": "button",
                                                "text": {"type": "plain_text", "text": "Reject"},
                                                "value": f"reject_{state.id}",
                                                "action_id": "reject_lead"
                                            }
                                        ]
                                    }
                                ]
                await slack_notification_tool.ainvoke({"channel": approval_channel_id, "text": "Lead Requires Approval", "blocks": block_content})
                    
    except Exception as e:
        logger.error(f"Assignment failed for {state.lead_email}: {str(e)}")

