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

    async def download_file_smart(self, file_id: str, output_path: str) -> str:
        """Download a file with smart format conversion based on file type."""
        self.logger.info("Smart downloading file: %s to %s", file_id, output_path)

        # Get file information to determine MIME type
        file_info = self.get_file_info(file_id)
        mime_type = file_info.get("mimeType", "")
        file_name = file_info.get("name", "unknown")

        self.logger.info("File MIME type: %s", mime_type)

        # Define export formats for Google Workspace files
        export_formats = {
            "application/vnd.google-apps.document": {
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "extension": ".docx",
                "description": "Word format",
            },
            "application/vnd.google-apps.spreadsheet": {
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "extension": ".xlsx",
                "description": "Excel format",
            },
            "application/vnd.google-apps.presentation": {
                "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "extension": ".pptx",
                "description": "PowerPoint format",
            },
            "application/vnd.google-apps.drawing": {
                "mime_type": "application/pdf",
                "extension": ".pdf",
                "description": "PDF format",
            },
            "application/vnd.google-apps.form": {
                "mime_type": "application/pdf",
                "extension": ".pdf",
                "description": "PDF format",
            },
            "application/vnd.google-apps.script": {
                "mime_type": "application/vnd.google-apps.script+json",
                "extension": ".json",
                "description": "Apps Script JSON format",
            },
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if mime_type in export_formats:
            # Google Workspace file - export with conversion
            export_info = export_formats[mime_type]
            self.logger.info("Exporting Google Workspace file as %s", export_info["description"])

            # Ensure output path has correct extension
            if not output_path.endswith(export_info["extension"]):
                base_path = os.path.splitext(output_path)[0]
                output_path = base_path + export_info["extension"]

            request = self.service.files().export_media(fileId=file_id, mimeType=export_info["mime_type"])

            with io.BytesIO() as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    self.logger.debug("Export progress: %d%%", int(status.progress() * 100))

                async with aiofiles.open(output_path, "wb") as f:
                    await f.write(fh.getvalue())

            self.logger.info("File exported successfully to: %s (%s)", output_path, export_info["description"])

        else:
            # Regular file - download as-is
            self.logger.info("Downloading regular file as-is")
            request = self.service.files().get_media(fileId=file_id)

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
