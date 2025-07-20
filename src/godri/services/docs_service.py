"""Google Docs service wrapper."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..commons.api.google_api_client import GoogleApiClient
from ..commons.api.docs_api import DocsApiClient
from ..commons.api.drive_api import DriveApiClient
from .auth_service_new import AuthService


class DocsService:
    """Google Docs operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.docs_api = None
        self.drive_api = None

    async def initialize(self):
        """Initialize the Docs service."""
        credentials = await self.auth_service.authenticate()
        if not credentials:
            raise ValueError("Failed to authenticate with Google Docs")

        api_client = GoogleApiClient(credentials)
        await api_client.initialize()
        self.docs_api = DocsApiClient(api_client)
        self.drive_api = DriveApiClient(api_client)
        self.logger.info("Docs service initialized")

    async def create_document(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Google Doc."""
        self.logger.info("Creating document: %s", title)

        document = await self.docs_api.create_document(title, folder_id)
        document_id = document.get("documentId")

        self.logger.info("Document created successfully: %s", document_id)
        return document

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document content."""
        self.logger.info("Getting document: %s", document_id)

        document = await self.docs_api.get_document(document_id)
        return document

    async def get_document_text(self, document_id: str) -> str:
        """Extract plain text from document."""
        text = await self.docs_api.get_document_text(document_id)
        return text

    async def insert_markdown_text(self, document_id: str, markdown_text: str, index: int = 1) -> Dict[str, Any]:
        """Insert markdown-formatted text into document with proper formatting."""
        self.logger.info("Inserting markdown text into document: %s", document_id)

        result = await self.docs_api.insert_markdown_text(document_id, markdown_text, index)

        self.logger.info("Markdown text inserted successfully")
        return result

    async def set_markdown_content(self, document_id: str, markdown_content: str) -> Dict[str, Any]:
        """Replace entire document content with markdown-formatted content."""
        return await self.docs_api.set_markdown_content(document_id, markdown_content)

    async def insert_text(self, document_id: str, text: str, index: int = 1) -> Dict[str, Any]:
        """Insert text at specified index."""
        self.logger.info("Inserting text into document: %s", document_id)

        result = await self.docs_api.insert_text(document_id, text, index)

        self.logger.info("Text inserted successfully")
        return result

    async def append_text(self, document_id: str, text: str) -> Dict[str, Any]:
        """Append text to the end of document."""
        return await self.docs_api.append_text(document_id, text)

    async def set_document_content(self, document_id: str, content: str) -> Dict[str, Any]:
        """Replace entire document content."""
        return await self.docs_api.set_document_content(document_id, content)

    async def apply_text_style(
        self, document_id: str, start_index: int, end_index: int, style: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply text formatting to a range."""
        self.logger.info("Applying text style to range %d-%d in document: %s", start_index, end_index, document_id)
        return await self.docs_api.apply_text_style(document_id, start_index, end_index, style)

    async def apply_paragraph_style(
        self, document_id: str, start_index: int, end_index: int, style: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply paragraph formatting to a range."""
        self.logger.info("Applying paragraph style to range %d-%d in document: %s", start_index, end_index, document_id)
        return await self.docs_api.apply_paragraph_style(document_id, start_index, end_index, style)

    async def create_table(self, document_id: str, rows: int, columns: int, index: int) -> Dict[str, Any]:
        """Insert a table at specified position."""
        self.logger.info("Creating %dx%d table at index %d in document: %s", rows, columns, index, document_id)
        return await self.docs_api.create_table(document_id, rows, columns, index)

    async def insert_page_break(self, document_id: str, index: int) -> Dict[str, Any]:
        """Insert page break at specified position."""
        self.logger.info("Inserting page break at index %d in document: %s", index, document_id)
        return await self.docs_api.insert_page_break(document_id, index)

    async def translate_document(
        self,
        document_id: str,
        target_language: str,
        source_language: Optional[str] = None,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> bool:
        """Translate document content while preserving formatting."""
        self.logger.info("Translating document: %s to %s", document_id, target_language)

        success = await self.docs_api.translate_document(
            document_id, target_language, source_language, start_index, end_index
        )

        if success:
            self.logger.info("Document translation completed successfully")
        else:
            self.logger.warning("Document translation failed or no content to translate")

        return success

    async def batch_update(self, document_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch updates on document."""
        self.logger.info("Executing batch update with %d requests on document: %s", len(requests), document_id)
        return await self.docs_api.batch_update(document_id, requests)

    # Version Management Methods

    async def list_document_versions(self, document_id: str) -> List[Dict[str, Any]]:
        """List all versions/revisions of a document."""
        self.logger.info("Listing versions for document: %s", document_id)

        try:
            result = await self.drive_api.list_file_revisions(document_id)
            revisions = result.get("revisions", [])

            # Enhance revision data with document-specific information
            for revision in revisions:
                revision["file_type"] = "document"
                revision["mime_type"] = revision.get("mimeType", "application/vnd.google-apps.document")

            self.logger.info("Found %d versions for document %s", len(revisions), document_id)
            return revisions

        except Exception as e:
            self.logger.error("Failed to list document versions: %s", e)
            raise

    async def get_document_version(self, document_id: str, revision_id: str) -> Dict[str, Any]:
        """Get metadata for a specific document version."""
        self.logger.info("Getting version %s for document: %s", revision_id, document_id)

        try:
            revision = await self.drive_api.get_file_revision(document_id, revision_id)
            revision["file_type"] = "document"
            revision["mime_type"] = revision.get("mimeType", "application/vnd.google-apps.document")

            self.logger.info("Retrieved version metadata for %s", revision_id)
            return revision

        except Exception as e:
            self.logger.error("Failed to get document version: %s", e)
            raise

    async def download_document_version(
        self, document_id: str, revision_id: str, output_path: str, format_type: str = "docx"
    ) -> str:
        """Download a specific version of a document in the specified format."""
        self.logger.info("Downloading version %s of document %s as %s", revision_id, document_id, format_type)

        try:
            # Map format types to MIME types
            format_mime_types = {
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "pdf": "application/pdf",
                "txt": "text/plain",
                "html": "text/html",
                "rtf": "application/rtf",
                "odt": "application/vnd.oasis.opendocument.text",
                "epub": "application/epub+zip",
            }

            if format_type not in format_mime_types:
                raise ValueError(f"Unsupported format: {format_type}. Supported: {list(format_mime_types.keys())}")

            export_mime_type = format_mime_types[format_type]

            # Ensure output path has correct extension
            output_path_obj = Path(output_path)
            if not output_path_obj.suffix == f".{format_type}":
                output_path = str(output_path_obj.with_suffix(f".{format_type}"))

            result_path = await self.drive_api.export_file_revision(
                document_id, revision_id, export_mime_type, output_path
            )

            self.logger.info("Version downloaded successfully to: %s", result_path)
            return result_path

        except Exception as e:
            self.logger.error("Failed to download document version: %s", e)
            raise

    async def compare_document_versions(
        self, document_id: str, revision_id_1: str, revision_id_2: str, output_dir: str = "/tmp"
    ) -> Dict[str, Any]:
        """Compare two versions of a document and return detailed diff analysis."""
        self.logger.info("Comparing document %s versions %s vs %s", document_id, revision_id_1, revision_id_2)

        try:
            import json
            import tempfile

            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Download both versions as text for comparison
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Download version 1 as text
                v1_path = temp_path / f"v1_{revision_id_1}.txt"
                await self.download_document_version(document_id, revision_id_1, str(v1_path), "txt")

                # Download version 2 as text
                v2_path = temp_path / f"v2_{revision_id_2}.txt"
                await self.download_document_version(document_id, revision_id_2, str(v2_path), "txt")

                # Read the text content
                with open(v1_path, "r", encoding="utf-8") as f:
                    v1_content = f.read()
                with open(v2_path, "r", encoding="utf-8") as f:
                    v2_content = f.read()

                # Get revision metadata
                v1_metadata = await self.get_document_version(document_id, revision_id_1)
                v2_metadata = await self.get_document_version(document_id, revision_id_2)

                # Perform diff analysis
                diff_result = await self._perform_document_diff(v1_content, v2_content, v1_metadata, v2_metadata)

                # Save comparison result
                comparison_file = output_dir / f"comparison_{revision_id_1}_vs_{revision_id_2}.json"
                with open(comparison_file, "w", encoding="utf-8") as f:
                    json.dump(diff_result, f, indent=2, default=str)

                self.logger.info("Comparison completed successfully. Results saved to: %s", comparison_file)
                return diff_result

        except Exception as e:
            self.logger.error("Failed to compare document versions: %s", e)
            raise

    async def _perform_document_diff(
        self, v1_content: str, v2_content: str, v1_metadata: Dict[str, Any], v2_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform detailed diff analysis between two document contents."""
        try:
            import difflib
            from datetime import datetime

            diff_result = {
                "comparison_summary": {
                    "version_1": {
                        "revision_id": v1_metadata["id"],
                        "modified_time": v1_metadata.get("modifiedTime"),
                        "size": v1_metadata.get("size"),
                        "last_modifying_user": v1_metadata.get("lastModifyingUser", {}).get("displayName"),
                        "word_count": len(v1_content.split()),
                        "character_count": len(v1_content),
                    },
                    "version_2": {
                        "revision_id": v2_metadata["id"],
                        "modified_time": v2_metadata.get("modifiedTime"),
                        "size": v2_metadata.get("size"),
                        "last_modifying_user": v2_metadata.get("lastModifyingUser", {}).get("displayName"),
                        "word_count": len(v2_content.split()),
                        "character_count": len(v2_content),
                    },
                },
                "changes": {
                    "word_count_change": len(v2_content.split()) - len(v1_content.split()),
                    "character_count_change": len(v2_content) - len(v1_content),
                    "size_change": None,
                    "time_difference": None,
                },
                "detailed_analysis": {
                    "content_changes": [],
                    "line_by_line_diff": [],
                    "summary": {},
                },
            }

            # Calculate basic differences
            v1_size = int(v1_metadata.get("size", "0"))
            v2_size = int(v2_metadata.get("size", "0"))
            diff_result["changes"]["size_change"] = v2_size - v1_size

            # Parse modification times
            try:
                v1_time = datetime.fromisoformat(v1_metadata["modifiedTime"].replace("Z", "+00:00"))
                v2_time = datetime.fromisoformat(v2_metadata["modifiedTime"].replace("Z", "+00:00"))
                time_diff = v2_time - v1_time
                diff_result["changes"]["time_difference"] = str(time_diff)
            except (ValueError, TypeError, KeyError):
                diff_result["changes"]["time_difference"] = "Unable to calculate"

            # Perform line-by-line diff
            v1_lines = v1_content.splitlines()
            v2_lines = v2_content.splitlines()

            differ = difflib.unified_diff(v1_lines, v2_lines, lineterm="", n=3)
            diff_lines = list(differ)

            diff_result["detailed_analysis"]["line_by_line_diff"] = diff_lines

            # Count different types of changes
            additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
            deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

            diff_result["detailed_analysis"]["summary"] = {
                "lines_added": additions,
                "lines_deleted": deletions,
                "total_changes": additions + deletions,
            }

            # Add content change analysis
            if v1_content != v2_content:
                diff_result["detailed_analysis"]["content_changes"].append(
                    {
                        "type": "text_content_change",
                        "description": f"Content modified: {additions} lines added, {deletions} lines deleted",
                        "word_change": diff_result["changes"]["word_count_change"],
                        "character_change": diff_result["changes"]["character_count_change"],
                    }
                )

            return diff_result

        except Exception as e:
            self.logger.error("Failed to perform document diff: %s", e)
            raise

    async def keep_document_version_forever(
        self, document_id: str, revision_id: str, keep_forever: bool = True
    ) -> Dict[str, Any]:
        """Mark a document version to be kept forever or allow auto-deletion."""
        self.logger.info("Setting keepForever=%s for version %s of document %s", keep_forever, revision_id, document_id)

        try:
            result = await self.drive_api.keep_file_revision_forever(document_id, revision_id, keep_forever)
            self.logger.info("Version %s keepForever updated to %s", revision_id, keep_forever)
            return result

        except Exception as e:
            self.logger.error("Failed to update version keep forever setting: %s", e)
            raise

    async def restore_document_version(self, document_id: str, revision_id: str) -> Dict[str, Any]:
        """Restore a document to a specific revision by creating a new file with the old content."""
        self.logger.info("Restoring document %s to revision %s", document_id, revision_id)

        try:
            result = await self.drive_api.restore_file_revision(document_id, revision_id)

            # Enhanced result with document-specific information
            result["file_type"] = "document"
            result["original_document_id"] = document_id

            self.logger.info(
                "Successfully restored document. New file: %s (ID: %s)",
                result.get("restored_file_name"),
                result.get("restored_file_id"),
            )
            return result

        except Exception as e:
            self.logger.error("Failed to restore document version: %s", e)
            raise
