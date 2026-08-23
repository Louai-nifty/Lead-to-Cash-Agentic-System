from contextlib import asynccontextmanager
from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from routers import webhooks
from agent.graph import graph
import asyncio
from utils.loggings import get_logger
from utils.paypal_auth import get_paypal_access_token
import config
import os

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
        
    try:
        config.Paypal_Access_Token = await get_paypal_access_token()
        logger.info("Initial PayPal access token fetched successfully.")
    except Exception as e:
        logger.error(f"Failed to fetch initial PayPal token: {e}")
        raise

    
    async def renew_token_loop():
        while True:
            await asyncio.sleep(8 * 60 * 60)
            try:
                config.Paypal_Access_Token = await get_paypal_access_token()
                logger.info("PayPal access token renewed successfully.")
            except Exception as e:
                logger.error(f"Failed to renew PayPal token: {e}")

    renewal_task = asyncio.create_task(renew_token_loop())
    os.makedirs("checkpoints_data", exist_ok=True)
    
    async with AsyncSqliteSaver.from_conn_string("checkpoints_data/checkpoints.db") as checkpointer:
        app.state.agent = graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["approval_handler"],
            interrupt_after=["assignment", "proposal", "proposal_sender", "contract"]
        )
        yield

    renewal_task.cancel()
    try:
        await renewal_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Lead-to-Cash Agentic System",
    description="End-to-end lead automation pipeline with human-in-the-loop approval",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(webhooks.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Lead-to-Cash API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)