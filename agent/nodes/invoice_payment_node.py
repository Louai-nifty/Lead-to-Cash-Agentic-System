from agent.state import AgentState
from utils.loggings import get_logger
from agent.tools.payment import create_invoice, send_invoice
from database.db import get_client
from datetime import date, datetime, timedelta
from config import COMPANY_NAME, COMPANY_ADDRESS, BILLING_EMAIL


sup_client = get_client()
logger = get_logger(__name__)


async def payment_node(state: AgentState):
    try:
        logger.info("Starting invoice creation process")

        lead_id = state.lead_id
        lead_email = state.lead_email
        lead_name = state.lead_name
        company_name = state.company_name
        deal_size = state.deal_size

        accountant_email = sup_client.table("Users").select("email").eq("role", "accountant").execute().data[0]["email"]
                
        due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

        detail = {
            "invoice_number": f"INV-{str(lead_id)[:8]}",
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "currency_code": "USD", 
            "payment_term": {
                "term_type": "DUE_ON_DATE_SPECIFIED",
                "due_date": due_date
            }
                }

        invoicer = {
                    "business_name": COMPANY_NAME, 
                    "email_address": BILLING_EMAIL,
                    "name": {
                        "given_name": "Lucas"
                    },
                    "address": COMPANY_ADDRESS
                }

        primary_recipients = [
            {
                "billing_info": {
                    "name": {"given_name": lead_name},
                    "email_address": lead_email,
                    "business_name": company_name
                }
            }
        ]

        items = [
            {
                "name": "Professional Services / Software License",
                "description": f"Agreed upon services for {company_name}",
                "quantity": "1",
                "unit_amount": {
                            "currency_code": "USD",
                            "value": f"{float(deal_size):.2f}"
                        }
                    }
                ]

        additional_recipients = [
            accountant_email
        ]

        
        invoice = await create_invoice.ainvoke({
            "detail": detail,
            "invoicer": invoicer,
            "primary_recipients": primary_recipients,
            "items": items,
            "additional_recipients": additional_recipients
        })

        invoice_id = invoice["id"]
        invoice_url = invoice["links"][0]["href"]
        due_date = invoice["detail"]["payment_term"]["due_date"]

        logger.info(f"The invoice draft has been created : {invoice_id}")
                
        sup_client.table("invoices").insert({"invoice_id": invoice_id,"lead_id": lead_id, "amount": deal_size, "currency": "USD","status": "draft", "url": invoice_url, "due_date": due_date,"created_at": datetime.now().isoformat()}).eq("lead_id", lead_id).execute()

        return state
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        return AgentState(error_message=f"Error creating invoice: {str(e)}")
"""
    try:
        await send_invoice.ainvoke({
                "invoice_id": invoice_id,
                "subject": f"Invoice for {lead_name} from {company_name}",
                "note": "Please make the payment at your earliest convenience",
                "send_to_invoicer": True,
                "send_to_recipient": True,
                "additional_recipients": additional_recipients
            })

        logger.info("The invoice has been sent successfully")

        sup_client.table("invoices").update({"status": "sent", "updated_at": datetime.now().isoformat()}).eq("invoice_id", invoice_id).execute()
    except Exception as e:
        logger.error(f"Error sending invoice: {str(e)}")
        return AgentState(error_message=f"Error sending invoice: {str(e)}")"""