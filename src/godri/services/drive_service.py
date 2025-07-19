"""Google Drive service wrapper."""

import logging
from typing import List, Dict, Optional, Any
from ..commons.api.google_api_client import GoogleApiClient
from ..commons.api.drive_api import DriveApiClient
from .auth_service_new import AuthService


class DriveService:
    """Google Drive operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.drive_api = None

    async def initialize(self):
        """Initialize the Drive service."""
        credentials = await self.auth_service.authenticate()
        if not credentials:
            raise ValueError("Failed to authenticate with Google Drive")

        api_client = GoogleApiClient(credentials)
        await api_client.initialize()
        self.drive_api = DriveApiClient(api_client)
        self.logger.info("Drive service initialized")

    async def search_files(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for files in Google Drive."""
        self.logger.info("Searching files with query: %s", query)

        results = await self.drive_api.search_files(
            query=query, max_results=max_results, fields="id, name, mimeType, parents, modifiedTime, size"
        )

        items = results.get("files", [])
        self.logger.info("Found %d files", len(items))

        return items

    async def search_by_name(self, name: str, mime_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search files by name."""
        query = f"name contains '{name}'"
        if mime_type:
            query += f" and mimeType='{mime_type}'"

        return await self.search_files(query)

    async def list_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """List contents of a folder."""
        return await self.drive_api.list_folder_contents(folder_id)

    async def upload_file(
        self, file_path: str, parent_folder_id: Optional[str] = None, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to Google Drive."""
        self.logger.info("Uploading file: %s as %s", file_path, name or "original name")

        file = await self.drive_api.upload_file(
            file_path=file_path, name=name, parent_folder_id=parent_folder_id, fields="id, name, webViewLink"
        )

        self.logger.info("File uploaded successfully: %s", file.get("id"))
        return file

    async def download_file(self, file_id: str, output_path: str) -> str:
        """Download a file from Google Drive."""
        self.logger.info("Downloading file: %s to %s", file_id, output_path)

        result_path = await self.drive_api.download_file(file_id, output_path)

        self.logger.info("File downloaded successfully to: %s", result_path)
        return result_path

    async def download_file_smart(self, file_id: str, output_path: str) -> str:
        """Download a file with smart format conversion based on file type."""
        self.logger.info("Smart downloading file: %s to %s", file_id, output_path)

        result_path = await self.drive_api.download_file_smart(file_id, output_path)

        self.logger.info("File downloaded successfully to: %s", result_path)
        return result_path

    async def create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder."""
        self.logger.info("Creating folder: %s", name)

        folder = await self.drive_api.create_folder(name, parent_folder_id)

        self.logger.info("Folder created successfully: %s", folder.get("id"))
        return folder

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file or folder."""
        self.logger.info("Deleting file: %s", file_id)

        try:
            success = await self.drive_api.delete_file(file_id)
            if success:
                self.logger.info("File deleted successfully")
            return success
        except Exception as e:
            self.logger.error("Failed to delete file: %s", str(e))
            return False

    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get file information."""
        self.logger.info("Getting file info: %s", file_id)

        file_info = await self.drive_api.get_file_info(
            file_id, fields="id, name, mimeType, parents, modifiedTime, size, webViewLink"
        )

        return file_info

    async def find_folder_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a folder by name."""
        return await self.drive_api.find_folder_by_name(name)

    async def move_file_to_folder(self, file_id: str, folder_id: str) -> Dict[str, Any]:
        """Move a file to a specific folder."""
        self.logger.info("Moving file %s to folder %s", file_id, folder_id)
        return await self.drive_api.move_file_to_folder(file_id, folder_id)

    async def share_file(self, file_id: str, email: str, role: str = "reader", notify: bool = True) -> Dict[str, Any]:
        """Share a file with a user."""
        self.logger.info("Sharing file %s with %s as %s", file_id, email, role)
        return await self.drive_api.share_file(file_id, email, role, notify)

    async def copy_file(self, file_id: str, name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Copy a file."""
        self.logger.info("Copying file %s as %s", file_id, name)
        return await self.drive_api.copy_file(file_id, name, parent_folder_id)

    async def create_file_from_content(
        self,
        name: str,
        content: str,
        mime_type: str = "text/plain",
        parent_folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a file from text content."""
        self.logger.info("Creating file from content: %s", name)
        return await self.drive_api.create_file_from_content(name, content, mime_type, parent_folder_id)
