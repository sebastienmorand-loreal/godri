"""Google API client using aiohttp for async operations."""

import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
import json
from urllib.parse import urlencode


class GoogleApiClient:
    """Async Google API client using aiohttp."""

    def __init__(self, credentials=None):
        """Initialize the Google API client.

        Args:
            credentials: Google OAuth2 credentials
        """
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://www.googleapis.com"

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self):
        """Initialize the HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary."""
        if not self.credentials:
            raise ValueError("No credentials provided")

        # Refresh token if expired
        if self.credentials.expired and self.credentials.refresh_token:
            from google.auth.transport.requests import Request

            self.credentials.refresh(Request())

        return self.credentials.token

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Google API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: API endpoint URL
            params: Query parameters
            json_data: JSON payload for POST/PUT requests
            headers: Additional headers

        Returns:
            Response JSON data

        Raises:
            aiohttp.ClientError: For HTTP errors
        """
        if not self.session:
            await self.initialize()

        access_token = await self._get_access_token()

        # Prepare headers
        request_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        if headers:
            request_headers.update(headers)

        # Prepare URL
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"

        self.logger.debug("Making %s request to %s", method, url)

        try:
            async with self.session.request(
                method=method, url=url, params=params, json=json_data, headers=request_headers
            ) as response:
                response_text = await response.text()

                if response.status >= 400:
                    self.logger.error(
                        "API request failed: %s %s - Status: %d - Response: %s",
                        method,
                        url,
                        response.status,
                        response_text,
                    )
                    response.raise_for_status()

                return await response.json() if response_text else {}

        except aiohttp.ClientError as e:
            self.logger.error("HTTP request failed: %s", str(e))
            raise
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse JSON response: %s", str(e))
            raise

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return await self._make_request("GET", url, params=params)

    async def post(self, url: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        return await self._make_request("POST", url, json_data=json_data)

    async def put(self, url: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return await self._make_request("PUT", url, json_data=json_data)

    async def delete(self, url: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self._make_request("DELETE", url)

    async def patch(self, url: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PATCH request."""
        return await self._make_request("PATCH", url, json_data=json_data)
