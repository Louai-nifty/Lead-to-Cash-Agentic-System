from agent.state import AgentState
from fastapi import requests
from _pytest import config
import asyncio
import re
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse
import httpx
from utils.loggings import get_logger
from models.requests import TallySubmission, EmailSubmission
import json
from database.db import get_client
import urllib.parse
from agent.tools.notification import slack_notification_tool
from config import contracts_channel_id

sup_client = get_client()
logger = get_logger(__name__)
router = APIRouter()

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
async def process_form_submission(agent, payload: TallySubmission) -> None:
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

        if count == 0:
            lead_data['status'] = "new"
            lead_data['source'] = "tally_form"
            lead_data['form_sub_json'] = payload.model_dump()
            sup_client.table("Leads").insert(lead_data).execute()
        else:
            sup_client.table("Leads").update({"status":"old"}).eq("email", lead_email).execute()
        lead_id = sup_client.table("Leads").select("lead_id").eq("email", lead_email).execute().data[0]["lead_id"]
        
        
        await agent.ainvoke({
            "lead_email": lead_data['email'],
            "lead_domain": domain,
        },
            config={"configurable": {"thread_id": str(lead_id)}}
        )
    except Exception as e:
        logger.error(f"Agent run with thread_id: {lead_id} failed {str(e)}", exc_info=True)

@router.post("/webhook/tally-form")
async def tally_form_webhook(request: Request, payload: TallySubmission, background_tasks: BackgroundTasks):
    
    logger.info(f"Received form submission: {payload}")

    agent = request.app.state.agent
    
    background_tasks.add_task(process_form_submission, agent, payload)
    
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Form submission received and queued for processing"}
    )



@router.post("/webhook/slack-approval")
async def slack_approval_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body_str = (await request.body()).decode()
        body = _parse_slack_body(body_str)
        
        action = body["actions"][0]
        raw_value = action.get("value", "")
        action_id = action["action_id"]
        
        decision = action_id.split("_")[0] 
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

        response_url = body.get("response_url")
        if response_url:
            background_tasks.add_task(httpx.post, response_url, json={"text": "Decision received."})

        agent = request.app.state.agent
        config = {"configurable": {"thread_id": thread_id}}

        state_update = {"approval_decision": decision}
        if lead_email is not None:
            state_update["lead_email"] = lead_email
        if deal_size is not None:
            state_update["deal_size"] = deal_size
        if manager_name is not None:
            state_update["manager_name"] = manager_name

        async def resume_graph():
            await agent.aupdate_state(config, state_update)
            await agent.ainvoke(None, config=config)

        background_tasks.add_task(resume_graph)
        
        return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logger.error(f"Error processing Slack approval: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error"})
    
    
    
    
@router.post("/slack/proposal-action")
async def handle_proposal_action(request: Request, background_tasks: BackgroundTasks):
    try:
        body_str = (await request.body()).decode()
        body = _parse_slack_body(body_str)

        action = body["actions"][0]
        lead_id = str(action["value"].split("_", 1)[1])
        action_id = action["action_id"]
        response_url = body["response_url"]

        agent = request.app.state.agent

        if action_id == "review_proposal":
            logger.info(f"Rep is reviewing the proposal for lead {lead_id}")

        elif action_id == "send_proposal":
            httpx.post(response_url, json={
                "replace_original": True,
                "text": "Sending proposal to the lead now..."
            })

            
            config={"configurable": {"thread_id": lead_id}}
            snapshot = await agent.aget_state(config)
            logger.info(f"SNAPSHOT NEXT NODES: {snapshot.next}")
            
            background_tasks.add_task(
                agent.ainvoke,
                None,
                config=config
            )

        return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logger.error(f"Error processing Slack approval: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error"})

@router.get("/proposals/view/{filename}")
async def view_proposal(filename: str):
    try:
        # Fetch the raw HTML file bytes from Supabase storage
        file_bytes = sup_client.storage.from_("proposals").download(f"proposals/{filename}")
        return HTMLResponse(content=file_bytes)
    except Exception as e:
        logger.error(f"Failed to fetch proposal {filename}: {str(e)}")
        return HTMLResponse(content="<h1>Proposal not found or an error occurred.</h1>", status_code=404)



@router.post("/contract/sign/{lead_id}")

async def sign_contract(lead_id: str, request: Request, background_tasks: BackgroundTasks):
    """
    Lead clicks signature link from proposal email.
    Triggers contract generation.
    """
    try:
        logger.info("Lead clicked the signature link. Contract generation is about to start.")
        agent = request.app.state.agent
        config={"configurable": {"thread_id": lead_id}}
        background_tasks.add_task(
            agent.ainvoke,
            None,
            config=config
        )


    except Exception as e:
        logger.error(f"Error generating contract for lead {lead_id}: {str(e)}")
        return HTMLResponse(content="<h1>Error generating contract. Please contact support.</h1>", status_code=500)


