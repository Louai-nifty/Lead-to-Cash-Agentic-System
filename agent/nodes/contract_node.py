import base64
from agent.state import AgentState
from utils.loggings import get_logger
from database.db import get_client
from tools.contract import create_opensign_contact, create_opensign_document, get_opensign_document, setup_opensign_webhook

sup_client = get_client()
logger = get_logger(__name__)


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

        lead_contact = await create_opensign_contact.ainvoke({"email": lead_email,"name": lead_name,"role": role,"company": company_name,"phone": phone})

        
        signers = [
                {
                    "email": lead_email,
                    "name": lead_name,
                    "company": company_name,
                    "role": role,
                    "phone": phone,                    "signer_role": "signer",
                    "widgets": [
                        {
                            "type": "signature",
                            "page": 8,
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
                            "page": 8,
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
            title="Contract Agreement",
            signers=signers,
            note="Please review and sign.",
            description="Annual contract for services.",
            time_to_complete_days=15,
            send_email=True,
            email_subject="{{sender_name}} has requested you to sign {{document_title}}",
            email_body="<p>Hi {{receiver_name}},</p><p>Please sign <a href='{{signing_url}}'>here</a>.</p>",
            enable_otp=False,
            allow_modifications=False,
        )




    except Exception as e:
        logger.error("")