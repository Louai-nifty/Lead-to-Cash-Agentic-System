from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from nodes.enrichment_node import enrichment_node
from checkpointer import get_checkpointer

cash_agent = StateGraph(AgentState)

# The orchestration of the agent
cash_agent.add_node("enrichment", enrichment_node)

cash_agent.set_entry_point("enrichment")

cash_agent.add_edge("enrichment", END)

checkpointer = MemorySaver()
app = cash_agent.compile(checkpointer=get_checkpointer(use_persistence=True))