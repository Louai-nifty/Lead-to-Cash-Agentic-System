from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from config import Slack_Approval_Bot_Token, Slack_Proposal_Bot_Token
import logging

logger = logging.getLogger(__name__)

class SlackApprovalClient:
    def __init__(self):
        self.client = AsyncWebClient(token=Slack_Approval_Bot_Token)
    
    async def send_message(self, channel: str, text: str) -> dict:
        """Send a simple message to a channel"""
        try:
            result = await self.client.chat_postMessage(channel=channel, text=text)
            return result
        except SlackApiError as e:
            logger.error(f"Slack error: {e}")
            raise
    
    async def send_approval_request(self, channel: str, text: str, blocks: list) -> dict:
        """Send a message with interactive buttons for approvals"""
        try:
            result = await self.client.chat_postMessage(channel=channel, text=text, blocks=blocks)
            return result
        except SlackApiError as e:
            logger.error(f"Slack error: {e}")
            raise

class SlackProposalClient:
    def __init__(self):
        self.client = AsyncWebClient(token=Slack_Proposal_Bot_Token)
    
    async def send_message(self, channel: str, text: str) -> dict:
        """Send a simple message to a channel"""
        try:
            result = await self.client.chat_postMessage(channel=channel, text=text)
            return result
        except SlackApiError as e:
            logger.error(f"Slack error: {e}")
            raise
    
    async def send_approval_request(self, channel: str, text: str, blocks: list) -> dict:
        """Send a message with interactive buttons for approvals"""
        try:
            result = await self.client.chat_postMessage(channel=channel, text=text, blocks=blocks)
            return result
        except SlackApiError as e:
            logger.error(f"Slack error: {e}")
            raise