from langgraph import graph
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes.enrichment_node import enrichment_node
from .nodes.scoring_node import scoring_node
from .checkpointer import get_checkpointer
from .nodes.assignment_node import assignment_node
from .nodes.approval_handler_node import approval_handler_node
from .nodes.proposal_node import proposal_node, proposal_send_node

graph = StateGraph(AgentState)

# The orchestration of the agent
graph.add_node("enrichment", enrichment_node)
graph.add_node("scoring", scoring_node)
graph.add_node("assignment", assignment_node)
graph.add_node("approval_handler", approval_handler_node)
graph.add_node("proposal", proposal_node)
graph.add_node("proposal_sender", proposal_send_node)


graph.set_entry_point("enrichment")

graph.add_edge("enrichment", "scoring")
graph.add_edge("scoring", "assignment")
graph.add_edge("assignment", "approval_handler")
graph.add_edge("approval_handler", "proposal")
graph.add_edge("proposal", "proposal_sender")
graph.add_edge("proposal_sender", END)

graph.add_conditional_edges(
    "assignment",
    lambda state: "END" if state.status == "rejected" else "proposal_node",
    {"END": END, "proposal": proposal_node}
)

checkpointer = MemorySaver()
cash_agent = graph.compile(checkpointer=get_checkpointer(use_persistence=True), interrupt_before="approval_handler", interrupt_after=["assignment", "approval_handler", "proposal"])