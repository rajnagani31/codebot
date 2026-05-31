"""
Central model registry for Alembic discovery
"""

# Import Base from centralized database module
from ..core.database import Base

# Import all models to register them with SQLAlchemy
from .chat_history import ChatUser, ChatThread, ChatMessage, AuthIdentity, UserSession
from .web_search import WebSearchRun, WebSource
from .pg_vectore import DocumentData, VectorData

# Export Base for Alembic
__all__ = ['Base']