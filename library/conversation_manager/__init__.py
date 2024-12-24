"""
conversation_manager/__init__.py

This is the package initializer for the conversation_manager library.
It makes core classes and functions available at the package level.
"""

from .config import ConversationConfig
from .cosmos_db_service import CosmosDBConversationClient
from .azure_openai_service import AzureOpenAIService
from .conversation_service import ConversationManager

__all__ = [
    "ConversationConfig",
    "CosmosDBConversationClient",
    "AzureOpenAIService",
    "ConversationManager",
]