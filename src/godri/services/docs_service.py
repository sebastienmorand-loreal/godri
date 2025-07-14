"""Google Docs service wrapper."""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
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

    def _parse_markdown_to_requests(self, markdown_text: str) -> List[Dict[str, Any]]:
        """Parse markdown text and convert to Google Docs API requests."""
        requests = []

        # First, insert all text with minimal formatting
        clean_text = self._strip_markdown_syntax(markdown_text)
        requests.append({"insertText": {"location": {"index": 1}, "text": clean_text}})

        # Then apply formatting based on original markdown
        formatting_requests = self._generate_formatting_requests(markdown_text, clean_text)
        requests.extend(formatting_requests)

        return requests

    def _strip_markdown_syntax(self, markdown_text: str) -> str:
        """Strip markdown syntax and return clean text."""
        # Remove heading markers
        text = re.sub(r"^#{1,6}\s+", "", markdown_text, flags=re.MULTILINE)

        # Remove bold markers
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)

        # Remove italic markers (but not bold)
        text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\1", text)
        text = re.sub(r"(?<!_)_([^_]+?)_(?!_)", r"\1", text)

        return text

    def _generate_formatting_requests(self, original_text: str, clean_text: str) -> List[Dict[str, Any]]:
        """Generate formatting requests based on markdown syntax."""
        requests = []
        lines = original_text.split("\n")
        clean_lines = clean_text.split("\n")
        current_index = 1

        for i, line in enumerate(lines):
            if i < len(clean_lines):
                clean_line = clean_lines[i]

                # Check for headings
                heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
                if heading_match:
                    heading_level = len(heading_match.group(1))
                    heading_text = heading_match.group(2)

                    # Apply heading style
                    requests.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": current_index, "endIndex": current_index + len(clean_line) + 1},
                                "paragraphStyle": self._get_heading_style(heading_level),
                                "fields": "namedStyleType",
                            }
                        }
                    )

                # Apply bold formatting
                for match in re.finditer(r"\*\*(.+?)\*\*", line):
                    bold_text = match.group(1)
                    # Find position in clean text
                    clean_pos = clean_line.find(bold_text)
                    if clean_pos >= 0:
                        requests.append(
                            {
                                "updateTextStyle": {
                                    "range": {
                                        "startIndex": current_index + clean_pos,
                                        "endIndex": current_index + clean_pos + len(bold_text),
                                    },
                                    "textStyle": {"bold": True},
                                    "fields": "bold",
                                }
                            }
                        )

                # Apply italic formatting
                for match in re.finditer(r"(?<!\*)\*([^*]+?)\*(?!\*)", line):
                    italic_text = match.group(1)
                    clean_pos = clean_line.find(italic_text)
                    if clean_pos >= 0:
                        requests.append(
                            {
                                "updateTextStyle": {
                                    "range": {
                                        "startIndex": current_index + clean_pos,
                                        "endIndex": current_index + clean_pos + len(italic_text),
                                    },
                                    "textStyle": {"italic": True},
                                    "fields": "italic",
                                }
                            }
                        )

                current_index += len(clean_line) + 1

        return requests

    def _get_heading_style(self, level: int) -> Dict[str, Any]:
        """Get Google Docs heading style for markdown heading level."""
        heading_styles = {
            1: {"namedStyleType": "HEADING_1"},
            2: {"namedStyleType": "HEADING_2"},
            3: {"namedStyleType": "HEADING_3"},
            4: {"namedStyleType": "HEADING_4"},
            5: {"namedStyleType": "HEADING_5"},
            6: {"namedStyleType": "HEADING_6"},
        }
        return heading_styles.get(level, {"namedStyleType": "NORMAL_TEXT"})

    def _process_inline_formatting(self, text: str, start_index: int) -> Tuple[List[Dict[str, Any]], int]:
        """Process inline markdown formatting (bold, italic, etc.) and return requests."""
        requests = []
        current_text = text
        current_index = start_index

        # Insert the text first
        requests.append({"insertText": {"location": {"index": current_index}, "text": current_text}})

        # Process bold text (**text** or __text__)
        bold_patterns = [r"\*\*(.+?)\*\*", r"__(.+?)__"]
        for pattern in bold_patterns:
            for match in re.finditer(pattern, text):
                start_pos = current_index + match.start()
                end_pos = current_index + match.end()

                # Update text style to bold
                requests.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": start_pos, "endIndex": end_pos},
                            "textStyle": {"bold": True},
                            "fields": "bold",
                        }
                    }
                )

        # Process italic text (*text* or _text_)
        italic_patterns = [r"\*(.+?)\*", r"_(.+?)_"]
        for pattern in italic_patterns:
            for match in re.finditer(pattern, text):
                # Skip if it's part of bold formatting
                if not any(
                    bold_match.start() <= match.start() < bold_match.end()
                    for bold_match in re.finditer(r"\*\*(.+?)\*\*", text)
                ):
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

        return requests, len(current_text)

    def insert_markdown_text(self, document_id: str, markdown_text: str, index: int = 1) -> Dict[str, Any]:
        """Insert markdown-formatted text into document with proper formatting."""
        self.logger.info("Inserting markdown text into document: %s", document_id)

        # Parse markdown and generate requests
        requests = self._parse_markdown_to_requests(markdown_text)

        if not requests:
            return {}

        # Execute batch update
        result = self.service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

        self.logger.info("Markdown text inserted successfully")
        return result

    def set_markdown_content(self, document_id: str, markdown_content: str) -> Dict[str, Any]:
        """Replace entire document content with markdown-formatted content."""
        self.clear_document(document_id)
        return self.insert_markdown_text(document_id, markdown_content, 1)

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

    async def translate_document(
        self,
        document_id: str,
        target_language: str,
        source_language: Optional[str] = None,
        start_index: int = 1,
        end_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Translate document content while preserving formatting."""
        from .translate_service import TranslateService

        self.logger.info("Translating document: %s to %s", document_id, target_language)

        # Get document content
        document = self.get_document(document_id)
        content = document.get("body", {}).get("content", [])

        if not content:
            self.logger.info("No content to translate")
            return {}

        # Initialize translate service
        translate_service = TranslateService(self.auth_service)
        await translate_service.initialize()

        # Determine translation range
        if end_index is None:
            end_index = content[-1].get("endIndex", 1) - 1

        # Extract text elements to translate while preserving structure
        text_elements = []
        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for text_element in paragraph.get("elements", []):
                    if "textRun" in text_element:
                        text_run = text_element["textRun"]
                        element_start = text_run.get("startIndex", 1)
                        element_end = text_run.get("endIndex", 1)

                        # Check if element is within translation range
                        if element_start >= start_index and element_end <= end_index:
                            content_text = text_run.get("content", "")
                            if content_text.strip():  # Only translate non-empty text
                                text_elements.append(
                                    {
                                        "text": content_text,
                                        "start_index": element_start,
                                        "end_index": element_end,
                                        "element": text_element,
                                    }
                                )

        if not text_elements:
            self.logger.info("No text elements found in specified range")
            return {}

        # Translate each text element
        requests = []
        for element_data in text_elements:
            original_text = element_data["text"]

            # Skip if text is just whitespace or formatting characters
            if not original_text.strip() or original_text in ["\n", "\t", " "]:
                continue

            try:
                # Translate the text
                translation_result = translate_service.translate_text(
                    original_text.strip(), target_language, source_language
                )
                translated_text = translation_result["translatedText"]

                # Preserve leading/trailing whitespace
                if original_text.startswith(" ") or original_text.startswith("\t"):
                    prefix = original_text[: len(original_text) - len(original_text.lstrip())]
                    translated_text = prefix + translated_text

                if original_text.endswith(" ") or original_text.endswith("\n"):
                    suffix = original_text[len(original_text.rstrip()) :]
                    translated_text = translated_text + suffix

                # Create replace request
                requests.append(
                    {
                        "replaceAllText": {
                            "containsText": {"text": original_text, "matchCase": True},
                            "replaceText": translated_text,
                        }
                    }
                )

                self.logger.debug("Translating: '%s' -> '%s'", original_text.strip(), translated_text.strip())

            except Exception as e:
                self.logger.error("Failed to translate text '%s': %s", original_text.strip(), str(e))
                continue

        if not requests:
            self.logger.info("No text was translated")
            return {}

        # Execute batch update to replace translated text
        result = self.service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

        self.logger.info("Document translation completed. Processed %d text elements", len(requests))
        return result
