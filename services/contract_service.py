import pdfkit
from datetime import datetime

contract_template = """
        # **PROFESSIONAL SERVICES AGREEMENT**

        This **Professional Services Agreement** ("Agreement") is made and entered into as of **{date}** (the "Effective Date"), by and between:

        ---
        **{company_name}**,
        a corporation ("**Client**");

        ---
        **AND**

        ---
        **{rep_name}**,
        an authorized representative ("**Service Provider**").

        ---
        ---
        ## **1. PARTIES**
        - **Client Name:** {lead_name}
        - **Client Email:** {lead_email}
        - **Service Provider Name:** {rep_name}
        - **Service Provider Email:** {rep_email}

        ---
        ---
        ## **2. SCOPE AND COMPENSATION**
        Service Provider agrees to provide services to Client for a total compensation of **${{deal_size}}**.

        ---
        ---
        ## **3. SIGNATURES**

        **CLIENT:**
        **Name:** {lead_name}
        **Email:** {lead_email}
        **Signature:** _____________________
        **Date:** _________________________

        ---
        **SERVICE PROVIDER:**
        **Name:** {rep_name}
        **Email:** {rep_email}
        **Signature:** _____________________
        **Date:** _________________________
        """

def generate_contract_pdf(lead_name: str, lead_email: str, rep_name: str, rep_email: str, company_name: str, deal_size: int, date: str = None) -> bytes:
    

    date = date or datetime.now().strftime("%B %d, %Y")
    filled_template = contract_template.format(
        date=date,
        company_name=company_name,
        lead_name=lead_name,
        lead_email=lead_email,
        rep_name=rep_name,
        rep_email=rep_email,
        deal_size=deal_size
    )

    pdf_bytes = pdfkit.from_string(filled_template, False)
    return pdf_bytes