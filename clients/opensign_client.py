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
    
    async def create_document(self, template_id: str, document_name: str, signers: list, default_values: dict = None) -> dict:
        """Create document from template with signer details"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "templateId": template_id,
                "documentName": document_name,
                "signers": signers
            }
            if default_values:
                payload["defaultValues"] = default_values
            
            response = await client.post(
                f"{self.base_url}/createdocument/{template_id}",
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