"""Command-line interface for Copilot Studio agent interactions."""

import logging
import os
import sys
import time
from typing import Optional

import click
from dotenv import load_dotenv

from copilot_directline import DirectLineClient, EntraIDAuth
from copilot_directline.models import Conversation

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


def print_message(activity, is_bot: bool = True):
    """Print a message activity in a formatted way."""
    prefix = "🤖 Bot" if is_bot else "👤 You"
    text = activity.text or "[No text]"
    click.echo(f"{prefix}: {text}")


@click.command()
@click.option(
    "--message",
    "-m",
    help="Single message to send (non-interactive mode)",
)
@click.option(
    "--conversation-id",
    "-c",
    help="Continue existing conversation by ID",
)
@click.option(
    "--no-auth",
    is_flag=True,
    help="Skip Entra ID authentication (use Direct Line secret only)",
)
@click.option(
    "--user-name",
    "-n",
    help="Display name for the user",
)
def main(message: Optional[str], conversation_id: Optional[str], no_auth: bool, user_name: Optional[str]):
    """Interactive CLI for chatting with Copilot Studio agents."""
    try:
        # Initialize Direct Line client
        client = DirectLineClient.from_env()

        # Authenticate if needed
        user_token = None
        if not no_auth:
            click.echo("🔐 Authenticating with Microsoft Entra ID...")
            try:
                auth = EntraIDAuth.from_env()
                token_result = auth.acquire_token_interactive()
                user_token = token_result.get("access_token")
                if user_token:
                    click.echo("✅ Authentication successful!")
                else:
                    click.echo("⚠️  No access token received, continuing without user auth")
            except Exception as e:
                click.echo(f"⚠️  Authentication failed: {e}", err=True)
                click.echo("Continuing without user authentication...")

        # Start or continue conversation
        if conversation_id:
            click.echo(f"📝 Continuing conversation: {conversation_id}")
            conversation = Conversation(
                conversation_id=conversation_id,
                token=client.secret,  # Use secret for existing conversation
                expires_in=0,
            )
        else:
            click.echo("🚀 Starting new conversation...")
            if user_token:
                conversation = client.start_conversation(
                    user_token=user_token, user_name=user_name
                )
            else:
                conversation = client.start_conversation(user_name=user_name)
            click.echo(f"✅ Conversation started: {conversation.conversation_id}")

        # Single message mode
        if message:
            click.echo(f"\n📤 Sending: {message}")
            client.send_message(conversation.conversation_id, message, conversation.token)

            # Wait a bit for response
            time.sleep(2)

            # Get activities
            activities_response = client.get_activities(
                conversation.conversation_id, token=conversation.token
            )

            # Print bot responses
            for activity in activities_response.activities:
                if activity.type == "message" and activity.from_user.get("id") != client.user_id:
                    print_message(activity, is_bot=True)

            click.echo(f"\n💡 Conversation ID: {conversation.conversation_id}")
            return

        # Interactive mode
        click.echo("\n💬 Interactive chat mode (type 'exit' or 'quit' to end)\n")

        watermark = None
        while True:
            # Get user input
            try:
                user_input = click.prompt("You", default="", show_default=False)
            except (KeyboardInterrupt, EOFError):
                click.echo("\n👋 Goodbye!")
                break

            if user_input.lower() in ["exit", "quit", "q"]:
                click.echo("👋 Goodbye!")
                break

            if not user_input.strip():
                continue

            # Send message
            try:
                client.send_message(
                    conversation.conversation_id, user_input, conversation.token
                )
            except Exception as e:
                click.echo(f"❌ Error sending message: {e}", err=True)
                continue

            # Wait for response
            time.sleep(1)

            # Get new activities
            try:
                activities_response = client.get_activities(
                    conversation.conversation_id,
                    watermark=watermark,
                    token=conversation.token,
                )
                watermark = activities_response.watermark

                # Print bot responses
                for activity in activities_response.activities:
                    if activity.type == "message" and activity.from_user.get("id") != client.user_id:
                        print_message(activity, is_bot=True)

            except Exception as e:
                click.echo(f"❌ Error getting activities: {e}", err=True)

    except Exception as e:
        logger.exception("CLI error")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