@router.post("/webhook/opensign-listener")
async def opensign_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle OpenSign events (signing, completion, etc.).
    and triggers the next node (invoice & payment) once the document is signed by both parties.
    """
    try:
        data = await request.json()
        
        event_type = data["event"]
        
        document_id = data["objectId"]
        logger.info(f"OpenSign event received: {event_type} for {document_id}")

        if not document_id:
            logger.warning("No document_id in OpenSign event")
            return JSONResponse(status_code=400, content={"status": "error", "message": "Missing document_id"})

        if event_type == "created":
            logger.info(f"Ignoring 'created' event for {document_id} to allow DB insert to complete.")
            return JSONResponse(status_code=200, content={"status": "success"})

        contract_response = None
        max_retries = 6
        retry_delay = 1 

        for attempt in range(max_retries):
            contract_response = sup_client.table("contracts").select(
                "lead_id, opensign_id, contract_data, rep_sign_url"
            ).eq("opensign_id", document_id).execute()
            
            if contract_response.data:
                break
            
            logger.warning(f"Contract not found on attempt {attempt + 1} for {document_id}. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)

        lead_id = contract_response.data[0]["lead_id"]

        lead_data = sup_client.table("Leads").select("email, lead_name").eq("lead_id", lead_id).execute().data[0]
        lead_email = lead_data["email"]
        lead_name = lead_data["lead_name"]

        rep_id = sup_client.table("Leads").select("assigned_rep_id").eq("lead_id", lead_id).execute().data[0]
        rep_data = sup_client.table("Users").select("name, email").eq("id", rep_id["assigned_rep_id"]).execute().data[0]
        rep_name = rep_data["name"]
        rep_email = rep_data["email"]

        rep_link = contract_response.data[0]["rep_sign_url"]

        if event_type == "signed":
            signer_email = data["signer"]["email"]
            if signer_email == lead_email:

                logger.info(f"Contract {document_id} has been signed by {lead_email}")

                sup_client.table("contracts").update({"lead_signed_at": datetime.now().isoformat(), "status": "half-signed"}).eq("opensign_id", document_id).execute()

                message = f"""Lead {lead_name} has signed the contract,The contract is ready for the rep's {rep_name} to sign
                
                Link to sign : {rep_link}"""

                await slack_notification_tool.ainvoke({"channel": contracts_channel_id, "text": message, "webhook_type": "contract"})
            elif signer_email == rep_email:

                logger.info(f"Contract {document_id} has been signed by Rep {rep_name}")

                sup_client.table("contracts").update({"rep_signed_at": datetime.now().isoformat(), "status": "half-signed"}).eq("opensign_id", document_id).execute()

        elif event_type == "viewed":
            signer_email = data["signers"][0]["email"]
            if signer_email == lead_email:
                logger.info(f"Contract {document_id} has been viewed by {lead_email} at {datetime.now()}")
                sup_client.table("contracts").update({"lead_viewed_at": datetime.now().isoformat(), "status": "viewed"}).eq("opensign_id", document_id).execute()
            elif signer_email == rep_email:
                logger.info(f"Contract {document_id} has been viewed by Rep {rep_name} at {datetime.now()}")
                sup_client.table("contracts").update({"rep_viewed_at": datetime.now().isoformat(), "status": "viewed"}).eq("opensign_id", document_id).execute()
                
            logger.info(f"Contract {document_id} viewed for lead {lead_id}")

        elif event_type == "expired":
            logger.info(f"Contract {document_id} expired for lead {lead_email}")
            sup_client.table("contracts").update({"status": "expired"}).eq("opensign_id", document_id).execute()

        elif event_type == "declined":
            logger.info(f"Contract {document_id} declined for lead {lead_email}")
            sup_client.table("contracts").update({"status": "declined"}).eq("opensign_id", document_id).execute()

        elif event_type == "completed":
            logger.info(f"Contract {document_id} has been signed by both parties")
            sup_client.table("contracts").update({"status": "completed","updated_at": datetime.now().isoformat()}).eq("opensign_id", document_id).execute()

            agent = request.app.state.agent
            config={"configurable": {"thread_id": lead_id}}
            background_tasks.add_task(
                agent.ainvoke,
                None,
                config=config
            )
            logger.info("The invoice node has been triggered successfully!")

        
        return JSONResponse(status_code=200, content={"status": "success", "event": event_type})
        

    except json.JSONDecodeError:
        logger.error("Invalid JSON in OpenSign webhook")
        return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid JSON payload"})
    except Exception as e:
        logger.error(f"Error processing OpenSign webhook: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@router.post("/webhook/paypal-payment")
async def paypal_payment_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()

        event_id = data["id"]
        event_type = data["event_type"]
        event_time = data["create_time"]

        if event_type == "INVOICING.INVOICE.CREATED":
            logger.info(f"Invoice {event_id} has been created")

        elif event_type == "INVOICING.INVOICE.PAID":
            logger.info(f"Invoice {event_id} has been paid")
        
        
        elif event_type == "INVOICING.INVOICE.CANCELLED":
            logger.info(f"Invoice {event_id} has been cancelled")
        
        elif event_type == "INVOICING.INVOICE.REFUNDED":
            logger.info(f"Invoice {event_id} has been refunded")
        
            
        


        
        
    except Exception as e:
        logger.error(f"Error processing PayPal payment webhook: {str(e)}", exc_info=True)
        return AgentState(status="error", error_message=f"Error processing PayPal payment webhook: {str(e)}") 