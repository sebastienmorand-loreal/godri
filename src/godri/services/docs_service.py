"""Google Docs service wrapper."""

import logging
from typing import Dict, Any, List, Optional
from .auth_service import AuthService


class DocsService:
    """Google Docs operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.drive_service = None

    async def initialize(self):
        """Initialize the Docs service."""
        await self.auth_service.authenticate()
        self.service = self.auth_service.get_service("docs", "v1")
        self.drive_service = self.auth_service.get_service("drive", "v3")
        self.logger.info("Docs service initialized")

    def create_document(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Google Doc."""
        self.logger.info("Creating document: %s", title)

        document = self.service.documents().create(body={"title": title}).execute()
        document_id = document.get("documentId")

        if folder_id:
            self.drive_service.files().update(fileId=document_id, addParents=folder_id, fields="id, parents").execute()
            self.logger.info("Document moved to folder: %s", folder_id)

        self.logger.info("Document created successfully: %s", document_id)
        return document

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document content."""
        self.logger.info("Getting document: %s", document_id)

        document = self.service.documents().get(documentId=document_id).execute()
        return document

    def get_document_text(self, document_id: str) -> str:
        """Extract plain text from document."""
        document = self.get_document(document_id)
        content = document.get("body", {}).get("content", [])

        text_parts = []
        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for text_element in paragraph.get("elements", []):
                    if "textRun" in text_element:
                        text_parts.append(text_element["textRun"]["content"])

        return "".join(text_parts)

    def insert_text(self, document_id: str, text: str, index: int = 1) -> Dict[str, Any]:
        """Insert text at specified index."""
        self.logger.info("Inserting text into document: %s", document_id)

        requests = [{"insertText": {"location": {"index": index}, "text": text}}]

        result = self.service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

        self.logger.info("Text inserted successfully")
        return result

    def replace_text(self, document_id: str, old_text: str, new_text: str) -> Dict[str, Any]:
        """Replace all occurrences of text."""
        self.logger.info("Replacing text in document: %s", document_id)

        requests = [
            {"replaceAllText": {"containsText": {"text": old_text, "matchCase": False}, "replaceText": new_text}}
        ]

        result = self.service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

        self.logger.info("Text replaced successfully")
        return result

    def append_text(self, document_id: str, text: str) -> Dict[str, Any]:
        """Append text to the end of document."""
        document = self.get_document(document_id)
        end_index = document.get("body", {}).get("content", [{}])[-1].get("endIndex", 1) - 1

        return self.insert_text(document_id, text, end_index)

    def format_text(
        self,
        document_id: str,
        start_index: int,
        end_index: int,
        bold: bool = False,
        italic: bool = False,
        font_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Format text in document."""
        self.logger.info("Formatting text in document: %s", document_id)

        text_style = {}
        if bold:
            text_style["bold"] = True
        if italic:
            text_style["italic"] = True
        if font_size:
            text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}

        requests = [
            {
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": text_style,
                    "fields": ",".join(text_style.keys()),
                }
            }
        ]

        result = self.service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

        self.logger.info("Text formatted successfully")
        return result

    def clear_document(self, document_id: str) -> Dict[str, Any]:
        """Clear all content from document."""
        self.logger.info("Clearing document: %s", document_id)

        document = self.get_document(document_id)
        content = document.get("body", {}).get("content", [])

        if len(content) > 1:
            end_index = content[-1].get("endIndex", 1) - 1

            requests = [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index}}}]

            result = self.service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

            self.logger.info("Document cleared successfully")
            return result

        return {}

    def set_document_content(self, document_id: str, content: str) -> Dict[str, Any]:
        """Replace entire document content."""
        self.clear_document(document_id)
        return self.insert_text(document_id, content, 1)
