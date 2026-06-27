import httpx
from config import APOLLO_API_KEY
import asyncio

class ApolloClient:
    def __init__(self):
        self.base_url = "https://api.apollo.io/api/v1/"
        self.headers = {"Authorization": f"Bearer {APOLLO_API_KEY}",
                        "Cache-Control": "no-cache",
                        "Content-Type": "application/json",
                        "accept": "application/json"}
        self.timeout = 30
        self.max_retries = 3
    
    async def _retry_request(self, func, max_attempts=3):
        """Retry logic"""
        for attempt in range(max_attempts):
            try:
                return await func()
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def enrich_organization(self, domain: str) -> dict:
        """Get company data with retry"""
        async def request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/organizations/enrich",
                    params={"domain": domain},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        
        return await self._retry_request(request, self.max_retries)