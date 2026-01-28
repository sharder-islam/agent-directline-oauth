# Unblock Manual Authentication and Direct Line in a Developer Environment (DLP)

If manual authentication or Direct Line is blocked by a Data Loss Prevention (DLP) policy in your developer environment, follow these steps in the **Power Platform admin center**.

## Prerequisites

- You need **Power Platform admin** (tenant admin) or **Environment admin** for the developer environment.
- If you don’t have access, ask your Power Platform or M365 admin to apply these changes.

## Step 1: Open Power Platform admin center

1. Go to **[Power Platform admin center](https://admin.powerplatform.microsoft.com/)**.
2. Sign in with an account that has admin rights (tenant admin or environment admin for your dev environment).

## Step 2: Open Data policies

1. In the left sidebar, select **Security**.
2. Select **Data and privacy**.
3. Open **Data policy** (or **Data policies**).
4. You’ll see the list of data policies in the tenant.

## Step 3: Find the policy that applies to your developer environment

- Check which policies include your **developer environment** in their scope (e.g. “Add multiple environments” or “Exclude certain environments”).
- Click the policy that applies to your developer environment so you can edit it.

If no policy includes your dev environment, that environment uses default connector behavior (often “Non-business”); in that case, manual auth/blocking is usually controlled at the Copilot Studio app level, not DLP.

## Step 4: Edit the policy and adjust connectors

1. Open the policy, then choose **Edit policy** (or equivalent).
2. Go through the wizard until you reach the **Connectors** (or “Assign connectors”) step.
3. Use the search box to find these Copilot Studio–related connectors and set them as follows.

### For manual authentication + Direct Line

| Goal | Connector name in admin center | Action |
|------|----------------------------------------|--------|
| Require authentication (so “Authenticate manually” is allowed) | **Chat without Microsoft Entra ID authentication in Copilot Studio** | **Block** (so only “Authenticate with Microsoft” or “Authenticate manually” can be used). |
| Allow Direct Line (Demo website, custom apps, mobile, Direct Line API) | **Direct Line channels in Copilot Studio** | **Do not block** – leave in **Business** or **Non-business**. If it’s **Blocked**, move it to Business or Non-business. |

### Important

- If **Direct Line channels in Copilot Studio** is **Blocked**, the agent cannot use Direct Line (including the Direct Line API). Unblock it for your developer environment.
- If **Chat without Microsoft Entra ID authentication in Copilot Studio** is **not** blocked, makers can choose “No authentication.” Blocking it forces “Authenticate with Microsoft” or “Authenticate manually,” which is what you want for OAuth with Direct Line.
- All connectors that the agent uses (including any used by manual auth) must be in the **same data group** (e.g. all Business or all Non-business). If Direct Line is in one group and another connector in another, you can get errors; keep them in the same group.

## Step 5: Scope the policy to your developer environment only (recommended)

1. In the same policy wizard, find the step where you **add or exclude environments** (e.g. “Add an environment” / “Define scope”).
2. Either:
   - **Add only your developer environment** to this policy (so only that environment gets these rules), or  
   - **Exclude** your developer environment from a broader policy, and create a **separate** policy that applies only to the developer environment with the connector settings above.

That way you don’t change production or other environments.

## Step 6: Save and wait for propagation

1. Complete the wizard and **Save** / **Update policy**.
2. Changes can take a short time to apply. If Copilot Studio still shows errors, wait a few minutes and refresh, or try in an incognito session.

## Step 7: Confirm in Copilot Studio

1. Open **Copilot Studio** and your agent in the **developer environment**.
2. Go to **Settings** → **Security** → **Authentication**.
3. You should be able to select **Authenticate manually** and configure Entra ID (e.g. Azure AD v2 with client secrets).
4. Go to **Channels** and ensure **Direct Line**–related options (e.g. Demo website, custom websites, mobile app) are available and not showing a DLP error.
5. **Publish** the agent and test with the Direct Line API again.

## If you still can’t change to manual authentication

1. **Download the DLP error details**  
   In Copilot Studio, on the **Channels** page, if there’s an error, use **Details** → **Download** and open the Excel file. It lists which **connector** and **policy** are causing the violation.

2. **Adjust the policy**  
   In the admin center, edit the same policy and:
   - **Unblock** the connector mentioned in the report (e.g. **Direct Line channels in Copilot Studio**), or  
   - Move that connector to **Business** or **Non-business** so it’s in the same group as the rest of the agent.

3. **Ask an admin**  
   If you’re not a tenant or environment admin, send the downloaded report and this doc to your Power Platform / M365 admin and ask them to:
   - Unblock **Direct Line channels in Copilot Studio** for your developer environment, and  
   - Keep **Chat without Microsoft Entra ID authentication in Copilot Studio** blocked so manual authentication remains required.

## References

- [Configure data policies for agents (Copilot Studio)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-data-loss-prevention)
- [Troubleshoot data policy enforcement for Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-dlp-troubleshooting)
- [Data loss prevention (Power Platform)](https://learn.microsoft.com/en-us/power-platform/admin/wp-data-loss-prevention)
