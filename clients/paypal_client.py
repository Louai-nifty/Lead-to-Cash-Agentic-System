import httpx
from utils.loggings import get_logger
from typing import Optional, List, Dict, Any
from config import Paypal_Base_Url, Paypal_Access_Token

logger = get_logger(__name__)

class PayPalClient:
    def __init__(self):
        self.base_url = Paypal_Base_Url
        self.timeout = 30
    
    async def create_draft_invoice(self, detail: Dict[str, Any], invoicer: Dict[str, Any], primary_recipients: List[Dict[str, Any]], items: List[Dict[str, Any]],additional_recipients: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Creates a draft invoice in PayPal.
        """
        payload = {
            "detail": detail,
            "invoicer": invoicer,
            "primary_recipients": primary_recipients,
            "items": items
        }
        
        if additional_recipients is not None:
            payload["additional_recipients"] = additional_recipients


        headers = {
            "Authorization": f"Bearer {Paypal_Access_Token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v2/invoicing/invoices",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"PayPal API HTTP Error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"PayPal API Request Error: {e}")
                raise

    async def send_invoice(self, invoice_id: str, subject: Optional[str] = None, note: Optional[str] = None, send_to_invoicer: Optional[bool] = None, send_to_recipient: Optional[bool] = None, additional_recipients: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sends an invoice to recipients.
        """
        payload = {}
        if subject is not None:
            payload["subject"] = subject
        if note is not None:
            payload["note"] = note
        if send_to_invoicer is not None:
            payload["send_to_invoicer"] = send_to_invoicer
        if send_to_recipient is not None:
            payload["send_to_recipient"] = send_to_recipient
        if additional_recipients is not None:
            payload["additional_recipients"] = additional_recipients

        headers = {
            "Authorization": f"Bearer {Paypal_Access_Token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v2/invoicing/invoices/{invoice_id}/send",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"PayPal API HTTP Error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"PayPal API Request Error: {e}")
                raise