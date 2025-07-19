"""Google Forms API wrapper using async HTTP client."""

import logging
from typing import Optional, Dict, Any, List
from .google_api_client import GoogleApiClient


class FormsApiClient:
    """Async Google Forms API client."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Forms API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.base_url = "/forms/v1"

    async def get_form(self, form_id: str) -> Dict[str, Any]:
        """Get form metadata and structure.

        Args:
            form_id: Google Forms form ID

        Returns:
            Form data
        """
        return await self.api_client.get(f"{self.base_url}/forms/{form_id}")

    async def create_form(self, title: str, document_title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new form.

        Args:
            title: Form title
            document_title: Document title (defaults to title)

        Returns:
            Created form metadata
        """
        body = {"info": {"title": title, "documentTitle": document_title or title}}
        return await self.api_client.post(f"{self.base_url}/forms", json_data=body)

    async def batch_update(self, form_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on form.

        Args:
            form_id: Google Forms form ID
            requests: List of update requests

        Returns:
            Update response
        """
        body = {"requests": requests}
        return await self.api_client.post(f"{self.base_url}/forms/{form_id}:batchUpdate", json_data=body)
