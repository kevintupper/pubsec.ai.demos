"""
conversation_manager/config.py

Handles environment-driven configuration for both Cosmos DB and Azure OpenAI.
All necessary credentials and configuration details should be in .env.
"""

import os
from dotenv import load_dotenv


class ConversationConfig:
    """
    Loads and stores configuration settings for Cosmos DB and Azure OpenAI from environment variables.
    """
    def __init__(self) -> None:
        # Load .env if present
        load_dotenv()

        # Cosmos DB
        self.COSMOS_DB_ENDPOINT: str = os.getenv("COSMOS_DB_ENDPOINT", "")
        self.COSMOS_DB_KEY: str = os.getenv("COSMOS_DB_KEY", "")
        self.CHAT_HISTORY_DATABASE: str = os.getenv("CHAT_HISTORY_DATABASE", "ChatHistoryDB")
        self.CHAT_HISTORY_CONTAINER: str = os.getenv("CHAT_HISTORY_CONTAINER", "Conversations")

        # Azure OpenAI
        self.AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        self.AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-15-preview")

        # Logging
        self.LOGLEVEL: str = os.getenv("LOGLEVEL", "INFO").upper()  # Default to INFO if not set

    def validate(self) -> None:
        """
        Ensures all variables are set before usage.
        Raises ValueError if a required setting is not configured.
        """
        required_fields: list[str] = [
            "COSMOS_DB_ENDPOINT",
            "COSMOS_DB_KEY",
            "CHAT_HISTORY_DATABASE",
            "CHAT_HISTORY_CONTAINER",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "AZURE_OPENAI_API_VERSION",
        ]
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Missing required configuration: {field}")
