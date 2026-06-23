import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import imaplib
import email
from models.requests import EmailSubmission 
from email.header import decode_header
from utils.loggings import get_logger
from typing import List, Dict
from database.db import get_client
from agent.graph import cash_agent
from config import GMAIL_EMAIL, GMAIL_APP_PASSWORD, IMAP_SERVER, IMAP_PORT

logger = get_logger()

sup_client = get_client()
scheduler = AsyncIOScheduler()


async def fetch_new_emails() -> List[Dict]:
    """
    Connect to Gmail via IMAP and fetch new emails.
    
    Returns:
        List of dictionaries containing email data with keys:
        - from_email: Sender's email address
        - subject_line: Email subject
        - email_body: Email body text
    """
    emails_data = []
    
    try:
        logger.info("Connecting to Gmail IMAP server...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        
        mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        logger.info(f"Successfully logged in as {GMAIL_EMAIL}")
        
        mail.select("INBOX")
        
        logger.info("Searching for unread emails...")
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK":
            logger.warning("Failed to search for emails")
            mail.close()
            mail.logout()
            return emails_data
        
        email_ids = messages[0].split()
        
        if not email_ids:
            logger.info("No new unread emails found")
            mail.close()
            mail.logout()
            return emails_data
        
        logger.info(f"Found {len(email_ids)} new emails")
        
        # Process each email
        for email_id in email_ids:
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    logger.warning(f"Failed to fetch email {email_id}")
                    continue
                
                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Extract sender email
                from_email = msg.get("From", "")
                # Clean up email format (extract just the email part if it's "Name <email@domain.com>")
                if "<" in from_email and ">" in from_email:
                    from_email = from_email.split("<")[1].split(">")[0]
                
                # Extract subject
                subject_line = decode_header_line(msg.get("Subject", "No Subject"))
                
                # Extract email body
                email_body = extract_email_body(msg)
                
                # Create email data dictionary matching EmailSubmission model
                email_data = {
                    "from_email": from_email,
                    "subject_line": subject_line,
                    "email_body": email_body
                }
                
                emails_data.append(email_data)
                logger.info(f"Extracted email from {from_email} with subject: {subject_line}")
                
                # Mark email as read so it doesn't get fetched again
                mail.store(email_id, "+FLAGS", "\\Seen")
                
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {str(e)}", exc_info=True)
                continue
        
        mail.close()
        mail.logout()
        logger.info(f"Successfully processed {len(emails_data)} emails")
        
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP error: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in fetch_new_emails: {str(e)}", exc_info=True)
    
    return emails_data


def decode_header_line(header: str) -> str:
    """
    Decode email header lines (handles encoding like =?utf-8?...)
    """
    if not header:
        return ""
    
    try:
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or "utf-8", errors="replace")
            else:
                decoded_string += str(part)
        
        return decoded_string
    except Exception as e:
        logger.warning(f"Error decoding header: {str(e)}")
        return header


def extract_email_body(msg) -> str:
    """
    Extract plain text body from email message.
    Handles both plain text and multipart emails.
    """
    body = ""
    
    try:
        if msg.is_multipart():
            # For multipart emails, get the first plain text part
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get plain text
                if content_type == "text/plain":
                    charset = part.get_content_charset()
                    body = part.get_payload(decode=True).decode(charset or "utf-8", errors="replace")
                    break
                
                # Fallback to HTML if no plain text
                elif content_type == "text/html" and not body:
                    charset = part.get_content_charset()
                    body = part.get_payload(decode=True).decode(charset or "utf-8", errors="replace")
        else:
            # Simple text email
            charset = msg.get_content_charset()
            body = msg.get_payload(decode=True).decode(charset or "utf-8", errors="replace")
    
    except Exception as e:
        logger.warning(f"Error extracting email body: {str(e)}")
        body = ""
    
    # Clean up body (remove excess whitespace)
    body = body.strip()
    return body if body else "No content"


@scheduler.scheduled_job('interval', minutes=4)
async def poll_gmail():
    """
    Scheduler job that runs every 4 minutes to poll Gmail for new emails.
    Fetches new emails and prepares them for processing.
    """
    logger.info("=== Starting Gmail poll ===")
    
    try:
        emails = await fetch_new_emails()
        lead_data = {}
        if emails:
            logger.info(f"Processing {len(emails)} new emails")
            for email_data in emails:
                email_submission = EmailSubmission(**email_data)
                
                lead_data['email'] = email_submission.from_email
                lead_data['message'] = email_submission.email_body
                lead_data['company'] = email_submission.from_email.split("@")[1].split(".")[0]
                lead_data['domain']= email_submission.from_email.split("@")[1]
                response = sup_client.table("Leads").select("*", count="exact").eq("email", lead_data['email']).execute()
                count = response.count
                if count == 0:
                    lead_data['source'] = "email"
                    lead_data['Status'] = "new"
                    sup_client.table("Leads").insert(lead_data).execute()
                else:
                    sup_client.table("Leads").update({"Status":"old"}).eq("email", lead_data['email']).execute()
                cash_agent.invoke({
                    "lead_email": lead_data['email'],
                    "lead_domain": lead_data['domain']
                    })
        
        else:
            logger.info("No new emails to process")
    
    except Exception as e:
        logger.error(f"Error in poll_gmail scheduler: {str(e)}", exc_info=True)
    
    logger.info("=== Completed Gmail poll ===")