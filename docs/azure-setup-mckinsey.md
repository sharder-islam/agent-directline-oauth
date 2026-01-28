# Azure App Registration via Platform McKinsey

This guide walks you through creating an Azure/Entra app registration **McKinsey’s way**—using Platform McKinsey to provision the app, then configuring API permissions and redirect URLs so you can use the app with Direct Line and this CLI. The detailed steps below are taken from McKinsey’s official internal guides; follow those guides as the source of truth.

**Tenant:** This guide applies only to the **mckinsey.com** tenant. All App Registrations created through Platform McKinsey are registered under the mckinsey.com tenant.

**Official internal guides (source of the steps in this doc):**
- **[How to create an Azure App Registration?](https://platform.mckinsey.com/knowledge-base/service-guide/851773088/how-to-create-an-azure-app-registration-)** – Creating the app and getting credentials
- **[How to request MSGraph permissions for App Registration](https://platform.mckinsey.com/knowledge-base/service-guide/1560346639/how-to-request-msgraph-permissions-for-app-registration)** – Adding API permissions and granting admin consent for mckinsey.com

---

## Table of contents

Use the links below to jump to a section.

- [Prerequisites](#prerequisites)
- [Step 1: Create or use a workspace](#step-1-create-or-use-a-workspace)
- [Step 2: Request the Azure App Registration service](#step-2-request-the-azure-app-registration-service)
- [Step 3: Get Client ID and Tenant ID](#step-3-get-client-id-and-tenant-id)
- [Step 4: Generate client secret (Credentials)](#step-4-generate-client-secret-credentials)
- [Step 5: API permissions and redirect URLs](#step-5-api-permissions-and-redirect-urls)
  - [Prerequisites (Step 5)](#prerequisites-from-the-official-guide)
  - [Add API permissions](#add-api-permissions-from-the-official-guide)
  - [Redirect URIs and authentication](#redirect-uris-and-authentication-for-direct-line-and-this-cli)
  - [Client secret expiration](#client-secret-expiration-from-the-official-guide)
- [Step 6: Configure Copilot Studio agent](#step-6-configure-copilot-studio-agent)
- [Step 7: Configure environment variables](#step-7-configure-environment-variables)
- [Step 8: Test your configuration](#step-8-test-your-configuration)
- [Troubleshooting](#troubleshooting)
- [Rotating secrets](#rotating-secrets)
  - [Overview of the rotation process](#overview-of-the-rotation-process)
  - [How to check secret expiration](#how-to-check-secret-expiration)
  - [Required information for secret rotation](#required-information-for-secret-rotation)
  - [How to submit a secret rotation request](#how-to-submit-a-secret-rotation-request-mckinseycom)
  - [Best practices](#best-practices)
- [Next steps](#next-steps)

---

## Prerequisites

- A **project** or **product workspace** in Platform McKinsey (required before adding the Azure App Registration service). If you don’t have one:
  - [Create a Product Workspace](https://platform.mckinsey.com/knowledge-base/portal-user-guide/KO100384/create-a-product-workspace)
  - [Set up and manage Project Workspace](https://platform.mckinsey.com/knowledge-base/portal-user-guide/KO83431/set-up-and-manage-project-workspace)
- Access to Copilot Studio with permissions to configure channels and authentication
- A published Copilot Studio agent

---

## Step 1: Create or use a workspace

Per the official guide **[How to create an Azure App Registration?](https://platform.mckinsey.com/knowledge-base/service-guide/851773088/how-to-create-an-azure-app-registration-)**:

You must have a project or product workspace in Platform McKinsey before you can add the Azure App Registration service.

1. Go to [Platform McKinsey](https://platform.mckinsey.com).
2. Create or use a workspace:
   - [Create a Product Workspace](https://platform.mckinsey.com/knowledge-base/portal-user-guide/KO100384/create-a-product-workspace)
   - [Set up and manage Project Workspace](https://platform.mckinsey.com/knowledge-base/portal-user-guide/KO83431/set-up-and-manage-project-workspace)

---

## Step 2: Request the Azure App Registration service

Follow the official guide **[How to create an Azure App Registration?](https://platform.mckinsey.com/knowledge-base/service-guide/851773088/how-to-create-an-azure-app-registration-)**:

1. In Platform McKinsey, search for **“Azure App Registration”** in the service catalog (or use [Add Azure App Registration service](https://platform.mckinsey.com/workspace/no-team/create-service/fb68694a-357e-4209-9cb4-27d36bf0d76a)).
2. Click **Add to workspace** to open the **Request Service** form.
3. Fill out the form as described in the guide:
   - **I am requesting for:** Choose “I am requesting for myself”, “I am requesting for a client team”, or “I am requesting for a team within McKinsey”.
   - **Configure App Registration:**  
     - What type of App Registration do you need? **I need a new App Registration** (or update existing if applicable).  
     - **App Name** (max 50 characters).  
     - **Environments:** **Production**.  
     - **Azure Tenant:** **McKinsey.com**.  
     - **Region:** Select the appropriate region.
   - **Details:** Your Project / Product Workspace, Contact email address, Description of the Application, Justification for the request, Expected Go-Live date, Notes (as required by the form).
4. Click **Save** to submit the request.

The official guide notes: **A new App Registration can take several hours to provision. You will receive an email once it is ready.**

---

## Step 3: Get Client ID and Tenant ID

Per the official guide **[How to create an Azure App Registration?](https://platform.mckinsey.com/knowledge-base/service-guide/851773088/how-to-create-an-azure-app-registration-)**:

1. After the service is provisioned, you will receive an **email** at the contact address you provided (provisioning can take several hours).
2. The email contains your **App ID** (Client ID) and **Tenant ID**.
3. You can also find these in your workspace: in the **App Registration** section you’ll see **App ID**, **Application Name**, **App Registration Name**, and **Tenant ID**.
4. Save both **App ID** and **Tenant ID** securely; you’ll need them for your `.env` file, Copilot Studio (Step 6), and for requesting API permissions (Step 5).

---

## Step 4: Generate client secret (Credentials)

Per the official guide **[How to create an Azure App Registration?](https://platform.mckinsey.com/knowledge-base/service-guide/851773088/how-to-create-an-azure-app-registration-)**:

1. In your Platform McKinsey workspace, open the **Azure App Registration** service you added.
2. In the **App Registration** section, click **Credentials**.
3. In the expanded **Credentials** area, use **Add Client Secret** (or, if the platform shows a PowerShell or Bash script in a pop-up, run that script to generate a secret).
4. **Copy and store the client secret value immediately**—it is shown only once. Use it in your `.env` file as `ENTRA_CLIENT_SECRET`.

---

## Step 5: API permissions and redirect URLs

Follow the official guide **[How to request MSGraph permissions for App Registration](https://platform.mckinsey.com/knowledge-base/service-guide/1560346639/how-to-request-msgraph-permissions-for-app-registration)** for the process in the mckinsey.com tenant. The steps below are from that guide, with Direct Line–specific values called out where needed.

### Prerequisites (from the official guide)

- You need an App Registration (you have this from Steps 1–4).
- You need the **Object ID**, **Name**, and **App ID** (Client ID) of your App Registration (from your workspace / Step 3).
- The person who adds permissions or grants admin consent must be **Owner** or **Contributor** on the App Registration.

**To assign Owner or Contributor:** In the Azure portal, open your App Registration → **Access control (IAM)** → **Add role assignment** → select **Owner** or **Contributor** → search for and select the user → **Review + assign**.

### Add API permissions (from the official guide)

1. Open your App Registration in the **Azure portal**.
2. Go to **API permissions** in the left sidebar.
3. Click **Add a permission**.
4. Select **Microsoft APIs** → **Microsoft Graph**.
5. For **Direct Line and this CLI**, you need **Delegated permissions** for user sign-in: under **OpenId permissions** select **openid** and **profile**. Click **Add permissions**.
6. **Grant admin consent for mckinsey.com:** After adding permissions, you **must** click **Grant admin consent for mckinsey.com** (as described in the official guide). This grants consent for the mckinsey.com tenant so users don’t see consent prompts.

The official guide also describes **Application permissions** for other MSGraph scenarios (e.g. User.Read.All, Group.Read.All); use that guide if you need those.

### Redirect URIs and authentication (for Direct Line and this CLI)

For Direct Line and the CLI to work, the same App Registration must have these settings in the Azure portal (these are standard Bot Framework / Entra requirements, not in the MSGraph permissions guide):

- **Authentication** → **Advanced settings** → **Allow public client flows** → **Yes** → Save.
- **Authentication** → **Add a platform** → **Web:**  
  Redirect URIs: `https://token.botframework.com/.auth/web/redirect` and (if Europe) `https://europe.token.botframework.com/.auth/web/redirect`.  
  Implicit grant: **Access tokens** and **ID tokens** → Configure.
- **Authentication** → **Add a platform** → **Mobile and desktop applications:**  
  Redirect URI: `http://localhost` → Configure.

Operations (Ops) or an Azure/Entra tenant admin for mckinsey.com can perform these steps if you don’t have access.

### Client secret expiration (from the official guide)

Per the official guide **[How to request MSGraph permissions for App Registration](https://platform.mckinsey.com/knowledge-base/service-guide/1560346639/how-to-request-msgraph-permissions-for-app-registration)**:

Client secrets for App Registrations in the mckinsey.com tenant typically expire after about 1 year. Renew them to avoid service outages.

- **Check expiration:** App Registration → **Certificates & secrets** → check the expiration date.
- **Renew:** **Certificates & secrets** → **New client secret** → add description and expiration (e.g. 24 months) → **Add** → copy the new secret value immediately and update your application (e.g. `.env`).

---

## Step 6: Configure Copilot Studio agent

Same as the standard [Azure setup guide](azure-setup.md):

1. **Get Direct Line secret:** [Copilot Studio](https://web.powerva.microsoft.com/) → your agent → **Settings** → **Security** → **Web channel security** → enable if needed, copy one Direct Line secret → use as `DIRECT_LINE_SECRET` in `.env`. (Optional) Enable **Require secure access**.
2. **Configure manual authentication:** **Settings** → **Security** → **Authentication** → **Authenticate manually** → **Require users to sign in** enabled → **Service provider:** Microsoft Entra ID V2 with client secrets (or federated credentials) → enter **Client ID** (from Step 3) and **Client secret** (from Step 4) → **Scopes:** `profile openid` → **Save**.
3. **Publish** the agent and test in the test panel.

---

## Step 7: Configure environment variables

Create a `.env` file in your project root:

```env
# From Step 3 (App ID and Tenant ID)
ENTRA_TENANT_ID=your-directory-tenant-id
ENTRA_CLIENT_ID=your-application-client-id

# From Step 4 (Credentials → Add Client Secret)
ENTRA_CLIENT_SECRET=your-client-secret-value

# From Step 6 (Copilot Studio – Web channel security)
DIRECT_LINE_SECRET=your-direct-line-secret

# Optional
DIRECT_LINE_ENDPOINT=https://directline.botframework.com
LOG_LEVEL=INFO
LOG_FILE=logs/copilot_directline.log
```

---

## Step 8: Test your configuration

1. **Auth:**  
   `uv run python -c "from copilot_directline import EntraIDAuth; auth = EntraIDAuth.from_env(); print('Auth configured correctly!')"`

2. **Direct Line:**  
   `uv run python -c "from copilot_directline import DirectLineClient; client = DirectLineClient.from_env(); print('Direct Line configured correctly!')"`

3. **CLI:**  
   `uv run python -m src.cli.main --message "Hello"`

---

## Troubleshooting

See the main guide: [azure-setup.md#troubleshooting](azure-setup.md#troubleshooting). In addition:

- **No email with App ID / Tenant ID:** Provisioning can take several hours. Check spam; confirm Production and McKinsey.com were selected. You can also find App ID and Tenant ID in the workspace under **App Registration**. Follow the [official guide for creating an Azure App Registration](https://platform.mckinsey.com/knowledge-base/service-guide/851773088/how-to-create-an-azure-app-registration-) if needed.
- **Credentials / Add Client Secret:** Ensure you’re in the correct workspace and have opened **Credentials** for your Azure App Registration. See the [official guide](https://platform.mckinsey.com/knowledge-base/service-guide/851773088/how-to-create-an-azure-app-registration-) for the full flow.
- **Redirect or permission errors:** Confirm redirect URIs, public client flows, Delegated permissions (openid, profile), and **Grant admin consent for mckinsey.com** were applied. Follow the [official guide for MSGraph permissions](https://platform.mckinsey.com/knowledge-base/service-guide/1560346639/how-to-request-msgraph-permissions-for-app-registration).

**Need help? (mckinsey.com tenant)**  
For McKinsey internal users: submit a ticket, request a callback, or contact **servicedesk@mckinsey.com** for Platform McKinsey and Azure App Registration support.

---

## Rotating secrets

Client secrets for App Registrations in the mckinsey.com tenant typically expire (e.g. after about 1 year). Use this section when you need to **replace an expired client secret**, **proactively rotate a secret** nearing expiration, or **submit a request to the OPS support team** for secret rotation.

### Overview of the rotation process

1. Identify the application requiring secret rotation.
2. Generate a new client secret in the Azure portal (or submit a request to OPS—see below).
3. Update dependent services, scripts, and integrations with the new secret (e.g. your `.env` file and any apps using `ENTRA_CLIENT_SECRET`).
4. Test and validate the application’s functionality.
5. Remove the expired secret from the application registration (only after the new secret is active everywhere).

### How to check secret expiration

- **Azure Portal** → **Entra** → **App registrations** → [Your App] → **Certificates & secrets**.
- Check the **Expires** column under **Client secrets**.

### Required information for secret rotation

| Field | Required |
|-------|----------|
| **Application Name** | Yes |
| **Application ID** (Client ID GUID) | Yes |
| **Expired Secret Name** (description of the expired secret) | Yes |
| **New Secret Expiration** | Yes (e.g. 90 days as required by policy) |
| **Requestor Info** (your name and contact email) | Yes |

**Finding your app details:** Entra → App registrations → [Your Application] → **Overview** (App Name and App ID are shown there).

### How to submit a secret rotation request (mckinsey.com)

Submit your request via email or Slack to the OPS support team. Include:

- **Subject:** Secret Rotation Request for Azure Application
- **Application Name:** &lt;App Name&gt;
- **Application ID:** &lt;Client ID GUID&gt;
- **Expired Secret Name:** &lt;Secret Name&gt;
- **New Secret Expiration:** 90 days (or as required)
- **Reason:** Secret expired, rotation required to restore functionality. (Or: Proactive rotation before expiration.)
- **Requested By:** &lt;Your name&gt;, &lt;your.email@mckinsey.com&gt;

**Need help? (mckinsey.com tenant)**  
- **MCS Wintel:** **wintel-ops@mckinsey.com**, Slack **#mcs-wintel-spoc**
- **IAM Directory Services:** **IAM-Directory_Services@mckinsey.com**

### Best practices

- Do **not** delete the expired secret before the new secret is active in all systems.
- Use Azure Key Vault for secure storage of secrets when possible.
- Document all systems and integrations that use the secret to reduce disruption during rotation.

All secret rotations are logged for compliance and audit. Ensure requests are clear and complete, and test the application after rotation.

---

[↑ Back to top](#azure-app-registration-via-platform-mckinsey)

---

## Next steps

- [authentication.md](authentication.md) – Authentication flows
- [api-reference.md](api-reference.md) – API usage
- [examples.md](examples.md) – Code examples
- [azure-setup.md](azure-setup.md) – Standard Azure Portal setup (non–Platform McKinsey)
