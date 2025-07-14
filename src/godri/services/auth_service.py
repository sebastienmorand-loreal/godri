"""Authentication service for Google APIs."""

import os
import logging
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class AuthService:
    """Handle Google API authentication."""

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/cloud-translation",
    ]

    def __init__(self, oauth_token: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.credentials: Optional[Credentials] = None
        self.oauth_token = oauth_token
        self.client_secret_file = os.getenv("GODRI_CLIENT_FILE")

        if not self.oauth_token and not self.client_secret_file:
            raise ValueError("Either oauth_token or GODRI_CLIENT_FILE environment variable is required")

        if self.client_secret_file and not os.path.exists(self.client_secret_file):
            raise FileNotFoundError(f"Client secret file not found: {self.client_secret_file}")

    async def authenticate(self) -> Credentials:
        """Authenticate user and return credentials."""
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
                self.credentials.refresh(Request())
            else:
                self.logger.info("Starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, self.SCOPES)
                self.credentials = flow.run_local_server(port=0)

            self.logger.info("Saving credentials to %s", token_file)
            with open(token_file, "w") as token:
                token.write(self.credentials.to_json())

        self.logger.info("Authentication successful")
        return self.credentials

    def get_service(self, service_name: str, version: str):
        """Get authenticated Google API service."""
        if not self.credentials:
            raise ValueError("Not authenticated. Call authenticate() first.")

        self.logger.info("Building %s service (version %s)", service_name, version)
        return build(service_name, version, credentials=self.credentials)
