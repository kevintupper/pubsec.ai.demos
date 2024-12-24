# Conversation Manager

A production-ready Python package for managing multi-user chat conversations in Cosmos DB, optionally integrating with Azure OpenAI for dynamic conversation naming. It follows the patterns found in typical enterprise applications, ensuring reliability, easy configuration, and clarity.

---

## Features

- **Multi-user conversation management**: Each conversation is partitioned by user ID (Entra ID).
- **Cosmos DB Integration**: Persists conversations and messages in a secure, high-scale database.
- **Azure OpenAI**: Dynamically generate short conversation titles from user messages.
- **Configurable via `.env`**: Credentials, endpoints, and optional flags are all environment-driven.
- **Production-grade patterns**: Based on the example code for a robust, maintainable solution.

---

## Setup Instructions

1. **Clone or copy** this package into your project. Ensure you have Python 3.8+ installed.

2. **Install dependencies** using the included `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in your project root, containing (at minimum):

   ```env
   # Cosmos DB Configuration
   COSMOS_DB_ENDPOINT=<your_cosmos_db_endpoint>
   COSMOS_DB_KEY=<your_cosmos_db_key>
   COSMOS_DB_DATABASE_NAME=<your_cosmos_db_database_name>
   COSMOS_DB_CONTAINER_NAME=<your_cosmos_db_container_name>

   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT=<your_azure_openai_endpoint>
   AZURE_OPENAI_KEY=<your_azure_openai_key>

   # General Configuration
   LOGLEVEL=<log_level>  # e.g., DEBUG, INFO, WARNING, ERROR
   ```

4. Validate your .env is correct. Check each variable carefully.

## Usage Instructions

Below is a minimal usage example illustrating initialization, conversation creation, message addition, and retrieval.

```python
import asyncio
from conversation_manager import (
    ConversationConfig,
    CosmosDBConversationClient,
    OpenAIService,
    ConversationManager,
)

async def main():
    # 1. Load config from .env
    config = ConversationConfig()
    config.validate()  # raise ValueError if critical env vars are missing

    # 2. Set up Cosmos DB client
    # If AZURE_AUTH_TYPE=keys, pass in AzureKeyCredential(...) 
    # or if rbac, pass a token credential from azure.identity
    if config.AZURE_AUTH_TYPE == "keys":
        from azure.core.credentials import AzureKeyCredential
        cosmos_credential = AzureKeyCredential("<cosmos-key-here or from env>")
    else:
        from azure.identity.aio import DefaultAzureCredential
        cosmos_credential = DefaultAzureCredential()

    cosmos_db_endpoint = f"https://{config.COSMOS_DB_ACCOUNT}.documents.azure.com:443/"

    cosmos_client = CosmosDBConversationClient(
        endpoint=cosmos_db_endpoint,
        key_or_token_credential=cosmos_credential,
        database_name=config.COSMOS_DB_DATABASE,
        container_name=config.COSMOS_DB_CONTAINER
    )

    # 3. Set up optional Azure OpenAI service
    if config.AZURE_AUTH_TYPE == "keys":
        openai_credential = config.OPENAI_API_KEY
    else:
        from azure.identity.aio import DefaultAzureCredential
        openai_credential = DefaultAzureCredential()

    openai_service = OpenAIService(
        endpoint=config.OPENAI_ENDPOINT,
        api_key_or_token_credential=openai_credential,
        deployment_name=config.OPENAI_DEPLOYMENT_NAME,
        api_version=config.OPENAI_API_VERSION
    )
    openai_service.create_client()

    # 4. Create ConversationManager 
    manager = ConversationManager(cosmos_client, openai_service=openai_service)
    await manager.initialize()

    # 5. Create a new conversation for a given user
    user_id = "00000000-0000-0000-0000-000000000000"
    user_messages = ["Hello, I'd like to discuss sales figures."]
    new_conv = await manager.create_conversation(user_id, user_messages=user_messages)
    print("Created conversation:", new_conv)

    # 6. Add messages
    conversation_id = new_conv["id"]
    await manager.add_message(conversation_id, user_id, "user", "What are last quarter's numbers?")
    await manager.add_message(conversation_id, user_id, "assistant", "Last quarter's numbers rose by 15%. [doc1]")

    # 7. Retrieve conversation info and messages
    conv_info = await manager.get_conversation(conversation_id, user_id)
    conv_messages = await manager.get_messages(conversation_id, user_id)
    print("Conversation info:", conv_info)
    print("Messages:", conv_messages)

    # 8. Cleanup
    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Renaming a Conversation
```python
Copy code
await manager.rename_conversation(conversation_id, user_id, "New Title")
```

### Deleting a Conversation
```python
Copy code
await manager.delete_conversation(conversation_id, user_id)
```

## Integration

- Import the conversation_manager package in your Python app.
- Ensure your .env or environment variables are set.
- Use any standard Python web framework to expose endpoints for chat creation, retrieval, etc.

## Troubleshooting

1. **Authentication Errors:** Check that your credentials (keys) are correct.
2. **Cosmos DB:** Make sure the container is created in Azure Portal or via infrastructure scripts.
3. **Azure OpenAI:** Confirm the deployment name (model) matches what you created in Azure.
4. **Logs:** Enable Python logging (e.g., logging.basicConfig(level=logging.INFO)) to see debug logs.
