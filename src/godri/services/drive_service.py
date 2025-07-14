"""Google Drive service wrapper."""

import logging
import os
import io
from typing import List, Dict, Optional, Any
import aiofiles
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .auth_service import AuthService


class DriveService:
    """Google Drive operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.service = None

    async def initialize(self):
        """Initialize the Drive service."""
        await self.auth_service.authenticate()
        self.service = self.auth_service.get_service("drive", "v3")
        self.logger.info("Drive service initialized")

    def search_files(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for files in Google Drive."""
        self.logger.info("Searching files with query: %s", query)

        results = (
            self.service.files()
            .list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, parents, modifiedTime, size)",
            )
            .execute()
        )

        items = results.get("files", [])
        self.logger.info("Found %d files", len(items))

        return items

    def search_by_name(self, name: str, mime_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search files by name."""
        query = f"name contains '{name}'"
        if mime_type:
            query += f" and mimeType='{mime_type}'"

        return self.search_files(query)

    def list_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """List contents of a folder."""
        query = f"'{folder_id}' in parents and trashed=false"
        return self.search_files(query)

    async def upload_file(
        self, file_path: str, parent_folder_id: Optional[str] = None, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to Google Drive."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = name or os.path.basename(file_path)
        self.logger.info("Uploading file: %s as %s", file_path, file_name)

        file_metadata = {"name": file_name}
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        media = MediaFileUpload(file_path, resumable=True)

        file = (
            self.service.files().create(body=file_metadata, media_body=media, fields="id, name, webViewLink").execute()
        )

        self.logger.info("File uploaded successfully: %s", file.get("id"))
        return file

    async def download_file(self, file_id: str, output_path: str) -> str:
        """Download a file from Google Drive."""
        self.logger.info("Downloading file: %s to %s", file_id, output_path)

        request = self.service.files().get_media(fileId=file_id)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with io.BytesIO() as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                self.logger.debug("Download progress: %d%%", int(status.progress() * 100))

            async with aiofiles.open(output_path, "wb") as f:
                await f.write(fh.getvalue())

        self.logger.info("File downloaded successfully to: %s", output_path)
        return output_path

    def create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder."""
        self.logger.info("Creating folder: %s", name)

        file_metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}

        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        folder = self.service.files().create(body=file_metadata, fields="id, name, webViewLink").execute()

        self.logger.info("Folder created successfully: %s", folder.get("id"))
        return folder

    def delete_file(self, file_id: str) -> bool:
        """Delete a file or folder."""
        self.logger.info("Deleting file: %s", file_id)

        try:
            self.service.files().delete(fileId=file_id).execute()
            self.logger.info("File deleted successfully")
            return True
        except Exception as e:
            self.logger.error("Failed to delete file: %s", str(e))
            return False

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get file information."""
        self.logger.info("Getting file info: %s", file_id)

        file_info = (
            self.service.files()
            .get(fileId=file_id, fields="id, name, mimeType, parents, modifiedTime, size, webViewLink")
            .execute()
        )

        return file_info

    def find_folder_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a folder by name."""
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.search_files(query, max_results=1)

        return results[0] if results else None
