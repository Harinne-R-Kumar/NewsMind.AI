"""
NewsMind AI - Supervisor Agent
Orchestrates workflow with conditional routing. Never calls external APIs.
"""

import uuid
from datetime import datetime
from backend.graph.state import NewspaperState
from backend.utils.logging import setup_logger

logger = setup_logger("supervisor")


class SupervisorAgent:
    """Orchestrates the newspaper generation workflow."""

    def create_initial_state(
        self,
        user_id: int,
        user_name: str,
        user_email: str,
        preferences: dict,
        *,
        is_verified: bool = True,
        manual_trigger: bool = False,
    ) -> NewspaperState:
        """Create initial state for the workflow."""
        return NewspaperState(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            user_preferences=preferences,
            is_verified=is_verified,
            manual_trigger=manual_trigger,
            delivery_paused=preferences.get("delivery_paused", False),
            current_step="init",
            retry_count=0,
            max_retries=1,
            error_message=None,
            articles=[],
            html_content=None,
            pdf_path=None,
            email_sent=False,
            run_id=str(uuid.uuid4()),
            started_at=datetime.utcnow().isoformat(),
            completed_at=None,
        )

    def should_retry(self, state: NewspaperState) -> bool:
        return state["retry_count"] < state["max_retries"] and state.get("error_message") is not None

    def evaluate_routing(self, state: NewspaperState) -> str:
        """
        Conditional routing decisions (no external API calls).
        Returns: 'research', 'skip', or 'error'
        """
        if state.get("error_message") and not self.should_retry(state):
            return "error"

        # Manual generation bypasses delivery-pause and schedule checks
        if state.get("manual_trigger"):
            if not state.get("is_verified") and not state.get("manual_trigger"):
                return "skip"
            return "research"

        # Scheduled delivery checks
        if state.get("delivery_paused"):
            logger.info(f"User {state['user_id']}: delivery paused, skipping")
            return "skip"

        if not state.get("is_verified"):
            logger.info(f"User {state['user_id']}: email not verified, skipping")
            return "skip"

        interests = state.get("user_preferences", {}).get("interests", [])
        if not interests:
            logger.info(f"User {state['user_id']}: no interests, using defaults")

        return "research"

    def handle_error(self, state: NewspaperState, error: str) -> NewspaperState:
        logger.error(f"Error in workflow: {error}")
        return {
            **state,
            "error_message": error,
            "retry_count": state["retry_count"] + 1,
        }

    def log_progress(self, state: NewspaperState, step: str):
        logger.info(f"Run {state['run_id']}: {step} - User {state['user_id']}")


def supervisor_entry(state: NewspaperState) -> NewspaperState:
    """Entry point — evaluate routing and set next step."""
    agent = SupervisorAgent()
    route = agent.evaluate_routing(state)
    agent.log_progress(state, f"supervisor route={route}")

    if route == "skip":
        return {
            **state,
            "current_step": "complete",
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": "Delivery skipped by supervisor checks",
        }

    if route == "error":
        return {**state, "current_step": "error"}

    return {**state, "current_step": "research"}


def supervisor_route(state: NewspaperState) -> str:
    """Conditional edge function after supervisor."""
    if state.get("current_step") == "complete":
        return "skip"
    if state.get("current_step") == "error":
        return "error"
    return "research"


def supervisor_error_handler(state: NewspaperState) -> NewspaperState:
    if state.get("error_message"):
        logger.error(f"Workflow error: {state['error_message']}")
    return {
        **state,
        "completed_at": datetime.utcnow().isoformat(),
        "current_step": "error",
    }


def route_after_node(state: NewspaperState) -> str:
    """Route after agent nodes — retry once on failure."""
    if state.get("error_message"):
        if state.get("retry_count", 0) < state.get("max_retries", 1):
            return "retry"
        return "error"
    return "continue"
