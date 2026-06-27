"""
NewsMind AI - MCP Module
"""

from backend.mcp.tools import (
    search_news,
    github_trending,
    weather,
    research_papers,
    search_hackathons,
    search_competitions,
    search_conferences,
    learning_resources,
    generate_pdf,
    send_email,
    MCP_TOOLS,
)

__all__ = [
    "search_news",
    "github_trending",
    "weather",
    "research_papers",
    "search_hackathons",
    "search_competitions",
    "search_conferences",
    "learning_resources",
    "generate_pdf",
    "send_email",
    "MCP_TOOLS",
]
