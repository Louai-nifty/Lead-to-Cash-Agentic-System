from clients.slack_client import SlackProposalClient, SlackApprovalClient, SlackContractClient
from langchain_core.tools import tool
from utils.loggings import get_logger
from typing import Optional

approvalclient = SlackApprovalClient()
proposalclient = SlackProposalClient()
contractclient = SlackContractClient()
logger = get_logger(__name__)

@tool
async def slack_notification_tool(channel: str, text: str, webhook_type: str, blocks: Optional[list] = None):
  """Send a Slack message to a channel with optional interactive blocks."""
  try:
      if blocks is None:
        if webhook_type == "proposal":
          await proposalclient.send_message(channel, text)
        elif webhook_type == "approval":
          await approvalclient.send_message(channel, text)
        elif webhook_type == "contract":
          await contractclient.send_message(channel, text)

      else:
        if webhook_type == "proposal":
          await proposalclient.send_approval_request(channel, text, blocks)
        elif webhook_type == "approval":
          await approvalclient.send_approval_request(channel, text, blocks)
          
  except Exception as e:
      logger.error(f"Failed to send slack notification, {str(e)}")