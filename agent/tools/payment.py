from langchain_core.tools import tool
from clients.paypal_client import PayPalClient
from utils.loggings import get_logger
from typing import Optional, Any, Dict, List

logger = get_logger(__name__)
paypal_client = PayPalClient()

@tool
async def create_invoice(detail: Dict[str, Any], invoicer: Dict[str, Any], primary_recipients: List[Dict[str, Any]], items: List[Dict[str, Any]],additional_recipients: Optional[List[str]] = None,configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Creates a draft invoice in PayPal. 
    Returns the invoice details including the PayPal invoice ID and status.
    """
    try:
        logger.info(f"Creating PayPal draft invoice for recipient: {primary_recipients[0].get('billing_info', {}).get('email_address', 'Unknown')}")
        invoice = await paypal_client.create_draft_invoice(
            detail=detail,
            invoicer=invoicer,
            primary_recipients=primary_recipients,
            items=items,
            additional_recipients=additional_recipients,
            configuration=configuration
        )
        logger.info(f"PayPal draft invoice created successfully with ID: {invoice.get('id')}")
        return invoice
    except Exception as e:
        logger.error(f"Failed to create PayPal draft invoice: {str(e)}")
        raise

@tool
async def send_invoice(invoice_id: str,subject: Optional[str] = None,note: Optional[str] = None,send_to_invoicer: Optional[bool] = None,send_to_recipient: Optional[bool] = None,additional_recipients: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Sends or schedules a draft invoice in PayPal to the recipient.
    Returns the send confirmation details.
    """
    try:
        logger.info(f"Sending PayPal invoice with ID: {invoice_id}")
        response = await paypal_client.send_invoice(
            invoice_id=invoice_id,
            subject=subject,
            note=note,
            send_to_invoicer=send_to_invoicer,
            send_to_recipient=send_to_recipient,
            additional_recipients=additional_recipients
        )
        logger.info(f"PayPal invoice {invoice_id} sent successfully")
        return response
    except Exception as e:
        logger.error(f"Failed to send PayPal invoice {invoice_id}: {str(e)}")
        raise