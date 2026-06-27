from langchain_core.tools import tool
from clients.apollo_client import enrich_organization
from utils.loggings import get_logger

logger = get_logger()
@tool
async def enrichment_tool(lead_domain: str):
    "The tool responsible for the enrichment that uses Clearbit as a client for that"
    try:
        result = await enrich_organization(lead_domain)
        return result
    except Exception as e:
        return logger.error(f"Failed to use enrichment tool, {str(e)}")