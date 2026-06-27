"""
NewsMind AI - MCP Tools
Dynamic information retrieval tools backed by the configurable source registry.
"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import aiohttp
import feedparser

from backend.config import settings
from backend.mcp.source_registry import (
    build_source_url,
    get_defaults,
    get_fallbacks,
    get_sources_by_category,
)
from backend.utils.logging import setup_logger
from backend.utils.sanitize import sanitize_for_llm, is_valid_url
from lingua import Language, LanguageDetectorBuilder

detector = (
    LanguageDetectorBuilder
    .from_all_languages()
    .build()
)

logger = setup_logger("mcp_tools")


def _parse_published(entry: dict) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return None


def _is_fresh(entry: dict, max_age_hours: int) -> bool:
    pub = _parse_published(entry)
    if pub is None:
        return True
    age = datetime.utcnow() - pub
    return age.total_seconds() < max_age_hours * 3600


def _clean_summary(raw: str) -> str:
    return sanitize_for_llm(raw.replace("\n", " ").strip(), max_length=400)

LANGUAGE_MAP = {
    "English": Language.ENGLISH,
    "French": Language.FRENCH,
    "German": Language.GERMAN,
    "Spanish": Language.SPANISH,
    "Hindi": Language.HINDI,
    "Japanese": Language.JAPANESE,
    "Korean": Language.KOREAN,
}

def is_language(text: str, language: str) -> bool:
    try:
        detected = detector.detect_language_of(text)
        expected = LANGUAGE_MAP.get(language)

        if expected is None:
            return True

        return detected == expected

    except Exception:
        return False

async def _fetch_rss_url(
    url: str,
    source_name: str,
    section: str,
    query: str = "",
    limit: int = 10,
    max_age_hours: int = 72,
    language="English",
    credibility: float = 0.8,
) -> List[Dict[str, Any]]:
    """Fetch and parse a single RSS feed URL."""
    articles = []
    try:
        feed = feedparser.parse(url)
        feed_title = feed.feed.get("title", source_name)

        for entry in feed.entries:
            if not _is_fresh(entry, max_age_hours):
                continue

            title = entry.get("title", "").strip()
            if not title or len(title) < 8:
                continue

            if query and query.lower() not in title.lower():
                summary_raw = entry.get("summary", "")
                if query.lower() not in summary_raw.lower():
                    continue
            
            published = (
                entry.get("published")
                or entry.get("updated")
                or entry.get("pubDate")
            )

            pub = _parse_published(entry)
            articles.append({
                "title": sanitize_for_llm(title, max_length=300),
                "url": entry.get("link", ""),
                "source": feed_title or source_name,
                "summary": _clean_summary(entry.get("summary", "")),
                "section": section,
                "published_at": published,
                "credibility": credibility,
            })
            if not is_language(title + " " + summary, language):
                continue

            if len(articles) >= limit:
                break
    except Exception as e:
        logger.error(f"RSS fetch error for {url}: {e}")

    return articles


async def _fetch_from_sources(
    category: str,
    query: str,
    section: str,
    preferred_sources: Optional[List[str]] = None,
    language="English",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Fetch articles from all enabled sources in a category."""
    defaults = get_defaults()
    max_age = defaults.get("max_article_age_hours", 72)
    per_source = defaults.get("articles_per_source", 10)

    sources = get_sources_by_category(category, preferred=preferred_sources)
    if not sources:
        sources = get_sources_by_category(category)

    tasks = []
    for source in sources:
        if source.get("type") == "api":
            continue
        url = build_source_url(source, query)
        if not url:
            continue
        tasks.append(_fetch_rss_url(
            url=url,
            source_name=source.get("name", "Unknown"),
            section=section,
            query="" if source.get("type") == "rss_search" else query,
            limit=per_source,
            max_age_hours=max_age,
            language=language,
            credibility=source.get("credibility", 0.8),
        ))

    if not tasks:
        return []

    results = await asyncio.gather(*tasks, return_exceptions=True)
    articles = []
    for result in results:
        if isinstance(result, list):
            articles.extend(result)

    # Deduplicate by URL and similar titles
    seen_urls = set()
    seen_titles = set()
    unique = []
    for a in articles:
        url_key = a.get("url", "")
        title_key = a.get("title", "").lower()[:60]
        if url_key and url_key in seen_urls:
            continue
        if title_key in seen_titles:
            continue
        if url_key:
            seen_urls.add(url_key)
        seen_titles.add(title_key)
        unique.append(a)

    unique.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    return unique[:limit]


