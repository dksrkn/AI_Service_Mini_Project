from langgraph.graph import StateGraph, END
from app.graph.state import AgenticWorkflowState
from app.agents.supervisor import supervisor_node
from app.agents.rag_agent import rag_agent
from app.agents.web_search_agent import web_search_agent
from app.agents.draft_agent import draft_agent
from app.agents.policy_checker import policy_checker
from app.agents.formatter import formatter
from app.graph.routing import route_after_supervisor, route_after_policy_check


def build_workflow():
    graph = StateGraph(AgenticWorkflowState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag_agent", rag_agent)
    graph.add_node("web_search_agent", web_search_agent)
    graph.add_node("draft_agent", draft_agent)
    graph.add_node("policy_checker", policy_checker)
    graph.add_node("formatter", formatter)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "rag_agent": "rag_agent",
            "web_search_agent": "web_search_agent",
            "draft_agent": "draft_agent",
            "formatter": "formatter",
        }
    )

    graph.add_edge("rag_agent", "supervisor")
    graph.add_edge("web_search_agent", "supervisor")
    graph.add_edge("draft_agent", "policy_checker")

    graph.add_conditional_edges(
        "policy_checker",
        route_after_policy_check,
        {
            "supervisor": "supervisor",
            "formatter": "formatter",
        }
    )

    graph.add_edge("formatter", END)

    return graph.compile()