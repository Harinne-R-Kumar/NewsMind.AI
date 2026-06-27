"""
NewsMind AI - Content Sanitization
Strips prompt injection attempts from retrieved web content before LLM processing.
"""

import re
from html import escape
from typing import Optional
from urllib.parse import urlparse

# Patterns commonly used in prompt injection attacks
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)",
    r"(?i)you\s+are\s+now\s+(a|an)\s+",
    r"(?i)system\s*:\s*",
    r"(?i)\[INST\]",
    r"(?i)<<SYS>>",
    r"(?i)###\s*instruction",
    r"(?i)do\s+not\s+follow\s+your",
    r"(?i)reveal\s+(your\s+)?(system\s+)?prompt",
    r"(?i)bypass\s+(safety|filter|guardrail)",
    r"(?i)jailbreak",
    r"(?i)DAN\s+mode",
    r"(?i)act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
]

COMPILED_PATTERNS = [re.compile(p) for p in INJECTION_PATTERNS]

# Hidden unicode / zero-width characters sometimes used to smuggle instructions
HIDDEN_CHARS = re.compile(r"[\u200b-\u200f\u2028-\u202f\ufeff]")


def sanitize_for_llm(text: Optional[str], max_length: int = 2000) -> str:
    """Remove injection patterns and hidden characters from text destined for an LLM."""
    if not text:
        return ""

    cleaned = HIDDEN_CHARS.sub("", text)
    for pattern in COMPILED_PATTERNS:
        cleaned = pattern.sub("[filtered]", cleaned)

    # Strip HTML tags that might carry hidden instructions
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    cleaned = " ".join(cleaned.split())
    return cleaned[:max_length]


def sanitize_html_output(text: Optional[str]) -> str:
    """Escape HTML entities for safe rendering in emails/reports."""
    if not text:
        return ""
    return escape(text)


def is_valid_url(url: Optional[str]) -> bool:
    """Validate that a URL uses an allowed scheme."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False
