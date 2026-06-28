import httpx
from config import Hunter_API_Key

class HunterClient:
    def __init__(self):
        self.base_url = "https://api.hunter.io/v2"
        self.api_key = Hunter_API_Key
        self.timeout = 30
    
    async def enrich_organization(self, domain: str) -> dict:
        """Get company data by domain"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/companies/find",
                params={"domain": domain, "api_key": self.api_key}
            )
            response.raise_for_status()
            return response.json()