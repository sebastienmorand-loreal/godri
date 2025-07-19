"""Google Drive service wrapper using aiogoogle."""

import logging
import os
import io
from typing import List, Dict, Optional, Any
import aiofiles
from .auth_service import AuthService
from ..commons.api.drive_api import DriveApiClient


class DriveService:
    """Google Drive operations using aiogoogle."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.drive_api = None

    async def initialize(self):
        """Initialize the Drive service."""
        await self.auth_service.authenticate()
        api_client = await self.auth_service.get_api_client()
        self.drive_api = DriveApiClient(api_client)
        self.logger.info("Drive service initialized")

    async def search_files(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for files in Google Drive."""
        self.logger.info("Searching files with query: %s", query)

        response = await self.drive_api.list_files(
            query=query,
            page_size=max_results,
            fields="nextPageToken, files(id, name, mimeType, parents, modifiedTime, size)",
        )

        items = response.get("files", [])
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
        query = f"'{folder_id}' in parents and trashed=false"
        return await self.search_files(query)

    async def upload_file(
        self, file_path: str, parent_folder_id: Optional[str] = None, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to Google Drive."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = name or os.path.basename(file_path)
        self.logger.info("Uploading file: %s as %s", file_path, file_name)

        parents = [parent_folder_id] if parent_folder_id else None

        file_info = await self.drive_api.upload_file(file_path=file_path, name=file_name, parents=parents)

        self.logger.info("File uploaded successfully: %s", file_info.get("id"))
        return file_info

    async def download_file(self, file_id: str, output_path: str) -> str:
        """Download a file from Google Drive."""
        self.logger.info("Downloading file: %s to %s", file_id, output_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        await self.drive_api.download_file(file_id, output_path)

        self.logger.info("File downloaded successfully to: %s", output_path)
        return output_path

    async def download_file_smart(self, file_id: str, output_path: str) -> str:
        """Download a file with smart format conversion based on file type."""
        self.logger.info("Smart downloading file: %s to %s", file_id, output_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        await self.drive_api.smart_download_export(file_id, output_path)

        self.logger.info("File smart downloaded successfully to: %s", output_path)
        return output_path

    async def create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder."""
        self.logger.info("Creating folder: %s", name)

        parents = [parent_folder_id] if parent_folder_id else None

        folder_info = await self.drive_api.create_folder(name=name, parents=parents)

        self.logger.info("Folder created successfully: %s", folder_info.get("id"))
        return folder_info

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file or folder."""
        self.logger.info("Deleting file: %s", file_id)

        try:
            await self.drive_api.delete_file(file_id)
            self.logger.info("File deleted successfully")
            return True
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
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = await self.search_files(query, max_results=1)

        return results[0] if results else None
