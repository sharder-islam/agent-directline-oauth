# Troubleshooting Guide

Common issues, error messages, and solutions for the Copilot Studio Direct Line OAuth library.

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Direct Line API Issues](#direct-line-api-issues)
- [Configuration Issues](#configuration-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)

## Authentication Issues

### "Invalid client" Error

**Error Message:**
```
AADSTS700016: Application with identifier 'xxx' was not found in the directory 'xxx'
```

**Causes:**
- Incorrect `ENTRA_CLIENT_ID` in `.env` file
- App registration doesn't exist in the specified tenant
- Client ID copied incorrectly (extra spaces, wrong value)

**Solutions:**
1. Verify the Application (client) ID in Azure Portal:
   - Go to Azure Portal → App registrations → Your app
   - Copy the "Application (client) ID" exactly
   - Update `.env` file with correct value

2. Verify tenant ID:
   - Check that `ENTRA_TENANT_ID` matches the Directory (tenant) ID
   - Ensure the app registration exists in that tenant

3. Check for typos:
   - Remove any extra spaces or characters
   - Ensure no line breaks in the value

### "Redirect URI Mismatch" Error

**Error Message:**
```
AADSTS50011: The redirect URI 'xxx' specified in the request does not match the redirect URIs configured for the application 'xxx'
```

**Causes:**
- Redirect URI not configured in Azure Portal
- Typo in redirect URI
- Wrong redirect URI format

**Solutions:**
1. Verify redirect URI in Azure Portal:
   - Go to App registrations → Authentication
   - Check that `https://token.botframework.com/.auth/web/redirect` is listed
   - For Europe region: `https://europe.token.botframework.com/.auth/web/redirect`

2. Check for exact match:
   - URI must match exactly (case-sensitive, no trailing slashes)
   - Verify protocol (https, not http)

3. Add redirect URI if missing:
   - Click "Add a platform" → "Web"
   - Add the correct redirect URI
   - Save changes

### "Insufficient Privileges" Error

**Error Message:**
```
AADSTS65005: The application 'xxx' requested a scope 'xxx' that doesn't exist
```

**Causes:**
- API permissions not configured
- Admin consent not granted
- Wrong scopes requested

**Solutions:**
1. Verify API permissions:
   - Go to App registrations → API permissions
   - Ensure "Microsoft Graph" permissions are added:
     - `openid` (Delegated)
     - `profile` (Delegated)

2. Grant admin consent:
   - Click "Grant admin consent for [Tenant]"
   - Confirm the action
   - Wait a few minutes for propagation

3. Check scopes in code:
   - Default scopes are `['profile', 'openid']`
   - Don't request scopes that aren't configured

### "Token Acquisition Failed" Error

**Error Message:**
```
Failed to acquire token: User canceled authentication
```

**Causes:**
- User closed browser window
- User denied consent
- Network issues during authentication

**Solutions:**
1. Retry authentication:
   - User may have accidentally closed the browser
   - Try again and complete the sign-in process

2. Check network connectivity:
   - Ensure internet connection is active
   - Verify firewall isn't blocking Microsoft login

3. Clear browser cache:
   - Sometimes cached credentials cause issues
   - Try incognito/private browsing mode

## Direct Line API Issues

### "Unauthorized" Error (401)

**Error Message:**
```
401 Unauthorized
```

**Causes:**
- Invalid Direct Line secret
- Secret expired or regenerated
- Wrong endpoint URL

**Solutions:**
1. Verify Direct Line secret:
   - Go to Copilot Studio → Channels → Direct Line
   - Copy the secret again
   - Update `.env` file

2. Check secret format:
   - Secret should be a long string
   - No extra spaces or line breaks

3. Verify endpoint:
   - Default: `https://directline.botframework.com`
   - Europe: `https://europe.directline.botframework.com`
   - India: `https://india.directline.botframework.com`

### "Conversation Not Found" Error (404)

**Error Message:**
```
404 Not Found - Conversation 'xxx' not found
```

**Causes:**
- Conversation ID is incorrect
- Conversation expired
- Token expired

**Solutions:**
1. Start a new conversation:
   ```python
   conversation = client.start_conversation(user_token=token)
   ```

2. Verify conversation ID:
   - Check that you're using the correct conversation ID
   - Don't mix conversation IDs from different sessions

3. Check token expiration:
   - Direct Line tokens expire after 30 minutes
   - Refresh token or start new conversation

### "Message Not Sent" Error

**Error Message:**
```
Failed to send message: 400 Bad Request
```

**Causes:**
- Invalid message format
- Conversation ID incorrect
- Token expired

**Solutions:**
1. Verify message format:
   - Message should be a string
   - Not empty or None

2. Check conversation status:
   - Ensure conversation is active
   - Verify conversation ID is correct

3. Refresh token:
   ```python
   conversation = client.refresh_token(conversation.token)
   ```

## Configuration Issues

### "Environment Variable Not Set" Error

**Error Message:**
```
ValueError: ENTRA_TENANT_ID and ENTRA_CLIENT_ID must be set in environment
```

**Causes:**
- `.env` file not created
- `.env` file in wrong location
- Environment variable name typo

**Solutions:**
1. Create `.env` file:
   - Create `.env` in project root directory
   - Copy template from documentation

2. Verify file location:
   - `.env` should be in same directory as `pyproject.toml`
   - Check current working directory

3. Check variable names:
   - Must match exactly: `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`
   - Case-sensitive, no spaces

### "Module Not Found" Error

**Error Message:**
```
ModuleNotFoundError: No module named 'copilot_directline'
```

**Causes:**
- Dependencies not installed
- Wrong Python environment
- Package not in path

**Solutions:**
1. Install dependencies:
   ```bash
   uv sync
   ```

2. Verify Python environment:
   ```bash
   which python
   python --version  # Should be 3.9+
   ```

3. Install in development mode:
   ```bash
   uv pip install -e .
   ```

## Runtime Errors

### "Connection Timeout" Error

**Error Message:**
```
requests.exceptions.Timeout: Connection timed out
```

**Causes:**
- Network connectivity issues
- Firewall blocking requests
- Service unavailable

**Solutions:**
1. Check network connection:
   - Verify internet connectivity
   - Test with `ping` or `curl`

2. Check firewall/proxy:
   - Ensure firewall allows outbound HTTPS
   - Configure proxy if needed

3. Verify service status:
   - Check Microsoft service status
   - Try again later if service is down

### "SSL Certificate Verification Failed"

**Error Message:**
```
requests.exceptions.SSLError: Certificate verification failed
```

**Causes:**
- Corporate proxy/firewall
- System time incorrect
- Certificate chain issues

**Solutions:**
1. Check system time:
   - Ensure system clock is synchronized
   - SSL certificates are time-sensitive

2. Corporate environments:
   - May need to install corporate root certificates
   - Contact IT for assistance

3. Verify certificates:
   ```bash
   openssl s_client -connect directline.botframework.com:443
   ```

## Performance Issues

### Slow Authentication

**Symptoms:**
- Authentication takes 30+ seconds
- Browser opens slowly

**Solutions:**
1. Check network latency:
   - Test connection to `login.microsoftonline.com`
   - Consider network optimization

2. Clear MSAL cache:
   ```python
   auth.remove_account(account)
   ```

3. Use token caching:
   - MSAL caches tokens automatically
   - Subsequent authentications should be faster

### Slow Message Delivery

**Symptoms:**
- Messages take long to send/receive
- Bot responses delayed

**Solutions:**
1. Check Direct Line endpoint:
   - Use regional endpoint closest to you
   - Europe: `https://europe.directline.botframework.com`

2. Optimize polling:
   - Don't poll too frequently
   - Use watermark for incremental updates

3. Check bot performance:
   - Verify Copilot Studio agent is responsive
   - Check agent's processing time

## Debugging Tips

### Enable Debug Logging

Set `LOG_LEVEL=DEBUG` in `.env` file:
```env
LOG_LEVEL=DEBUG
```

This will show detailed logs including:
- HTTP requests and responses
- Token acquisition details
- API call parameters

### Test Individual Components

1. **Test authentication only:**
   ```python
   from copilot_directline import EntraIDAuth
   auth = EntraIDAuth.from_env()
   token = auth.acquire_token_interactive()
   print(f"Token acquired: {bool(token.get('access_token'))}")
   ```

2. **Test Direct Line connection:**
   ```python
   from copilot_directline import DirectLineClient
   client = DirectLineClient.from_env()
   conversation = client.start_conversation()
   print(f"Conversation started: {conversation.conversation_id}")
   ```

3. **Test message sending:**
   ```python
   result = client.send_message(conversation.conversation_id, "test", conversation.token)
   print(f"Message sent: {result.get('id')}")
   ```

### Check Logs

Logs are written to `logs/copilot_directline.log` by default. Review logs for:
- Error messages
- HTTP status codes
- Request/response details

### Verify Configuration

Use this script to verify all configuration:
```python
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    "ENTRA_TENANT_ID",
    "ENTRA_CLIENT_ID",
    "DIRECT_LINE_SECRET"
]

print("Configuration Check:")
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {'*' * min(len(value), 20)}")
    else:
        print(f"❌ {var}: NOT SET")
```

## Getting Help

If you're still experiencing issues:

1. **Check documentation:**
   - [API Reference](api-reference.md)
   - [Authentication Guide](authentication.md)
   - [Azure Setup](azure-setup.md)

2. **Review logs:**
   - Enable debug logging
   - Check `logs/copilot_directline.log`

3. **Verify Azure configuration:**
   - App registration settings
   - API permissions
   - Copilot Studio channel configuration

4. **Test with minimal example:**
   - Use `docs/examples/simple_chat.py`
   - Isolate the issue

5. **Contact support:**
   - Provide error messages
   - Include relevant log excerpts
   - Describe steps to reproduce
