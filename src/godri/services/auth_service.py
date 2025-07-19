"""Authentication service for Google APIs - refactored for async architecture."""

import os
import logging
import json
import asyncio
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from ..commons.api.google_api_client import GoogleApiClient


class AuthService:
    """Handle Google API authentication with async support."""

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
        self.credentials: Optional[Credentials] = None
        self.oauth_token = oauth_token
        self.client_secret_file = os.getenv("GODRI_CLIENT_FILE")
        self.api_client: Optional[GoogleApiClient] = None

        if not self.oauth_token and not self.client_secret_file:
            raise ValueError("Either oauth_token or GODRI_CLIENT_FILE environment variable is required")

        if self.client_secret_file and not os.path.exists(self.client_secret_file):
            raise FileNotFoundError(f"Client secret file not found: {self.client_secret_file}")

    async def authenticate(self) -> Credentials:
        """Authenticate user and return credentials.

        Returns:
            Google OAuth2 credentials
        """
        self.logger.info("Starting authentication process")

        if self.oauth_token:
            self.logger.info("Using OAuth token from headers")
            self.credentials = Credentials(token=self.oauth_token)
            self.logger.info("Authentication successful with OAuth token")
            return self.credentials

        token_file = os.path.expanduser("~/.godri-token.json")

        if os.path.exists(token_file):
            self.logger.info("Loading existing credentials from %s", token_file)
            self.credentials = Credentials.from_authorized_user_file(token_file, self.SCOPES)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.logger.info("Refreshing expired credentials")
                try:
                    self.credentials.refresh(Request())
                    self.logger.info("Credentials refreshed successfully")
                except Exception as e:
                    self.logger.warning("Failed to refresh credentials: %s", str(e))
                    self.credentials = None

            if not self.credentials:
                self.logger.info("Starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, self.SCOPES)
                # Run the OAuth flow in a thread to avoid blocking
                self.credentials = await asyncio.get_event_loop().run_in_executor(
                    None, flow.run_local_server, {"port": 0}
                )
                self.logger.info("OAuth flow completed successfully")

            # Save the credentials for future use
            with open(token_file, "w") as token:
                token.write(self.credentials.to_json())
            self.logger.info("Credentials saved to %s", token_file)

        self.logger.info("Authentication successful")
        return self.credentials

    async def get_api_client(self) -> GoogleApiClient:
        """Get authenticated Google API client.

        Returns:
            Initialized Google API client
        """
        if not self.credentials:
            await self.authenticate()

        if not self.api_client:
            self.api_client = GoogleApiClient(self.credentials)
            await self.api_client.initialize()

        return self.api_client

    async def ensure_valid_credentials(self) -> Credentials:
        """Ensure credentials are valid, refreshing if necessary.

        Returns:
            Valid credentials
        """
        if not self.credentials:
            return await self.authenticate()

        if self.credentials.expired and self.credentials.refresh_token:
            self.logger.info("Refreshing expired credentials")
            try:
                self.credentials.refresh(Request())

                # Update saved token file
                token_file = os.path.expanduser("~/.godri-token.json")
                with open(token_file, "w") as token:
                    token.write(self.credentials.to_json())

                self.logger.info("Credentials refreshed and saved")
            except Exception as e:
                self.logger.error("Failed to refresh credentials: %s", str(e))
                # Force re-authentication
                return await self.authenticate()

        return self.credentials

    async def revoke_credentials(self) -> bool:
        """Revoke current credentials.

        Returns:
            True if revocation was successful
        """
        if not self.credentials:
            return True

        try:
            # Revoke the token
            if self.credentials.token:
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://oauth2.googleapis.com/revoke", params={"token": self.credentials.token}
                    ) as response:
                        success = response.status == 200

            # Remove local token file
            token_file = os.path.expanduser("~/.godri-token.json")
            if os.path.exists(token_file):
                os.remove(token_file)

            # Clear credentials
            self.credentials = None
            if self.api_client:
                await self.api_client.close()
                self.api_client = None

            self.logger.info("Credentials revoked successfully")
            return True

        except Exception as e:
            self.logger.error("Failed to revoke credentials: %s", str(e))
            return False

    async def close(self):
        """Close authentication service and cleanup resources."""
        if self.api_client:
            await self.api_client.close()
            self.api_client = None
