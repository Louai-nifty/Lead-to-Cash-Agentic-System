import base64
from datetime import datetime
from agent.state import AgentState
from utils.loggings import get_logger
from database.db import get_client
from agent.tools.contract import create_opensign_contact, create_opensign_document, get_opensign_document, get_opensign_contact_list
from services.contract_service import generate_contract_pdf
from services.smtp_service import SMTPService

sup_client = get_client()
logger = get_logger(__name__)
smtp_client = SMTPService()


async def contract_generation_node(state: AgentState) -> AgentState:
    """
    Generate contract from template and prepare for signing via Docuseal/OpenSign.
    """
    try:
        lead_id = state.id
        lead_email = state.lead_email
        lead_name = state.lead_name
        company_name = state.company_name
        deal_size = state.estimated_deal_size
        rep_name = state.rep_name
        rep_email = state.rep_email


        late_data = sup_client.table("Leads").select("role", "phone").eq("id", lead_id).execute().data[0]

        role = late_data["role"]
        phone = late_data["phone"]

        rep_contact = await get_opensign_contact_list.ainvoke()
        for contact in rep_contact["result"]:
            if contact["email"] == rep_email:
                rep_signer_id = contact["objectId"]
                break
        else:
            logger.warning(f"No contact found with email: {rep_email}")
            return AgentState(
                error=f"No contact found with email: {rep_email}"
            )

        lead_contact = await create_opensign_contact.ainvoke({"email": lead_email,"name": lead_name,"role": role,"company": company_name,"phone": phone})

        lead_signer_id = lead_contact["objectId"]
        


        contract_pdf = generate_contract_pdf(lead_name, lead_email, rep_name, rep_email, company_name, deal_size)
        file_base64 = base64.b64encode(contract_pdf).decode("utf-8")
        signers = [
                {
                    "email": lead_email,
                    "name": lead_name,
                    "company": company_name,
                    "role": role,
                    "phone": phone,                    
                    "signer_role": "signer",
                    "widgets": [
                        {
                            "type": "signature",
                            "page": 1,
                            "x": 200,
                            "y": 300,
                            "w": 100,
                            "h": 30,
                            "options": {
                                "hint": f"{lead_name} Signature"
                            }
                        }
                    ]
                },
                {
                    "email": rep_email,
                    "name": rep_name,
                    "role": "Senior Rep",
                    "signer_role": "signer",
                    "widgets": [
                        {
                            "type": "signature",
                            "page": 1,
                            "x": 200,
                            "y": 400,
                            "w": 100,
                            "h": 30,
                            "options": {
                                "hint": f"Rep's {rep_name} Signature"
                            }
                        }
                    ]
                }
            ]

        response = await create_opensign_document.ainvoke(
            file_base64=file_base64,
            title=f"Contract Agreement for {lead_name} from {company_name}",
            signers=signers,
            note="Please review and sign.",
            description="Our legal contract for services.",
            email_subject=subject,
            email_body=html_content
        )
        
        contract_id = response["objectId"]
        url_links = {}
        for signer in response["signurl"]:
            email = signer['email'].lower()
            url = signer['url']

            if email == lead_email.lower():
                url_links['lead_sign_url'] = url
            elif email == rep_email.lower():
                url_links['rep_sign_url'] = url

        lead_link = url_links["lead_sign_url"]  
        rep_link = url_links["rep_sign_url"]
        subject = f"You have a new contract to sign {lead_name} from {company_name}"
        html_content = f"""
        <html>
            <body>
                <p>Hi {lead_name},</p>
                <p>Please review and sign your contract here:</p>
                <a href="{lead_link}">View Contract</a>
                <p>Looking forward to your feedback.</p>
            </body>
        </html>
        """



        logger.info(f"Contract created successfully {contract_id} for {lead_name} with {lead_email}")

        success = await smtp_client.send_email(lead_email, subject, html_content)

        if success:
            logger.info(f"Contract sent successfully {contract_id} for {lead_name} with {lead_email}")
        else:
            logger.error(f"Failed to send contract {contract_id} to {lead_email}")
            return AgentState(
                error=f"Failed to send contract {contract_id} to {lead_email}"
            )
        
        doc = await get_opensign_document.ainvoke(contract_id)
        file_url = doc["file"]

        contact_data = {
            "document_name": f"{lead_name}_Contract",
            "opensign_document_url": file_url,
            "signing_order": "sequential",
            "expiry_days": 21,
            "created_at": datetime.now().isoformat()
            }

        sup_client.table("contract").insert({
                "lead_id": lead_id,
                "opensign_id": contract_id,
                "status": "sent",
                "lead_signer_id": lead_signer_id,
                "rep_signer_id": rep_signer_id,
                "sent_at":datetime.now(),
                "contract_data": contact_data,
                "lead_sign_url": lead_link,
                "rep_sign_url": rep_link
        }).execute()

        logger.info("Contract created successfully")
        return state

    except Exception as e:
        logger.error(f"Failed to create contract: {str(e)}")