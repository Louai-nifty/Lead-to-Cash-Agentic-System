from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from utils.loggings import get_logger
from models.requests import TallySubmission, EmailSubmission
import json
from database.db import get_client
from agent.graph import cash_agent

sup_client = get_client()
logger = get_logger(__name__)
router = APIRouter()


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
        domain = lead_email.split("@")[1]
        response = await sup_client.table("Leads").select("*", count="exact").eq("email", lead_email).execute()
        count = response.count
        if count == 0:
            lead_data['Status'] = "new"
            lead_data['source'] = "tally_form"
            lead_data['form_sub_json'] = payload.model_dump()
            await sup_client.table("Leads").insert(lead_data).execute()
        else:
            await sup_client.table("Leads").update({"Status":"old"}).eq("email", lead_email).execute()
        
        cash_agent.invoke({
            "lead_email": lead_data['email'],
            "lead_domain": domain
        })
        
        logger.info(f"Form submission processed successfully: {payload} ({payload})")
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
    