"""
NewsMind AI - LangGraph State
Defines the state that flows through the agent workflow.
"""

from typing import TypedDict, Optional, List, Annotated
from operator import add


class Article(TypedDict):
    """Single article in the newspaper."""
    title: str
    url: str
    source: str
    summary: str
    section: str
    published_at: str


class NewspaperState(TypedDict):
    """State passed through the LangGraph workflow."""
    # User context
    user_id: int
    user_name: str
    user_email: str
    user_preferences: dict
    is_verified: bool
    manual_trigger: bool
    delivery_paused: bool

    # Workflow control
    current_step: str
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    
    # Accumulated data
    articles: Annotated[List[Article], add]
    
    # Final output
    html_content: Optional[str]
    pdf_path: Optional[str]
    email_sent: bool
    
    # Metadata
    run_id: str
    started_at: str
    completed_at: Optional[str]
