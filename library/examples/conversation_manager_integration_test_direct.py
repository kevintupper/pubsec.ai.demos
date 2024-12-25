# This is a direct integration  test of the ConversationManager class without using the API.
# It's useful for testing the ConversationManager class itself, but not for testing the API.    

# Add the parent directory to the Python path so we can import the ConversationManager classes
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports
import asyncio
import logging
from conversation_manager import (
    ConversationConfig,
    CosmosDBConversationClient,
    AzureOpenAIService,
    ConversationManager,
)
from typing import List, Dict, Optional

async def main() -> None:
    # 1. Load config from .env
    config: ConversationConfig = ConversationConfig()
    config.validate()  # Raise ValueError if critical env vars are missing

    # 2. Set up Cosmos DB client
    cosmos_client: CosmosDBConversationClient = CosmosDBConversationClient(config)
    await cosmos_client.connect()  # Ensure database and container exist

    # 3. Set up Azure OpenAI service
    azure_openai_service: AzureOpenAIService = AzureOpenAIService(config)  # Pass the config directly

    # 4. Create ConversationManager
    manager: ConversationManager = ConversationManager(
        cosmos_client=cosmos_client, azure_openai_service=azure_openai_service
    )
    await manager.initialize()

    try:
        # Test 1: Create a new conversation
        user_id: str = "00000000-0000-0000-0000-000000000000"
        user_messages: List[str] = ["Hello, I'd like to discuss sales figures."]
        new_conv: Dict[str, str] = await manager.create_conversation(user_id, user_messages=user_messages)
        print("Created conversation:", new_conv)
        print("\n\n")

        # Test 2: Add messages to the conversation
        conversation_id: str = new_conv["id"]
        await manager.add_message(conversation_id, user_id, "user", "What are last quarter's numbers?")
        await manager.add_message(conversation_id, user_id, "assistant", "Last quarter's numbers rose by 15%. [doc1]")
        print("\n\n")

        # Test 3: Retrieve conversation info
        conv_info: Optional[Dict[str, str]] = await manager.get_conversation(conversation_id, user_id)
        print("Conversation info:", conv_info)
        print("\n\n")

        # Test 4: Retrieve messages
        conv_messages: List[Dict[str, str]] = await manager.get_messages(conversation_id, user_id)
        print("Messages:", conv_messages)
        print("\n\n")

        # Test 5: Rename the conversation
        new_title: str = "Sales Discussion"
        updated_conv: Dict[str, str] = await manager.rename_conversation(conversation_id, user_id, new_title)
        print("Renamed conversation:", updated_conv)
        print("\n\n")

        # Test 6: List all conversations for the user
        conversations: List[Dict[str, str]] = await manager.list_conversations(user_id, limit=10, offset=0)
        print("List of conversations:", conversations)
        print("\n\n")

        # Test 7: Delete the conversation
        await manager.delete_conversation(conversation_id, user_id)
        print(f"Deleted conversation with ID: {conversation_id}")
        print("\n\n")

        # Test 8: Edge case - Try to retrieve a deleted conversation
        deleted_conv: Optional[Dict[str, str]] = await manager.get_conversation(conversation_id, user_id)
        print("Deleted conversation retrieval (should be None):", deleted_conv)
        print("\n\n")

        # Test 9: Edge case - Try to add a message to a non-existent conversation
        try:
            await manager.add_message("non-existent-id", user_id, "user", "This should fail.")
        except ValueError as e:
            print("Expected error when adding message to non-existent conversation:", e)
        print("\n\n")

    finally:
        # Ensure proper cleanup
        await manager.close()
        print("Manager closed")

if __name__ == "__main__":

    # Add logging to debug unclosed resources
    logging.basicConfig(level=logging.DEBUG)

    # Run the main function and ensure proper cleanup
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error("Unhandled exception during test execution", exc_info=True)
