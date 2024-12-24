"""
test_manager_apps/sample_conversation_manager.py

Example application demonstrating usage of conversation_manager.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import logging
from quart import Quart, request, jsonify

from conversation_manager import (
    ConversationConfig,
    CosmosDBConversationClient,
    AzureOpenAIService,
    ConversationManager,
)

app = Quart(__name__)
logging.basicConfig(level=logging.INFO)

# Globally initialize managers
config = ConversationConfig()
config.validate()

# Pass the config object directly to CosmosDBConversationClient
cosmos_client = CosmosDBConversationClient(config)

# Initialize AzureOpenAIService with the config
azure_openai_svc = AzureOpenAIService(config)

# Initialize ConversationManager with the CosmosDB and Azure OpenAI services
manager = ConversationManager(cosmos_client, azure_openai_service=azure_openai_svc)

@app.before_serving
async def startup():
    await manager.initialize()

@app.after_serving
async def shutdown():
    await manager.close()

@app.route("/conversations", methods=["POST"])
async def create_new_conversation():
    data = await request.get_json()
    user_id = data.get("user_id", "")
    user_messages = data.get("messages", [])
    new_conv = await manager.create_conversation(user_id, user_messages=user_messages)
    return jsonify(new_conv), 201

@app.route("/conversations/<conv_id>/messages", methods=["POST"])
async def add_message(conv_id):
    data = await request.get_json()
    user_id = data.get("user_id", "")
    role = data.get("role", "user")
    content = data.get("content", "")

    try:
        msg = await manager.add_message(conv_id, user_id, role, content)
        return jsonify(msg), 200
    except ValueError as e:
        # Handle the case where the conversation does not exist
        logging.warning("ValueError: %s", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # Handle unexpected errors
        logging.error("Unexpected error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/conversations/<conv_id>/messages", methods=["GET"])
async def list_messages(conv_id):
    user_id = request.args.get("user_id", "")
    msgs = await manager.get_messages(conv_id, user_id)
    return jsonify(msgs), 200

@app.route("/conversations/<conv_id>", methods=["PUT"])
async def rename_conversation(conv_id):
    data = await request.get_json()
    user_id = data.get("user_id", "")
    new_title = data.get("new_title", "Untitled")
    updated = await manager.rename_conversation(conv_id, user_id, new_title)
    return jsonify(updated), 200

@app.route("/conversations/<conv_id>", methods=["DELETE"])
async def delete_conversation(conv_id):
    user_id = request.args.get("user_id", "")
    await manager.delete_conversation(conv_id, user_id)
    return jsonify({"status": "deleted"}), 204

@app.route("/conversations", methods=["GET"])
async def list_conversations():
    user_id = request.args.get("user_id", "")
    limit = int(request.args.get("limit", 25))
    offset = int(request.args.get("offset", 0))
    conversations = await manager.list_conversations(user_id, limit=limit, offset=offset)
    return jsonify(conversations), 200

@app.route("/conversations/<conv_id>", methods=["GET"])
async def get_conversation(conv_id):
    user_id = request.args.get("user_id", "")
    conversation = await manager.get_conversation(conversation_id=conv_id, user_id=user_id)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify(conversation), 200

if __name__ == "__main__":
    # For synchronous servers, wrap in asyncio
    import hypercorn.asyncio
    from hypercorn.config import Config as HyperConfig

    hyperconfig = HyperConfig()
    hyperconfig.bind = ["0.0.0.0:8000"]
    asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
