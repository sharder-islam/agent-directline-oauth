# Extended Usage Examples

This document provides comprehensive examples for different use cases and scenarios.

## Table of Contents

- [Basic Examples](#basic-examples)
- [CLI Usage](#cli-usage)
- [Web Application Integration](#web-application-integration)
- [Batch Processing](#batch-processing)
- [Error Handling](#error-handling)
- [Advanced Patterns](#advanced-patterns)

## Basic Examples

### Simple Chat

```python
"""Simple one-message chat example."""
from copilot_directline import DirectLineClient, EntraIDAuth
from dotenv import load_dotenv

load_dotenv()

# Authenticate
auth = EntraIDAuth.from_env()
token_result = auth.acquire_token_interactive()
user_token = token_result.get("access_token")

# Start conversation
client = DirectLineClient.from_env()
conversation = client.start_conversation(user_token=user_token)

# Send message
client.send_message(conversation.conversation_id, "Hello!", conversation.token)

# Get response
import time
time.sleep(2)  # Wait for bot response

activities = client.get_activities(conversation.conversation_id, token=conversation.token)
for activity in activities.activities:
    if activity.type == "message":
        print(f"Bot: {activity.text}")
```

### Interactive Chat Loop

```python
"""Interactive chat with continuous conversation."""
from copilot_directline import DirectLineClient, EntraIDAuth
from dotenv import load_dotenv
import time

load_dotenv()

# Authenticate
auth = EntraIDAuth.from_env()
token_result = auth.acquire_token_interactive()
user_token = token_result.get("access_token")

# Start conversation
client = DirectLineClient.from_env()
conversation = client.start_conversation(user_token=user_token)
watermark = None

print("Chat started! Type 'exit' to quit.\n")

while True:
    # Get user input
    user_message = input("You: ").strip()
    if user_message.lower() in ["exit", "quit"]:
        break

    if not user_message:
        continue

    # Send message
    client.send_message(conversation.conversation_id, user_message, conversation.token)

    # Wait for response
    time.sleep(1.5)

    # Get new activities
    activities_response = client.get_activities(
        conversation.conversation_id,
        watermark=watermark,
        token=conversation.token
    )
    watermark = activities_response.watermark

    # Print bot responses
    for activity in activities_response.activities:
        if activity.type == "message" and activity.from_user.get("id") != client.user_id:
            print(f"Bot: {activity.text}\n")
```

## CLI Usage

### Single Message

```bash
# Send a single message
uv run python -m src.cli.main --message "What is the weather today?"

# With user name
uv run python -m src.cli.main --message "Hello" --user-name "John Doe"

# Skip authentication (use Direct Line secret only)
uv run python -m src.cli.main --message "Hello" --no-auth
```

### Interactive Mode

```bash
# Start interactive chat
uv run python -m src.cli.main

# Continue existing conversation
uv run python -m src.cli.main --conversation-id "abc123"
```

### Using as Script

```bash
#!/bin/bash
# Send multiple messages in sequence

CONV_ID=$(uv run python -m src.cli.main --message "Start conversation" | grep "Conversation ID" | awk '{print $3}')

uv run python -m src.cli.main --conversation-id "$CONV_ID" --message "First question"
uv run python -m src.cli.main --conversation-id "$CONV_ID" --message "Follow-up question"
```

## Web Application Integration

### Flask REST API

```python
"""Flask REST API for chat operations."""
from flask import Flask, jsonify, request
from copilot_directline import DirectLineClient, EntraIDAuth
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

# Store conversations in memory (use Redis/DB in production)
conversations = {}

@app.route("/api/auth", methods=["POST"])
def authenticate():
    """Authenticate user and return access token."""
    try:
        auth = EntraIDAuth.from_env()
        token_result = auth.acquire_token_interactive()
        return jsonify({
            "success": True,
            "access_token": token_result.get("access_token")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/conversation", methods=["POST"])
def create_conversation():
    """Create a new conversation."""
    try:
        user_token = request.json.get("access_token")
        if not user_token:
            return jsonify({"success": False, "error": "access_token required"}), 400

        client = DirectLineClient.from_env()
        conversation = client.start_conversation(user_token=user_token)

        conversations[conversation.conversation_id] = {
            "token": conversation.token,
            "expires_in": conversation.expires_in
        }

        return jsonify({
            "success": True,
            "conversation_id": conversation.conversation_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/message", methods=["POST"])
def send_message():
    """Send a message to the bot."""
    try:
        data = request.json
        conversation_id = data.get("conversation_id")
        message = data.get("message")

        if not conversation_id or not message:
            return jsonify({"success": False, "error": "Missing parameters"}), 400

        if conversation_id not in conversations:
            return jsonify({"success": False, "error": "Conversation not found"}), 404

        client = DirectLineClient.from_env()
        result = client.send_message(
            conversation_id,
            message,
            conversations[conversation_id]["token"]
        )

        return jsonify({"success": True, "activity_id": result.get("id")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/activities/<conversation_id>", methods=["GET"])
def get_activities(conversation_id):
    """Get activities from conversation."""
    try:
        if conversation_id not in conversations:
            return jsonify({"success": False, "error": "Conversation not found"}), 404

        watermark = request.args.get("watermark")
        client = DirectLineClient.from_env()
        activities_response = client.get_activities(
            conversation_id,
            watermark=watermark,
            token=conversations[conversation_id]["token"]
        )

        activities = [
            {
                "id": a.id,
                "type": a.type,
                "text": a.text,
                "from": a.from_user
            }
            for a in activities_response.activities
        ]

        return jsonify({
            "success": True,
            "activities": activities,
            "watermark": activities_response.watermark
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=int(os.getenv("FLASK_PORT", 5000)))
```

### FastAPI Example

```python
"""FastAPI REST API for chat operations."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from copilot_directline import DirectLineClient, EntraIDAuth
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

class MessageRequest(BaseModel):
    conversation_id: str
    message: str

class ConversationRequest(BaseModel):
    access_token: str

@app.post("/api/conversation")
async def create_conversation(req: ConversationRequest):
    """Create a new conversation."""
    try:
        client = DirectLineClient.from_env()
        conversation = client.start_conversation(user_token=req.access_token)
        return {
            "success": True,
            "conversation_id": conversation.conversation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/message")
async def send_message(req: MessageRequest):
    """Send a message."""
    try:
        client = DirectLineClient.from_env()
        result = client.send_message(req.conversation_id, req.message)
        return {"success": True, "activity_id": result.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Batch Processing

### Process Multiple Questions

```python
"""Process a list of questions and collect responses."""
from copilot_directline import DirectLineClient, EntraIDAuth
from dotenv import load_dotenv
import time
import json

load_dotenv()

questions = [
    "What is the weather today?",
    "What are the business hours?",
    "How do I contact support?",
]

# Authenticate once
auth = EntraIDAuth.from_env()
token_result = auth.acquire_token_interactive()
user_token = token_result.get("access_token")

# Start conversation
client = DirectLineClient.from_env()
conversation = client.start_conversation(user_token=user_token)

results = []

for question in questions:
    print(f"Processing: {question}")
    
    # Send question
    client.send_message(conversation.conversation_id, question, conversation.token)
    
    # Wait for response
    time.sleep(2)
    
    # Get activities
    activities_response = client.get_activities(
        conversation.conversation_id,
        token=conversation.token
    )
    
    # Extract bot response
    bot_responses = [
        a.text for a in activities_response.activities
        if a.type == "message" and a.from_user.get("id") != client.user_id
    ]
    
    results.append({
        "question": question,
        "responses": bot_responses
    })

# Save results
with open("output/results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Processed {len(questions)} questions. Results saved to output/results.json")
```

## Error Handling

### Comprehensive Error Handling

```python
"""Example with comprehensive error handling."""
from copilot_directline import DirectLineClient, EntraIDAuth
from dotenv import load_dotenv
import requests
import time

load_dotenv()

def safe_authenticate():
    """Authenticate with error handling."""
    try:
        auth = EntraIDAuth.from_env()
        token_result = auth.acquire_token_interactive()
        return token_result.get("access_token")
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file")
        return None
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

def safe_send_message(client, conversation_id, message, token, max_retries=3):
    """Send message with retry logic."""
    for attempt in range(max_retries):
        try:
            return client.send_message(conversation_id, message, token)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                print("Token expired, refreshing...")
                # Refresh token logic here
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            raise
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)
                continue
            raise
    return None

# Usage
user_token = safe_authenticate()
if user_token:
    client = DirectLineClient.from_env()
    conversation = client.start_conversation(user_token=user_token)
    
    result = safe_send_message(
        client,
        conversation.conversation_id,
        "Hello!",
        conversation.token
    )
    
    if result:
        print("Message sent successfully!")
```

## Advanced Patterns

### Token Refresh Automation

```python
"""Automatically refresh tokens before expiration."""
import threading
import time
from copilot_directline import DirectLineClient

def auto_refresh(client, conversation, refresh_interval=1500):
    """Background thread to refresh tokens."""
    while True:
        time.sleep(refresh_interval)  # 25 minutes
        try:
            new_conversation = client.refresh_token(conversation.token)
            conversation.token = new_conversation.token
            conversation.expires_in = new_conversation.expires_in
            print("Token refreshed successfully")
        except Exception as e:
            print(f"Token refresh failed: {e}")

# Start conversation
client = DirectLineClient.from_env()
conversation = client.start_conversation()

# Start refresh thread
refresh_thread = threading.Thread(
    target=auto_refresh,
    args=(client, conversation),
    daemon=True
)
refresh_thread.start()

# Use conversation normally
# Token will be refreshed automatically
```

### Conversation State Management

```python
"""Manage multiple conversations with state tracking."""
from copilot_directline import DirectLineClient, EntraIDAuth
from dataclasses import dataclass
from typing import Dict, Optional
import time

@dataclass
class ConversationState:
    conversation_id: str
    token: str
    watermark: Optional[str] = None
    last_activity: Optional[float] = None

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}
        self.client = DirectLineClient.from_env()
        self.auth = EntraIDAuth.from_env()
        self.user_token = None

    def authenticate(self):
        """Authenticate user."""
        token_result = self.auth.acquire_token_interactive()
        self.user_token = token_result.get("access_token")

    def create_conversation(self, user_id: str) -> str:
        """Create a new conversation for a user."""
        if not self.user_token:
            self.authenticate()

        conversation = self.client.start_conversation(user_token=self.user_token)
        self.conversations[user_id] = ConversationState(
            conversation_id=conversation.conversation_id,
            token=conversation.token
        )
        return conversation.conversation_id

    def send_message(self, user_id: str, message: str):
        """Send message in user's conversation."""
        if user_id not in self.conversations:
            self.create_conversation(user_id)

        state = self.conversations[user_id]
        self.client.send_message(state.conversation_id, message, state.token)
        state.last_activity = time.time()

    def get_messages(self, user_id: str):
        """Get new messages for user."""
        if user_id not in self.conversations:
            return []

        state = self.conversations[user_id]
        activities_response = self.client.get_activities(
            state.conversation_id,
            watermark=state.watermark,
            token=state.token
        )
        state.watermark = activities_response.watermark

        return [
            a for a in activities_response.activities
            if a.type == "message"
        ]

# Usage
manager = ConversationManager()
manager.authenticate()

user1_conv = manager.create_conversation("user1")
manager.send_message("user1", "Hello!")
messages = manager.get_messages("user1")
```

### Async/Await Pattern

```python
"""Async/await pattern for concurrent operations."""
import asyncio
import aiohttp
from copilot_directline import DirectLineClient, EntraIDAuth

async def send_message_async(session, url, headers, payload):
    """Send message asynchronously."""
    async with session.post(url, headers=headers, json=payload) as response:
        return await response.json()

async def process_multiple_conversations():
    """Process multiple conversations concurrently."""
    # Authenticate
    auth = EntraIDAuth.from_env()
    token_result = auth.acquire_token_interactive()
    user_token = token_result.get("access_token")

    client = DirectLineClient.from_env()
    
    # Create multiple conversations
    conversations = []
    for i in range(3):
        conv = client.start_conversation(user_token=user_token)
        conversations.append(conv)

    # Send messages concurrently
    async with aiohttp.ClientSession() as session:
        tasks = []
        for conv in conversations:
            url = f"{client.base_url}/conversations/{conv.conversation_id}/activities"
            headers = client._get_headers(conv.token)
            payload = {"type": "message", "text": "Hello!"}
            tasks.append(send_message_async(session, url, headers, payload))

        results = await asyncio.gather(*tasks)
        return results

# Run async function
results = asyncio.run(process_multiple_conversations())
```

## Additional Resources

- [API Reference](api-reference.md) - Complete API documentation
- [Authentication Guide](authentication.md) - Authentication deep-dive
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
