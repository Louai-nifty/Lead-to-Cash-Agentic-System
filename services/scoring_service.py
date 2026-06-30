import asyncio
from typing import Any

async def scoring_func(size: Any, industry: str, source: str):
    try:
        primary_industry = ["Human Resources", "Real Estate"]
        secondary_industry = ["IT Services","Business Consulting"]
        industry_score = 0
        if any(industry.lower() in item.lower() for item in primary_industry):
            industry_score = 30
        elif any(industry.lower() in item.lower() for item in secondary_industry):
            industry_score = 15
        
        source_score = 0
        if source == "email":
            source_score = 10
        elif source == "tally_form":
            source_score = 15
        
        
        size_score = 0
        headcount = size.lower().strip()
        
        if headcount == "None":
            headcount = 0
        
        if "k" in headcount:
            headcount = headcount.split("-")[0].strip()
            if "k" in headcount:
                headcount = headcount.replace("k", "").strip()
                headcount = int(headcount) * 1000
        else:
            headcount = int(headcount.split("-")[1])
            
        if 1 <= headcount <= 10:
            size_score = 10
        elif 10 < headcount <= 50:
            size_score = 20
        elif 50 < headcount <= 200:
            size_score = 30
        elif 200 < headcount <= 1000:
            size_score = 40
        elif headcount > 1000:
            size_score = 50  
        
        
        final_score = (size_score * 0.4) + (industry_score * 0.35) + (source_score * 0.25)
        
        if final_score <= 50:
            priority = "low"
        elif 50 < final_score <= 74:
            priority = "mid"
        elif final_score > 74:
            priority = "high"
        
        return {"lead_score": final_score, "lead_priority": priority}    
            
    except Exception as e:
        print(f"An error occured in the scoring func {str(e)}")
    
    