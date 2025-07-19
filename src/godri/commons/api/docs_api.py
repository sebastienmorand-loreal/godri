"""Google Docs API client with async aiohttp."""

import json
import logging
from typing import Dict, Any, List, Optional
from .google_api_client import GoogleApiClient


class DocsApiClient:
    """Async Google Docs API client."""

    def __init__(self, api_client: GoogleApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://docs.googleapis.com/v1"

    async def create_document(
        self, title: str, folder_id: Optional[str] = None, fields: str = "documentId, title, revisionId"
    ) -> Dict[str, Any]:
        """Create a new Google Doc."""
        self.logger.info(f"Creating document: {title}")

        # First create the document
        document_metadata = {"title": title}
        url = f"{self.base_url}/documents"

        result = await self.api_client.make_request("POST", url, data=document_metadata)
        self.logger.info(f"Document created successfully: {result.get('documentId')}")

        # If folder_id specified, move document to folder using Drive API
        if folder_id:
            drive_url = "https://www.googleapis.com/drive/v3"
            file_id = result.get("documentId")

            # Get current parents
            file_info_url = f"{drive_url}/files/{file_id}"
            file_info = await self.api_client.make_request("GET", file_info_url, params={"fields": "parents"})
            current_parents = file_info.get("parents", [])

            # Move to new folder
            move_url = f"{drive_url}/files/{file_id}"
            move_params = {"addParents": folder_id, "removeParents": ",".join(current_parents), "fields": "id, parents"}
            await self.api_client.make_request("PATCH", move_url, params=move_params)
            self.logger.info(f"Document moved to folder: {folder_id}")

        return result

    async def get_document(self, document_id: str, fields: str = "title, body, documentStyle") -> Dict[str, Any]:
        """Get document content and metadata."""
        self.logger.info(f"Getting document: {document_id}")

        params = {"fields": fields}
        url = f"{self.base_url}/documents/{document_id}"

        return await self.api_client.make_request("GET", url, params=params)

    async def get_document_text(self, document_id: str) -> str:
        """Get plain text content from document."""
        self.logger.info(f"Getting document text: {document_id}")

        document = await self.get_document(document_id, "body")

        # Extract text from document structure
        def extract_text_from_content(content):
            text_parts = []
            for element in content:
                if "paragraph" in element:
                    paragraph = element["paragraph"]
                    for text_element in paragraph.get("elements", []):
                        if "textRun" in text_element:
                            text_parts.append(text_element["textRun"]["content"])
                elif "table" in element:
                    # Extract text from table cells
                    table = element["table"]
                    for row in table.get("tableRows", []):
                        for cell in row.get("tableCells", []):
                            cell_text = extract_text_from_content(cell.get("content", []))
                            if cell_text.strip():
                                text_parts.append(cell_text)
            return "".join(text_parts)

        body = document.get("body", {})
        content = body.get("content", [])
        return extract_text_from_content(content)

    async def batch_update(self, document_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch updates on document."""
        self.logger.info(f"Batch updating document: {document_id} with {len(requests)} requests")

        update_data = {"requests": requests}
        url = f"{self.base_url}/documents/{document_id}:batchUpdate"

        result = await self.api_client.make_request("POST", url, data=update_data)
        self.logger.info(f"Batch update completed successfully")
        return result

    async def insert_text(self, document_id: str, text: str, index: int = 1) -> Dict[str, Any]:
        """Insert text at specific position."""
        self.logger.info(f"Inserting text at index {index} in document: {document_id}")

        requests = [{"insertText": {"location": {"index": index}, "text": text}}]

        return await self.batch_update(document_id, requests)

    async def append_text(self, document_id: str, text: str) -> Dict[str, Any]:
        """Append text to end of document."""
        self.logger.info(f"Appending text to document: {document_id}")

        # Get document to find end index
        document = await self.get_document(document_id, "body")
        end_index = document.get("body", {}).get("content", [{}])[-1].get("endIndex", 1) - 1

        return await self.insert_text(document_id, text, end_index)

    async def set_document_content(self, document_id: str, content: str) -> Dict[str, Any]:
        """Replace entire document content."""
        self.logger.info(f"Setting document content: {document_id}")

        # Get document to find content range
        document = await self.get_document(document_id, "body")
        body = document.get("body", {})
        content_elements = body.get("content", [])

        if len(content_elements) < 2:
            # Document is empty, just insert
            return await self.insert_text(document_id, content, 1)

        # Delete existing content (except first and last elements which are structural)
        start_index = content_elements[0].get("endIndex", 1)
        end_index = content_elements[-1].get("startIndex", 1)

        requests = []
        if end_index > start_index:
            requests.append({"deleteContentRange": {"range": {"startIndex": start_index, "endIndex": end_index}}})

        # Insert new content
        requests.append({"insertText": {"location": {"index": start_index}, "text": content}})

        return await self.batch_update(document_id, requests)

    async def insert_markdown_text(self, document_id: str, markdown_text: str, index: int = 1) -> Dict[str, Any]:
        """Insert markdown text with formatting."""
        self.logger.info(f"Inserting markdown text at index {index} in document: {document_id}")

        # Convert markdown to Google Docs requests
        requests = self._markdown_to_requests(markdown_text, index)

        return await self.batch_update(document_id, requests)

    async def set_markdown_content(self, document_id: str, markdown_content: str) -> Dict[str, Any]:
        """Replace document content with markdown formatting."""
        self.logger.info(f"Setting markdown content: {document_id}")

        # First clear content
        await self.set_document_content(document_id, "")

        # Then insert markdown
        return await self.insert_markdown_text(document_id, markdown_content, 1)

    def _markdown_to_requests(self, markdown_text: str, start_index: int) -> List[Dict[str, Any]]:
        """Convert markdown text to Google Docs API requests."""
        requests = []
        current_index = start_index

        # Simple markdown parsing - this could be enhanced
        lines = markdown_text.split("\n")

        for line in lines:
            line = line.rstrip()
            if not line:
                # Empty line
                requests.append({"insertText": {"location": {"index": current_index}, "text": "\n"}})
                current_index += 1
                continue

            # Handle headers
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("# ").strip() + "\n"

                # Insert text
                requests.append({"insertText": {"location": {"index": current_index}, "text": text}})

                # Apply heading style
                end_index = current_index + len(text) - 1  # Exclude newline from formatting
                requests.append(
                    {
                        "updateParagraphStyle": {
                            "range": {"startIndex": current_index, "endIndex": end_index},
                            "paragraphStyle": {"namedStyleType": f"HEADING_{min(level, 6)}"},
                            "fields": "namedStyleType",
                        }
                    }
                )
                current_index += len(text)

            else:
                # Regular text with inline formatting
                processed_text, format_requests = self._process_inline_formatting(line + "\n", current_index)

                requests.append({"insertText": {"location": {"index": current_index}, "text": processed_text}})

                requests.extend(format_requests)
                current_index += len(processed_text)

        return requests

    def _process_inline_formatting(self, text: str, start_index: int) -> tuple[str, List[Dict[str, Any]]]:
        """Process inline markdown formatting (bold, italic)."""
        import re

        format_requests = []

        # Handle bold (**text**)
        bold_pattern = r"\*\*(.*?)\*\*"
        bold_matches = list(re.finditer(bold_pattern, text))

        # Handle italic (*text*)
        italic_pattern = r"(?<!\*)\*([^*]+?)\*(?!\*)"
        italic_matches = list(re.finditer(italic_pattern, text))

        # Remove markdown syntax from text
        clean_text = re.sub(bold_pattern, r"\1", text)
        clean_text = re.sub(italic_pattern, r"\1", clean_text)

        # Calculate offset adjustments due to removed markdown syntax
        offset = 0

        for match in bold_matches:
            # Position in clean text
            clean_start = match.start() - offset
            clean_end = clean_start + len(match.group(1))

            format_requests.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start_index + clean_start, "endIndex": start_index + clean_end},
                        "textStyle": {"bold": True},
                        "fields": "bold",
                    }
                }
            )

            # Adjust offset for removed ** **
            offset += 4

        # Reset offset for italic processing
        offset = 0
        for match in italic_matches:
            # Skip if this is part of a bold section
            if any(bold.start() <= match.start() <= bold.end() for bold in bold_matches):
                continue

            clean_start = match.start() - offset
            clean_end = clean_start + len(match.group(1))

            format_requests.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start_index + clean_start, "endIndex": start_index + clean_end},
                        "textStyle": {"italic": True},
                        "fields": "italic",
                    }
                }
            )

            # Adjust offset for removed * *
            offset += 2

        return clean_text, format_requests

    async def translate_document(
        self,
        document_id: str,
        target_language: str,
        source_language: Optional[str] = None,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> bool:
        """Translate document content."""
        self.logger.info(f"Translating document {document_id} to {target_language}")

        # Get document content
        document = await self.get_document(document_id, "body")
        body = document.get("body", {})
        content_elements = body.get("content", [])

        if not content_elements:
            self.logger.warning("No content found in document")
            return False

        # Determine translation range
        if start_index is None:
            start_index = content_elements[0].get("endIndex", 1)
        if end_index is None:
            end_index = content_elements[-1].get("startIndex", start_index)

        # Extract text to translate
        text_to_translate = []
        current_pos = start_index

        for element in content_elements:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for text_element in paragraph.get("elements", []):
                    if "textRun" in text_element:
                        text_run = text_element["textRun"]
                        text_content = text_run["content"]

                        # Check if this text is in our translation range
                        if current_pos >= start_index and current_pos < end_index:
                            if text_content.strip():  # Only translate non-empty text
                                text_to_translate.append(text_content.strip())

                        current_pos += len(text_content)

        if not text_to_translate:
            self.logger.warning("No translatable text found in specified range")
            return False

        # Translate text using Google Translate API
        translate_url = "https://translation.googleapis.com/language/translate/v2"
        translate_data = {"q": text_to_translate, "target": target_language, "format": "text"}

        if source_language:
            translate_data["source"] = source_language

        translation_result = await self.api_client.make_request("POST", translate_url, data=translate_data)
        translations = translation_result.get("data", {}).get("translations", [])

        if not translations:
            self.logger.error("Translation failed - no results returned")
            return False

        # Replace text in document
        requests = []
        text_index = 0
        current_pos = start_index

        for element in content_elements:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for text_element in paragraph.get("elements", []):
                    if "textRun" in text_element:
                        text_run = text_element["textRun"]
                        text_content = text_run["content"]
                        text_length = len(text_content)

                        # Check if this text is in our translation range
                        if current_pos >= start_index and current_pos < end_index:
                            if text_content.strip() and text_index < len(translations):
                                translated_text = translations[text_index]["translatedText"]

                                # Add whitespace back if original had it
                                if text_content.startswith(" "):
                                    translated_text = " " + translated_text
                                if text_content.endswith(" "):
                                    translated_text = translated_text + " "
                                if text_content.endswith("\n"):
                                    translated_text = translated_text + "\n"

                                # Delete original text and insert translation
                                requests.append(
                                    {
                                        "deleteContentRange": {
                                            "range": {"startIndex": current_pos, "endIndex": current_pos + text_length}
                                        }
                                    }
                                )

                                requests.append(
                                    {"insertText": {"location": {"index": current_pos}, "text": translated_text}}
                                )

                                text_index += 1

                        current_pos += text_length

        if requests:
            await self.batch_update(document_id, requests)
            self.logger.info(f"Document translated successfully - {len(translations)} text segments")
            return True

        return False

    async def create_table(self, document_id: str, rows: int, columns: int, index: int) -> Dict[str, Any]:
        """Insert a table at specified position."""
        self.logger.info(f"Creating {rows}x{columns} table at index {index} in document: {document_id}")

        requests = [{"insertTable": {"location": {"index": index}, "rows": rows, "columns": columns}}]

        return await self.batch_update(document_id, requests)

    async def insert_page_break(self, document_id: str, index: int) -> Dict[str, Any]:
        """Insert page break at specified position."""
        self.logger.info(f"Inserting page break at index {index} in document: {document_id}")

        requests = [{"insertPageBreak": {"location": {"index": index}}}]

        return await self.batch_update(document_id, requests)

    async def apply_text_style(
        self, document_id: str, start_index: int, end_index: int, style: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply text formatting to a range."""
        self.logger.info(f"Applying text style to range {start_index}-{end_index} in document: {document_id}")

        requests = [
            {
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": style,
                    "fields": ",".join(style.keys()),
                }
            }
        ]

        return await self.batch_update(document_id, requests)

    async def apply_paragraph_style(
        self, document_id: str, start_index: int, end_index: int, style: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply paragraph formatting to a range."""
        self.logger.info(f"Applying paragraph style to range {start_index}-{end_index} in document: {document_id}")

        requests = [
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "paragraphStyle": style,
                    "fields": ",".join(style.keys()),
                }
            }
        ]

        return await self.batch_update(document_id, requests)
