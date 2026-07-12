from utils.loggings import get_logger
from database.db import get_client
from agent.state import AgentState
from datetime import datetime, timedelta
from services.proposal_service import proposal_generator
from agent.tools.notification import slack_notification_tool
from config import proposals_channel_id
from services.smtp_service import SMTPService
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
        
        logger.info(f"preparing the proposal of {email} to get sent to Rep {rep_name}")
        
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
                                        "text": {"type": "plain_text", "text": "Send Now"},
                                        "value": f"send_{lead_id}",
                                        "action_id": "send_proposal"
                                    },
                                    {
                                        "type": "button",
                                        "text": {"type": "plain_text", "text": "Review"},
                                        "value": f"review_{lead_id}",
                                        "action_id": "review_proposal",
                                        "url": pdf_url
                                    }
                                ]
                            }
                        ]
        
        sup_client.table("proposals").update({"status": "awaiting"}).eq("pdf_url", pdf_url).execute()
        await slack_notification_tool.ainvoke({"channel": proposals_channel_id, "text": message, "blocks": block_content})
        
        logger.info(f"proposal has been sent to Rep {rep_name} on Slack for review")

        state.proposal_status = "awaiting"
        state.proposal_pdf_url = pdf_url 
        state.lead_name = lead_name
        state.company_name = company_name
        return state
    except Exception as e:
        logger.error(f"Proposal node failed, {str(e)}", exc_info=True)
        



smtp_client = SMTPService()


async def proposal_send_node(state: AgentState):
    try:
        
        company_name = state.company_name
        lead_name = state.lead_name
        pdf_url = state.proposal_pdf_url
        lead_email = state.lead_email
        
        subject = f"Your Proposal - {lead_name} from {company_name}"
        
        html_content = f"""
        <html>
            <body>
                <p>Hi {lead_name},</p>
                <p>Please review your proposal below:</p>
                <a href="{pdf_url}">View Proposal</a>
                <p>Looking forward to your feedback.</p>
            </body>
        </html>
        """
        
        success = await smtp_client.send_proposal(lead_email, subject, html_content)
        
        if success:
            logger.info(f"proposal has been sent to lead {lead_name} with {lead_email}")
            
            time_sent= datetime.now().isoformat()
            sup_client.table("proposals").update({"status": "sent", "sent_at": time_sent}).eq("pdf_url", pdf_url).execute()
            
            state.proposal_status = "sent"
            
        else:
            state.proposal_status = "send_failed"
            logger.error(f"Failed to send proposal to {lead_email}")
        
        
        return state
    except Exception as e:
        logger.error(f"Proposal failed to be sent to lead {str(e)}")
        state.proposal_status = "send_error"
        return state