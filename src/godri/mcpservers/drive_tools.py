"""Google Drive MCP tools."""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from .base_tools import BaseTools
from ..commons.api.drive_api import DriveApiClient
from ..commons.utils.file_helper import file_helper


class DriveTools(BaseTools):
    """Google Drive MCP tools."""

    def __init__(self, drive_api: DriveApiClient):
        """Initialize Drive tools.

        Args:
            drive_api: Drive API client instance
        """
        super().__init__()
        self.drive_api = drive_api

    def register_tools(self, server: FastMCP) -> None:
        """Register Drive tools with MCP server."""

        @server.tool()
        async def drive_search(query: str = "", name: str = "", mime_type: str = "", limit: int = 20) -> Dict[str, Any]:
            """Search for files in Google Drive. Use query for general search or name for exact filename matching. Optionally filter by MIME type."""
            try:
                if name:
                    # Search by name with optional MIME type filter
                    search_query = f"name contains '{name}'"
                    if mime_type:
                        search_query += f" and mimeType = '{mime_type}'"
                else:
                    # Use general query
                    search_query = query

                result = await self.drive_api.list_files(search_query, limit)

                files = result.get("files", [])
                return {"files": files, "count": len(files), "success": True}

            except Exception as e:
                return self.handle_error(e, "drive_search")

        @server.tool()
        async def drive_upload(file_path: str, name: str = "", folder_id: str = "") -> Dict[str, Any]:
            """Upload a local file to Google Drive. Optionally specify a parent folder ID and custom name."""
            try:
                # Read file content
                content = await file_helper.read_file(file_path)

                # Get MIME type
                mime_type = file_helper.get_mime_type(file_path)

                # Use custom name or file name
                if not name:
                    import os

                    name = os.path.basename(file_path)

                # Upload file
                result = await self.drive_api.create_file(
                    name=name, mime_type=mime_type, content=content, parent_id=folder_id if folder_id else None
                )

                return {"file": result, "success": True, "message": f"File uploaded successfully: {result.get('name')}"}

            except Exception as e:
                return self.handle_error(e, "drive_upload")

        @server.tool()
        async def drive_download(file_id: str, output_path: str, smart: bool = False) -> Dict[str, Any]:
            """Download a file from Google Drive. Use smart=True for automatic format conversion of Google Workspace files."""
            try:
                # Get file metadata to determine if it's a Google Workspace file
                file_metadata = await self.drive_api.get_file(file_id)
                mime_type = file_metadata.get("mimeType", "")

                if smart and file_helper.is_google_workspace_file(mime_type):
                    # Export Google Workspace file
                    export_mime_type = None

                    # Determine export format based on file extension
                    import os

                    _, ext = os.path.splitext(output_path)
                    if ext:
                        export_mime_type = file_helper.get_export_mime_type(ext[1:])  # Remove dot

                    if not export_mime_type:
                        # Default export formats
                        if "document" in mime_type:
                            export_mime_type = "application/pdf"
                        elif "spreadsheet" in mime_type:
                            export_mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        elif "presentation" in mime_type:
                            export_mime_type = "application/pdf"
                        else:
                            export_mime_type = "application/pdf"

                    content = await self.drive_api.export_file(file_id, export_mime_type)
                else:
                    # Download regular file
                    content = await self.drive_api.download_file(file_id)

                # Write to output path
                await file_helper.write_file(output_path, content)

                return {"success": True, "message": f"File downloaded to: {output_path}", "file_size": len(content)}

            except Exception as e:
                return self.handle_error(e, "drive_download")

        @server.tool()
        async def drive_folder_create(name: str, parent_id: str = "") -> Dict[str, Any]:
            """Create a new folder in Google Drive. Optionally specify a parent folder ID."""
            try:
                result = await self.drive_api.create_folder(name=name, parent_id=parent_id if parent_id else None)

                return {
                    "folder": result,
                    "success": True,
                    "message": f"Folder created successfully: {result.get('name')}",
                }

            except Exception as e:
                return self.handle_error(e, "drive_folder_create")

        @server.tool()
        async def drive_folder_delete(file_id: str) -> Dict[str, Any]:
            """Delete a file or folder from Google Drive by its ID."""
            try:
                success = await self.drive_api.delete_file(file_id)

                return {
                    "success": success,
                    "message": "File/folder deleted successfully" if success else "Delete operation failed",
                }

            except Exception as e:
                return self.handle_error(e, "drive_folder_delete")
