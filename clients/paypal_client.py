import httpx
import logging
from typing import Optional, List, Dict, Any

# Assuming these are defined in your config.py
# PayPal_Base_Url = "https://api-m.sandbox.paypal.com" (or "https://api-m.paypal.com" for live)
# PayPal_Access_Token = "YOUR_OAUTH2_BEARER_TOKEN" 
from config import PayPal_Base_Url, PayPal_Access_Token

logger = logging.getLogger(__name__)

class PayPalClient:
    def __init__(self):
        self.base_url = PayPal_Base_Url
        self.api_token = PayPal_Access_Token
        self.timeout = 30
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def create_draft_invoice(self, detail: Dict[str, Any], invoicer: Dict[str, Any], primary_recipients: List[Dict[str, Any]], items: List[Dict[str, Any]],additional_recipients: Optional[List[str]] = None,configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates a draft invoice in PayPal.
        """
        payload = {
            "detail": detail,
            "invoicer": invoicer,
            "primary_recipients": primary_recipients,
            "items": items
        }
        
        # Add optional fields only if they are provided to keep the payload clean
        if additional_recipients is not None:
            payload["additional_recipients"] = additional_recipients
            
        if configuration is not None:
            payload["configuration"] = configuration

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v2/invoicing/invoices",
                    json=payload,
                    headers=self.headers
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v2/invoicing/invoices/{invoice_id}/send",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"PayPal API HTTP Error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"PayPal API Request Error: {e}")
                raise