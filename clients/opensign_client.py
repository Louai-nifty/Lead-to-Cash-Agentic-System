import httpx
from config import Sandbox_API_Token, OpenSign_Base_Url
import logging

logger = logging.getLogger(__name__)

class OpenSignClient:
    def __init__(self):
        self.base_url = OpenSign_Base_Url
        self.api_token = Sandbox_API_Token
        self.timeout = 30
        self.headers = {
            "x-api-token": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def create_contact(self, email: str, name: str, phone: str = None) -> dict:
        """Create a new contact (signer) in OpenSign"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "email": email,
                "name": name
            }
            if phone:
                payload["phone"] = phone
            
            response = await client.post(
                f"{self.base_url}/createcontact",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_document(self, file_base64: str, title: str, signers: list, note: str = None, description: str = None, time_to_complete_days: int = 21, send_in_order: bool = True, send_email: bool = True) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "file": file_base64,
                "title": title,
                "signers": signers,
                "timeToCompleteDays": time_to_complete_days,
                "sendInOrder": send_in_order,
                "send_email": send_email
            }
            if note:
                payload["note"] = note
            if description:
                payload["description"] = description

            response = await client.post(
                f"{self.base_url}/createdocument",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_document(self, document_id: str) -> dict:
        """Get document details including signing status"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/documents/{document_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def setup_webhook(self, webhook_url: str) -> dict:
        """Setup webhook URL for document events (one-time setup)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "url": webhook_url
            }
            
            response = await client.post(
                f"{self.base_url}/webhook",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()