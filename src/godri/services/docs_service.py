"""Google Docs service wrapper."""

import logging
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
