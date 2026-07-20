import asyncio
import re
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import httpx
from utils.loggings import get_logger
from models.requests import TallySubmission, EmailSubmission
import json
from database.db import get_client
from agent.graph import cash_agent
from agent.state import AgentState
from agent.nodes.approval_handler_node import approval_handler_node
from langgraph.errors import GraphInterrupt
from langgraph.types import Command
import urllib.parse

sup_client = get_client()
logger = get_logger(__name__)
router = APIRouter()


async def _resume_approval_workflow(
    thread_id: str,
    decision: str,
    lead_email: str | None = None,
    deal_size: int | None = None,
    manager_name: str | None = None,
) -> None:
    logger.info(
        "Resuming approval workflow for thread %s with decision %s",
        thread_id,
        decision,
    )

    state_update = {
        "approval_decision": decision,
        "lead_id": thread_id,
    }
    if lead_email is not None:
        state_update["lead_email"] = lead_email
    if deal_size is not None:
        state_update["deal_size"] = deal_size
    if manager_name is not None:
        state_update["manager_name"] = manager_name

    fallback_state = AgentState(
        lead_email=lead_email,
        deal_size=deal_size,
        manager_name=manager_name,
        approval_decision=decision,
        lead_id=thread_id,
    )

    logger.info(
        "Executing approval handler directly for thread %s with decision %s",
        thread_id,
        decision,
    )
    await approval_handler_node(fallback_state)

    try:
        await cash_agent.ainvoke(
            Command(
                update=state_update,
                goto="approval_handler",
            ),
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception as exc:
        logger.warning(
            "Graph resume fallback completed after direct approval handling for thread %s: %s",
            thread_id,
            exc,
            exc_info=True,
        )


def _build_thread_id(lead_email: str, lead_id: str | None = None) -> str:
    normalized_email = (lead_email or "lead").strip().lower()
    normalized_email = re.sub(r"[^a-z0-9._:-]+", "-", normalized_email)

    if lead_id:
        return f"{lead_id}:{normalized_email}"
    return f"lead:{normalized_email}"


def _parse_slack_body(body_str: str) -> dict:
    if not body_str:
        raise ValueError("Empty request body")

    if body_str.startswith("payload="):
        parsed = urllib.parse.parse_qs(body_str, keep_blank_values=True)
        encoded_payload = parsed.get("payload", [""])[0]
        if not encoded_payload:
            raise ValueError("Missing Slack payload")
        return json.loads(urllib.parse.unquote_plus(encoded_payload))

    try:
        return json.loads(body_str)
    except json.JSONDecodeError:
        return json.loads(urllib.parse.unquote_plus(body_str))


# Background task functions for the for submission
async def process_form_submission(payload: TallySubmission) -> None:
    """
    Background task to process form submission.
    This function will be called asynchronously after webhook returns.
    """
    try:
        logger.info(f"Processing form submission from {payload}")
        
        fields = payload.data.fields
        lead_data = {}
        for field in fields:
            if field.label == "What is your first name?":
                lead_data['lead_name'] = field.value
            if field.label == "What is your email address?":
                lead_data['email'] = field.value
            if field.label == "What is your phone number?":
                lead_data['phone'] = field.value
            if field.label == "What is your company name?":
                lead_data['company'] = field.value
            if field.label == "What is your job title?":
                lead_data['role'] = field.value
            if field.label == "Tell us a bit about what you want":
                lead_data['message'] = field.value
 
        
        lead_email = lead_data.get("email")
        if not lead_email:
            raise ValueError("Missing lead email in form submission")

        domain = lead_email.split("@")[1]
        response = sup_client.table("Leads").select("*", count="exact").eq("email", lead_email).execute()
        count = response.count
        lead_record = None

        if count == 0:
            lead_data['Status'] = "new"
            lead_data['source'] = "tally_form"
            lead_data['form_sub_json'] = payload.model_dump()
            insert_response = sup_client.table("Leads").insert(lead_data).execute()
            lead_record = insert_response.data[0] if insert_response.data else None
        else:
            sup_client.table("Leads").update({"Status":"old"}).eq("email", lead_email).execute()
        lead_id = sup_client.table("Leads").select("lead_id").eq("email", lead_email).execute().data[0]["lead_id"]
        
        
        await cash_agent.ainvoke({
            "lead_email": lead_data['email'],
            "lead_domain": domain,
        },
            config={"configurable": {"thread_id": lead_id}}
        )

        lead_record = response.data[0] if response.data else None

        thread_id = _build_thread_id(
            lead_email,
            (lead_record or {}).get("lead_id") or (lead_record or {}).get("id")
        )
        
        try:
            await cash_agent.ainvoke(
                {
                    "lead_email": lead_data['email'],
                    "lead_domain": domain,
                    "lead_id": thread_id,
                },
                config={"configurable": {"thread_id": thread_id}}
            )
        except GraphInterrupt:
            logger.info("Workflow paused for manager approval")

    except Exception as e:
        logger.error(f"Error processing form submission: {str(e)}", exc_info=True)


@router.post("/webhook/tally-form")
async def tally_form_webhook(payload: TallySubmission, background_tasks: BackgroundTasks):
    
    logger.info(f"Received form submission: {payload}")
    
    background_tasks.add_task(process_form_submission, payload)
    
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Form submission received and queued for processing"}
    )



@router.post("/webhook/slack-approval")
async def slack_approval_webhook(request: Request):
    """
    Endpoint to handle Slack approval responses.
    This endpoint will be called by Slack when a user interacts with the approval buttons.
    """
    try:
        body_str = (await request.body()).decode()
        body = _parse_slack_body(body_str)
        
        action = body["actions"][0]
        raw_value = action.get("value", "")
        decision = action["action_id"].split("_")[0]  # "approve" or "reject"
        thread_id = None
        lead_email = None
        deal_size = None
        manager_name = None

        if raw_value.startswith("{"):
            try:
                parsed_value = json.loads(raw_value)
                thread_id = str(parsed_value.get("thread_id") or parsed_value.get("lead_id") or "")
                lead_email = parsed_value.get("lead_email")
                deal_size = parsed_value.get("deal_size")
                manager_name = parsed_value.get("manager_name")
                if parsed_value.get("action"):
                    decision = parsed_value["action"]
            except json.JSONDecodeError:
                logger.warning("Could not parse Slack approval payload as JSON: %s", raw_value)

        if not thread_id:
            thread_id = raw_value.split("_", 1)[1] if "_" in raw_value else raw_value
        
        response_url = body["response_url"]
        httpx.post(response_url, json={"text": "Decision received."})

        if not thread_id and lead_email:
            thread_id = _build_thread_id(lead_email)

        await _resume_approval_workflow(
            thread_id=thread_id,
            decision=decision,
            lead_email=lead_email,
            deal_size=deal_size,
            manager_name=manager_name,
        )

        return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logger.error(f"Error processing Slack approval: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error"})
    
    
    
    
@router.post("/slack/proposal-action")
async def handle_proposal_action(request: Request):
    try:
        body = await request.json()
    
        action = body["actions"][0]
        lead_id = action["value"].split("_")[1]
        action_id = action["action_id"]
    
        response_url = body["response_url"]
        httpx.post(response_url, json={"text": "Processing..."})
        
        
    
        if action_id == "send_proposal":
            asyncio.create_task(
                cash_agent.ainvoke(
                    Command(
                        update={"proposal_send_trigger": True},
                        goto="proposal_sender"
                    ),
                    config={"configurable": {"thread_id": lead_id}}
                )
            )
    
        return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logger.error(f"Error processing Slack approval: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error"})