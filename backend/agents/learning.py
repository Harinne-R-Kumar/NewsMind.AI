"""
NewsMind AI
Learning Agent

Analyzes user feedback and converts it into structured learning signals.
"""

import json
from typing import Dict, Any

from backend.utils.logging import setup_logger
from backend.config import settings

import ollama

logger = setup_logger("learning")


class LearningAgent:

    def __init__(self):
        self.model = settings.DEFAULT_LLM_MODEL

    async def analyze_feedback(
        self,
        rating: int,
        comment: str
    ) -> Dict[str, Any]:

        prompt = f"""
You are the Learning Agent for NewsMind AI.

A user has rated today's newspaper.

Rating:
{rating}/5

Comment:
{comment}

Your job is to determine what the user likes and dislikes.

Return ONLY valid JSON.

Schema:

{{
    "problem_type":"",
    "liked_topics":[],
    "disliked_topics":[],
    "preferred_sources":[],
    "avoid_sources":[],
    "reading_level":"",
    "summary_style":"",
    "search_changes":"",
    "editorial_changes":""
}}

Do not explain anything.

Return JSON only.
"""

        try:

            response = ollama.chat(

                model=self.model,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

            )

            content = response["message"]["content"]

            return json.loads(content)

        except Exception as e:

            logger.error(f"Learning Agent failed: {e}")

            return {

                "problem_type": "",

                "liked_topics": [],

                "disliked_topics": [],

                "preferred_sources": [],

                "avoid_sources": [],

                "reading_level": "",

                "summary_style": "",

                "search_changes": "",

                "editorial_changes": ""

            }