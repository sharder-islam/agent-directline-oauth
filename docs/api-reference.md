# API Reference

Complete API documentation for the `copilot_directline` library.

## Table of Contents

- [EntraIDAuth](#entraidauth)
- [DirectLineClient](#directlineclient)
- [Models](#models)

## EntraIDAuth

Handles Microsoft Entra ID authentication using MSAL (Microsoft Authentication Library).

### Constructor

```python
EntraIDAuth(
    tenant_id: str,
    client_id: str,
    client_secret: Optional[str] = None,
    authority: Optional[str] = None,
    scopes: Optional[list] = None
)
```

**Parameters:**
- `tenant_id` (str): Microsoft Entra ID tenant ID
- `client_id` (str): Application (client) ID from app registration
- `client_secret` (Optional[str]): Client secret for confidential client flows
- `authority` (Optional[str]): Authority URL (defaults to `https://login.microsoftonline.com/{tenant_id}`)
- `scopes` (Optional[list]): List of scopes to request (defaults to `['profile', 'openid']`)

**Example:**
```python
from copilot_directline import EntraIDAuth

auth = EntraIDAuth(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"  # Optional
)
```

### Methods

#### `acquire_token_interactive(account: Optional[msal.Account] = None) -> Dict[str, any]`

Acquire an access token using interactive browser-based OAuth flow.

**Parameters:**
- `account` (Optional[msal.Account]): Account to attempt silent token acquisition first

**Returns:**
- `Dict[str, any]`: Dictionary containing:
  - `access_token` (str): The access token
  - `expires_in` (int): Token expiration time in seconds
  - `token_type` (str): Usually "Bearer"
  - Other metadata fields

**Raises:**
- `Exception`: If token acquisition fails

**Example:**
```python
token_result = auth.acquire_token_interactive()
access_token = token_result.get("access_token")
```

#### `acquire_token_for_client() -> Dict[str, any]`

Acquire token using client credentials flow (service-to-service, no user interaction).

**Returns:**
- `Dict[str, any]`: Token dictionary (same format as `acquire_token_interactive`)

**Raises:**
- `ValueError`: If client secret not provided
- `Exception`: If token acquisition fails

**Example:**
```python
# Requires client_secret in constructor
token_result = auth.acquire_token_for_client()
```

#### `get_accounts() -> list`

Get all cached accounts from MSAL cache.

**Returns:**
- `list`: List of account objects

#### `remove_account(account: msal.Account) -> None`

Remove an account from the MSAL cache.

**Parameters:**
- `account` (msal.Account): Account to remove

#### `from_env() -> EntraIDAuth`

Class method to create `EntraIDAuth` instance from environment variables.

**Reads from environment:**
- `ENTRA_TENANT_ID`: Tenant ID
- `ENTRA_CLIENT_ID`: Client ID
- `ENTRA_CLIENT_SECRET`: Client secret (optional)

**Returns:**
- `EntraIDAuth`: Configured instance

**Example:**
```python
auth = EntraIDAuth.from_env()
```

## DirectLineClient

Client for interacting with Direct Line API.

### Constructor

```python
DirectLineClient(
    secret: Optional[str] = None,
    endpoint: Optional[str] = None,
    user_id: Optional[str] = None
)
```

**Parameters:**
- `secret` (Optional[str]): Direct Line secret (or read from `DIRECT_LINE_SECRET` env var)
- `endpoint` (Optional[str]): Direct Line API endpoint (defaults to `https://directline.botframework.com`)
- `user_id` (Optional[str]): User ID for enhanced authentication (should start with `dl_`)

**Example:**
```python
from copilot_directline import DirectLineClient

client = DirectLineClient(
    secret="your-direct-line-secret",
    endpoint="https://directline.botframework.com"
)
```

### Methods

#### `generate_token(user_id: Optional[str] = None, user_name: Optional[str] = None, trusted_origins: Optional[List[str]] = None) -> Conversation`

Generate a Direct Line token for a conversation without starting it.

**Parameters:**
- `user_id` (Optional[str]): User ID to embed in token
- `user_name` (Optional[str]): Display name of the user
- `trusted_origins` (Optional[List[str]]): List of trusted domains for enhanced authentication

**Returns:**
- `Conversation`: Conversation object with token and conversation ID

**Example:**
```python
conversation = client.generate_token(
    user_id="dl_user123",
    user_name="John Doe",
    trusted_origins=["https://myapp.com"]
)
```

#### `start_conversation(user_token: Optional[str] = None, user_id: Optional[str] = None, user_name: Optional[str] = None) -> Conversation`

Start a new conversation with the bot.

**Parameters:**
- `user_token` (Optional[str]): User access token from Entra ID (for authenticated conversations)
- `user_id` (Optional[str]): User ID (defaults to instance user_id)
- `user_name` (Optional[str]): Display name of the user

**Returns:**
- `Conversation`: Conversation object with conversation ID, token, and expiration

**Example:**
```python
conversation = client.start_conversation(
    user_token=access_token,
    user_name="John Doe"
)
print(f"Conversation ID: {conversation.conversation_id}")
```

#### `send_message(conversation_id: str, message: str, token: Optional[str] = None) -> Dict[str, any]`

Send a message to the bot.

**Parameters:**
- `conversation_id` (str): ID of the conversation
- `message` (str): Message text to send
- `token` (Optional[str]): Direct Line token (uses secret if not provided)

**Returns:**
- `Dict[str, any]`: Response dictionary containing activity ID

**Example:**
```python
result = client.send_message(
    conversation.conversation_id,
    "Hello, bot!",
    conversation.token
)
print(f"Activity ID: {result.get('id')}")
```

#### `get_activities(conversation_id: str, watermark: Optional[str] = None, token: Optional[str] = None) -> ActivitiesResponse`

Get activities (messages) from a conversation.

**Parameters:**
- `conversation_id` (str): ID of the conversation
- `watermark` (Optional[str]): Watermark for getting only new activities
- `token` (Optional[str]): Direct Line token (uses secret if not provided)

**Returns:**
- `ActivitiesResponse`: Object containing list of activities and watermark

**Example:**
```python
activities_response = client.get_activities(
    conversation.conversation_id,
    watermark=previous_watermark,
    token=conversation.token
)

for activity in activities_response.activities:
    if activity.type == "message":
        print(f"Bot: {activity.text}")
```

#### `refresh_token(token: str) -> Conversation`

Refresh a Direct Line token before it expires.

**Parameters:**
- `token` (str): Token to refresh

**Returns:**
- `Conversation`: Conversation object with new token

**Example:**
```python
# Refresh token before expiration (tokens expire in 30 minutes)
new_conversation = client.refresh_token(conversation.token)
```

#### `from_env() -> DirectLineClient`

Class method to create `DirectLineClient` instance from environment variables.

**Reads from environment:**
- `DIRECT_LINE_SECRET`: Direct Line secret
- `DIRECT_LINE_ENDPOINT`: Direct Line endpoint (optional)

**Returns:**
- `DirectLineClient`: Configured instance

**Example:**
```python
client = DirectLineClient.from_env()
```

## Models

### Conversation

Represents a Direct Line conversation.

**Attributes:**
- `conversation_id` (str): Unique conversation identifier
- `token` (str): Direct Line token for this conversation
- `expires_in` (int): Token expiration time in seconds (typically 1800 = 30 minutes)
- `stream_url` (Optional[str]): WebSocket URL for streaming (if available)

**Example:**
```python
from copilot_directline.models import Conversation

conversation = Conversation(
    conversation_id="abc123",
    token="token_value",
    expires_in=1800
)
```

### Activity

Represents a Direct Line activity (message or event).

**Attributes:**
- `id` (str): Activity ID
- `type` (str): Activity type (e.g., "message", "conversationUpdate")
- `from_user` (Dict[str, str]): User information (id, name)
- `text` (Optional[str]): Message text (for message activities)
- `channel_data` (Optional[Dict[str, Any]]): Channel-specific data
- `timestamp` (Optional[str]): Activity timestamp
- `attachments` (Optional[List[Dict[str, Any]]]): File attachments

**Example:**
```python
from copilot_directline.models import Activity

activity = Activity(
    id="act123",
    type="message",
    from_user={"id": "user123", "name": "John"},
    text="Hello!"
)
```

### Message

Represents a message to send to the bot.

**Attributes:**
- `text` (str): Message text
- `type` (str): Message type (defaults to "message")
- `from_user` (Optional[Dict[str, str]]): User information

**Methods:**
- `to_dict() -> Dict[str, Any]`: Convert to dictionary for API request

**Example:**
```python
from copilot_directline.models import Message

message = Message(text="Hello, bot!")
message_dict = message.to_dict()
```

### ActivitiesResponse

Response containing activities from Direct Line API.

**Attributes:**
- `activities` (List[Activity]): List of activities
- `watermark` (Optional[str]): Watermark for pagination

**Example:**
```python
from copilot_directline.models import ActivitiesResponse

response = ActivitiesResponse(
    activities=[activity1, activity2],
    watermark="watermark_value"
)
```

## Error Handling

All methods may raise `requests.HTTPError` for HTTP errors. Check response status codes:

```python
try:
    conversation = client.start_conversation()
except requests.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed")
    elif e.response.status_code == 404:
        print("Resource not found")
    else:
        print(f"HTTP error: {e}")
```

## Logging

The library uses Python's `logging` module. Configure logging level via `LOG_LEVEL` environment variable:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Logs are written to the file specified in `LOG_FILE` environment variable (default: `logs/copilot_directline.log`).
