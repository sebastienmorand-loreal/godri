"""Google Docs API wrapper using aiogoogle for full async operations."""

import logging
from typing import Optional, Dict, Any, List, Union
import re

from .google_api_client import GoogleApiClient


class DocsApiClient:
    """Async Google Docs API client using aiogoogle."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Docs API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self._service = None

    async def _get_service(self):
        """Get or create Docs service."""
        if self._service is None:
            self._service = await self.api_client.discover_service("docs", "v1")
        return self._service

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document content and metadata.

        Args:
            document_id: Google Docs document ID

        Returns:
            Document data
        """
        service = await self._get_service()
        return await self.api_client.execute_request(service, "documents.get", documentId=document_id)

    async def create_document(self, title: str) -> Dict[str, Any]:
        """Create a new document.

        Args:
            title: Document title

        Returns:
            Created document metadata
        """
        service = await self._get_service()
        body = {"title": title}
        return await self.api_client.execute_request(service, "documents.create", body=body)

    async def batch_update(self, document_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on document.

        Args:
            document_id: Google Docs document ID
            requests: List of update requests

        Returns:
            Update response
        """
        service = await self._get_service()
        body = {"requests": requests}
        return await self.api_client.execute_request(
            service, "documents.batchUpdate", documentId=document_id, body=body
        )

    async def get_document_text(self, document_id: str, plain_text: bool = False) -> str:
        """Get document text content.

        Args:
            document_id: Google Docs document ID
            plain_text: If True, return plain text without formatting

        Returns:
            Document text content
        """
        document = await self.get_document(document_id)
        return self._extract_text_from_document(document, plain_text)

    async def insert_text(self, document_id: str, text: str, index: int = 1, markdown: bool = False) -> Dict[str, Any]:
        """Insert text at specified index.

        Args:
            document_id: Google Docs document ID
            text: Text to insert
            index: Position to insert text (1-based)
            markdown: If True, apply basic markdown formatting

        Returns:
            Update response
        """
        requests = []

        if markdown:
            # Parse markdown and create formatted text requests
            requests.extend(self._create_markdown_requests(text, index))
        else:
            # Simple text insertion
            requests.append({"insertText": {"location": {"index": index}, "text": text}})

        return await self.batch_update(document_id, requests)

    async def replace_text(
        self, document_id: str, old_text: str, new_text: str, markdown: bool = False
    ) -> Dict[str, Any]:
        """Replace text in document.

        Args:
            document_id: Google Docs document ID
            old_text: Text to find and replace
            new_text: Replacement text
            markdown: If True, apply basic markdown formatting to new text

        Returns:
            Update response
        """
        requests = []

        if markdown:
            # Replace with formatted text
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {"text": old_text, "matchCase": False},
                        "replaceText": "",  # Remove old text first
                    }
                }
            )
            # Then insert formatted text (would need to track positions)
            # For simplicity, just replace with plain text for now
            requests.append(
                {"replaceAllText": {"containsText": {"text": old_text, "matchCase": False}, "replaceText": new_text}}
            )
        else:
            requests.append(
                {"replaceAllText": {"containsText": {"text": old_text, "matchCase": False}, "replaceText": new_text}}
            )

        return await self.batch_update(document_id, requests)

    async def replace_content(
        self,
        document_id: str,
        content: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        markdown: bool = False,
    ) -> Dict[str, Any]:
        """Replace document content in specified range.

        Args:
            document_id: Google Docs document ID
            content: New content
            start_index: Start position (1-based, None for beginning)
            end_index: End position (1-based, None for end)
            markdown: If True, apply basic markdown formatting

        Returns:
            Update response
        """
        if start_index is None or end_index is None:
            # Get document to determine range
            document = await self.get_document(document_id)
            total_length = self._get_document_length(document)

            if start_index is None:
                start_index = 1
            if end_index is None:
                end_index = total_length

        requests = []

        # Delete existing content in range
        if end_index > start_index:
            requests.append({"deleteContentRange": {"range": {"startIndex": start_index, "endIndex": end_index}}})

        # Insert new content
        if markdown:
            requests.extend(self._create_markdown_requests(content, start_index))
        else:
            requests.append({"insertText": {"location": {"index": start_index}, "text": content}})

        return await self.batch_update(document_id, requests)

    async def format_text(
        self,
        document_id: str,
        start_index: int,
        end_index: int,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        font_size: Optional[int] = None,
        color: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Apply formatting to text range.

        Args:
            document_id: Google Docs document ID
            start_index: Start position (1-based)
            end_index: End position (1-based)
            bold: Apply bold formatting
            italic: Apply italic formatting
            underline: Apply underline formatting
            font_size: Font size in points
            color: Text color as RGB dict (values 0.0-1.0)

        Returns:
            Update response
        """
        text_style = {}

        if bold is not None:
            text_style["bold"] = bold
        if italic is not None:
            text_style["italic"] = italic
        if underline is not None:
            text_style["underline"] = underline
        if font_size is not None:
            text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
        if color is not None:
            text_style["foregroundColor"] = {"color": {"rgbColor": color}}

        requests = [
            {
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": text_style,
                    "fields": ",".join(text_style.keys()),
                }
            }
        ]

        return await self.batch_update(document_id, requests)

    async def insert_page_break(self, document_id: str, index: int) -> Dict[str, Any]:
        """Insert page break at specified position.

        Args:
            document_id: Google Docs document ID
            index: Position to insert page break (1-based)

        Returns:
            Update response
        """
        requests = [{"insertPageBreak": {"location": {"index": index}}}]

        return await self.batch_update(document_id, requests)

    async def insert_table(self, document_id: str, index: int, rows: int, columns: int) -> Dict[str, Any]:
        """Insert table at specified position.

        Args:
            document_id: Google Docs document ID
            index: Position to insert table (1-based)
            rows: Number of rows
            columns: Number of columns

        Returns:
            Update response
        """
        requests = [{"insertTable": {"location": {"index": index}, "rows": rows, "columns": columns}}]

        return await self.batch_update(document_id, requests)

    def _extract_text_from_document(self, document: Dict[str, Any], plain_text: bool = False) -> str:
        """Extract text content from document structure.

        Args:
            document: Document data from API
            plain_text: If True, return plain text without formatting

        Returns:
            Extracted text
        """
        content = document.get("body", {}).get("content", [])
        text_parts = []

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                elements = paragraph.get("elements", [])

                for elem in elements:
                    if "textRun" in elem:
                        text_content = elem["textRun"].get("content", "")
                        text_parts.append(text_content)

        return "".join(text_parts)

    def _get_document_length(self, document: Dict[str, Any]) -> int:
        """Get total character length of document.

        Args:
            document: Document data from API

        Returns:
            Document length in characters
        """
        content = document.get("body", {}).get("content", [])
        total_length = 0

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                elements = paragraph.get("elements", [])

                for elem in elements:
                    if "textRun" in elem:
                        text_content = elem["textRun"].get("content", "")
                        total_length += len(text_content)

        return total_length

    def _create_markdown_requests(self, text: str, start_index: int) -> List[Dict[str, Any]]:
        """Create batch update requests for markdown-formatted text.

        Args:
            text: Markdown text
            start_index: Starting position

        Returns:
            List of batch update requests
        """
        requests = []
        current_index = start_index

        # Simple markdown parsing - handle bold, italic, and headers
        lines = text.split("\n")

        for line in lines:
            if line.startswith("# "):
                # Header 1
                header_text = line[2:] + "\n"
                requests.append({"insertText": {"location": {"index": current_index}, "text": header_text}})

                # Apply heading style
                requests.append(
                    {
                        "updateParagraphStyle": {
                            "range": {"startIndex": current_index, "endIndex": current_index + len(header_text) - 1},
                            "paragraphStyle": {"namedStyleType": "HEADING_1"},
                            "fields": "namedStyleType",
                        }
                    }
                )

                current_index += len(header_text)

            elif line.startswith("## "):
                # Header 2
                header_text = line[3:] + "\n"
                requests.append({"insertText": {"location": {"index": current_index}, "text": header_text}})

                requests.append(
                    {
                        "updateParagraphStyle": {
                            "range": {"startIndex": current_index, "endIndex": current_index + len(header_text) - 1},
                            "paragraphStyle": {"namedStyleType": "HEADING_2"},
                            "fields": "namedStyleType",
                        }
                    }
                )

                current_index += len(header_text)

            else:
                # Regular text with inline formatting
                line_with_newline = line + "\n"
                requests.append({"insertText": {"location": {"index": current_index}, "text": line_with_newline}})

                # Apply bold and italic formatting
                bold_pattern = r"\*\*(.*?)\*\*"
                italic_pattern = r"\*(.*?)\*"

                # Handle bold text
                for match in re.finditer(bold_pattern, line):
                    start_pos = current_index + match.start()
                    end_pos = current_index + match.end()

                    requests.append(
                        {
                            "updateTextStyle": {
                                "range": {"startIndex": start_pos, "endIndex": end_pos},
                                "textStyle": {"bold": True},
                                "fields": "bold",
                            }
                        }
                    )

                # Handle italic text (excluding bold)
                for match in re.finditer(italic_pattern, line):
                    if not re.search(r"\*\*.*?" + re.escape(match.group()) + r".*?\*\*", line):
                        start_pos = current_index + match.start()
                        end_pos = current_index + match.end()

                        requests.append(
                            {
                                "updateTextStyle": {
                                    "range": {"startIndex": start_pos, "endIndex": end_pos},
                                    "textStyle": {"italic": True},
                                    "fields": "italic",
                                }
                            }
                        )

                current_index += len(line_with_newline)

        return requests
