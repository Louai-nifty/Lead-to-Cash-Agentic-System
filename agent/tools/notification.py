from clients.slack_client import SlackClient
from langchain_core.tools import tool
from utils.loggings import get_logger
from typing import Optional

client = SlackClient()
logger = get_logger(__name__)

@tool
async def slack_notification_tool(channel: str, text: str, blocks: Optional[list] = None):
  """Send a Slack message to a channel with optional interactive blocks."""
  try:
      if blocks is None:
        await client.send_message(channel, text) 
      else:
        await client.send_approval_request(channel, text, blocks)
          
  except Exception as e:
      logger.error(f"Failed to send slack notification, {str(e)}")