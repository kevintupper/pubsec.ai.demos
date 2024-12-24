import asyncio
import httpx

API_BASE_URL = "http://0.0.0.0:8000"  # Base URL of the running API

async def main():
    async with httpx.AsyncClient() as client:
        # 1. Create a new conversation
        user_id = "00000000-0000-0000-0000-000000000000"
        user_messages = ["Hello, I'd like to discuss sales figures."]
        response = await client.post(
            f"{API_BASE_URL}/conversations",
            json={"user_id": user_id, "messages": user_messages},
        )
        assert response.status_code == 201, f"Failed to create conversation: {response.text}"
        new_conv = response.json()
        print("Created conversation:", new_conv)
        print("\n\n")

        # Extract conversation ID
        conversation_id = new_conv["id"]

        # 2. Add messages to the conversation
        response = await client.post(
            f"{API_BASE_URL}/conversations/{conversation_id}/messages",
            json={"user_id": user_id, "role": "user", "content": "What are last quarter's numbers?"},
        )
        assert response.status_code == 200, f"Failed to add user message: {response.text}"
        print("Added user message:", response.json())
        print("\n\n")
        response = await client.post(
            f"{API_BASE_URL}/conversations/{conversation_id}/messages",
            json={"user_id": user_id, "role": "assistant", "content": "Last quarter's numbers rose by 15%. [doc1]"},
        )
        assert response.status_code == 200, f"Failed to add assistant message: {response.text}"
        print("Added assistant message:", response.json())
        print("\n\n")
        # 3. Retrieve conversation info
        response = await client.get(
            f"{API_BASE_URL}/conversations/{conversation_id}",
            params={"user_id": user_id},
        )
        assert response.status_code == 200, f"Failed to retrieve conversation info: {response.text}"
        conv_info = response.json()
        print("Conversation info:", conv_info)
        print("\n\n")
        # 4. Retrieve messages
        response = await client.get(
            f"{API_BASE_URL}/conversations/{conversation_id}/messages",
            params={"user_id": user_id},
        )
        assert response.status_code == 200, f"Failed to retrieve messages: {response.text}"
        conv_messages = response.json()
        print("Messages:", conv_messages)
        print("\n\n")

        # 5. Rename the conversation
        new_title = "Sales Discussion"
        response = await client.put(
            f"{API_BASE_URL}/conversations/{conversation_id}",
            json={"user_id": user_id, "new_title": new_title},
        )
        assert response.status_code == 200, f"Failed to rename conversation: {response.text}"
        updated_conv = response.json()
        print("Renamed conversation:", updated_conv)
        print("\n\n")

        # 6. List all conversations for the user
        response = await client.get(
            f"{API_BASE_URL}/conversations",
            params={"user_id": user_id, "limit": 10, "offset": 0},
        )
        assert response.status_code == 200, f"Failed to list conversations: {response.text}"
        conversations = response.json()
        print("List of conversations:", conversations)
        print("\n\n")

        # 7. Delete the conversation
        response = await client.delete(
            f"{API_BASE_URL}/conversations/{conversation_id}",
            params={"user_id": user_id},
        )
        assert response.status_code == 204, f"Failed to delete conversation: {response.text}"
        print("Deleted conversation successfully.")
        print("\n\n")

        # 8. Edge case - Try to retrieve a deleted conversation
        response = await client.get(
            f"{API_BASE_URL}/conversations/{conversation_id}",
            params={"user_id": user_id},
        )
        assert response.status_code == 404, f"Expected 404 for deleted conversation, got: {response.status_code}"
        print("Deleted conversation retrieval (should be 404):", response.json())
        print("\n\n")

        # 9. Edge case - Try to add a message to a non-existent conversation
        print("Trying to add a message to a non-existent conversation...")
        response = await client.post(
            f"{API_BASE_URL}/conversations/non-existent-id/messages",
            json={"user_id": user_id, "role": "user", "content": "This should fail."},
        )
        assert response.status_code == 404, f"Expected 404 for non-existent conversation, got: {response.status_code}"
        print("Expected error when adding message to non-existent conversation:", response.json())
        print("\n\n")

if __name__ == "__main__":
    asyncio.run(main())