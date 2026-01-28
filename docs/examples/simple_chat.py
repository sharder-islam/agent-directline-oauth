"""Simple example of using the Copilot Direct Line library.

Run this from the project root directory:
    uv run python docs/examples/simple_chat.py
"""

import os
import sys
from pathlib import Path

# Add src directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv

from copilot_directline import DirectLineClient, EntraIDAuth

# Load environment variables
load_dotenv()


def main():
    """Simple chat example."""
    print("🚀 Copilot Studio Direct Line Example\n")

    # Authenticate with Entra ID
    print("🔐 Authenticating with Microsoft Entra ID...")
    auth = EntraIDAuth.from_env()
    token_result = auth.acquire_token_interactive()
    user_token = token_result.get("access_token")

    if not user_token:
        print("❌ Failed to get access token")
        return

    print("✅ Authentication successful!\n")

    # Create Direct Line client
    client = DirectLineClient.from_env()

    # Start conversation
    print("📝 Starting conversation...")
    conversation = client.start_conversation(user_token=user_token)
    print(f"✅ Conversation started: {conversation.conversation_id}\n")

    # Send a message
    message = "Hello! How are you?"
    print(f"📤 Sending: {message}")
    client.send_message(conversation.conversation_id, message, conversation.token)

    # Get activities
    import time
    time.sleep(2)  # Wait for bot response

    activities_response = client.get_activities(
        conversation.conversation_id, token=conversation.token
    )

    # Print bot responses
    print("\n📥 Bot responses:")
    for activity in activities_response.activities:
        if activity.type == "message" and activity.from_user.get("id") != client.user_id:
            print(f"  🤖 {activity.text}")

    print(f"\n💡 Conversation ID: {conversation.conversation_id}")


if __name__ == "__main__":
    main()
