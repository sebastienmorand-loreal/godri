"""File handling utilities."""

import logging
import aiofiles
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import mimetypes


class FileHelper:
    """Utility class for file operations."""

    def __init__(self):
        """Initialize file helper."""
        self.logger = logging.getLogger(__name__)

        # MIME type mappings for Google Workspace exports
        self.export_mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "odt": "application/vnd.oasis.opendocument.text",
            "txt": "text/plain",
            "html": "text/html",
            "epub": "application/epub+zip",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ods": "application/vnd.oasis.opendocument.spreadsheet",
            "csv": "text/csv",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "odp": "application/vnd.oasis.opendocument.presentation",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "svg": "image/svg+xml",
        }

        # Google Workspace MIME types
        self.google_mime_types = {
            "document": "application/vnd.google-apps.document",
            "spreadsheet": "application/vnd.google-apps.spreadsheet",
            "presentation": "application/vnd.google-apps.presentation",
            "form": "application/vnd.google-apps.form",
            "folder": "application/vnd.google-apps.folder",
            "drawing": "application/vnd.google-apps.drawing",
        }

    async def read_file(self, file_path: str) -> bytes:
        """Read file content asynchronously.

        Args:
            file_path: Path to file

        Returns:
            File content as bytes
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def write_file(self, file_path: str, content: bytes) -> None:
        """Write content to file asynchronously.

        Args:
            file_path: Path to write file
            content: Content to write
        """
        path = Path(file_path)

        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

    def get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file.

        Args:
            file_path: Path to file

        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def get_export_mime_type(self, format_name: str) -> Optional[str]:
        """Get MIME type for export format.

        Args:
            format_name: Export format (pdf, docx, etc.)

        Returns:
            MIME type or None if not supported
        """
        return self.export_mime_types.get(format_name.lower())

    def get_google_mime_type(self, type_name: str) -> Optional[str]:
        """Get Google Workspace MIME type.

        Args:
            type_name: Google type (document, spreadsheet, etc.)

        Returns:
            MIME type or None if not supported
        """
        return self.google_mime_types.get(type_name.lower())

    def is_google_workspace_file(self, mime_type: str) -> bool:
        """Check if MIME type is a Google Workspace file.

        Args:
            mime_type: MIME type to check

        Returns:
            True if it's a Google Workspace file
        """
        return mime_type.startswith("application/vnd.google-apps.")

    def get_file_extension(self, mime_type: str) -> str:
        """Get file extension for MIME type.

        Args:
            mime_type: MIME type

        Returns:
            File extension (with dot)
        """
        extension_map = {
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.oasis.opendocument.text": ".odt",
            "text/plain": ".txt",
            "text/html": ".html",
            "application/epub+zip": ".epub",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "application/vnd.oasis.opendocument.spreadsheet": ".ods",
            "text/csv": ".csv",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
            "application/vnd.oasis.opendocument.presentation": ".odp",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/svg+xml": ".svg",
        }

        return extension_map.get(mime_type, "")

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem usage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace problematic characters
        import re

        # Replace problematic characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(" .")

        # Ensure it's not empty
        if not sanitized:
            sanitized = "untitled"

        return sanitized

    def ensure_directory(self, directory_path: str) -> None:
        """Ensure directory exists, create if necessary.

        Args:
            directory_path: Path to directory
        """
        Path(directory_path).mkdir(parents=True, exist_ok=True)


# Global file helper instance
file_helper = FileHelper()
