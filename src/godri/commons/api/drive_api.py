"""Google Drive API client with async aiohttp."""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from .google_api_client import GoogleApiClient


class DriveApiClient:
    """Async Google Drive API client."""

    def __init__(self, api_client: GoogleApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.googleapis.com/drive/v3"
        self.upload_url = "https://www.googleapis.com/upload/drive/v3/files"

    async def search_files(
        self,
        query: str = "",
        max_results: int = 100,
        fields: str = "id, name, mimeType, parents, modifiedTime, size",
        order_by: str = "modifiedTime desc",
    ) -> Dict[str, Any]:
        """Search for files in Google Drive."""
        self.logger.info(f"Searching files with query: {query}")

        params = {
            "q": query,
            "pageSize": min(max_results, 1000),  # API limit is 1000
            "fields": f"nextPageToken, files({fields})",
            "orderBy": order_by,
        }

        url = f"{self.base_url}/files"
        result = await self.api_client.make_request("GET", url, params=params)

        self.logger.info(f"Found {len(result.get('files', []))} files")
        return result

    async def get_file_info(
        self, file_id: str, fields: str = "id, name, mimeType, parents, modifiedTime, size, webViewLink"
    ) -> Dict[str, Any]:
        """Get file information."""
        self.logger.info(f"Getting file info for: {file_id}")

        params = {"fields": fields}
        url = f"{self.base_url}/files/{file_id}"

        return await self.api_client.make_request("GET", url, params=params)

    async def create_folder(
        self, name: str, parent_folder_id: Optional[str] = None, fields: str = "id, name, webViewLink"
    ) -> Dict[str, Any]:
        """Create a new folder."""
        self.logger.info(f"Creating folder: {name}")

        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}

        if parent_folder_id:
            metadata["parents"] = [parent_folder_id]

        params = {"fields": fields}
        url = f"{self.base_url}/files"

        result = await self.api_client.make_request("POST", url, params=params, data=metadata)
        self.logger.info(f"Folder created successfully: {result.get('id')}")
        return result

    async def upload_file(
        self,
        file_path: str,
        name: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        mime_type: Optional[str] = None,
        fields: str = "id, name, webViewLink",
    ) -> Dict[str, Any]:
        """Upload a file to Google Drive."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = name or file_path.name
        self.logger.info(f"Uploading file: {file_path} as {file_name}")

        metadata = {"name": file_name}
        if parent_folder_id:
            metadata["parents"] = [parent_folder_id]
        if mime_type:
            metadata["mimeType"] = mime_type

        # Use the upload URL with fields parameter
        url = f"{self.upload_url}?fields={fields}"

        result = await self.api_client.upload_file(url, str(file_path), metadata)
        self.logger.info(f"File uploaded successfully: {result.get('id')}")
        return result

    async def download_file(self, file_id: str, output_path: str) -> str:
        """Download a file from Google Drive."""
        self.logger.info(f"Downloading file: {file_id} to {output_path}")

        url = f"{self.base_url}/files/{file_id}"
        params = {"alt": "media"}

        # Make the request and handle the response manually for downloads
        download_url = f"{url}?alt=media"
        result_path = await self.api_client.download_file(download_url, output_path)

        self.logger.info(f"File downloaded successfully to: {result_path}")
        return result_path

    async def download_file_smart(self, file_id: str, output_path: str) -> str:
        """Download a file with smart format conversion for Google Workspace files."""
        self.logger.info(f"Smart downloading file: {file_id} to {output_path}")

        # Get file information to determine MIME type
        file_info = await self.get_file_info(file_id, "mimeType, name")
        mime_type = file_info.get("mimeType", "")
        file_name = file_info.get("name", "unknown")

        self.logger.info(f"File MIME type: {mime_type}")

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
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if mime_type in export_formats:
            # Google Workspace file - export with conversion
            export_info = export_formats[mime_type]
            self.logger.info(f"Exporting Google Workspace file as {export_info['description']}")

            # Ensure output path has correct extension
            if not str(output_path).endswith(export_info["extension"]):
                output_path = output_path.with_suffix(export_info["extension"])

            url = f"{self.base_url}/files/{file_id}/export"
            params = {"mimeType": export_info["mime_type"]}
            export_url = f"{url}?mimeType={export_info['mime_type']}"

            result_path = await self.api_client.download_file(export_url, str(output_path))
            self.logger.info(f"File exported successfully to: {result_path} ({export_info['description']})")
            return result_path
        else:
            # Regular file - download as-is
            self.logger.info("Downloading regular file as-is")
            return await self.download_file(file_id, str(output_path))

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file or folder."""
        self.logger.info(f"Deleting file: {file_id}")

        url = f"{self.base_url}/files/{file_id}"

        try:
            await self.api_client.make_request("DELETE", url)
            self.logger.info("File deleted successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            return False

    async def move_file_to_folder(self, file_id: str, folder_id: str) -> Dict[str, Any]:
        """Move a file to a specific folder."""
        self.logger.info(f"Moving file {file_id} to folder {folder_id}")

        # Get current parents
        file_info = await self.get_file_info(file_id, "parents")
        current_parents = file_info.get("parents", [])

        # Update file with new parent
        url = f"{self.base_url}/files/{file_id}"
        params = {"addParents": folder_id, "removeParents": ",".join(current_parents), "fields": "id, parents"}

        result = await self.api_client.make_request("PATCH", url, params=params)
        self.logger.info(f"File moved successfully to folder: {folder_id}")
        return result

    async def share_file(self, file_id: str, email: str, role: str = "reader", notify: bool = True) -> Dict[str, Any]:
        """Share a file with a user."""
        self.logger.info(f"Sharing file {file_id} with {email} as {role}")

        permission_data = {"type": "user", "role": role, "emailAddress": email}

        params = {"sendNotificationEmail": str(notify).lower()}
        url = f"{self.base_url}/files/{file_id}/permissions"

        result = await self.api_client.make_request("POST", url, params=params, data=permission_data)
        self.logger.info(f"File shared successfully with {email}")
        return result

    async def list_file_revisions(
        self,
        file_id: str,
        fields: str = "nextPageToken,revisions(id,modifiedTime,size,keepForever,lastModifyingUser,mimeType,originalFilename,md5Checksum)",
    ) -> Dict[str, Any]:
        """List all revisions for a file."""
        self.logger.info(f"Listing revisions for file: {file_id}")

        params = {"fields": fields}
        url = f"{self.base_url}/files/{file_id}/revisions"

        result = await self.api_client.make_request("GET", url, params=params)
        revisions = result.get("revisions", [])
        self.logger.info(f"Found {len(revisions)} revisions for file {file_id}")

        # Debug: Log the first revision to see what fields are actually returned
        if revisions:
            self.logger.info(f"DEBUG - Sample revision fields: {list(revisions[0].keys())}")
            self.logger.info(f"DEBUG - Sample revision data: {revisions[0]}")

        return result

    async def get_file_revision(
        self,
        file_id: str,
        revision_id: str,
        fields: str = "id,modifiedTime,size,keepForever,lastModifyingUser,mimeType,originalFilename,md5Checksum",
    ) -> Dict[str, Any]:
        """Get metadata for a specific revision."""
        self.logger.info(f"Getting revision {revision_id} for file: {file_id}")

        params = {"fields": fields}
        url = f"{self.base_url}/files/{file_id}/revisions/{revision_id}"

        result = await self.api_client.make_request("GET", url, params=params)
        self.logger.info(f"Retrieved revision metadata for {revision_id}")
        return result

    async def download_file_revision(self, file_id: str, revision_id: str, output_path: str) -> str:
        """Download specific revision content."""
        self.logger.info(f"Downloading revision {revision_id} for file {file_id}")

        url = f"{self.base_url}/files/{file_id}/revisions/{revision_id}"
        download_url = f"{url}?alt=media"

        result_path = await self.api_client.download_file(download_url, output_path)
        self.logger.info(f"Revision downloaded successfully to: {result_path}")
        return result_path

    async def export_file_revision(
        self, file_id: str, revision_id: str, export_mime_type: str, output_path: str
    ) -> str:
        """Export revision in specific format for Google Workspace files."""
        self.logger.info(f"Exporting revision {revision_id} for file {file_id} as {export_mime_type}")

        url = f"{self.base_url}/files/{file_id}/revisions/{revision_id}/export"
        export_url = f"{url}?mimeType={export_mime_type}"

        result_path = await self.api_client.download_file(export_url, output_path)
        self.logger.info(f"Revision exported successfully to: {result_path}")
        return result_path

    async def keep_file_revision_forever(
        self, file_id: str, revision_id: str, keep_forever: bool = True
    ) -> Dict[str, Any]:
        """Update revision to keep forever or allow auto-deletion."""
        self.logger.info(f"Setting keepForever={keep_forever} for revision {revision_id} of file {file_id}")

        url = f"{self.base_url}/files/{file_id}/revisions/{revision_id}"
        data = {"keepForever": keep_forever}

        result = await self.api_client.make_request("PATCH", url, data=data)
        self.logger.info(f"Revision {revision_id} keepForever updated to {keep_forever}")
        return result

    async def restore_file_revision(self, file_id: str, revision_id: str) -> Dict[str, Any]:
        """Restore a file to a specific revision by copying the revision content to the current file."""
        self.logger.info(f"Restoring file {file_id} to revision {revision_id}")

        try:
            # First, get the revision content by downloading it
            revision_url = f"{self.base_url}/files/{file_id}/revisions/{revision_id}"
            download_url = f"{revision_url}?alt=media"

            # Download the revision content
            revision_content = await self.api_client.make_request("GET", download_url, return_content=True)

            # For Google Workspace files, we need to use the export functionality
            # Get file metadata to determine if it's a Google Workspace file
            file_metadata = await self.get_file_info(file_id, "mimeType,name,parents")
            mime_type = file_metadata.get("mimeType", "")

            if mime_type.startswith("application/vnd.google-apps"):
                # For Google Workspace files, we need to export the old revision in a compatible format
                # and then create a new file with that content
                file_name = file_metadata.get("name", "Unknown")
                restore_name = f"{file_name} (Restored from revision {revision_id})"

                self.logger.info(f"Creating new file '{restore_name}' with content from revision {revision_id}")

                # Determine export format based on file type
                export_formats = {
                    "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                }

                export_mime_type = export_formats.get(mime_type)
                if not export_mime_type:
                    raise ValueError(f"Unsupported Google Workspace file type for restoration: {mime_type}")

                # Export the old revision
                export_url = f"{self.base_url}/files/{file_id}/revisions/{revision_id}/export"
                export_params = {"mimeType": export_mime_type}

                old_content = await self.api_client.make_request(
                    "GET", export_url, params=export_params, return_content=True
                )

                # Create new file with the old content
                # Note: This creates a new file rather than restoring the original
                upload_metadata = {"name": restore_name, "parents": file_metadata.get("parents", [])}

                # Use multipart upload for the new file
                boundary = "----formdata-gdrive-restore"
                upload_data = (
                    (
                        f"--{boundary}\r\n"
                        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
                        f"{json.dumps(upload_metadata)}\r\n"
                        f"--{boundary}\r\n"
                        f"Content-Type: {export_mime_type}\r\n\r\n"
                    ).encode()
                    + old_content
                    + f"\r\n--{boundary}--\r\n".encode()
                )

                upload_headers = {
                    "Content-Type": f"multipart/related; boundary={boundary}",
                    "Content-Length": str(len(upload_data)),
                }

                upload_url = f"{self.base_url}/files?uploadType=multipart"
                result = await self.api_client.make_request(
                    "POST", upload_url, data=upload_data, headers=upload_headers
                )

                self.logger.info(f"Successfully created restored file: {result.get('name')} (ID: {result.get('id')})")

                return {
                    "restored_file_id": result.get("id"),
                    "restored_file_name": restore_name,
                    "original_file_id": file_id,
                    "revision_id": revision_id,
                    "method": "export_and_create",
                    "note": f"Created new file '{restore_name}' with content from revision {revision_id}",
                }

            # For regular files, we can update the content
            url = f"{self.base_url}/files/{file_id}"

            # Update the file with the revision content
            result = await self.api_client.make_request(
                "PATCH", url, data=revision_content, headers={"Content-Type": mime_type}
            )

            self.logger.info(f"Successfully restored file {file_id} to revision {revision_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to restore file revision: {e}")
            raise

    async def copy_file(
        self, file_id: str, name: str, parent_folder_id: Optional[str] = None, fields: str = "id, name, webViewLink"
    ) -> Dict[str, Any]:
        """Copy a file."""
        self.logger.info(f"Copying file {file_id} as {name}")

        metadata = {"name": name}
        if parent_folder_id:
            metadata["parents"] = [parent_folder_id]

        params = {"fields": fields}
        url = f"{self.base_url}/files/{file_id}/copy"

        result = await self.api_client.make_request("POST", url, params=params, data=metadata)
        self.logger.info(f"File copied successfully: {result.get('id')}")
        return result

    async def create_file_from_content(
        self,
        name: str,
        content: str,
        mime_type: str = "text/plain",
        parent_folder_id: Optional[str] = None,
        fields: str = "id, name, webViewLink",
    ) -> Dict[str, Any]:
        """Create a file from text content."""
        self.logger.info(f"Creating file from content: {name}")

        metadata = {"name": name, "mimeType": mime_type}
        if parent_folder_id:
            metadata["parents"] = [parent_folder_id]

        # Create multipart form data
        import aiohttp

        data = aiohttp.FormData()
        data.add_field("metadata", json.dumps(metadata), content_type="application/json")
        data.add_field("file", content, filename=name, content_type=mime_type)

        url = f"{self.upload_url}?fields={fields}"
        result = await self.api_client.make_request("POST", url, files=data)

        self.logger.info(f"File created successfully from content: {result.get('id')}")
        return result

    async def update_file(
        self,
        file_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        fields: str = "id, name, modifiedTime",
    ) -> Dict[str, Any]:
        """Update file metadata and/or content."""
        self.logger.info(f"Updating file: {file_id}")

        if file_path:
            # Update both metadata and content
            url = f"{self.upload_url}/{file_id}?fields={fields}"
            result = await self.api_client.upload_file(url, file_path, metadata)
        else:
            # Update only metadata
            url = f"{self.base_url}/files/{file_id}"
            params = {"fields": fields}
            result = await self.api_client.make_request("PATCH", url, params=params, data=metadata or {})

        self.logger.info(f"File updated successfully: {file_id}")
        return result

    async def list_folder_contents(
        self, folder_id: str, fields: str = "id, name, mimeType, modifiedTime, size"
    ) -> List[Dict[str, Any]]:
        """List contents of a specific folder."""
        query = f"'{folder_id}' in parents and trashed=false"
        result = await self.search_files(query=query, fields=fields)
        return result.get("files", [])

    async def find_folder_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a folder by name."""
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        result = await self.search_files(query=query, max_results=1)
        files = result.get("files", [])
        return files[0] if files else None
