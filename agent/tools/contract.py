from langchain_core.tools import tool
from clients.opensign_client import OpenSignClient
from config import OPENSIGN_TEMPLATE_ID
from utils.loggings import get_logger
from typing import Optional

logger = get_logger(__name__)
opensign_client = OpenSignClient()

@tool
async def create_opensign_contact(email: str, name: str, role: str, company: str ,phone: Optional[str] = None) -> dict:
    """
    Create a new contact (signer) in OpenSign.
    Returns contact ID and details.
    """
    try:
        logger.info(f"Creating OpenSign contact: {email}")
        contact = await opensign_client.create_contact(
            email=email,
            name=name,
            phone=phone
        )
        logger.info(f"Contact created: {contact['id']}")
        return contact
    except Exception as e:
        logger.error(f"Failed to create contact: {str(e)}")
        raise

@tool
async def create_opensign_document(template_id: str, document_name: str, signers: list, company_name: str, client_name: str, deal_size: str, date: str) -> dict:
    """
    Create document from OpenSign template with signer details.
    Returns document ID and details.
    """
    try:
        logger.info(f"Creating OpenSign document: {document_name}")
        
        default_values = {
            "company_name": company_name,
            "client_name": client_name,
            "deal_size": deal_size,
            "date": date
        }
        
        document = await opensign_client.create_document(
            template_id=template_id,
            document_name=document_name,
            signers=signers,
            default_values=default_values
        )
        logger.info(f"Document created: {document['id']}")
        return document
    except Exception as e:
        logger.error(f"Failed to create document: {str(e)}")
        raise

@tool
async def get_opensign_document(document_id: str) -> dict:
    """
    Get document details including signing status and signer information.
    Returns document data and signature status.
    """
    try:
        logger.info(f"Fetching OpenSign document: {document_id}")
        document = await opensign_client.get_document(document_id)
        logger.info(f"Document fetched: {document_id}")
        return document
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}")
        raise

@tool
async def setup_opensign_webhook(webhook_url: str) -> dict:
    """
    Setup webhook URL for OpenSign document events (one-time setup).
    Webhook receives events: viewed, created, signed.
    """
    try:
        logger.info(f"Setting up OpenSign webhook: {webhook_url}")
        result = await opensign_client.setup_webhook(webhook_url)
        logger.info("Webhook setup successful")
        return result
    except Exception as e:
        logger.error(f"Failed to setup webhook: {str(e)}")
        raise