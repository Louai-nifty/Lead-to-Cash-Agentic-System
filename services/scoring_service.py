import asyncio
from typing import Any

async def scoring_func(size: Any, industry: str, revenue: Any, source: str):
    try:
        primary_industry = ["Human Resources", "Real Estate"]
        secondary_industry = ["IT Services","Business Consulting"]
        industry_score = 0
        if any(industry.lower() in item.lower() for item in primary_industry):
            industry_score = 30
        elif any(industry.lower() in item.lower() for item in secondary_industry):
            industry_score = 15
        else:
            industry_score = 0
        
        source_score = 0
        if source == "email":
            source_score = 10
        elif source == "tally_form":
            source_score = 15
        
        
        
        
        
        
        return {"lead_score": , "lead_priority":}    
            
    except Exception as e:
        print(f"An error occured in the scoring func {str(e)}")
    
    