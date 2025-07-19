"""Authentication service for Google APIs using aiogoogle."""

import os
import logging
import json
import asyncio
from typing import Optional
from pathlib import Path

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import UserCreds
from aiogoogle.auth.managers import Oauth2Manager

from ..commons.api.google_api_client import GoogleApiClient


class AuthService:
    """Handle Google API authentication using aiogoogle."""

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/cloud-translation",
        "https://www.googleapis.com/auth/forms",
        "https://www.googleapis.com/auth/cloud-platform",  # For Speech API
    ]

    def __init__(self, oauth_token: Optional[str] = None):
        """Initialize authentication service.

        Args:
            oauth_token: Optional OAuth token for direct authentication
        """
        self.logger = logging.getLogger(__name__)
        self.user_creds: Optional[UserCreds] = None
        self.oauth_token = oauth_token
        self.client_secret_file = os.getenv("GODRI_CLIENT_FILE")
        self.api_client: Optional[GoogleApiClient] = None
        self.token_file = os.path.expanduser("~/.godri-token.json")

        if not self.oauth_token and not self.client_secret_file:
            raise ValueError("Either oauth_token or GODRI_CLIENT_FILE environment variable is required")

        if self.client_secret_file and not os.path.exists(self.client_secret_file):
            raise FileNotFoundError(f"Client secret file not found: {self.client_secret_file}")

    async def authenticate(self, force_reauth: bool = False) -> UserCreds:
        """Authenticate user and return credentials.

        Args:
            force_reauth: Force re-authentication even if valid credentials exist

        Returns:
            aiogoogle UserCreds object
        """
        self.logger.info("Starting authentication process")

        # If we have a direct OAuth token, use it
        if self.oauth_token and not force_reauth:
            self.logger.info("Using OAuth token from headers")
            self.user_creds = UserCreds(access_token=self.oauth_token)
            self.logger.info("Authentication successful with OAuth token")
            return self.user_creds

        # Try to load existing credentials
        if not force_reauth and os.path.exists(self.token_file):
            self.logger.info("Loading existing credentials from %s", self.token_file)
            try:
                self.user_creds = await self._load_credentials()

                # Check if credentials are still valid
                if self.user_creds and not self.user_creds.expired:
                    self.logger.info("Using valid existing credentials")
                    return self.user_creds
                elif self.user_creds and self.user_creds.refresh_token:
                    self.logger.info("Refreshing expired credentials")
                    refreshed_creds = await self._refresh_credentials()
                    if refreshed_creds:
                        return refreshed_creds

            except Exception as e:
                self.logger.warning("Failed to load/refresh existing credentials: %s", str(e))

        # Perform new OAuth flow
        self.logger.info("Starting new OAuth flow")
        self.user_creds = await self._perform_oauth_flow()

        # Save credentials for future use
        await self._save_credentials()

        self.logger.info("Authentication successful")
        return self.user_creds

    async def get_api_client(self) -> GoogleApiClient:
        """Get authenticated Google API client.

        Returns:
            Initialized Google API client
        """
        if not self.user_creds:
            await self.authenticate()

        if not self.api_client:
            self.api_client = GoogleApiClient(credentials_path=self.client_secret_file, user_creds=self.user_creds)
            await self.api_client.initialize()

        return self.api_client

    async def is_authenticated(self) -> bool:
        """Check if user is currently authenticated.

        Returns:
            True if authenticated with valid credentials
        """
        if not self.user_creds:
            return False

        return not self.user_creds.expired

    async def get_user_info(self) -> Optional[dict]:
        """Get authenticated user information.

        Returns:
            User info dictionary or None if not authenticated
        """
        try:
            api_client = await self.get_api_client()
            oauth2_service = await api_client.discover_service("oauth2", "v2")

            user_info = await api_client.execute_request(oauth2_service, "userinfo.get")
            return user_info

        except Exception as e:
            self.logger.error("Failed to get user info: %s", str(e))
            return None

    async def revoke_credentials(self) -> bool:
        """Revoke current credentials and remove token file.

        Returns:
            True if successful
        """
        try:
            if self.user_creds and self.user_creds.access_token:
                # Try to revoke the token
                async with Aiogoogle(client_creds_file=self.client_secret_file) as aiogoogle:
                    await aiogoogle.oauth2.revoke(self.user_creds)

            # Remove token file
            if os.path.exists(self.token_file):
                os.remove(self.token_file)

            # Clear in-memory credentials
            self.user_creds = None
            self.api_client = None

            self.logger.info("Credentials revoked successfully")
            return True

        except Exception as e:
            self.logger.error("Failed to revoke credentials: %s", str(e))
            return False

    async def _load_credentials(self) -> Optional[UserCreds]:
        """Load credentials from token file."""
        try:
            with open(self.token_file, "r") as f:
                creds_data = json.load(f)

            return UserCreds(
                access_token=creds_data.get("access_token"),
                refresh_token=creds_data.get("refresh_token"),
                expires_at=creds_data.get("expires_at"),
                scopes=creds_data.get("scopes", self.SCOPES),
            )

        except Exception as e:
            self.logger.error("Failed to load credentials: %s", str(e))
            return None

    async def _save_credentials(self) -> bool:
        """Save credentials to token file."""
        try:
            if not self.user_creds:
                return False

            creds_data = {
                "access_token": self.user_creds.access_token,
                "refresh_token": self.user_creds.refresh_token,
                "expires_at": self.user_creds.expires_at,
                "scopes": self.user_creds.scopes or self.SCOPES,
            }

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)

            with open(self.token_file, "w") as f:
                json.dump(creds_data, f, indent=2)

            self.logger.info("Credentials saved to %s", self.token_file)
            return True

        except Exception as e:
            self.logger.error("Failed to save credentials: %s", str(e))
            return False

    async def _refresh_credentials(self) -> Optional[UserCreds]:
        """Refresh expired credentials."""
        try:
            if not self.user_creds or not self.user_creds.refresh_token:
                return None

            async with Aiogoogle(client_creds_file=self.client_secret_file) as aiogoogle:
                refreshed_creds = await aiogoogle.oauth2.refresh(self.user_creds)

            self.user_creds = refreshed_creds
            await self._save_credentials()

            self.logger.info("Credentials refreshed successfully")
            return self.user_creds

        except Exception as e:
            self.logger.error("Failed to refresh credentials: %s", str(e))
            return None

    async def _perform_oauth_flow(self) -> UserCreds:
        """Perform OAuth2 flow to get new credentials."""
        try:
            async with Aiogoogle(client_creds_file=self.client_secret_file) as aiogoogle:
                # Get authorization URL
                auth_uri = aiogoogle.oauth2.authorization_url(
                    scopes=self.SCOPES, access_type="offline", include_granted_scopes=True, prompt="consent"
                )

                print(f"\nPlease visit this URL to authorize the application:")
                print(f"{auth_uri}")

                # Get authorization code from user
                auth_code = input("\nEnter the authorization code: ").strip()

                # Exchange code for credentials
                user_creds = await aiogoogle.oauth2.build_user_creds(grant=auth_code, scopes=self.SCOPES)

                return user_creds

        except Exception as e:
            self.logger.error("OAuth flow failed: %s", str(e))
            raise

    async def get_authorization_url(self) -> str:
        """Get authorization URL for OAuth flow.

        Returns:
            Authorization URL for user to visit
        """
        try:
            async with Aiogoogle(client_creds_file=self.client_secret_file) as aiogoogle:
                auth_uri = aiogoogle.oauth2.authorization_url(
                    scopes=self.SCOPES, access_type="offline", include_granted_scopes=True, prompt="consent"
                )
                return auth_uri

        except Exception as e:
            self.logger.error("Failed to get authorization URL: %s", str(e))
            raise

    async def exchange_code_for_credentials(self, auth_code: str) -> UserCreds:
        """Exchange authorization code for credentials.

        Args:
            auth_code: Authorization code from OAuth flow

        Returns:
            User credentials
        """
        try:
            async with Aiogoogle(client_creds_file=self.client_secret_file) as aiogoogle:
                user_creds = await aiogoogle.oauth2.build_user_creds(grant=auth_code, scopes=self.SCOPES)

                self.user_creds = user_creds
                await self._save_credentials()

                return user_creds

        except Exception as e:
            self.logger.error("Failed to exchange code for credentials: %s", str(e))
            raise

    async def close(self):
        """Clean up resources."""
        if self.api_client:
            await self.api_client.close()
            self.api_client = None
