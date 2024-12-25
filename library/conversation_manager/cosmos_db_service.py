"""
conversation_manager/cosmos_db_service.py

Manages conversation history in Cosmos DB, following the reference patterns.
"""

import logging
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError
from .config import ConversationConfig
from typing import Optional, List, Dict, Any

# Configure logging for your application
logging.basicConfig(level=logging.INFO)  # Set the default logging level for your app

# Suppress Azure SDK logs by setting their log level to WARNING or ERROR
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.cosmos").setLevel(logging.WARNING)

class CosmosDBConversationClient:
    """
    Wraps Cosmos DB operations for storing and managing chat conversations.
    Automatically ensures that the database and container exist.
    """

    def __init__(self, config: ConversationConfig):
        """
        Args:
            config (ConversationConfig): Configuration object with Cosmos DB and logging settings.
        """
        # Load configuration
        self.endpoint = config.COSMOS_DB_ENDPOINT
        self.credential = config.COSMOS_DB_KEY
        self.database_name = config.CHAT_HISTORY_DATABASE
        self.container_name = config.CHAT_HISTORY_CONTAINER

        # Initialize Cosmos DB client and container
        self._client = None
        self._container = None

        # Configure logging for this class based on config
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config.LOGLEVEL) 

        # Dynamically set Azure SDK logging levels to WARNING if our logging level is INFO we don't need to debug Azure SDK
        if config.LOGLEVEL == "INFO":
            logging.getLogger("azure.core").setLevel(logging.WARNING)
            logging.getLogger("azure.cosmos").setLevel(logging.WARNING)

    async def connect(self) -> None:
        """
        Initializes CosmosClient and ensures the database and container exist.
        This must be called before any CRUD operations.
        """
        self.logger.info("Connecting to Cosmos DB...")
        try:
            self._client = CosmosClient(self.endpoint, credential=self.credential)
            await self.ensure_database_and_container()
            self.logger.info("Connected to Cosmos DB container: %s", self.container_name)
        except Exception as e:
            self.logger.error("Failed to connect to Cosmos DB: %s", e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def close(self) -> None:
        """
        Closes the underlying CosmosClient session.
        """
        if self._client:
            await self._client.close()
            self.logger.info("CosmosDB client closed successfully.")

    async def ensure_database_and_container(self) -> None:
        """
        Ensures the Cosmos DB database and container exist. Creates them if they do not.
        """
        try:
            # Ensure the database exists
            self.logger.info("Ensuring database '%s' exists...", self.database_name)
            database = await self._client.create_database_if_not_exists(id=self.database_name)

            # Ensure the container exists without setting throughput (for serverless accounts)
            self.logger.info("Ensuring container '%s' exists...", self.container_name)
            self._container = await database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/entra_oid"),
            )
            self.logger.info("Database and container are ready.")
        except CosmosHttpResponseError as e:
            self.logger.error("Failed to ensure database and container: %s", e)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def create_conversation(self, conversation_id: str, user_id: str, title: str = "") -> Dict[str, Any]:
        """
        Creates a new conversation record in Cosmos DB.
        """
        self.logger.info("Creating conversation ID=%s for user=%s", conversation_id, user_id)
        self.logger.debug("Conversation title: %s", title)
        try:
            conversation_doc = {
                "id": conversation_id,
                "entra_oid": user_id,
                "title": title or "Untitled Conversation",
            }
            resp = await self._container.upsert_item(conversation_doc)
            return resp
        except Exception as e:
            self.logger.error("Failed to create conversation ID=%s for user=%s", conversation_id, user_id)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves conversation from Cosmos DB if it belongs to the user.
        """
        self.logger.debug("Fetching conversation id=%s for user=%s", conversation_id, user_id)
        try:
            return await self._container.read_item(item=conversation_id, partition_key=user_id)
        except CosmosResourceNotFoundError:
            self.logger.info("Conversation ID=%s not found for user=%s", conversation_id, user_id)
            return None
        except Exception as e:
            self.logger.error("Failed to fetch conversation ID=%s for user=%s", conversation_id, user_id)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def upsert_conversation(self, conversation_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates or inserts conversation item. Must include correct 'id' and 'entra_oid' partition key.
        """
        return await self._container.upsert_item(conversation_item)

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Deletes conversation for the user.
        """
        self.logger.info("Deleting conversation id=%s for user=%s", conversation_id, user_id)
        try:
            await self._container.delete_item(item=conversation_id, partition_key=user_id)
            self.logger.info("Successfully deleted conversation id=%s for user=%s", conversation_id, user_id)
            return True
        except Exception as e:
            self.logger.error("Failed to delete conversation ID=%s for user=%s", conversation_id, user_id)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def get_conversations(self, user_id: str, limit: int = 25, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Queries user conversations, sorted by timestamp.
        """
        self.logger.info("Querying conversations for user=%s with limit=%d and offset=%d", user_id, limit, offset)
        query_str = """
        SELECT c.id, c.entra_oid, c.title
        FROM c
        WHERE c.entra_oid = @userId
        ORDER BY c._ts DESC
        OFFSET @offset LIMIT @limit
        """
        params = [
            {"name": "@userId", "value": user_id},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit},
        ]

        results = []
        try:
            async for item in self._container.query_items(query_str, parameters=params):
                results.append(item)
            self.logger.debug("Retrieved %d conversations for user=%s", len(results), user_id)
            return results
        except Exception as e:
            self.logger.error("Failed to query conversations for user=%s", user_id)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def create_message(
        self, conversation_id: str, user_id: str, message_id: str, role: str, content: str
    ) -> Dict[str, Any]:
        """
        Persists a single message within a conversation.
        """
        self.logger.info("Creating message for conversation %s, role=%s", conversation_id, role)
        self.logger.debug("Message content: %s", content)
        try:
            message_doc = {
                "id": message_id,
                "type": "message",
                "entra_oid": user_id,
                "conversationId": conversation_id,
                "role": role,
                "content": content,
            }
            return await self._container.upsert_item(message_doc)
        except Exception as e:
            self.logger.error("Failed to create message for conversation ID=%s", conversation_id)
            self.logger.debug("Exception details:", exc_info=True)
            raise

    async def get_messages(self, conversation_id: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve messages associated with the conversation, sorted by creation order.
        """
        query_str = """
        SELECT *
        FROM c
        WHERE c.entra_oid = @userId
          AND c.conversationId = @convId
          AND c.type = 'message'
        ORDER BY c._ts ASC
        """
        params = [
            {"name": "@userId", "value": user_id},
            {"name": "@convId", "value": conversation_id},
        ]
        results = []
        async for item in self._container.query_items(query_str, parameters=params):
            results.append(item)
        return results

    async def delete_messages(self, conversation_id: str, user_id: str) -> bool:
        """
        Removes all messages for a conversation.
        """
        self.logger.info("Deleting all messages for conversation ID=%s and user=%s", conversation_id, user_id)
        try:
            messages = await self.get_messages(conversation_id, user_id)
            for msg in messages:
                await self._container.delete_item(item=msg["id"], partition_key=msg["entra_oid"])
            self.logger.info("Successfully deleted all messages for conversation ID=%s and user=%s", conversation_id, user_id)
            return True
        except Exception as e:
            self.logger.error("Failed to delete messages for conversation ID=%s and user=%s", conversation_id, user_id)
            self.logger.debug("Exception details:", exc_info=True)
            raise
