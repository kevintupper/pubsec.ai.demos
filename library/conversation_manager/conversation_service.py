"""
conversation_manager/conversation_service.py

Provides high-level conversation management for multi-user scenarios,
combining CosmosDBConversationClient with OpenAIService for optional title generation.
"""

import logging
import uuid
from typing import List, Optional
from .cosmos_db_service import CosmosDBConversationClient
from .azure_openai_service import AzureOpenAIService

class ConversationManager:
    """
    High-level conversation manager that handles creation, retrieval, and naming
    of conversations for multiple users. Integrates with Azure OpenAI for dynamic naming.
    """

    def __init__(self, cosmos_client: CosmosDBConversationClient, azure_openai_service: Optional[AzureOpenAIService] = None):
        self.cosmos_client = cosmos_client
        self.azure_openai_service = azure_openai_service
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """
        Call this once before performing operations. Connects to Cosmos DB.
        """
        self.logger.info("Initializing ConversationManager...")
        try:
            await self.cosmos_client.connect()
            self.logger.info("ConversationManager initialized successfully.")
        except Exception as e:
            self.logger.error("Failed to initialize ConversationManager: %s", e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def close(self):
        """
        Closes underlying connections (Cosmos DB, Azure OpenAI, etc.).
        """
        self.logger.info("Closing ConversationManager...")
        try:
            await self.cosmos_client.close()  # Close Cosmos DB client
            if self.azure_openai_service:
                await self.azure_openai_service.close()  # Close Azure OpenAI client session
            self.logger.info("ConversationManager closed successfully.")
        except Exception as e:
            self.logger.error("Failed to close ConversationManager: %s", e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def create_conversation(self, user_id: str, user_messages: Optional[List[str]] = None) -> dict:
        """
        Creates a new conversation doc. Optionally generates a conversation title using Azure OpenAI.
        """
        self.logger.info("Creating a new conversation for user=%s", user_id)
        conv_id = str(uuid.uuid4())
        self.logger.debug("Generated conversation ID: %s", conv_id)

        # Attempt to generate a dynamic title
        title = "Chat"
        if self.azure_openai_service and user_messages:
            self.logger.info("Generating conversation title using Azure OpenAI...")
            try:
                title = await self.azure_openai_service.generate_conversation_title(user_messages)
                self.logger.info("Generated title: %s", title)
            except Exception as e:
                self.logger.error("Title generation failed, defaulting to 'Chat': %s", e)
                self.logger.debug("Exception details:", exc_info=True)

        try:
            conversation_doc = await self.cosmos_client.create_conversation(
                conversation_id=conv_id,
                user_id=user_id,
                title=title
            )
            self.logger.info("Conversation created successfully with ID=%s", conv_id)
            return conversation_doc
        except Exception as e:
            self.logger.error("Failed to create conversation for user=%s: %s", user_id, e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def rename_conversation(self, conversation_id: str, user_id: str, new_title: str):
        """
        Allows the user to rename an existing conversation.
        """
        self.logger.info("Renaming conversation ID=%s for user=%s", conversation_id, user_id)
        self.logger.debug("New title: %s", new_title)
        try:
            conversation = await self.cosmos_client.get_conversation(conversation_id, user_id)
            if not conversation:
                self.logger.warning("No conversation found for ID=%s and user=%s", conversation_id, user_id)
                raise ValueError(f"No conversation found for ID={conversation_id} and user={user_id}")
            conversation["title"] = new_title
            updated = await self.cosmos_client.upsert_conversation(conversation)
            self.logger.info("Conversation ID=%s renamed successfully.", conversation_id)
            return updated
        except Exception as e:
            self.logger.error("Failed to rename conversation ID=%s for user=%s: %s", conversation_id, user_id, e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def get_conversation(self, conversation_id: str, user_id: str) -> dict:
        """
        Retrieves conversation record. If not found, returns None.
        """
        self.logger.info("Retrieving conversation ID=%s for user=%s", conversation_id, user_id)
        try:
            conversation = await self.cosmos_client.get_conversation(conversation_id, user_id)
            if conversation:
                self.logger.info("Conversation ID=%s retrieved successfully.", conversation_id)
            else:
                self.logger.warning("Conversation ID=%s not found for user=%s", conversation_id, user_id)
            return conversation
        except Exception as e:
            self.logger.error("Failed to retrieve conversation ID=%s for user=%s: %s", conversation_id, user_id, e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def list_conversations(self, user_id: str, limit: int = 25, offset: int = 0) -> List[dict]:
        """
        Returns a list of conversation docs for the user.
        """
        self.logger.info("Listing conversations for user=%s with limit=%d and offset=%d", user_id, limit, offset)
        try:
            conversations = await self.cosmos_client.get_conversations(user_id, limit=limit, offset=offset)
            self.logger.info("Retrieved %d conversations for user=%s", len(conversations), user_id)
            self.logger.debug("Conversations: %s", conversations)
            return conversations
        except Exception as e:
            self.logger.error("Failed to list conversations for user=%s: %s", user_id, e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def delete_conversation(self, conversation_id: str, user_id: str):
        """
        Deletes the conversation and all of its messages for the user.
        """
        self.logger.info("Deleting conversation ID=%s for user=%s", conversation_id, user_id)
        try:
            await self.cosmos_client.delete_messages(conversation_id, user_id)
            await self.cosmos_client.delete_conversation(conversation_id, user_id)
            self.logger.info("Conversation ID=%s deleted successfully for user=%s", conversation_id, user_id)
            return True
        except Exception as e:
            self.logger.error("Failed to delete conversation ID=%s for user=%s: %s", conversation_id, user_id, e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def add_message(self, conversation_id: str, user_id: str, role: str, content: str) -> dict:
        """
        Adds a message to an existing conversation doc.
        """
        self.logger.info("Adding message to conversation ID=%s for user=%s", conversation_id, user_id)
        self.logger.debug("Message role: %s, content: %s", role, content)
        try:
            existing_conv = await self.cosmos_client.get_conversation(conversation_id, user_id)
            if not existing_conv:
                self.logger.warning("Conversation ID=%s not found for user=%s", conversation_id, user_id)
                raise ValueError(f"Conversation {conversation_id} not found or belongs to different user.")

            message_id = str(uuid.uuid4())
            message = await self.cosmos_client.create_message(conversation_id, user_id, message_id, role, content)
            self.logger.info("Message added successfully to conversation ID=%s", conversation_id)
            return message
        except Exception as e:
            self.logger.error("Failed to add message to conversation ID=%s for user=%s: %s", conversation_id, user_id, e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def get_messages(self, conversation_id: str, user_id: str, limit: int = 100):
        """
        Returns messages for a specific conversation, in ascending time order.
        """
        self.logger.info("Retrieving messages for conversation ID=%s for user=%s with limit=%d", conversation_id, user_id, limit)
        try:
            messages = await self.cosmos_client.get_messages(conversation_id, user_id, limit=limit)
            self.logger.info("Retrieved %d messages for conversation ID=%s", len(messages), conversation_id)
            self.logger.debug("Messages: %s", messages)
            return messages
        except Exception as e:
            self.logger.error("Failed to retrieve messages for conversation ID=%s for user=%s: %s", conversation_id, user_id, e)
            self.logger.debug("Exception details:", exc_info=True)
            raise
