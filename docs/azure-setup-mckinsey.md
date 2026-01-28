# Azure App Registration via Platform McKinsey

This guide walks you through creating an Azure/Entra app registration **McKinsey’s way**—using Platform McKinsey to provision the app, then having Operations or an Entra tenant admin complete the required Azure configuration. The rest (Copilot Studio, env vars, testing) matches the standard [Azure setup guide](azure-setup.md).

## Prerequisites

- Access to [Platform McKinsey](https://platform.mckinsey.com) with ability to create or use a project/product workspace
- Access to Copilot Studio with permissions to configure channels and authentication
- A published Copilot Studio agent
- For the Azure configuration step: Operations support or Azure/Entra tenant admin (mckinsey.com tenant)

---

## Step 1: Create or Use a Workspace on Platform McKinsey

1. Go to **[Platform McKinsey](https://platform.mckinsey.com)**.
2. Create a **project** or **product workspace** if you don’t already have one.
3. Use that workspace for the Azure App Registration service in the next step.

---

## Step 2: Add Azure App Registration Service to Your Workspace

1. In your workspace, search for **“Azure App Registration”** (or use the direct link: [Add Azure App Registration service](https://platform.mckinsey.com/workspace/no-team/create-service/fb68694a-357e-4209-9cb4-27d36bf0d76a)).
2. Add the **Azure App Registration** service to your workspace.
3. When filling out the form:
   - **Environment**: select **Prod**.
   - **Azure tenant**: select **mckinsey.com**.
4. Submit the form.

---

## Step 3: Get Client ID and Tenant ID from Email

1. After the service is added, you’ll receive an **email** (typically within a few minutes) with:
   - **Client ID** (Application ID)
   - **Tenant ID** (Directory ID)
2. **Save both values** securely; you’ll need them for:
   - Your `.env` file
   - Copilot Studio authentication (Step 6)
   - The consolidated Azure configuration (Step 5) if you’re providing them to Operations/admin

---

## Step 4: Generate Client Secret via Platform McKinsey

1. In your **Platform McKinsey workspace**, find the **Azure App Registration** service you added.
2. **Expand** the Azure App Registration section.
3. Click the **Credentials** button.
4. A new window opens with a **PowerShell** and/or **Bash** script to generate a client secret.
5. Run the script in your environment (PowerShell or Bash as appropriate).
6. **Copy and store the client secret value** immediately—it is shown only once. Use it in your `.env` file as `ENTRA_CLIENT_SECRET`.

---

## Step 5: Azure/Entra App Registration Configuration (Operations or Tenant Admin)

Have **Operations** or an **Azure/Entra tenant admin** (mckinsey.com tenant) apply the following configuration to your app registration. This consolidates all Azure-side settings in one place for easy reference.

**App registration**: Use the **Client ID** (and tenant) from the email in Step 3. The app should already exist in Entra from the Platform McKinsey provisioning.

### 5.1 Authentication – Allow Public Client Flows

- In the app registration: **Manage** → **Authentication**.
- **Advanced settings** → **Allow public client flows** → set to **Yes**.
- **Save**.

This allows interactive (device-code) auth without admin consent for basic OpenID scopes.

### 5.2 Authentication – Redirect URIs and Token Settings

**Web (Bot Framework):**

- **Authentication** → **Add a platform** → **Web**.
- **Redirect URIs**, add:
  - `https://token.botframework.com/.auth/web/redirect` (standard regions)
  - `https://europe.token.botframework.com/.auth/web/redirect` (Europe region)
- **Implicit grant and hybrid flows**:
  - ✅ **Access tokens (used for implicit flows)**
  - ✅ **ID tokens (used for implicit and hybrid flows)**
- **Configure**.

**Mobile and desktop (Public client – for CLI/local apps):**

- **Authentication** → **Add a platform** → **Mobile and desktop applications**.
- **Redirect URIs**, add:
  - `http://localhost` (covers dynamic ports such as `http://localhost:63100` used by MSAL)
- **Configure**.

### 5.3 API Permissions

- **Manage** → **API permissions** → **Add a permission**.
- Choose **Microsoft Graph** → **Delegated permissions**.
- Under **OpenId permissions**:
  - ✅ `openid`
  - ✅ `profile`
- **Add permissions**.
- (Recommended) **Grant admin consent for [McKinsey Tenant]** so users don’t see consent prompts.

### 5.4 Summary Checklist for Admin

| Item | Value / Action |
|------|----------------|
| **Tenant** | mckinsey.com (prod) |
| **Public client flows** | Yes |
| **Web redirect URIs** | `https://token.botframework.com/.auth/web/redirect`, `https://europe.token.botframework.com/.auth/web/redirect` |
| **Web implicit/hybrid** | Access tokens + ID tokens |
| **Mobile/desktop redirect URI** | `http://localhost` |
| **API permissions (Delegated)** | Microsoft Graph: `openid`, `profile` |
| **Admin consent** | Recommended for Microsoft Graph (openid, profile) |

After this step, the app registration is ready for use with Direct Line and the CLI.

---

## Step 6: Configure Copilot Studio Agent

Same as the standard guide:

1. **Get Direct Line secret**
   - [Copilot Studio](https://web.powerva.microsoft.com/) → your agent → **Settings** → **Security** → **Web channel security**.
   - Enable web channel security if needed, copy one of the Direct Line secrets → use as `DIRECT_LINE_SECRET` in `.env`.
   - (Optional) Enable **Require secure access** for token-based access.

2. **Configure manual authentication**
   - **Settings** → **Security** → **Authentication** → **Authenticate manually**.
   - **Require users to sign in**: enabled.
   - **Service provider**: **Microsoft Entra ID V2 with client secrets** (or federated credentials if you use that).
   - **Client ID**: from Step 3.
   - **Client secret**: from Step 4 (if using client secrets).
   - **Scopes**: `profile openid`.
   - **Save**.

3. **Publish** the agent and test in the test panel.

---

## Step 7: Configure Environment Variables

Create a `.env` file in your project root:

```env
# From Step 3 (Platform McKinsey email)
ENTRA_TENANT_ID=your-directory-tenant-id
ENTRA_CLIENT_ID=your-application-client-id

# From Step 4 (credentials script)
ENTRA_CLIENT_SECRET=your-client-secret-value

# From Step 6 (Copilot Studio – Web channel security)
DIRECT_LINE_SECRET=your-direct-line-secret

# Optional
DIRECT_LINE_ENDPOINT=https://directline.botframework.com
LOG_LEVEL=INFO
LOG_FILE=logs/copilot_directline.log
```

---

## Step 8: Test Your Configuration

1. **Auth**
   ```bash
   uv run python -c "from copilot_directline import EntraIDAuth; auth = EntraIDAuth.from_env(); print('Auth configured correctly!')"
   ```

2. **Direct Line**
   ```bash
   uv run python -c "from copilot_directline import DirectLineClient; client = DirectLineClient.from_env(); print('Direct Line configured correctly!')"
   ```

3. **CLI**
   ```bash
   uv run python -m src.cli.main --message "Hello"
   ```

---

## Troubleshooting

Use the same troubleshooting section as the main guide: [azure-setup.md#troubleshooting](azure-setup.md#troubleshooting). In addition:

- **No email with Client ID / Tenant ID**: Check spam; allow a few minutes; confirm the Azure App Registration service was added with **Prod** and **mckinsey.com** tenant. If still missing, contact Platform McKinsey or your workspace admin.
- **Credentials button / script**: Ensure you’re in the correct workspace and have expanded the Azure App Registration service. If the button or script is missing, contact Platform McKinsey support.
- **Redirect or permission errors**: Verify with Operations/admin that Step 5 was applied exactly (redirect URIs, public client flows, Graph delegated permissions, admin consent).

---

## Next Steps

- [authentication.md](authentication.md) – Authentication flows
- [api-reference.md](api-reference.md) – API usage
- [examples.md](examples.md) – Code examples
- [azure-setup.md](azure-setup.md) – Standard Azure Portal setup (non–Platform McKinsey)
