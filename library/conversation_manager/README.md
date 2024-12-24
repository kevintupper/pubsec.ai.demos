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

Below are the steps to use the `conversation_manager` package. You can test the functionality by running the provided examples, which demonstrate both direct integration and API-based usage.

---

### 1. Direct Integration Example

For direct integration with the `ConversationManager` class, refer to the example in:

**File**: `library/examples/conversation_manager_integration_test_direct.py`

This script demonstrates how to:

- Initialize the `ConversationManager` with Cosmos DB and Azure OpenAI services.
- Create a new conversation.
- Add messages to a conversation.
- Retrieve conversation details and messages.
- Rename and delete conversations.
- Handle edge cases, such as attempting to interact with non-existent conversations.

Run the script to test the functionality directly without using an API:

```bash
python library/examples/conversation_manager_integration_test_direct.py
```

---

### 2. API-Based Integration Example

For API-based usage, refer to the following files:

1. **API Implementation**: `library/examples/conversation_manager_api.py`  
   This file sets up a RESTful API using the `Quart` framework. It exposes endpoints for creating, retrieving, updating, and deleting conversations and messages.

   To start the API server, run:

   ```bash
   python library/examples/conversation_manager_api.py
   ```

   The API will be available at `http://0.0.0.0:8000`.

2. **API Integration Test**: `library/examples/conversation_manager_integration_test_api.py`  
   This script demonstrates how to interact with the API using `httpx`. It covers the same operations as the direct integration example but communicates with the API instead of directly calling the `ConversationManager` class.

   Run the script to test the API:

   ```bash
   python library/examples/conversation_manager_integration_test_api.py
   ```

---

### 3. Key Endpoints in the API

The following endpoints are available in the API:

- **Create a new conversation**: `POST /conversations`
- **Add a message to a conversation**: `POST /conversations/<conv_id>/messages`
- **Retrieve messages in a conversation**: `GET /conversations/<conv_id>/messages`
- **Rename a conversation**: `PUT /conversations/<conv_id>`
- **Delete a conversation**: `DELETE /conversations/<conv_id>`
- **List all conversations for a user**: `GET /conversations`
- **Retrieve a specific conversation**: `GET /conversations/<conv_id>`

Refer to the `conversation_manager_api.py` file for detailed implementation.

---

### Testing and Validation

- Ensure your `.env` file is correctly configured with all required environment variables before running the examples.
- Use the direct integration example to validate the core functionality of the `ConversationManager` class.
- Use the API example to test the RESTful interface and integration with external clients.

---

## Integration

- Import the conversation_manager package in your Python app.
- Ensure your .env or environment variables are set.
- Use any standard Python web framework to expose endpoints for chat creation, retrieval, etc.

## Troubleshooting

1. **Authentication Errors:** Check that your credentials (keys) are correct.
2. **Cosmos DB:** Make sure the container is created in Azure Portal or via infrastructure scripts.
3. **Azure OpenAI:** Confirm the deployment name (model) matches what you created in Azure.
4. **Logs:** Enable Python logging (e.g., logging.basicConfig(level=logging.INFO)) to see debug logs.
