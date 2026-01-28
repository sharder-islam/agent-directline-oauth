"""Direct Line API client for interacting with Copilot Studio agents."""

import logging
import os
import uuid
from typing import Dict, List, Optional

import requests

from copilot_directline.models import Activity, ActivitiesResponse, Conversation, Message

# Configure logging
log_file = os.getenv("LOG_FILE", "logs/copilot_directline.log")
log_level = os.getenv("LOG_LEVEL", "INFO")

# Ensure logs directory exists
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


class DirectLineClient:
    """Client for interacting with Direct Line API."""

    def __init__(
        self,
        secret: Optional[str] = None,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Initialize Direct Line client.

        Args:
            secret: Direct Line secret (or read from DIRECT_LINE_SECRET env var)
            endpoint: Direct Line API endpoint (defaults to standard endpoint)
            user_id: User ID for enhanced authentication (must start with 'dl_')
        """
        self.secret = secret or os.getenv("DIRECT_LINE_SECRET")
        if not self.secret:
            raise ValueError(
                "Direct Line secret required. Provide as argument or set DIRECT_LINE_SECRET env var"
            )

        self.endpoint = endpoint or os.getenv(
            "DIRECT_LINE_ENDPOINT", "https://directline.botframework.com"
        )
        self.user_id = user_id or f"dl_{uuid.uuid4().hex}"

        # Validate user_id for enhanced authentication
        if not self.user_id.startswith("dl_"):
            logger.warning(
                f"User ID '{self.user_id}' should start with 'dl_' for enhanced authentication"
            )

        self.base_url = f"{self.endpoint}/v3/directline"
        logger.info(f"Initialized Direct Line client for endpoint: {self.endpoint}")

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers with authentication.

        Args:
            token: Direct Line token (uses secret if not provided)

        Returns:
            Dictionary of headers
        """
        auth_token = token or self.secret
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

    def generate_token(
        self,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        trusted_origins: Optional[List[str]] = None,
    ) -> Conversation:
        """Generate a Direct Line token for a conversation.

        Args:
            user_id: User ID to embed in token (defaults to instance user_id)
            user_name: Display name of the user
            trusted_origins: List of trusted domains for enhanced authentication

        Returns:
            Conversation object with token and conversation ID
        """
        url = f"{self.base_url}/tokens/generate"
        headers = self._get_headers()

        payload: Dict[str, any] = {}
        if user_id or self.user_id:
            payload["user"] = {
                "id": user_id or self.user_id,
            }
            if user_name:
                payload["user"]["name"] = user_name
        if trusted_origins:
            payload["trustedOrigins"] = trusted_origins

        logger.info(f"Generating Direct Line token for user: {payload.get('user', {}).get('id')}")
        response = requests.post(url, headers=headers, json=payload)

        response.raise_for_status()
        data = response.json()

        conversation = Conversation.from_dict(data)
        logger.info(f"Generated token for conversation: {conversation.conversation_id}")
        return conversation

    def start_conversation(
        self,
        user_token: Optional[str] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> Conversation:
        """Start a new conversation with the bot.

        Args:
            user_token: User access token from Entra ID (for authenticated conversations)
            user_id: User ID (defaults to instance user_id)
            user_name: Display name of the user

        Returns:
            Conversation object
        """
        url = f"{self.base_url}/conversations"
        headers = self._get_headers()

        # If user_token is provided, include it in headers for authentication
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"

        payload: Dict[str, any] = {}
        if user_id or self.user_id:
            payload["user"] = {
                "id": user_id or self.user_id,
            }
            if user_name:
                payload["user"]["name"] = user_name

        logger.info(f"Starting conversation for user: {payload.get('user', {}).get('id')}")
        response = requests.post(url, headers=headers, json=payload if payload else None)

        response.raise_for_status()
        data = response.json()

        conversation = Conversation.from_dict(data)
        logger.info(f"Started conversation: {conversation.conversation_id}")
        return conversation

    def send_message(
        self, conversation_id: str, message: str, token: Optional[str] = None
    ) -> Dict[str, any]:
        """Send a message to the bot.

        Args:
            conversation_id: ID of the conversation
            message: Message text to send
            token: Direct Line token (uses secret if not provided)

        Returns:
            Response dictionary with activity ID
        """
        url = f"{self.base_url}/conversations/{conversation_id}/activities"
        headers = self._get_headers(token)

        message_obj = Message(text=message)
        payload = message_obj.to_dict()

        logger.info(f"Sending message to conversation: {conversation_id}")
        response = requests.post(url, headers=headers, json=payload)

        response.raise_for_status()
        data = response.json()

        activity_id = data.get("id", "")
        logger.info(f"Message sent with activity ID: {activity_id}")
        return data

    def get_activities(
        self,
        conversation_id: str,
        watermark: Optional[str] = None,
        token: Optional[str] = None,
    ) -> ActivitiesResponse:
        """Get activities from a conversation.

        Args:
            conversation_id: ID of the conversation
            watermark: Watermark for getting new activities (optional)
            token: Direct Line token (uses secret if not provided)

        Returns:
            ActivitiesResponse with list of activities
        """
        url = f"{self.base_url}/conversations/{conversation_id}/activities"
        headers = self._get_headers(token)

        params = {}
        if watermark:
            params["watermark"] = watermark

        logger.debug(f"Getting activities for conversation: {conversation_id}")
        response = requests.get(url, headers=headers, params=params)

        response.raise_for_status()
        data = response.json()

        activities_response = ActivitiesResponse.from_dict(data)
        logger.debug(
            f"Retrieved {len(activities_response.activities)} activities for conversation: {conversation_id}"
        )
        return activities_response

    def refresh_token(self, token: str) -> Conversation:
        """Refresh a Direct Line token.

        Args:
            token: Token to refresh

        Returns:
            Conversation object with new token
        """
        url = f"{self.base_url}/tokens/refresh"
        headers = self._get_headers(token)

        logger.info("Refreshing Direct Line token")
        response = requests.post(url, headers=headers)

        response.raise_for_status()
        data = response.json()

        conversation = Conversation.from_dict(data)
        logger.info(f"Token refreshed for conversation: {conversation.conversation_id}")
        return conversation

    @classmethod
    def from_env(cls) -> "DirectLineClient":
        """Create DirectLineClient instance from environment variables.

        Reads:
            DIRECT_LINE_SECRET: Direct Line secret
            DIRECT_LINE_ENDPOINT: Direct Line endpoint (optional)

        Returns:
            DirectLineClient instance
        """
        return cls()
