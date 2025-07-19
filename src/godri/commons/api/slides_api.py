"""Google Slides API wrapper using async HTTP client."""

import logging
from typing import Optional, Dict, Any, List
from .google_api_client import GoogleApiClient


class SlidesApiClient:
    """Async Google Slides API client."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Slides API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.base_url = "/slides/v1"

    async def get_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """Get presentation metadata and content.

        Args:
            presentation_id: Google Slides presentation ID

        Returns:
            Presentation data
        """
        return await self.api_client.get(f"{self.base_url}/presentations/{presentation_id}")

    async def create_presentation(self, title: str) -> Dict[str, Any]:
        """Create a new presentation.

        Args:
            title: Presentation title

        Returns:
            Created presentation metadata
        """
        body = {"title": title}
        return await self.api_client.post(f"{self.base_url}/presentations", json_data=body)

    async def batch_update(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on presentation.

        Args:
            presentation_id: Google Slides presentation ID
            requests: List of update requests

        Returns:
            Update response
        """
        body = {"requests": requests}
        return await self.api_client.post(
            f"{self.base_url}/presentations/{presentation_id}:batchUpdate", json_data=body
        )
