"""Google API client using aiogoogle for full async operations."""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import os

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import UserCreds, ServiceAccountCreds
from aiogoogle.auth.managers import Oauth2Manager


class GoogleApiClient:
    """Async Google API client using aiogoogle."""

    def __init__(self, credentials_path: Optional[str] = None, user_creds: Optional[UserCreds] = None):
        """Initialize the Google API client.

        Args:
            credentials_path: Path to client credentials JSON file
            user_creds: Existing user credentials
        """
        self.logger = logging.getLogger(__name__)
        self.credentials_path = credentials_path or os.getenv("GODRI_CLIENT_FILE")
        self.user_creds = user_creds
        self.aiogoogle: Optional[Aiogoogle] = None
        self._auth_manager: Optional[Oauth2Manager] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self):
        """Initialize the aiogoogle client."""
        if self.aiogoogle is None:
            # Initialize client credentials from file
            if self.credentials_path and Path(self.credentials_path).exists():
                self.aiogoogle = Aiogoogle(client_creds_file=self.credentials_path)
            else:
                self.aiogoogle = Aiogoogle()

            # Set up auth manager if we have user credentials
            if self.user_creds:
                self.aiogoogle.user_creds = self.user_creds

    async def close(self):
        """Close the aiogoogle client."""
        if self.aiogoogle:
            await self.aiogoogle.close()
            self.aiogoogle = None

    async def get_user_creds(self) -> Optional[UserCreds]:
        """Get current user credentials."""
        return self.user_creds if self.user_creds else getattr(self.aiogoogle, "user_creds", None)

    async def set_user_creds(self, user_creds: UserCreds):
        """Set user credentials."""
        self.user_creds = user_creds
        if self.aiogoogle:
            self.aiogoogle.user_creds = user_creds

    async def refresh_creds(self) -> UserCreds:
        """Refresh user credentials if needed."""
        if not self.aiogoogle:
            await self.initialize()

        if not self.user_creds:
            raise ValueError("No user credentials to refresh")

        # Check if credentials need refresh
        if self.user_creds.expired:
            self.logger.debug("Refreshing expired credentials")
            refreshed_creds = await self.aiogoogle.oauth2.refresh(self.user_creds)
            await self.set_user_creds(refreshed_creds)

        return self.user_creds

    async def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return bool(self.user_creds and not self.user_creds.expired)

    async def discover_service(self, service_name: str, version: str):
        """Discover a Google API service.

        Args:
            service_name: Name of the service (e.g., 'drive', 'docs', 'sheets')
            version: API version (e.g., 'v3', 'v1')

        Returns:
            Discovered service object
        """
        if not self.aiogoogle:
            await self.initialize()

        try:
            service = await self.aiogoogle.discover(service_name, version)
            self.logger.debug(f"Discovered {service_name} {version} service")
            return service
        except Exception as e:
            self.logger.error(f"Failed to discover {service_name} {version}: {str(e)}")
            raise

    async def execute_request(self, service, method_name: str, **kwargs):
        """Execute an API request using aiogoogle.

        Args:
            service: Discovered service object
            method_name: Method name to call on the service
            **kwargs: Method parameters

        Returns:
            API response
        """
        if not self.aiogoogle:
            await self.initialize()

        # Ensure credentials are fresh
        await self.refresh_creds()

        try:
            # Get the method from the service
            method_parts = method_name.split(".")
            method = service
            for part in method_parts:
                method = getattr(method, part)

            # Execute the request
            request = method(**kwargs)
            response = await self.aiogoogle.as_user(request)

            self.logger.debug(f"Executed {method_name} successfully")
            return response

        except Exception as e:
            self.logger.error(f"Failed to execute {method_name}: {str(e)}")
            raise

    async def batch_execute(self, requests: List[tuple]):
        """Execute multiple requests in batch.

        Args:
            requests: List of (service, method_name, kwargs) tuples

        Returns:
            List of responses
        """
        if not self.aiogoogle:
            await self.initialize()

        # Ensure credentials are fresh
        await self.refresh_creds()

        try:
            # Prepare batch requests
            batch_requests = []
            for service, method_name, kwargs in requests:
                method_parts = method_name.split(".")
                method = service
                for part in method_parts:
                    method = getattr(method, part)
                batch_requests.append(method(**kwargs))

            # Execute batch
            responses = await self.aiogoogle.as_user(*batch_requests)
            self.logger.debug(f"Executed batch of {len(requests)} requests")
            return responses

        except Exception as e:
            self.logger.error(f"Failed to execute batch requests: {str(e)}")
            raise

    async def upload_file(self, service, method_name: str, file_path: str, **kwargs):
        """Upload a file using aiogoogle.

        Args:
            service: Discovered service object
            method_name: Method name for upload
            file_path: Path to file to upload
            **kwargs: Additional method parameters

        Returns:
            Upload response
        """
        if not self.aiogoogle:
            await self.initialize()

        # Ensure credentials are fresh
        await self.refresh_creds()

        try:
            method_parts = method_name.split(".")
            method = service
            for part in method_parts:
                method = getattr(method, part)

            # Prepare upload request
            request = method(**kwargs, upload_file=file_path)
            response = await self.aiogoogle.as_user(request)

            self.logger.debug(f"Uploaded file {file_path} using {method_name}")
            return response

        except Exception as e:
            self.logger.error(f"Failed to upload file {file_path}: {str(e)}")
            raise

    async def download_file(self, service, method_name: str, file_path: str, **kwargs):
        """Download a file using aiogoogle.

        Args:
            service: Discovered service object
            method_name: Method name for download
            file_path: Path to save downloaded file
            **kwargs: Additional method parameters

        Returns:
            Download response
        """
        if not self.aiogoogle:
            await self.initialize()

        # Ensure credentials are fresh
        await self.refresh_creds()

        try:
            method_parts = method_name.split(".")
            method = service
            for part in method_parts:
                method = getattr(method, part)

            # Prepare download request
            request = method(**kwargs)
            response = await self.aiogoogle.as_user(request, full_response=True)

            # Write downloaded content to file
            with open(file_path, "wb") as f:
                f.write(response.content)

            self.logger.debug(f"Downloaded file to {file_path} using {method_name}")
            return response

        except Exception as e:
            self.logger.error(f"Failed to download file to {file_path}: {str(e)}")
            raise

    # Compatibility methods for existing code
    async def get(self, service, method_name: str, **kwargs):
        """Compatibility method for GET requests."""
        return await self.execute_request(service, method_name, **kwargs)

    async def post(self, service, method_name: str, **kwargs):
        """Compatibility method for POST requests."""
        return await self.execute_request(service, method_name, **kwargs)

    async def put(self, service, method_name: str, **kwargs):
        """Compatibility method for PUT requests."""
        return await self.execute_request(service, method_name, **kwargs)

    async def delete(self, service, method_name: str, **kwargs):
        """Compatibility method for DELETE requests."""
        return await self.execute_request(service, method_name, **kwargs)

    async def patch(self, service, method_name: str, **kwargs):
        """Compatibility method for PATCH requests."""
        return await self.execute_request(service, method_name, **kwargs)
