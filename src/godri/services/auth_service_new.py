"""Async authentication service for Google APIs."""

import json
import logging
import os
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class AuthService:
    """Async authentication service for Google APIs."""

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/forms",
        "https://www.googleapis.com/auth/cloud-translation",
        "https://www.googleapis.com/auth/cloud-platform",
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.credentials = None
        self.token_file = os.path.expanduser("~/.godri-token.json")
        self.client_file = os.getenv("GODRI_CLIENT_FILE")

        if not self.client_file:
            self.logger.warning("GODRI_CLIENT_FILE environment variable not set")

    async def authenticate(self, force_refresh: bool = False) -> Optional[Credentials]:
        """Authenticate and return valid credentials."""
        self.logger.info("Starting authentication process")

        # Try to load existing credentials
        if not force_refresh:
            credentials = await self._load_existing_credentials()
            if credentials and credentials.valid:
                self.credentials = credentials
                self.logger.info("Using existing valid credentials")
                return credentials
            elif credentials and credentials.expired and credentials.refresh_token:
                self.logger.info("Refreshing expired credentials")
                try:
                    await self._refresh_credentials(credentials)
                    self.credentials = credentials
                    await self._save_credentials(credentials)
                    return credentials
                except Exception as e:
                    self.logger.warning(f"Failed to refresh credentials: {e}")

        # Perform new authentication flow
        credentials = await self._perform_oauth_flow()
        if credentials:
            self.credentials = credentials
            await self._save_credentials(credentials)
            self.logger.info("Authentication successful")
            return credentials

        raise RuntimeError("Authentication failed")

    async def _load_existing_credentials(self) -> Optional[Credentials]:
        """Load credentials from token file."""
        if not os.path.exists(self.token_file):
            self.logger.debug("No existing token file found")
            return None

        try:
            async with aiofiles.open(self.token_file, "r") as f:
                token_data = await f.read()
                creds_data = json.loads(token_data)

            credentials = Credentials.from_authorized_user_info(creds_data, self.SCOPES)
            self.logger.debug("Successfully loaded existing credentials")
            return credentials

        except Exception as e:
            self.logger.error(f"Failed to load existing credentials: {e}")
            return None

    async def _refresh_credentials(self, credentials: Credentials) -> None:
        """Refresh expired credentials."""
        self.logger.info("Refreshing credentials")

        # Run the blocking refresh in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, credentials.refresh, Request())

        self.logger.info("Credentials refreshed successfully")

    async def _perform_oauth_flow(self) -> Optional[Credentials]:
        """Perform OAuth 2.0 flow for new credentials."""
        if not self.client_file or not os.path.exists(self.client_file):
            raise RuntimeError(
                "Client credentials file not found. "
                "Please set GODRI_CLIENT_FILE environment variable to the path of your client_secret.json file"
            )

        self.logger.info("Starting OAuth 2.0 flow")

        try:
            # Run the OAuth flow in a thread pool since it's blocking
            loop = asyncio.get_event_loop()
            flow = InstalledAppFlow.from_client_secrets_file(self.client_file, self.SCOPES)

            # Use run_local_server in thread pool
            credentials = await loop.run_in_executor(None, lambda: flow.run_local_server(port=0))

            self.logger.info("OAuth flow completed successfully")
            return credentials

        except Exception as e:
            self.logger.error(f"OAuth flow failed: {e}")
            return None

    async def _save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to token file."""
        try:
            token_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)

            async with aiofiles.open(self.token_file, "w") as f:
                await f.write(json.dumps(token_data, indent=2))

            # Set restrictive permissions
            os.chmod(self.token_file, 0o600)

            self.logger.debug("Credentials saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save credentials: {e}")

    async def get_valid_credentials(self) -> Credentials:
        """Get valid credentials, refreshing if necessary."""
        if not self.credentials:
            await self.authenticate()

        if not self.credentials:
            raise RuntimeError("No valid credentials available")

        # Check if credentials need refresh
        if self.credentials.expired and self.credentials.refresh_token:
            self.logger.info("Credentials expired, refreshing")
            await self._refresh_credentials(self.credentials)
            await self._save_credentials(self.credentials)

        return self.credentials

    async def ensure_valid_token(self) -> str:
        """Ensure we have a valid access token and return it."""
        credentials = await self.get_valid_credentials()

        if not credentials.token:
            raise RuntimeError("No access token available")

        return credentials.token

    async def revoke_credentials(self) -> bool:
        """Revoke current credentials."""
        if not self.credentials:
            self.logger.warning("No credentials to revoke")
            return False

        try:
            # Run revoke in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.credentials.revoke, Request())

            # Remove token file
            if os.path.exists(self.token_file):
                os.remove(self.token_file)

            self.credentials = None
            self.logger.info("Credentials revoked successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to revoke credentials: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        return self.credentials is not None and self.credentials.valid

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get user information from credentials."""
        if not self.credentials:
            return None

        try:
            # This would require calling the userinfo API
            # For now, return basic info if available
            return {
                "authenticated": True,
                "scopes": self.credentials.scopes,
                "client_id": getattr(self.credentials, "client_id", None),
            }
        except Exception as e:
            self.logger.error(f"Failed to get user info: {e}")
            return None

    def get_credentials_for_api_client(self) -> Credentials:
        """Get credentials object for use with API clients."""
        if not self.credentials:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return self.credentials

    async def get_gcloud_access_token(self) -> Optional[str]:
        """Get access token from gcloud CLI."""
        try:
            self.logger.info("Getting access token from gcloud CLI")

            # Run gcloud auth print-access-token
            result = await asyncio.create_subprocess_shell(
                "gcloud auth print-access-token", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                token = stdout.decode().strip()
                self.logger.info("Successfully retrieved gcloud access token")
                return token
            else:
                self.logger.error("Failed to get gcloud token: %s", stderr.decode())
                return None

        except Exception as e:
            self.logger.error("Failed to run gcloud command: %s", str(e))
            return None
