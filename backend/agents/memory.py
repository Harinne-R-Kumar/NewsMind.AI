"""
NewsMind AI - Memory Agent
Manages user preferences, feedback, and reading history using ChromaDB.
"""

from typing import List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_ollama import OllamaEmbeddings
from backend.config import settings
from backend.graph.state import NewspaperState
from backend.utils.logging import setup_logger

logger = setup_logger("memory")


class MemoryAgent:
    """Manages persistent memory using ChromaDB."""
    
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL,
            base_url=settings.OLLAMA_URL
        )
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Collections
        self.interests_collection = self.client.get_or_create_collection("user_interests")
        self.reading_collection = self.client.get_or_create_collection("reading_history")
        self.feedback_collection = self.client.get_or_create_collection("feedback")
    
    async def store_interests(self, user_id: int, interests: List[str]):
        """Store user interests as embeddings."""
        try:
            for interest in interests:
                embedding = await self.embeddings.aembed_query(interest)
                self.interests_collection.upsert(
                    ids=[f"user_{user_id}_{interest}"],
                    embeddings=[embedding],
                    metadatas=[{"user_id": user_id, "interest": interest}],
                    documents=[interest]
                )
            logger.info(f"Stored {len(interests)} interests for user {user_id}")
        except Exception as e:
            logger.error(f"Error storing interests: {e}")
    
    async def get_similar_interests(self, user_id: int, query: str, n_results: int = 5) -> List[str]:
        """Find similar interests for recommendations."""
        try:
            query_embedding = await self.embeddings.aembed_query(query)
            results = self.interests_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"user_id": user_id}
            )
            return results.get("documents", [[]])[0]
        except Exception as e:
            logger.error(f"Error getting similar interests: {e}")
            return []
    
    async def store_reading_history(self, user_id: int, article: dict):
        """Store article reading history."""
        try:
            article_text = f"{article.get('title', '')} {article.get('summary', '')}"
            embedding = await self.embeddings.aembed_query(article_text)
            
            self.reading_collection.add(
                ids=[f"read_{user_id}_{datetime.utcnow().timestamp()}"],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": user_id,
                    "article_title": article.get("title", ""),
                    "article_url": article.get("url", ""),
                    "section": article.get("section", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }],
                documents=[article_text]
            )
        except Exception as e:
            logger.error(f"Error storing reading history: {e}")
    
    async def store_feedback(self, user_id: int, article_title: str, feedback_type: str):
        """Store user feedback for learning."""
        try:
            embedding = await self.embeddings.aembed_query(article_title)
            
            self.feedback_collection.add(
                ids=[f"feedback_{user_id}_{datetime.utcnow().timestamp()}"],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": user_id,
                    "article_title": article_title,
                    "feedback_type": feedback_type,
                    "timestamp": datetime.utcnow().isoformat()
                }],
                documents=[article_title]
            )
            logger.info(f"Stored feedback '{feedback_type}' for article from user {user_id}")
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
    
    async def get_user_preferences_embedding(self, user_id: int) -> Optional[List[float]]:
        """Get aggregated user preferences as embedding."""
        try:
            results = self.interests_collection.get(
                where={"user_id": user_id}
            )
            if results and results.get("embeddings"):
                # Average the embeddings
                import numpy as np
                embeddings = np.array(results["embeddings"])
                return embeddings.mean(axis=0).tolist()
        except Exception as e:
            logger.error(f"Error getting preferences embedding: {e}")
        return None
    
    async def update(self, state: NewspaperState) -> NewspaperState:
        """Update memory with new articles and sync interests."""
        logger.info(f"Memory agent updating for user {state['user_id']}")

        user_id = state["user_id"]
        articles = state.get("articles", [])
        preferences = state.get("user_preferences", {})

        interests = preferences.get("interests", [])
        if interests:
            await self.store_interests(user_id, interests)

        for article in articles[:10]:
            await self.store_reading_history(user_id, article)

        logger.info(f"Updated memory with {min(len(articles), 10)} articles")

        return {
            **state,
            "current_step": "delivery"
        }


# LangGraph node function
async def memory_node(state: NewspaperState) -> NewspaperState:
    """LangGraph node for memory agent."""
    agent = MemoryAgent()
    return await agent.update(state)
