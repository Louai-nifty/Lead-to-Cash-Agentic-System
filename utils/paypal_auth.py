import httpx
import base64
from config import Paypal_Client_ID, Paypal_Secret, Paypal_Base_Url

async def get_paypal_access_token() -> str:
    credentials = f"{Paypal_Client_ID}:{Paypal_Secret}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{Paypal_Base_Url}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        response.raise_for_status()
        return response.json()["access_token"]