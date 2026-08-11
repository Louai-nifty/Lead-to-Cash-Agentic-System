from contextlib import asynccontextmanager
from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from routers import webhooks
from agent.graph import graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        app.state.agent = graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["approval_handler"],
            interrupt_after=["assignment", "proposal", "proposal_sender"]
        )
        yield

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