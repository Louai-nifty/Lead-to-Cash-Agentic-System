from database.db import get_client
from utils.loggings import get_logger


logger = get_logger(__name__)
sup_client = get_client()

def routing_func(score, email):
    try:
        if score < 50:
            sup_client.table("Leads").update({"status": "rejected"}).eq("email", email).execute()
            return {"to_what_level": "Not_Qualified", "assigned_to": None, "assigned_rep_id": None, "assigned_rep_name": None}
        elif score >= 50 and score < 80:
            Rep = sup_client.table("Users").select("id").eq("role", "Junior_Rep").eq("leads_assigned_atm", 0).execute().data[0]
            Rep_id = Rep["id"]
            Rep_email = Rep["email"]
            assigned_to = Rep["lead_assigned_atm"]
                
            sup_client.table("Users").update({"leads_assigned_atm": assigned_to + 1}).eq("id", Rep_id).execute()
            sup_client.table("Leads").update({"status": "assigned", "assigned_rep_id": Rep_id}).eq("email", email).execute()
            
            
            
            return {"to_what_level": "Junior_Rep", "assigned_to": Rep_email, "assigned_rep_id": Rep_id, "assigned_rep_name": Rep_name}
        else:
            Rep = sup_client.table("Users").select("id").eq("role", "Senior_Rep").eq("leads_assigned_atm", 0).execute().data[0]
            Rep_id = Rep["id"]
            Rep_email = Rep["email"]
            Rep_name = Rep["name"]
            assigned_to = Rep["lead_assigned_atm"]

            sup_client.table("Users").update({"leads_assigned_atm": assigned_to + 1}).eq("id", Rep_id).execute()
            sup_client.table("Leads").update({"status": "assigned", "assigned_rep_id": Rep_id}).eq("email", email).execute()

            return {"to_what_level": "Senior_Rep", "assigned_to": Rep_email, "assigned_rep_id": Rep_id, "assigned_rep_name": Rep_name}
    except Exception as e:
        logger.error(f"An error occured in the routing service function {str(e)}", exc_info=True)
        return {"to_what_level": "Not_Qualified", "assigned_to": None, "assigned_rep_id": None, "assigned_rep_name": None}