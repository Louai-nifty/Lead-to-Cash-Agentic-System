from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState

cash_agent = StateGraph(AgentState)

# The orchestration of the agent

checkpointer = MemorySaver()
app = cash_agent.compile()