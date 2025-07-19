"""Google Drive API wrapper using async HTTP client."""

import logging
from typing import Optional, Dict, Any, List
from .google_api_client import GoogleApiClient


class DriveApiClient:
    """Async Google Drive API client."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Drive API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.base_url = "/drive/v3"

    async def list_files(self, query: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """List files in Google Drive.

        Args:
            query: Search query in Drive API format
            limit: Maximum number of files to return

        Returns:
            Drive API response with files list
        """
        params = {
            "pageSize": min(limit, 1000),
            "fields": "files(id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink)",
        }

        if query:
            params["q"] = query

        return await self.api_client.get(f"{self.base_url}/files", params=params)

    async def get_file(self, file_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get file metadata.

        Args:
            file_id: Google Drive file ID
            fields: Comma-separated list of fields to return

        Returns:
            File metadata
        """
        params = {}
        if fields:
            params["fields"] = fields

        return await self.api_client.get(f"{self.base_url}/files/{file_id}", params=params)

    async def download_file(self, file_id: str) -> bytes:
        """Download file content.

        Args:
            file_id: Google Drive file ID

        Returns:
            File content as bytes
        """
        # For binary downloads, we need to handle the response differently
        import aiohttp

        access_token = await self.api_client._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        url = f"{self.api_client.base_url}{self.base_url}/files/{file_id}"
        params = {"alt": "media"}

        async with self.api_client.session.get(url, params=params, headers=headers) as response:
            if response.status >= 400:
                response.raise_for_status()
            return await response.read()

    async def export_file(self, file_id: str, mime_type: str) -> bytes:
        """Export Google Workspace file to specified format.

        Args:
            file_id: Google Drive file ID
            mime_type: Target MIME type for export

        Returns:
            Exported file content as bytes
        """
        import aiohttp

        access_token = await self.api_client._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        url = f"{self.api_client.base_url}{self.base_url}/files/{file_id}/export"
        params = {"mimeType": mime_type}

        async with self.api_client.session.get(url, params=params, headers=headers) as response:
            if response.status >= 400:
                response.raise_for_status()
            return await response.read()

    async def create_file(
        self, name: str, mime_type: str, content: bytes, parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new file in Google Drive.

        Args:
            name: File name
            mime_type: File MIME type
            content: File content as bytes
            parent_id: Parent folder ID

        Returns:
            Created file metadata
        """
        # Google Drive API requires multipart upload for file creation
        import aiohttp
        from aiohttp import FormData

        access_token = await self.api_client._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Prepare metadata
        metadata = {"name": name}
        if parent_id:
            metadata["parents"] = [parent_id]

        # Create multipart form data
        form_data = FormData()
        form_data.add_field("metadata", str(metadata), content_type="application/json")
        form_data.add_field("media", content, content_type=mime_type, filename=name)

        url = "https://www.googleapis.com/upload/drive/v3/files"
        params = {"uploadType": "multipart"}

        async with self.api_client.session.post(url, params=params, headers=headers, data=form_data) as response:
            if response.status >= 400:
                response.raise_for_status()
            return await response.json()

    async def create_folder(self, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder in Google Drive.

        Args:
            name: Folder name
            parent_id: Parent folder ID

        Returns:
            Created folder metadata
        """
        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}

        if parent_id:
            metadata["parents"] = [parent_id]

        return await self.api_client.post(f"{self.base_url}/files", json_data=metadata)

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            True if successful
        """
        try:
            await self.api_client.delete(f"{self.base_url}/files/{file_id}")
            return True
        except Exception as e:
            self.logger.error("Failed to delete file %s: %s", file_id, str(e))
            return False

    async def copy_file(self, file_id: str, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Copy a file in Google Drive.

        Args:
            file_id: Source file ID
            name: New file name
            parent_id: Parent folder ID for the copy

        Returns:
            Copied file metadata
        """
        metadata = {"name": name}
        if parent_id:
            metadata["parents"] = [parent_id]

        return await self.api_client.post(f"{self.base_url}/files/{file_id}/copy", json_data=metadata)
