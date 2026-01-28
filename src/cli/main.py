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

# Configure logging - suppress INFO from copilot_directline modules in console
# Note: directline and auth modules set up their own logging via basicConfig
root_logger = logging.getLogger()

# Find and modify existing StreamHandlers to suppress copilot_directline INFO
class SuppressDirectLineInfoFilter(logging.Filter):
    def filter(self, record):
        # Allow OAuth URL from msal.oauth2cli (needed for manual extraction)
        msg = record.getMessage()
        if 'msal.oauth2cli' in record.name and ('Open a browser' in msg or 'login.microsoftonline.com' in msg):
            return True
        # Suppress INFO messages from copilot_directline modules
        if record.name.startswith('copilot_directline') and record.levelno == logging.INFO:
            return False
        # Allow WARNING and above for all modules
        return record.levelno >= logging.WARNING

# Update existing StreamHandlers
for handler in root_logger.handlers[:]:
    if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
        # Add filter to suppress copilot_directline INFO but allow OAuth URL
        handler.addFilter(SuppressDirectLineInfoFilter())
        # Set level to INFO so OAuth URL can pass through filter
        handler.setLevel(logging.INFO)
        # Simplify formatter for console
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

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
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug mode to show all activities",
)
def main(message: Optional[str], conversation_id: Optional[str], no_auth: bool, user_name: Optional[str], debug: bool):
    """Interactive CLI for chatting with Copilot Studio agents."""
    try:
        # Enable debug logging if requested
        if debug:
            logging.getLogger("copilot_directline").setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        
        # Initialize Direct Line client
        client = DirectLineClient.from_env()

        # Authenticate if needed
        user_token = None
        if not no_auth:
            click.echo("🔐 Authenticating...", nl=False)
            try:
                auth = EntraIDAuth.from_env()
                token_result = auth.acquire_token_interactive()
                user_token = token_result.get("access_token")
                if user_token:
                    click.echo(" ✅")
                else:
                    click.echo(" ⚠️  (no token)")
            except Exception as e:
                click.echo(f" ❌ Failed: {e}", err=True)
                click.echo("Continuing without authentication...")

        # Start or continue conversation
        if conversation_id:
            conversation = Conversation(
                conversation_id=conversation_id,
                token=client.secret,  # Use secret for existing conversation
                expires_in=0,
            )
        else:
            if user_token:
                conversation = client.start_conversation(
                    user_token=user_token, user_name=user_name
                )
            else:
                conversation = client.start_conversation(user_name=user_name)

        # Single message mode
        if message:
            click.echo(f"You: {message}")
            client.send_message(
                conversation.conversation_id, 
                message, 
                conversation.token,
                user_token=user_token  # Include user token for authenticated conversations
            )

            # Wait for response and poll for bot messages
            max_polls = 10
            poll_interval = 1.0
            watermark = None
            
            for poll_count in range(max_polls):
                time.sleep(poll_interval)
                
                try:
                    activities_response = client.get_activities(
                        conversation.conversation_id,
                        watermark=watermark,
                        token=conversation.token,
                    )
                    
                    if activities_response.watermark:
                        watermark = activities_response.watermark
                    
                    # Print bot responses (messages not from the user)
                    found_any = False
                    for activity in activities_response.activities:
                        from_id = activity.from_user.get("id", "")
                        from_role = activity.from_user.get("role", "")
                        
                        # Bot messages are those that:
                        # 1. Are of type "message"
                        # 2. Have a from_user.id that's different from our user_id, OR
                        # 3. Have a role of "bot", OR
                        # 4. Don't have an id field (some bots don't set it)
                        is_bot_message = (
                            activity.type == "message" and 
                            (
                                from_role == "bot" or
                                (from_id and from_id != client.user_id) or
                                (not from_id and activity.text)  # If no from_id but has text, likely bot
                            )
                        )
                        
                        if is_bot_message:
                            print_message(activity, is_bot=True)
                            found_any = True
                    
                    # If we found responses and no new activities, we're done
                    if found_any and poll_count > 2:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error getting activities (poll {poll_count + 1}): {e}")
                    if poll_count == max_polls - 1:
                        click.echo(f"❌ Error: {e}", err=True)

            return

        # Interactive mode
        click.echo("\n💬 Chat mode (type 'exit' or 'quit' to end)\n")

        # Initialize watermark by getting initial activities
        watermark = None
        seen_activity_ids = set()  # Track activities we've already shown
        
        try:
            initial_activities = client.get_activities(
                conversation.conversation_id,
                token=conversation.token,
            )
            watermark = initial_activities.watermark
            # Mark initial activities as seen
            for activity in initial_activities.activities:
                seen_activity_ids.add(activity.id)
            logger.debug(f"Initial watermark: {watermark}, seen {len(seen_activity_ids)} activities")
        except Exception as e:
            logger.debug(f"Could not get initial activities: {e}")
        
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
                    conversation.conversation_id, 
                    user_input, 
                    conversation.token,
                    user_token=user_token  # Include user token for authenticated conversations
                )
                
                # Update watermark after sending to only get new activities
                try:
                    current_activities = client.get_activities(
                        conversation.conversation_id,
                        watermark=watermark,
                        token=conversation.token,
                    )
                    if current_activities.watermark:
                        watermark = current_activities.watermark
                        # Mark current activities as seen
                        for activity in current_activities.activities:
                            seen_activity_ids.add(activity.id)
                except Exception as e:
                    logger.debug(f"Could not update watermark after sending: {e}")
            except Exception as e:
                click.echo(f"❌ Error sending message: {e}", err=True)
                continue

            # Wait for response and poll for bot messages
            # Poll multiple times as bot responses may take a few seconds
            max_polls = 10
            poll_interval = 1.0
            found_responses = False
            
            # Show loading indicator
            spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            spinner_idx = 0
            spinner_shown = False
            
            for poll_count in range(max_polls):
                if poll_count > 0:
                    time.sleep(poll_interval)
                
                # Update spinner
                click.echo(f"\r{spinner_chars[spinner_idx % len(spinner_chars)]} ", nl=False)
                spinner_idx += 1
                spinner_shown = True
                
                try:
                    activities_response = client.get_activities(
                        conversation.conversation_id,
                        watermark=watermark,
                        token=conversation.token,
                    )
                    new_watermark = activities_response.watermark
                    
                    # Print bot responses (messages not from the user)
                    new_activities_found = False
                    for activity in activities_response.activities:
                        # Skip activities we've already seen
                        if activity.id in seen_activity_ids:
                            continue
                        
                        # Bot activities have from_user.id that's different from client.user_id
                        # or they might have a role field set to "bot"
                        from_id = activity.from_user.get("id", "")
                        from_role = activity.from_user.get("role", "")
                        is_from_bot = (
                            from_role == "bot" or
                            (from_id and from_id != client.user_id) or
                            (not from_id)  # If no from_id, likely from bot
                        )
                        
                        # Log bot activities for debugging (only to file, not console)
                        if is_from_bot and debug:
                            logger.debug(
                                f"Bot activity: id={activity.id}, type={activity.type}, "
                                f"text={activity.text[:100] if activity.text else '(no text)'}, "
                                f"attachments={len(activity.attachments) if activity.attachments else 0}"
                            )
                            if activity.type != "message":
                                click.echo(f"🔍 [DEBUG] Bot sent {activity.type} activity")
                        
                        # Handle message activities
                        if activity.type == "message" and is_from_bot:
                            # Skip activities with no text (empty messages) unless they have attachments
                            if not activity.text or not activity.text.strip():
                                if activity.attachments:
                                    # Show message about attachments
                                    click.echo(f"🤖 Bot: [Message with {len(activity.attachments)} attachment(s)]")
                                    # In debug mode, show attachment details
                                    if debug:
                                        for att in activity.attachments:
                                            click.echo(f"   📎 Attachment: {att.get('contentType', 'unknown')}")
                                            if 'content' in att:
                                                content = att['content']
                                                if isinstance(content, dict):
                                                    if 'buttons' in content:
                                                        click.echo(f"   🔘 Buttons: {len(content['buttons'])}")
                                                    if 'text' in content:
                                                        click.echo(f"   📝 Content text: {content['text'][:100]}")
                                    found_responses = True
                                    new_activities_found = True
                                elif debug:
                                    # In debug mode, show empty activities to help diagnose
                                    click.echo(f"🔍 [DEBUG] Bot sent empty message activity (id: {activity.id})")
                                    if activity.channel_data:
                                        click.echo(f"   Channel data: {activity.channel_data}")
                                seen_activity_ids.add(activity.id)
                                continue
                            
                            # Clear spinner before printing message
                            if spinner_shown:
                                click.echo("\r" + " " * 2 + "\r", nl=False)
                                spinner_shown = False
                            print_message(activity, is_bot=True)
                            found_responses = True
                            new_activities_found = True
                        
                        # Handle other activity types (like sign-in cards, OAuth cards, etc.)
                        elif activity.type in ["invoke", "event"] and is_from_bot:
                            if debug:
                                logger.debug(f"Bot sent {activity.type} activity: {activity.text or '(no text)'}")
                            if activity.text:
                                # Clear spinner before printing
                                if spinner_shown:
                                    click.echo("\r" + " " * 2 + "\r", nl=False)
                                    spinner_shown = False
                                click.echo(f"🤖 Bot: {activity.text}")
                                found_responses = True
                                new_activities_found = True
                        
                        # Check for attachments (sign-in cards, OAuth cards, etc.)
                        if activity.attachments and is_from_bot:
                            for attachment in activity.attachments:
                                content_type = attachment.get("contentType", "")
                                if "signin" in content_type.lower() or "oauth" in content_type.lower():
                                    if debug:
                                        logger.debug(f"Sign-in card detected: {attachment}")
                                    # Only show sign-in cards in debug mode
                                    if debug:
                                        click.echo(f"🤖 Bot: [Sign-in card detected]")
                                    found_responses = True
                                    new_activities_found = True
                        
                        # Mark this activity as seen
                        seen_activity_ids.add(activity.id)
                    
                    # Update watermark for next poll only if we got new activities
                    if new_watermark and new_activities_found:
                        watermark = new_watermark
                    elif new_watermark:
                        # Still update watermark even if no new bot messages (to avoid re-fetching)
                        watermark = new_watermark
                    
                    # If we found responses and no new activities in last few polls, we're done
                    if found_responses and not new_activities_found and poll_count > 2:
                        # Clear spinner if we're done
                        if spinner_shown:
                            click.echo("\r" + " " * 2 + "\r", nl=False)
                        break
                        
                except Exception as e:
                    logger.debug(f"Error getting activities (poll {poll_count + 1}): {e}")
                    # Continue polling even if one request fails
                    if poll_count == max_polls - 1:
                        if spinner_shown:
                            click.echo("\r", nl=False)
                        click.echo(f"❌ Error: {e}", err=True)
            
            # Clear spinner if still showing
            if spinner_shown:
                click.echo("\r" + " " * 2 + "\r", nl=False)
            
            if not found_responses:
                click.echo("⚠️  No response received")

    except Exception as e:
        logger.exception("CLI error")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
