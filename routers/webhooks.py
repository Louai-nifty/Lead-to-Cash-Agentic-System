from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from utils.loggings import get_logger
from models import FormSubmission, EmailSubmission



logger = get_logger(__name__)

router = APIRouter()


# Background task functions
async def process_form_submission(payload: FormSubmission) -> None:
    """
    Background task to process form submission.
    This function will be called asynchronously after webhook returns.
    """
    try:
        logger.info(f"Processing form submission from {payload.email}")
        lead_data = payload.model_dump()
        
        
        
        
        logger.info(f"Form submission processed successfully: {payload.name} ({payload.email})")
    except Exception as e:
        logger.error(f"Error processing form submission: {str(e)}", exc_info=True)


async def process_email_submission(payload: EmailSubmission) -> None:
    """
    Background task to process email submission.
    This function will be called asynchronously after webhook returns.
    """
    try:
        logger.info(f"Processing email submission from {payload.from_email}")
        
        logger.info(f"Email submission processed successfully: {payload.from_email}")
    except Exception as e:
        logger.error(f"Error processing email submission: {str(e)}", exc_info=True)


@router.post("/webhook/tally-form")
async def tally_form_webhook(payload: FormSubmission, background_tasks: BackgroundTasks):
    logger.info(f"Received form submission: {payload.dict()}")
    
    background_tasks.add_task(process_form_submission, payload)
    
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Form submission received and queued for processing"}
    )


@router.post("/webhook/email-hook")
async def email_webhook(payload: EmailSubmission, background_tasks: BackgroundTasks):

    logger.info(f"Received email submission: {payload.dict()}")
    
    background_tasks.add_task(process_email_submission, payload)
    
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Email submission received and queued for processing"}
    )
    