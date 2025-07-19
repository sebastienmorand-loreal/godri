"""Google Drive API wrapper using aiogoogle for full async operations."""

import logging
from typing import Optional, Dict, Any, List, Union
import mimetypes
import os
from pathlib import Path

from .google_api_client import GoogleApiClient


class DriveApiClient:
    """Async Google Drive API client using aiogoogle."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Drive API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self._service = None

    async def _get_service(self):
        """Get or create Drive service."""
        if self._service is None:
            self._service = await self.api_client.discover_service("drive", "v3")
        return self._service

    async def list_files(
        self, query: Optional[str] = None, limit: int = 100, fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """List files in Google Drive.

        Args:
            query: Search query in Drive API format
            limit: Maximum number of files to return
            fields: Comma-separated list of fields to return

        Returns:
            Drive API response with files list
        """
        service = await self._get_service()

        params = {
            "pageSize": min(limit, 1000),
            "fields": fields or "files(id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink)",
        }

        if query:
            params["q"] = query

        return await self.api_client.execute_request(service, "files.list", **params)

    async def get_file(self, file_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get file metadata.

        Args:
            file_id: Google Drive file ID
            fields: Comma-separated list of fields to return

        Returns:
            File metadata
        """
        service = await self._get_service()

        params = {"fileId": file_id}
        if fields:
            params["fields"] = fields

        return await self.api_client.execute_request(service, "files.get", **params)

    async def download_file(self, file_id: str, file_path: str) -> bool:
        """Download file content.

        Args:
            file_id: Google Drive file ID
            file_path: Local path to save the file

        Returns:
            True if successful
        """
        try:
            service = await self._get_service()

            # Check if it's a Google Workspace file that needs export
            file_metadata = await self.get_file(file_id, "mimeType")
            mime_type = file_metadata.get("mimeType", "")

            if mime_type.startswith("application/vnd.google-apps"):
                # Use export for Google Workspace files
                export_mime_type = self._get_export_mime_type(mime_type)
                return await self.export_file(file_id, export_mime_type, file_path)
            else:
                # Use regular download for binary files
                return await self.api_client.download_file(service, "files.get", file_path, fileId=file_id, alt="media")

        except Exception as e:
            self.logger.error(f"Failed to download file {file_id}: {str(e)}")
            return False

    async def export_file(self, file_id: str, mime_type: str, file_path: str) -> bool:
        """Export Google Workspace file to specified format.

        Args:
            file_id: Google Drive file ID
            mime_type: Target MIME type for export
            file_path: Local path to save the exported file

        Returns:
            True if successful
        """
        try:
            service = await self._get_service()

            return await self.api_client.download_file(
                service, "files.export", file_path, fileId=file_id, mimeType=mime_type
            )

        except Exception as e:
            self.logger.error(f"Failed to export file {file_id}: {str(e)}")
            return False

    async def create_file(
        self, name: str, file_path: str, parent_id: Optional[str] = None, mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new file in Google Drive by uploading from local path.

        Args:
            name: File name in Drive
            file_path: Local file path to upload
            parent_id: Parent folder ID
            mime_type: File MIME type (auto-detected if not provided)

        Returns:
            Created file metadata
        """
        service = await self._get_service()

        # Auto-detect MIME type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"

        # Prepare metadata
        metadata = {"name": name}
        if parent_id:
            metadata["parents"] = [parent_id]

        return await self.api_client.upload_file(
            service, "files.create", file_path, body=metadata, media_body=file_path, media_mime_type=mime_type
        )

    async def create_file_from_content(
        self, name: str, content: Union[str, bytes], mime_type: str, parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new file in Google Drive from content.

        Args:
            name: File name
            content: File content (string or bytes)
            mime_type: File MIME type
            parent_id: Parent folder ID

        Returns:
            Created file metadata
        """
        service = await self._get_service()

        # Create temporary file for upload
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            if isinstance(content, str):
                temp_file.write(content.encode("utf-8"))
            else:
                temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Prepare metadata
            metadata = {"name": name}
            if parent_id:
                metadata["parents"] = [parent_id]

            result = await self.api_client.upload_file(
                service, "files.create", temp_path, body=metadata, media_body=temp_path, media_mime_type=mime_type
            )

            return result

        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    async def create_folder(self, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder in Google Drive.

        Args:
            name: Folder name
            parent_id: Parent folder ID

        Returns:
            Created folder metadata
        """
        service = await self._get_service()

        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}

        if parent_id:
            metadata["parents"] = [parent_id]

        return await self.api_client.execute_request(service, "files.create", body=metadata)

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            True if successful
        """
        try:
            service = await self._get_service()
            await self.api_client.execute_request(service, "files.delete", fileId=file_id)
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete file {file_id}: {str(e)}")
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
        service = await self._get_service()

        metadata = {"name": name}
        if parent_id:
            metadata["parents"] = [parent_id]

        return await self.api_client.execute_request(service, "files.copy", fileId=file_id, body=metadata)

    async def update_file(
        self,
        file_id: str,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing file in Google Drive.

        Args:
            file_id: File ID to update
            file_path: Local file path for content update (optional)
            metadata: Metadata to update (optional)
            mime_type: File MIME type (auto-detected if not provided)

        Returns:
            Updated file metadata
        """
        service = await self._get_service()

        params = {"fileId": file_id}

        if metadata:
            params["body"] = metadata

        if file_path:
            # Auto-detect MIME type if not provided
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = "application/octet-stream"

            params["media_body"] = file_path
            params["media_mime_type"] = mime_type

            return await self.api_client.upload_file(service, "files.update", file_path, **params)
        else:
            return await self.api_client.execute_request(service, "files.update", **params)

    async def search_files(
        self,
        name: Optional[str] = None,
        mime_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search for files with common filters.

        Args:
            name: File name to search for (partial match)
            mime_type: MIME type filter
            parent_id: Parent folder ID
            limit: Maximum number of results

        Returns:
            List of matching files
        """
        query_parts = []

        if name:
            query_parts.append(f"name contains '{name}'")
        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")

        # Always exclude trashed files
        query_parts.append("trashed = false")

        query = " and ".join(query_parts)

        result = await self.list_files(query=query, limit=limit)
        return result.get("files", [])

    def _get_export_mime_type(self, google_mime_type: str) -> str:
        """Get appropriate export MIME type for Google Workspace files.

        Args:
            google_mime_type: Google Workspace MIME type

        Returns:
            Export MIME type
        """
        export_map = {
            "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.google-apps.drawing": "image/png",
        }

        return export_map.get(google_mime_type, "application/pdf")

    async def get_file_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        """Get file permissions.

        Args:
            file_id: Google Drive file ID

        Returns:
            List of permissions
        """
        service = await self._get_service()

        result = await self.api_client.execute_request(service, "permissions.list", fileId=file_id)
        return result.get("permissions", [])

    async def share_file(self, file_id: str, email: str, role: str = "reader", notify: bool = True) -> Dict[str, Any]:
        """Share a file with specific user.

        Args:
            file_id: Google Drive file ID
            email: Email address to share with
            role: Permission role (reader, writer, commenter)
            notify: Whether to send notification email

        Returns:
            Permission metadata
        """
        service = await self._get_service()

        permission = {"type": "user", "role": role, "emailAddress": email}

        return await self.api_client.execute_request(
            service, "permissions.create", fileId=file_id, body=permission, sendNotificationEmail=notify
        )
