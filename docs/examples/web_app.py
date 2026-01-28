"""Flask web application example for Copilot Studio agent interactions.

Run this from the project root directory:
    uv run python docs/examples/web_app.py
"""

import json
import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Dict, Optional

# Add src directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from flask import Flask, jsonify, render_template_string, request, session
from dotenv import load_dotenv

from copilot_directline import DirectLineClient, EntraIDAuth

# Load environment variables
load_dotenv()

# Configure logging
log_file = os.getenv("LOG_FILE", "logs/copilot_directline.log")
log_level = os.getenv("LOG_LEVEL", "INFO")

os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)

logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Copilot Studio Chat</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .chat-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #fafafa;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
        }
        .message.user {
            background-color: #0078d4;
            color: white;
            margin-left: 20%;
            text-align: right;
        }
        .message.bot {
            background-color: #e8e8e8;
            color: #333;
            margin-right: 20%;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            font-size: 14px;
        }
        button {
            padding: 12px 24px;
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        button:hover {
            background-color: #106ebe;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .status.info {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        .status.error {
            background-color: #ffebee;
            color: #c62828;
        }
        .status.success {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>Copilot Studio Chat</h1>
        <div id="status" class="status info">Initializing...</div>
        <div id="messages" class="chat-messages"></div>
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Type your message..." disabled>
            <button id="sendButton" onclick="sendMessage()" disabled>Send</button>
        </div>
    </div>

    <script>
        let conversationId = null;
        let watermark = null;

        async function init() {
            try {
                const response = await fetch('/api/conversation/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                
                if (data.success) {
                    conversationId = data.conversation_id;
                    updateStatus('Connected! You can start chatting.', 'success');
                    document.getElementById('messageInput').disabled = false;
                    document.getElementById('sendButton').disabled = false;
                    
                    // Poll for messages
                    pollMessages();
                } else {
                    updateStatus('Failed to start conversation: ' + data.error, 'error');
                }
            } catch (error) {
                updateStatus('Error: ' + error.message, 'error');
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !conversationId) return;

            addMessage(message, 'user');
            input.value = '';
            input.disabled = true;
            document.getElementById('sendButton').disabled = true;

            try {
                const response = await fetch('/api/message/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        conversation_id: conversationId,
                        message: message
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    setTimeout(() => {
                        pollMessages();
                        input.disabled = false;
                        document.getElementById('sendButton').disabled = false;
                    }, 1000);
                } else {
                    updateStatus('Failed to send message: ' + data.error, 'error');
                    input.disabled = false;
                    document.getElementById('sendButton').disabled = false;
                }
            } catch (error) {
                updateStatus('Error: ' + error.message, 'error');
                input.disabled = false;
                document.getElementById('sendButton').disabled = false;
            }
        }

        async function pollMessages() {
            if (!conversationId) return;

            try {
                const response = await fetch(`/api/activities?conversation_id=${conversationId}&watermark=${watermark || ''}`);
                const data = await response.json();
                
                if (data.success && data.activities) {
                    data.activities.forEach(activity => {
                        if (activity.type === 'message' && activity.text) {
                            addMessage(activity.text, 'bot');
                        }
                    });
                    watermark = data.watermark;
                }
            } catch (error) {
                console.error('Error polling messages:', error);
            }
        }

        function addMessage(text, type) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function updateStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
        }

        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        init();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Render the main chat interface."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/conversation/start", methods=["POST"])
def start_conversation():
    """Start a new conversation."""
    try:
        # Authenticate user
        auth = EntraIDAuth.from_env()
        token_result = auth.acquire_token_interactive()
        user_token = token_result.get("access_token")

        if not user_token:
            return jsonify({"success": False, "error": "Failed to get access token"}), 401

        # Store token in session
        session["user_token"] = user_token

        # Create Direct Line client
        client = DirectLineClient.from_env()

        # Start conversation
        conversation = client.start_conversation(user_token=user_token)

        # Store conversation ID in session
        session["conversation_id"] = conversation.conversation_id
        session["conversation_token"] = conversation.token

        logger.info(f"Started conversation: {conversation.conversation_id}")

        return jsonify(
            {
                "success": True,
                "conversation_id": conversation.conversation_id,
            }
        )

    except Exception as e:
        logger.exception("Error starting conversation")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/message/send", methods=["POST"])
def send_message():
    """Send a message to the bot."""
    try:
        data = request.json
        conversation_id = data.get("conversation_id") or session.get("conversation_id")
        message = data.get("message")

        if not conversation_id or not message:
            return jsonify({"success": False, "error": "Missing conversation_id or message"}), 400

        conversation_token = session.get("conversation_token")

        # Create Direct Line client
        client = DirectLineClient.from_env()

        # Send message
        result = client.send_message(conversation_id, message, conversation_token)

        logger.info(f"Sent message to conversation: {conversation_id}")

        return jsonify({"success": True, "activity_id": result.get("id")})

    except Exception as e:
        logger.exception("Error sending message")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/activities", methods=["GET"])
def get_activities():
    """Get activities from the conversation."""
    try:
        conversation_id = request.args.get("conversation_id") or session.get("conversation_id")
        watermark = request.args.get("watermark")

        if not conversation_id:
            return jsonify({"success": False, "error": "Missing conversation_id"}), 400

        conversation_token = session.get("conversation_token")

        # Create Direct Line client
        client = DirectLineClient.from_env()

        # Get activities
        activities_response = client.get_activities(
            conversation_id, watermark=watermark, token=conversation_token
        )

        # Convert activities to dictionaries
        activities = [
            {
                "id": activity.id,
                "type": activity.type,
                "text": activity.text,
                "from": activity.from_user,
            }
            for activity in activities_response.activities
        ]

        return jsonify(
            {
                "success": True,
                "activities": activities,
                "watermark": activities_response.watermark,
            }
        )

    except Exception as e:
        logger.exception("Error getting activities")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
