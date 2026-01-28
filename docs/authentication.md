# Authentication Deep-Dive

This document provides a comprehensive explanation of authentication flows, token management, and security best practices for the Copilot Studio Direct Line OAuth library.

## Authentication Architecture

The library uses a two-stage authentication process:

1. **User Authentication**: Microsoft Entra ID OAuth to authenticate the user
2. **Direct Line Authentication**: Direct Line API token for bot communication

```
┌─────────┐         ┌──────────────┐         ┌─────────────┐
│  User  │────────▶│ Entra ID    │────────▶│ Access Token│
└─────────┘         │ (OAuth)     │         └─────────────┘
                    └──────────────┘                │
                                                     │
┌──────────────┐         ┌──────────────┐          │
│Direct Line   │────────▶│ Direct Line  │◀─────────┘
│Secret        │         │ API          │
└──────────────┘         └──────────────┘
                              │
                              ▼
                         ┌──────────────┐
                         │ Conversation │
                         │   Started    │
                         └──────────────┘
```

## Authentication Flows

### Interactive Flow (Recommended for User Applications)

The interactive flow opens a browser window for the user to sign in with their Microsoft account.

**When to use:**
- CLI tools
- Desktop applications
- Web applications where users need to authenticate

**Flow:**
1. User initiates authentication
2. Browser opens to Microsoft login page
3. User signs in with their Microsoft account
4. User is redirected back with authorization code
5. Library exchanges code for access token
6. Access token is used for Direct Line API calls

**Example:**
```python
from copilot_directline import EntraIDAuth

auth = EntraIDAuth.from_env()
token_result = auth.acquire_token_interactive()
access_token = token_result.get("access_token")
```

### Client Credentials Flow (Service-to-Service)

The client credentials flow authenticates the application itself, not a user.

**When to use:**
- Background services
- Automated scripts
- Service-to-service communication

**Requirements:**
- Client secret must be configured
- Application permissions (not delegated permissions)

**Example:**
```python
from copilot_directline import EntraIDAuth

auth = EntraIDAuth(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)
token_result = auth.acquire_token_for_client()
```

## Token Management

### Access Token Lifecycle

1. **Acquisition**: Token obtained via OAuth flow
2. **Usage**: Token used in Direct Line API requests
3. **Expiration**: Tokens expire (typically 1 hour for Entra ID, 30 minutes for Direct Line)
4. **Refresh**: Tokens can be refreshed before expiration

### Direct Line Token Management

Direct Line tokens are conversation-specific and expire after 30 minutes.

**Best Practices:**
- Store tokens securely (not in code or logs)
- Refresh tokens before expiration
- Use tokens for client applications, secrets for service-to-service

**Token Refresh Example:**
```python
# Check token expiration
if conversation.expires_in < 300:  # Less than 5 minutes remaining
    conversation = client.refresh_token(conversation.token)
```

### Token Caching

MSAL automatically caches tokens in memory. For persistent caching:

```python
# MSAL uses in-memory cache by default
# For persistent cache, configure cache location:
from msal import SerializableTokenCache

cache = SerializableTokenCache()
if os.path.exists("token_cache.json"):
    cache.deserialize(open("token_cache.json", "r").read())

auth = EntraIDAuth.from_env()
# Configure auth.app with cache parameter
```

## Enhanced Authentication

Enhanced authentication provides additional security by embedding user information in Direct Line tokens.

### Benefits

1. **User ID Validation**: Prevents user ID tampering
2. **Impersonation Prevention**: Ensures user ID consistency
3. **Immediate Conversation Updates**: Faster conversation initialization

### Requirements

- User ID must start with `dl_` prefix
- User ID should be unguessable (use UUIDs)
- Enable "Require secure access" in Copilot Studio (Settings > Security > Web channel security)

### Implementation

```python
import uuid

# Generate unguessable user ID
user_id = f"dl_{uuid.uuid4().hex}"

# Use when starting conversation
conversation = client.start_conversation(
    user_token=access_token,
    user_id=user_id
)
```

## Security Best Practices

### 1. Secret Management

**DO:**
- Store secrets in `.env` file (excluded from git)
- Use environment variables in production
- Consider Azure Key Vault for production
- Rotate secrets regularly

**DON'T:**
- Commit secrets to version control
- Hardcode secrets in code
- Log secrets or tokens
- Share secrets via insecure channels

### 2. Token Security

**DO:**
- Use tokens for client applications
- Use secrets only for service-to-service
- Refresh tokens before expiration
- Validate token expiration

**DON'T:**
- Expose Direct Line secrets in client-side code
- Store tokens in browser localStorage (use secure cookies)
- Share tokens between users

### 3. User ID Security

**DO:**
- Use unguessable user IDs (UUIDs)
- Prefix with `dl_` for enhanced authentication
- Generate unique IDs per conversation
- Validate user IDs server-side

**DON'T:**
- Use predictable user IDs (e.g., email addresses)
- Reuse user IDs across different users
- Trust client-provided user IDs without validation

### 4. Network Security

**DO:**
- Use HTTPS for all API calls
- Validate SSL certificates
- Use secure redirect URIs
- Implement rate limiting

**DON'T:**
- Use HTTP for production
- Disable SSL verification
- Allow open redirects

## Troubleshooting Authentication

### Common Issues

1. **"Invalid client" error**
   - Verify client ID matches app registration
   - Check tenant ID is correct

2. **"Redirect URI mismatch"**
   - Verify redirect URI in Azure Portal matches exactly
   - Check for typos or extra characters

3. **"Token expired" error**
   - Implement token refresh logic
   - Check system clock synchronization

4. **"Insufficient privileges"**
   - Verify API permissions are granted
   - Verify API permissions are configured (admin consent is optional for openid/profile scopes)

For more troubleshooting, see [troubleshooting.md](troubleshooting.md).

## Advanced Scenarios

### Multi-Tenant Applications

For applications supporting multiple tenants:

```python
# Store tenant-specific configurations
tenant_configs = {
    "tenant1": {
        "tenant_id": "...",
        "client_id": "...",
    },
    "tenant2": {
        "tenant_id": "...",
        "client_id": "...",
    }
}

# Use appropriate config based on user
tenant_id = get_user_tenant(user_id)
config = tenant_configs[tenant_id]
auth = EntraIDAuth(**config)
```

### Token Refresh Automation

Automatically refresh tokens before expiration:

```python
import threading
import time

def auto_refresh_token(client, conversation, interval=1500):
    """Refresh token every 25 minutes (1500 seconds)."""
    while True:
        time.sleep(interval)
        try:
            conversation = client.refresh_token(conversation.token)
            print("Token refreshed successfully")
        except Exception as e:
            print(f"Token refresh failed: {e}")

# Start background thread
refresh_thread = threading.Thread(
    target=auto_refresh_token,
    args=(client, conversation),
    daemon=True
)
refresh_thread.start()
```

### Custom Scopes

Request additional scopes for accessing other Microsoft services:

```python
auth = EntraIDAuth(
    tenant_id="...",
    client_id="...",
    scopes=["profile", "openid", "User.Read", "Mail.Read"]
)
```

## References

- [Microsoft Entra ID Documentation](https://learn.microsoft.com/en-us/entra/identity-platform/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Direct Line API Authentication](https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-direct-line-3-0-authentication)
- [Copilot Studio Authentication](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-authentication-azure-ad)
