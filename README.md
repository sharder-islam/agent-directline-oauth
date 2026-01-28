# Copilot Studio Direct Line OAuth

A secure Python solution for accessing Copilot Studio agents via Direct Line API with Microsoft Entra ID (Azure AD) OAuth authentication. This library supports both command-line tools and web applications with interactive browser-based SSO.

## Features

- 🔐 **Secure Authentication**: Microsoft Entra ID OAuth integration with interactive SSO
- 💬 **Direct Line API**: Full support for Direct Line API 3.0
- 🖥️ **CLI Tool**: Interactive command-line interface for testing and automation
- 🌐 **Web Application**: Flask-based web app example for integration
- 📝 **Comprehensive Logging**: Configurable logging to files and console
- 🛡️ **Enhanced Security**: Support for enhanced authentication and user ID validation

## Quick Start

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Microsoft Entra ID app registration
- Copilot Studio agent (Direct Line secrets available in Settings > Security)
- Direct Line secret from Copilot Studio

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd agent-directline-oauth
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   
   Create a `.env` file in the project root with your credentials:
   ```env
   ENTRA_TENANT_ID=your-tenant-id
   ENTRA_CLIENT_ID=your-client-id
   ENTRA_CLIENT_SECRET=your-client-secret
   DIRECT_LINE_SECRET=your-direct-line-secret
   ```

   See [docs/azure-setup.md](docs/azure-setup.md) for detailed Azure configuration instructions.

### Basic Usage

#### CLI Tool

Start an interactive chat session:
```bash
uv run python -m src.cli.main
```

Send a single message:
```bash
uv run python -m src.cli.main --message "Hello, agent!"
```

Continue an existing conversation:
```bash
uv run python -m src.cli.main --conversation-id "abc123" --message "Follow up question"
```

#### Python Library

```python
from copilot_directline import DirectLineClient, EntraIDAuth

# Authenticate user
auth = EntraIDAuth.from_env()
token_result = auth.acquire_token_interactive()
user_token = token_result.get("access_token")

# Create Direct Line client
client = DirectLineClient.from_env()

# Start conversation
conversation = client.start_conversation(user_token=user_token)

# Send message
client.send_message(conversation.conversation_id, "Hello!", conversation.token)

# Get activities
activities = client.get_activities(conversation.conversation_id, token=conversation.token)
for activity in activities.activities:
    if activity.type == "message":
        print(f"Bot: {activity.text}")
```

#### Web Application

Run the Flask web application example:
```bash
uv run python docs/examples/web_app.py
```

Then open your browser to `http://localhost:5000` to access the chat interface.

## Project Structure

```
agent-directline-oauth/
├── src/                    # Source code
│   ├── copilot_directline/ # Core library
│   │   ├── auth.py        # Entra ID OAuth authentication
│   │   ├── directline.py  # Direct Line API client
│   │   └── models.py      # Data models
│   └── cli/               # Command-line tool
│       └── main.py        # CLI entry point
├── docs/                   # Comprehensive documentation
│   ├── examples/          # Example applications
│   │   ├── simple_chat.py
│   │   └── web_app.py
│   ├── azure-setup.md
│   ├── api-reference.md
│   ├── authentication.md
│   ├── troubleshooting.md
│   └── examples.md
├── logs/                   # Application logs
└── output/                 # Generated artifacts
```

## Documentation

- **[Azure Setup Guide](docs/azure-setup.md)**: Step-by-step instructions for configuring Azure Portal, app registration, and Copilot Studio
- **[API Reference](docs/api-reference.md)**: Complete API documentation for the library
- **[Authentication Deep-Dive](docs/authentication.md)**: Detailed explanation of authentication flows and security
- **[Troubleshooting](docs/troubleshooting.md)**: Common issues and solutions
- **[Extended Examples](docs/examples.md)**: More usage examples and scenarios

## Configuration

All configuration is done via environment variables in the `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `ENTRA_TENANT_ID` | Microsoft Entra ID tenant ID | Yes |
| `ENTRA_CLIENT_ID` | App registration client ID | Yes |
| `ENTRA_CLIENT_SECRET` | Client secret (for confidential clients) | Optional |
| `DIRECT_LINE_SECRET` | Direct Line secret (from Settings > Security > Web channel security) | Yes |
| `DIRECT_LINE_ENDPOINT` | Direct Line API endpoint | No (defaults to standard) |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (defaults to INFO) |
| `LOG_FILE` | Log file path | No (defaults to `logs/copilot_directline.log`) |

## Security Considerations

1. **Never commit `.env` file**: The `.env` file contains sensitive credentials and is excluded from version control
2. **Token Management**: Direct Line tokens expire after 30 minutes and should be refreshed before expiration
3. **User ID Security**: Use unguessable user IDs (prefixed with `dl_` for enhanced authentication)
4. **Enhanced Authentication**: Enable enhanced authentication in Direct Line settings for production use

For more details, see [docs/authentication.md](docs/authentication.md).

## Examples

See the `docs/examples/` directory for:
- `simple_chat.py`: Basic usage example
- `web_app.py`: Flask web application with OAuth

For more examples, see [docs/examples.md](docs/examples.md).

## Troubleshooting

Common issues and solutions are documented in [docs/troubleshooting.md](docs/troubleshooting.md).

## License

This project is provided as-is for internal use.

## Support

For issues, questions, or contributions, please refer to the troubleshooting guide or contact your development team.
