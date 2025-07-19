"""Google Docs API wrapper using async HTTP client."""

import logging
from typing import Optional, Dict, Any, List
from .google_api_client import GoogleApiClient


class DocsApiClient:
    """Async Google Docs API client."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Docs API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.base_url = "/docs/v1"

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document content and metadata.

        Args:
            document_id: Google Docs document ID

        Returns:
            Document data
        """
        return await self.api_client.get(f"{self.base_url}/documents/{document_id}")

    async def create_document(self, title: str) -> Dict[str, Any]:
        """Create a new document.

        Args:
            title: Document title

        Returns:
            Created document metadata
        """
        body = {"title": title}
        return await self.api_client.post(f"{self.base_url}/documents", json_data=body)

    async def batch_update(self, document_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on document.

        Args:
            document_id: Google Docs document ID
            requests: List of update requests

        Returns:
            Update response
        """
        body = {"requests": requests}
        return await self.api_client.post(f"{self.base_url}/documents/{document_id}:batchUpdate", json_data=body)
