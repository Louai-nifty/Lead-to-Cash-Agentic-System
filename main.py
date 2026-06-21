from fastapi import FastAPI
from routers import webhooks, triggers


app = FastAPI(
    title="Lead-to-Cash Agentic System",
    description="End-to-end lead automation pipeline with human-in-the-loop approval",
    version="1.0.0"
)


app.include_router(webhooks.router)
app.include_router(triggers.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Lead-to-Cash API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)