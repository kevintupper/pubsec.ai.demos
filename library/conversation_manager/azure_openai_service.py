"""
conversation_manager/azure_openai_service.py

Provides a wrapper around Azure OpenAI to generate conversation titles or other LLM usage.
"""

import logging
from typing import List
from openai import AsyncAzureOpenAI
from .config import ConversationConfig


class AzureOpenAIService:
    """
    Simplifies calls to Azure OpenAI for multi-user chat applications.
    Example usage: generate a short conversation title from conversation context.
    """

    def __init__(self, config: ConversationConfig):
        """
        Args:
            config (ConversationConfig): Configuration object with Azure OpenAI and logging settings.
        """
        # Load configuration
        self.endpoint = config.AZURE_OPENAI_ENDPOINT
        self.api_key = config.AZURE_OPENAI_API_KEY
        self.deployment_name = config.AZURE_OPENAI_DEPLOYMENT_NAME
        self.api_version = config.AZURE_OPENAI_API_VERSION

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config.LOGLEVEL)  # Set logging level dynamically

        # Dynamically set Azure SDK logging levels based on config
        if config.LOGLEVEL == "INFO":
            logging.getLogger("azure.core").setLevel(logging.WARNING)
            logging.getLogger("openai").setLevel(logging.WARNING)

        # Initialize the client during __init__
        self._client = None
        self.logger.info("Initializing Azure OpenAI client...")
        try:
            self._client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version
            )
            self.logger.info("Azure OpenAI client initialized successfully.")
        except Exception as e:
            self.logger.error("Failed to initialize Azure OpenAI client: %s", e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def generate_conversation_title(self, user_messages: List[str]) -> str:
        """
        Creates a short conversation title from the user messages.
        This is a simplistic example. You can expand the logic as needed.
        """
        self.logger.info("Generating conversation title...")
        self.logger.debug("User messages: %s", user_messages)

        if not self._client:
            self.logger.error("OpenAIService client not initialized.")
            raise RuntimeError("OpenAIService client not initialized.")

        system_prompt = (
            "You are a system that provides short, concise chat conversation titles. "
            "Take the user's messages and produce a 4-word max title. No punctuation. "
            "No quotes. If insufficient context, output 'New Chat'."
        )

        # Prepare messages for the OpenAI API
        messages = [{"role": "system", "content": system_prompt}]
        for msg in user_messages:
            messages.append({"role": "user", "content": msg})

        self.logger.debug("Prepared messages for OpenAI API: %s", messages)

        try:
            completion = await self._client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.9,
                max_tokens=20
            )
            self.logger.debug("OpenAI API response: %s", completion)

            if completion and completion.choices:
                raw_title = completion.choices[0].message.content.strip()
                self.logger.info("Generated conversation title: %s", raw_title)
                return raw_title

            self.logger.warning("No valid title generated. Defaulting to 'New Chat'.")
            return "Untitled Chat"
        except Exception as e:
            self.logger.error("Failed to generate conversation title: %s", e)
            self.logger.debug("Exception details:", exc_info=True)
            return "Chat"

    async def close(self):
        """
        Closes the underlying client session.
        """
        if self._client:
            await self._client.close()  # Close the AsyncAzureOpenAI client
            self.logger.info("Azure OpenAI client session closed.")
