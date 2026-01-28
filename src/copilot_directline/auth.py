"""Microsoft Entra ID authentication using MSAL."""

import logging
import os
from typing import Dict, Optional

import msal

logger = logging.getLogger(__name__)


class EntraIDAuth:
    """Handles Microsoft Entra ID authentication using MSAL."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: Optional[str] = None,
        authority: Optional[str] = None,
        scopes: Optional[list] = None,
    ):
        """Initialize Entra ID authentication.

        Args:
            tenant_id: Microsoft Entra ID tenant ID
            client_id: Application (client) ID from app registration
            client_secret: Client secret (optional, for confidential client)
            authority: Authority URL (defaults to common endpoint)
            scopes: List of scopes to request (defaults to ['profile', 'openid'])
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = authority or f"https://login.microsoftonline.com/{tenant_id}"
        # For interactive flows, openid and profile are automatically included by MSAL
        # Don't explicitly request them as they're reserved scopes
        # Only specify additional scopes if needed beyond openid/profile
        # Default to empty list - MSAL will automatically include openid and profile
        self.scopes = scopes or []

        # Initialize MSAL app
        # For interactive flows, always use PublicClientApplication
        # Client secret is used for token exchange, not for app initialization in interactive flows
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
        )
        
        # Store client_secret separately for client credentials flow if needed
        self._confidential_app = None
        if client_secret:
            self._confidential_app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
            )

        logger.info(f"Initialized Entra ID auth for tenant: {tenant_id}")

    def acquire_token_interactive(
        self, account: Optional[Dict[str, any]] = None
    ) -> Dict[str, any]:
        """Acquire token using interactive browser-based flow.

        Args:
            account: Optional account to use for silent token acquisition first

        Returns:
            Dictionary containing access token and metadata

        Raises:
            Exception: If token acquisition fails
        """
        # For interactive flows, use empty scopes list - MSAL automatically includes
        # openid, profile, and email. Only specify additional scopes if needed.
        interactive_scopes = self.scopes if self.scopes else []
        
        # Try silent token acquisition first if account is provided
        if account:
            result = self.app.acquire_token_silent(
                scopes=interactive_scopes, account=account
            )
            if result and "access_token" in result:
                logger.info("Acquired token silently")
                return result

        # Interactive flow - opens browser
        logger.info("Starting interactive authentication flow")
        result = self.app.acquire_token_interactive(scopes=interactive_scopes)

        if "error" in result:
            error_msg = result.get("error_description", result.get("error"))
            logger.error(f"Token acquisition failed: {error_msg}")
            raise Exception(f"Failed to acquire token: {error_msg}")

        logger.info("Successfully acquired token via interactive flow")
        return result

    def acquire_token_for_client(self) -> Dict[str, any]:
        """Acquire token using client credentials flow (service-to-service).

        Returns:
            Dictionary containing access token and metadata

        Raises:
            Exception: If token acquisition fails or client secret not provided
        """
        if not self._confidential_app:
            raise ValueError(
                "Client secret required for client credentials flow. "
                "Use acquire_token_interactive() for user authentication."
            )

        logger.info("Acquiring token using client credentials flow")
        # For client credentials flow, use .default scope or specific scopes
        client_scopes = self.scopes if self.scopes else [f"{self.client_id}/.default"]
        result = self._confidential_app.acquire_token_for_client(scopes=client_scopes)

        if "error" in result:
            error_msg = result.get("error_description", result.get("error"))
            logger.error(f"Token acquisition failed: {error_msg}")
            raise Exception(f"Failed to acquire token: {error_msg}")

        logger.info("Successfully acquired token via client credentials flow")
        return result

    def get_accounts(self) -> list:
        """Get all cached accounts.

        Returns:
            List of account objects
        """
        return self.app.get_accounts()

    def remove_account(self, account: Dict[str, any]) -> None:
        """Remove an account from the cache.

        Args:
            account: Account to remove
        """
        self.app.remove_account(account)
        logger.info(f"Removed account: {account.get('username', 'unknown')}")

    @classmethod
    def from_env(cls) -> "EntraIDAuth":
        """Create EntraIDAuth instance from environment variables.

        Reads:
            ENTRA_TENANT_ID: Tenant ID
            ENTRA_CLIENT_ID: Client ID
            ENTRA_CLIENT_SECRET: Client secret (optional)

        Returns:
            EntraIDAuth instance
        """
        tenant_id = os.getenv("ENTRA_TENANT_ID")
        client_id = os.getenv("ENTRA_CLIENT_ID")
        client_secret = os.getenv("ENTRA_CLIENT_SECRET")

        if not tenant_id or not client_id:
            raise ValueError(
                "ENTRA_TENANT_ID and ENTRA_CLIENT_ID must be set in environment"
            )

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
