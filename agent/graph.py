from langgraph import graph
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.enrichment_node import enrichment_node
from .nodes.scoring_node import scoring_node
from .nodes.assignment_node import assignment_node
from .nodes.approval_handler_node import approval_handler_node
from .nodes.proposal_node import proposal_node, proposal_send_node
from .nodes.contract_node import contract_generation_node
from .nodes.invoice_payment_node import payment_node

graph = StateGraph(AgentState)


graph.add_node("enrichment", enrichment_node)
graph.add_node("scoring", scoring_node)
graph.add_node("assignment", assignment_node)
graph.add_node("approval_handler", approval_handler_node)
graph.add_node("proposal", proposal_node)
graph.add_node("proposal_sender", proposal_send_node)
graph.add_node("contract", contract_generation_node)
graph.add_node("invoice", payment_node)


graph.set_entry_point("enrichment")

graph.add_edge("enrichment", "scoring")
graph.add_edge("scoring", "assignment")
graph.add_edge("assignment", "approval_handler")

graph.add_conditional_edges(
    "approval_handler",
    lambda state: "proposal" if state.approval_decision == "approved" else END
)

graph.add_edge("proposal", "proposal_sender")
graph.add_edge("proposal_sender", "contract")
graph.add_edge("contract", "invoice")
graph.add_edge("invoice", END)