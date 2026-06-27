"""
NewsMind AI - LangGraph Workflow
Defines the newspaper generation workflow with conditional routing.
"""

from langgraph.graph import StateGraph, END
from backend.graph.state import NewspaperState
from backend.agents.supervisor import (
    supervisor_entry,
    supervisor_route,
    supervisor_error_handler,
)
from backend.agents.research import research_node
from backend.agents.editorial import editorial_node
from backend.agents.memory import memory_node
from backend.agents.delivery import delivery_node
from backend.utils.logging import setup_logger

logger = setup_logger("workflow")


def should_continue_delivery(state: NewspaperState) -> str:
    """Determine if delivery succeeded or should error out."""
    if state.get("error_message") and state.get("retry_count", 0) >= state.get("max_retries", 1):
        return "error"
    return "end"


def create_newspaper_workflow():
    workflow = StateGraph(NewspaperState)

    workflow.add_node("supervisor", supervisor_entry)
    workflow.add_node("research", research_node)
    workflow.add_node("editorial", editorial_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("delivery", delivery_node)
    workflow.add_node("error_handler", supervisor_error_handler)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        supervisor_route,
        {
            "research": "research",
            "skip": END,
            "error": "error_handler",
        },
    )

    workflow.add_edge("research", "editorial")
    workflow.add_edge("editorial", "memory")
    workflow.add_edge("memory", "delivery")

    workflow.add_conditional_edges(
        "delivery",
        should_continue_delivery,
        {
            "end": END,
            "error": "error_handler",
        },
    )

    workflow.add_edge("error_handler", END)

    return workflow.compile()


newspaper_workflow = create_newspaper_workflow()


async def run_newspaper_workflow(
    user_id: int,
    user_name: str,
    user_email: str,
    preferences: dict,
    *,
    is_verified: bool = True,
    manual_trigger: bool = False,
) -> NewspaperState:
    """Execute the complete newspaper workflow for a user."""
    from backend.agents.supervisor import SupervisorAgent

    logger.info(f"Starting newspaper workflow for user {user_id}")

    supervisor = SupervisorAgent()
    initial_state = supervisor.create_initial_state(
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        preferences=preferences,
        is_verified=is_verified,
        manual_trigger=manual_trigger,
    )

    try:
        final_state = await newspaper_workflow.ainvoke(initial_state)
        logger.info(f"Workflow completed for user {user_id}")
        return final_state
    except Exception as e:
        logger.error(f"Workflow failed for user {user_id}: {e}")
        return {
            **initial_state,
            "error_message": str(e),
            "current_step": "error",
        }
