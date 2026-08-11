from utils.loggings import get_logger
from database.db import get_client
from datetime import datetime, timedelta
import time
from jinja2 import Template
from config import Company_Email, App_Domain

try:
    from weasyprint import HTML as WeasyHTML
except Exception:
    WeasyHTML = None


logger = get_logger(__name__)
sup_client = get_client()

def proposal_generator(email, headcount, deal_size, assigned_to, rep_name, rep_email, lead_id):
    try:
        lead = sup_client.table("Leads").select("*").eq("email", email).execute().data[0]
        lead_name = lead["lead_name"]
        lead_email = lead["email"]
        lead_role = lead["role"]
        contact_phone = lead["phone"]
        
        company_name = lead["company"]
        company_location = lead["location"]
        
        proposal_date = datetime.now().strftime("%B %d, %Y")
        expiry_date = (datetime.now() + timedelta(days=30)).strftime("%B %d, %Y")
        signature_link = f"{App_Domain}/contract/sign/{lead_id}"
        company_email = Company_Email
        
        
        if headcount < 50:
            template_file = "templates/starter_proposal.html"
        elif headcount < 500:
            template_file = "templates/professional_proposal.html"
        else:
            template_file = "templates/enterprise_proposal.html"
            
        
        with open(template_file, "r") as f:
            template_content = f.read()
        
        template = Template(template_content)
        filled_html = template.render(
            company_name=company_name,
            contact_name=lead_name,
            contact_email=lead_email,
            contact_phone=contact_phone,
            contact_title=lead_role,
            company_location=company_location,
            deal_size=deal_size,
            proposal_date=proposal_date,
            expiry_date=expiry_date,
            signature_link=signature_link,
            company_email=company_email
        )

        pdf_bytes = filled_html.encode("utf-8")
        safe_company = company_name.replace(" ", "_")
        safe_lead = lead_name.replace(" ", "_")
        pdf_filename = f"proposal_{safe_company}_{safe_lead}_{int(time.time())}.html"
        pdf_path = f"proposals/{pdf_filename}"

        if WeasyHTML is not None:
            try:
                pdf_bytes = WeasyHTML(string=filled_html).write_pdf()
                pdf_filename = f"proposal_{safe_company}_{safe_lead}_{int(time.time())}.pdf"
                pdf_path = pdf_filename
                logger.info("PDF generated successfully via WeasyPrint")
            except Exception as e:
                logger.warning(f"WeasyPrint failed ({str(e)}); using HTML fallback instead")
        
        sup_client.storage.from_("proposals").upload(pdf_path, pdf_bytes)
        
        if pdf_filename.endswith(".html"):
            pdf_url = f"{App_Domain}/proposals/view/{pdf_filename}"
        else:
            pdf_url = sup_client.storage.from_("proposals").get_public_url(pdf_path)
        
        template_name = template_file.split("/")[-1]
        
        sup_client.table("proposals").insert({
            "lead_id": lead_id,
            "assigned_to": assigned_to,
            "template_name": template_name,
            "pdf_url": pdf_url,
            "status": "draft"
        }).execute()
        
        logger.info("The prosposal has been drafted and inserted in the database")
    
        return {"pdf_url": pdf_url, "template": template_name}
    except Exception as e:
        logger.error(f"Proposal generation failed: {str(e)}")
        raise