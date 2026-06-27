"""
NewsMind AI - Research Agent
Decides WHAT information is required and delegates retrieval to MCP tools.
Never contains hardcoded URLs or topic-specific source logic.
"""

import asyncio
import random
from datetime import datetime
from typing import List

from backend.graph.state import NewspaperState, Article
from backend.mcp.tools import (
    search_news,
    github_trending,
    research_papers,
    search_conferences,
    search_hackathons,
    search_competitions,
    learning_resources,
    weather,
)
from backend.utils.logging import setup_logger
from backend.utils.sanitize import is_valid_url

logger = setup_logger("research")

CAREER_TIPS = [
    "Build in public — share your learning journey to attract opportunities.",
    "Focus on one deep skill rather than chasing every new framework.",
    "Contribute to open source to demonstrate real-world collaboration.",
    "Practice explaining complex topics simply — communication is a superpower.",
    "Network authentically; offer value before asking for favors.",
]

CODING_QUESTIONS = [
    "Two Sum — Given an array of integers, return indices of two numbers that add up to a target.",
    "Valid Parentheses — Determine if a string of brackets is properly balanced.",
    "Merge Two Sorted Lists — Merge two sorted linked lists into one sorted list.",
    "Binary Search — Find the index of a target value in a sorted array in O(log n).",
    "Longest Substring Without Repeating Characters — Find the length of the longest unique substring.",
]

QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
    ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
]


def _to_article(item: dict, default_section: str = "General") -> Article:
    """Convert MCP tool result dict to Article TypedDict."""
    published = (
        item.get("published_at")
        or item.get("published")
        or item.get("pubDate")
        or item.get("updated")
        or item.get("created")
    )

    return Article(
        title=item.get("title", "Untitled"),
        url=item.get("url", "") if is_valid_url(item.get("url")) else "",
        source=item.get("source", "Unknown"),
        summary=item.get("summary", ""),
        section=item.get("section", default_section),
        published_at=published or "",
    )


class ResearchAgent:
    """Collects intelligence by orchestrating MCP tool calls — no direct URL access."""

    async def _collect_for_interest(
        self,
        interest: str,
        preferred_sources: List[str],
        preferred_language: str,
    ) -> List[Article]:
        """Gather all information types for a single user interest."""
        tasks = [
            search_news(
                interest,
                sources=preferred_sources or None,
                language=preferred_language,
                limit=8,
            ),
            github_trending(topic=interest, limit=3),
            research_papers(interest, limit=3),
            search_conferences(interest, language=preferred_language,limit=3),
            search_hackathons(interest, language=preferred_language,limit=3),
            search_competitions(interest,language=preferred_language, limit=3),
            learning_resources(
                interest,
                language=preferred_language,
                limit=3,
            )
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for result in results:
            if isinstance(result, list):
                for item in result:
                    articles.append(_to_article(item))
            elif isinstance(result, Exception):
                logger.warning(f"MCP tool error for interest '{interest}': {result}")

        return articles

    async def _collect_daily_extras(
        self,
        city: str = "London",
    ) -> List[Article]:
        """Collect non-topic-specific daily content."""
        articles = []

        weather_data = await weather(city)
        if "error" not in weather_data:
            articles.append(Article(
                title=f"🌤 Weather in {weather_data.get('city', city)}: "
                      f"{weather_data.get('temperature')}°C, "
                      f"{weather_data.get('conditions', '').title()}",
                url="",
                source="OpenWeather",
                summary=(
                    f"Feels like {weather_data.get('feels_like')}°C | "
                    f"Humidity: {weather_data.get('humidity')}% | "
                    f"Wind: {weather_data.get('wind_speed')} m/s"
                ),
                section="Weather",
                published_at=datetime.utcnow().isoformat(),
            ))
        else:
            articles.append(Article(
                title="Weather Update",
                url="",
                source="System",
                summary="Weather data unavailable — configure OPENWEATHER_API_KEY",
                section="Weather",
                published_at=datetime.utcnow().isoformat(),
            ))

        quote, author = random.choice(QUOTES)
        articles.append(Article(
            title="💡 Quote of the Day",
            url="",
            source="Inspirational",
            summary=f'"{quote}" — {author}',
            section="Daily Inspiration",
            published_at=datetime.utcnow().isoformat(),
        ))

        articles.append(Article(
            title="💼 Career Tip",
            url="",
            source="NewsMind AI",
            summary=random.choice(CAREER_TIPS),
            section="Career",
            published_at=datetime.utcnow().isoformat(),
        ))

        articles.append(Article(
            title="🧩 Coding Interview Question",
            url="",
            source="NewsMind AI",
            summary=random.choice(CODING_QUESTIONS),
            section="Interview Prep",
            published_at=datetime.utcnow().isoformat(),
        ))

        return articles

    def _deduplicate(self, articles: List[Article]) -> List[Article]:
        """Remove duplicate URLs and near-identical headlines."""
        seen_urls = set()
        seen_titles = set()
        unique = []

        for article in articles:
            url = article.get("url", "")
            title_key = article.get("title", "").lower()[:60]

            if url and url in seen_urls:
                continue
            if title_key in seen_titles:
                continue

            if url:
                seen_urls.add(url)
            seen_titles.add(title_key)
            unique.append(article)

        return unique

    async def collect(self, state: NewspaperState) -> NewspaperState:
        """Main collection — delegates all retrieval to MCP tools."""
        logger.info(f"Research agent collecting for user {state['user_id']}")

        preferences = state.get("user_preferences", {})
        preferred_language = preferences.get("language", "English")
        interests = preferences.get("interests") or ["technology"]
        preferred_sources = preferences.get("preferred_sources", [])
        excluded = [t.lower() for t in preferences.get("excluded_topics", [])]
        city = preferences.get("city", "London")

        logger.info(f"Interests: {interests}, Sources: {preferred_sources}")

        # Collect per interest concurrently
        interest_tasks = [
            self._collect_for_interest(interest, preferred_sources,preferred_language)
            for interest in interests[:5]
        ]
        interest_results = await asyncio.gather(*interest_tasks, return_exceptions=True)

        all_articles: List[Article] = []
        for result in interest_results:
            if isinstance(result, list):
                all_articles.extend(result)

        # Daily extras (weather, quote, career tip, interview question)
        extras = await self._collect_daily_extras(city)
        all_articles.extend(extras)

        # Filter excluded topics
        if excluded:
            all_articles = [
                a for a in all_articles
                if not any(exc in a.get("title", "").lower() or exc in a.get("summary", "").lower()
                           for exc in excluded)
            ]

        unique = self._deduplicate(all_articles)
        logger.info(f"Collected {len(unique)} unique items via MCP tools")

        return {
            **state,
            "articles": unique,
            "current_step": "editorial",
        }


async def research_node(state: NewspaperState) -> NewspaperState:
    """LangGraph node for research agent."""
    agent = ResearchAgent()
    return await agent.collect(state)
