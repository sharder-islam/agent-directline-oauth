# Azure Portal Setup Guide

This guide walks you through configuring Microsoft Entra ID and Copilot Studio for secure authentication with Direct Line API.

## Prerequisites

- Access to Azure Portal with permissions to create app registrations
- Access to Copilot Studio with permissions to configure channels and authentication
- A published Copilot Studio agent

## Step 1: Create App Registration in Entra ID

1. **Sign in to Azure Portal**
   - Go to [https://portal.azure.com](https://portal.azure.com)
   - Sign in with an account that has tenant administration rights

2. **Navigate to App Registrations**
   - Search for "App registrations" in the top search bar
   - Click on "App registrations" from the results

3. **Create New Registration**
   - Click "New registration"
   - Enter a name for your app registration (e.g., "CopilotStudioDirectLine")
   - Under "Supported account types", select **"Accounts in this organizational directory only (Single tenant)"**
   - Leave "Redirect URI" blank for now (we'll add it in the next step)
   - Click "Register"

4. **Copy Application Details**
   - After registration, you'll be on the Overview page
   - Copy the **Application (client) ID** - you'll need this for your `.env` file
   - Copy the **Directory (tenant) ID** - you'll also need this for your `.env` file
   - Save these values securely

## Step 2: Configure Authentication

1. **Add Redirect URI**
   - In your app registration, go to **"Authentication"** under "Manage"
   - Click **"Add a platform"**
   - Select **"Web"**
   - Under "Redirect URIs", add:
     - `https://token.botframework.com/.auth/web/redirect` (for standard regions)
     - `https://europe.token.botframework.com/.auth/web/redirect` (for Europe region)
   - Under "Implicit grant and hybrid flows", check:
     - ✅ **Access tokens (used for implicit flows)**
     - ✅ **ID tokens (used for implicit and hybrid flows)**
   - Click "Configure"

2. **Configure API Permissions**
   - Go to **"API permissions"** under "Manage"
   - Click **"Add a permission"**
   - Select **"Microsoft Graph"**
   - Select **"Delegated permissions"**
   - Expand **"OpenId permissions"** and check:
     - ✅ `openid`
     - ✅ `profile`
   - Click **"Add permissions"**
   - (Optional) Click **"Grant admin consent for [Your Tenant]"** and confirm
   - Note: Admin consent is **not required** for these basic OpenID scopes - users can consent themselves. However, granting admin consent prevents individual users from seeing consent prompts, which is recommended for organizational use.

## Step 3: Create Client Secret (Optional)

If you're using client secrets (instead of federated credentials):

1. **Generate Client Secret**
   - Go to **"Certificates & secrets"** under "Manage"
   - Click **"New client secret"**
   - Enter a description (e.g., "Direct Line OAuth")
   - Select an expiration period (recommend shortest period appropriate for your use case)
   - Click **"Add"**
   - **IMPORTANT**: Copy the secret **Value** immediately - it won't be shown again
   - Save this value securely for your `.env` file

## Step 4: Configure Copilot Studio Agent

1. **Get Direct Line Secret**
   - Go to [Copilot Studio](https://web.powerva.microsoft.com/)
   - Open your agent
   - Go to **"Settings"** → **"Security"** → **"Web channel security"**
   - Enable web channel security (if not already enabled)
   - You'll see two Direct Line secrets displayed - copy either one
   - This is your `DIRECT_LINE_SECRET` for the `.env` file
   - (Optional) Enable **"Require secure access"** to enforce token-based authentication
   - Note: Direct Line access is available by default - you don't need to enable a separate "channel"

2. **Configure Manual Authentication**
   - Go to **"Settings"** → **"Security"** → **"Authentication"**
   - Click **"Authenticate manually"**
   - Ensure **"Require users to sign in"** is enabled
   - Under **"Service provider"**, select:
     - **"Microsoft Entra ID V2 with client secrets"** (if using client secrets)
     - OR **"Microsoft Entra ID V2 with federated credentials"** (recommended)
   - Enter your **Client ID** (from Step 1)
   - If using client secrets, enter your **Client secret** (from Step 3)
   - Under **"Scopes"**, enter: `profile openid`
   - Click **"Save"**

3. **Publish Your Agent**
   - Ensure your agent is published
   - Test the agent in the test panel to verify it works

## Step 5: Configure Environment Variables

Create a `.env` file in your project root with the following values:

```env
# From Step 1
ENTRA_TENANT_ID=your-directory-tenant-id
ENTRA_CLIENT_ID=your-application-client-id

# From Step 3 (if using client secrets)
ENTRA_CLIENT_SECRET=your-client-secret-value

# From Step 3 (Settings > Security > Web channel security)
DIRECT_LINE_SECRET=your-direct-line-secret

# Optional
DIRECT_LINE_ENDPOINT=https://directline.botframework.com
LOG_LEVEL=INFO
LOG_FILE=logs/copilot_directline.log
```

## Step 6: Test Your Configuration

1. **Test Authentication**
   ```bash
   uv run python -c "from copilot_directline import EntraIDAuth; auth = EntraIDAuth.from_env(); print('Auth configured correctly!')"
   ```

2. **Test Direct Line Connection**
   ```bash
   uv run python -c "from copilot_directline import DirectLineClient; client = DirectLineClient.from_env(); print('Direct Line configured correctly!')"
   ```

3. **Run CLI Tool**
   ```bash
   uv run python -m src.cli.main --message "Hello"
   ```

## Troubleshooting

### Common Issues

1. **"Invalid client" error**
   - Verify your `ENTRA_CLIENT_ID` matches the Application (client) ID from Azure Portal
   - Check that the app registration is in the same tenant

2. **"AADSTS700016: Application not found"**
   - Verify your `ENTRA_TENANT_ID` is correct
   - Ensure the app registration exists in the specified tenant

3. **"Redirect URI mismatch"**
   - Verify the redirect URI in Azure Portal matches exactly: `https://token.botframework.com/.auth/web/redirect`
   - Check for typos or extra spaces

4. **"Insufficient privileges"**
   - Verify API permissions are configured (admin consent is optional for openid/profile scopes)
   - Verify the user has appropriate permissions in the tenant

5. **Direct Line authentication fails**
   - Verify your `DIRECT_LINE_SECRET` is correct
   - Check that web channel security is enabled in Copilot Studio (Settings > Security)
   - Ensure the agent is published
   - Verify you copied the secret correctly (no extra spaces or characters)

For more troubleshooting help, see [troubleshooting.md](troubleshooting.md).

## Next Steps

- Review [authentication.md](authentication.md) for details on authentication flows
- Check [api-reference.md](api-reference.md) for API usage examples
- See [examples.md](examples.md) for code examples