async def search_news(
    topic: str,
    sources: Optional[List[str]] = None,
    language="English",
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """
    Search news for any topic using dynamically configured RSS sources.

    Args:
        topic: User interest or search topic (any string)
        sources: Optional preferred source names to filter
        limit: Maximum results
    """
    return await _fetch_from_sources(
        category="news",
        query=topic,
        section=topic.title(),
        preferred_sources=sources,
        language=language,
        limit=limit,
    )


async def github_trending(
    topic: str = "",
    language: Optional[str] = None,
    since: str = "daily",
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Get GitHub trending repositories related to a topic.

    Args:
        topic: Search topic (used in GitHub query)
        language: Optional programming language filter
        since: Time period hint (daily=7d, weekly=14d, monthly=30d)
        limit: Maximum results
    """
    days_map = {"daily": 7, "weekly": 14, "monthly": 30}
    days = days_map.get(since, 7)
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    query_parts = [f"created:>{cutoff}", "stars:>50"]
    if topic:
        query_parts.append(topic)
    if language:
        query_parts.append(f"language:{language}")
    query = " ".join(query_parts)

    repos = []
    try:
        async with aiohttp.ClientSession() as session:
            url = (
                f"https://api.github.com/search/repositories"
                f"?q={quote_plus(query)}&sort=stars&order=desc&per_page={limit}"
            )
            headers = {"Accept": "application/vnd.github.v3+json"}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    for repo in data.get("items", []):
                        repos.append({
                            "title": f"GitHub: {repo['full_name']} ⭐ {repo['stargazers_count']:,}",
                            "url": repo["html_url"],
                            "source": "GitHub",
                            "summary": sanitize_for_llm(
                                repo.get("description") or "No description", max_length=200
                            ),
                            "section": "GitHub Trending",
                            "published_at": repo.get("created_at", datetime.utcnow().isoformat()),
                            "credibility": 0.9,
                            "name": repo["full_name"],
                            "stars": repo["stargazers_count"],
                            "language": repo.get("language", "Unknown"),
                        })
    except Exception as e:
        logger.error(f"GitHub trending error: {e}")

    return repos


async def weather(city: str = "London", units: str = "metric") -> Dict[str, Any]:
    """Get current weather for a city."""
    if not settings.OPENWEATHER_API_KEY:
        return {
            "error": "OpenWeather API key not configured",
            "city": city,
            "temperature": "N/A",
            "conditions": "Configure OPENWEATHER_API_KEY",
        }

    try:
        async with aiohttp.ClientSession() as session:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={quote_plus(city)}&appid={settings.OPENWEATHER_API_KEY}&units={units}"
            )
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "city": data["name"],
                        "country": data["sys"]["country"],
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "conditions": data["weather"][0]["description"],
                        "humidity": data["main"]["humidity"],
                        "wind_speed": data["wind"]["speed"],
                        "icon": data["weather"][0]["icon"],
                    }
                return {"error": f"Weather API error: {response.status}"}
    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        return {"error": str(e)}


async def research_papers(topic: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get latest research papers from arXiv for any topic."""
    papers = []
    try:
        async with aiohttp.ClientSession() as session:
            url = (
                f"http://export.arxiv.org/api/query"
                f"?search_query=all:{quote_plus(topic)}&start=0&max_results={limit}"
                f"&sortBy=submittedDate&sortOrder=descending"
            )
            async with session.get(url) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    root = ET.fromstring(xml_content)
                    ns = {"arxiv": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall("arxiv:entry", ns):
                        title_el = entry.find("arxiv:title", ns)
                        summary_el = entry.find("arxiv:summary", ns)
                        published_el = entry.find("arxiv:published", ns)
                        link_el = entry.find("arxiv:id", ns)
                        authors = [
                            a.find("arxiv:name", ns).text
                            for a in entry.findall("arxiv:author", ns)
                        ][:3]
                        title = title_el.text.strip() if title_el is not None else "Untitled"
                        published = (
                            published_el.text
                            if published_el is not None
                            else ""
                        )
                        papers.append({
                            "title": sanitize_for_llm(title, max_length=300),
                            "url": link_el.text if link_el is not None else "",
                            "source": "arXiv",
                            "summary": sanitize_for_llm(
                                summary_el.text.strip()[:300] if summary_el is not None else "",
                                max_length=300,
                            ),
                            "section": "Research Papers",
                            "published_at": published,
                            "credibility": 0.95,
                            "authors": authors,
                        })
    except Exception as e:
        logger.error(f"Research papers fetch error: {e}")

    return papers


async def search_hackathons(topic: str = "",language="English", limit: int = 5) -> List[Dict[str, Any]]:
    """Search upcoming hackathons related to a topic."""
    query = topic or "technology"
    results = await _fetch_from_sources(
        category="hackathons",
        query=query,
        language=language,
        section="Hackathons",
        limit=limit,
    )
    if not results:
        for fb in get_fallbacks("hackathons")[:limit]:
            results.append({
                "title": fb["title"],
                "url": fb["url"],
                "source": fb["source"],
                "summary": fb.get("summary", "Browse upcoming hackathons"),
                "section": "Hackathons",
                "published_at": "",
                "credibility": 0.7,
            })
    return results[:limit]


async def search_competitions(topic: str = "",language="English", limit: int = 5) -> List[Dict[str, Any]]:
    """Search coding competitions related to a topic."""
    query = topic or "programming"
    results = await _fetch_from_sources(
        category="competitions",
        query=query,
        language=language,
        section="Coding Competitions",
        limit=limit,
    )
    if not results:
        for fb in get_fallbacks("competitions")[:limit]:
            results.append({
                "title": fb["title"],
                "url": fb["url"],
                "source": fb["source"],
                "summary": fb.get("summary", "Browse coding competitions"),
                "section": "Coding Competitions",
                "published_at": "",
                "credibility": 0.7,
            })
    return results[:limit]


async def search_conferences(topic: str = "",language="English", limit: int = 5) -> List[Dict[str, Any]]:
    """Search conferences, workshops, and webinars related to a topic."""
    query = topic or "technology"
    results = await _fetch_from_sources(
        category="conferences",
        query=query,
        section="Conferences & Events",
        language=language,
        limit=limit,
    )
    if not results:
        for fb in get_fallbacks("conferences")[:limit]:
            results.append({
                "title": fb["title"],
                "url": fb["url"],
                "source": fb["source"],
                "summary": fb.get("summary", "Browse upcoming conferences"),
                "section": "Conferences & Events",
                "published_at": "",
                "credibility": 0.7,
            })
    return results[:limit]


async def learning_resources(topic: str,language="English", limit: int = 5) -> List[Dict[str, Any]]:
    """Get learning resources and tutorials for any topic."""
    results = await _fetch_from_sources(
        category="learning",
        query=topic,
        language=language,
        section="Learning Resources",
        limit=limit,
    )
    return results[:limit]


async def generate_pdf(content: Dict[str, Any], output_path: str) -> Dict[str, Any]:
    """Generate PDF from structured content."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.colors import HexColor

    try:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title", parent=styles["Heading1"], fontSize=28,
            textColor=HexColor("#0ea0ea"), alignment=1,
        )
        section_style = ParagraphStyle(
            "Section", parent=styles["Heading2"], fontSize=16,
            textColor=HexColor("#0ea0ea"),
        )
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10)

        story = [
            Paragraph(content.get("title", "NewsMind AI"), title_style),
            Paragraph(content.get("date", ""), styles["Normal"]),
            Spacer(1, 20),
        ]
        for section in content.get("sections", []):
            story.append(Paragraph(section["title"], section_style))
            for item in section.get("items", []):
                story.append(Paragraph(item.replace("&", "&amp;").replace("<", "&lt;"), body_style))
            story.append(Spacer(1, 10))

        doc.build(story)
        return {"success": True, "path": output_path}
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return {"success": False, "error": str(e)}


async def send_email(
    to: str,
    subject: str,
    body: str,
    is_html: bool = True,
    attachment_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Send email via SMTP."""
    import os
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if is_html else "plain"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", "attachment",
                    filename=os.path.basename(attachment_path),
                )
                msg.attach(part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to, msg.as_string())

        return {"success": True, "message": f"Email sent to {to}"}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


# Aliases for backward compatibility
hackathons = search_hackathons
competitions = search_competitions
conferences = search_conferences


MCP_TOOLS = {
    "search_news": {
        "function": search_news,
        "description": "Search news articles dynamically for any topic",
        "parameters": {
            "topic": {"type": "string", "description": "Search topic"},
            "sources": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer", "default": 15},
        },
    },
    "github_trending": {
        "function": github_trending,
        "description": "Get trending GitHub repositories for a topic",
        "parameters": {
            "topic": {"type": "string"},
            "language": {"type": "string"},
            "since": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
            "limit": {"type": "integer", "default": 5},
        },
    },
    "weather": {
        "function": weather,
        "description": "Get current weather for a city",
        "parameters": {
            "city": {"type": "string", "default": "London"},
            "units": {"type": "string", "enum": ["metric", "imperial"]},
        },
    },
    "research_papers": {
        "function": research_papers,
        "description": "Get latest research papers from arXiv",
        "parameters": {
            "topic": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
        },
    },
    "search_hackathons": {
        "function": search_hackathons,
        "description": "Search upcoming hackathons",
        "parameters": {"topic": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
    },
    "search_competitions": {
        "function": search_competitions,
        "description": "Search coding competitions",
        "parameters": {"topic": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
    },
    "search_conferences": {
        "function": search_conferences,
        "description": "Search conferences and webinars",
        "parameters": {"topic": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
    },
    "learning_resources": {
        "function": learning_resources,
        "description": "Get learning resources for a topic",
        "parameters": {"topic": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
    },
    "generate_pdf": {
        "function": generate_pdf,
        "description": "Generate PDF document",
        "parameters": {
            "content": {"type": "object"},
            "output_path": {"type": "string"},
        },
    },
    "send_email": {
        "function": send_email,
        "description": "Send email via SMTP",
        "parameters": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
            "is_html": {"type": "boolean", "default": True},
            "attachment_path": {"type": "string"},
        },
    },
}
