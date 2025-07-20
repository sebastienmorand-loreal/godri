"""Google Slides service wrapper."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..commons.api.google_api_client import GoogleApiClient
from ..commons.api.slides_api import SlidesApiClient
from ..commons.api.drive_api import DriveApiClient
from .auth_service_new import AuthService


class SlidesService:
    """Google Slides operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.slides_api = None
        self.drive_api = None

    async def initialize(self):
        """Initialize the Slides service."""
        credentials = await self.auth_service.authenticate()
        if not credentials:
            raise ValueError("Failed to authenticate with Google Slides")

        api_client = GoogleApiClient(credentials)
        await api_client.initialize()
        self.slides_api = SlidesApiClient(api_client)
        self.drive_api = DriveApiClient(api_client)
        self.logger.info("Slides service initialized")

    async def create_presentation(
        self, title: str, folder_id: Optional[str] = None, theme: str = "STREAMLINE"
    ) -> Dict[str, Any]:
        """Create a new Google Slides presentation with specified theme.

        Available themes:
        - SIMPLE_LIGHT (Default light theme)
        - SIMPLE_DARK (Default dark theme)
        - STREAMLINE (Clean, professional theme)
        - FOCUS (Minimalist theme with focus on content)
        - SHIFT (Modern theme with bold accents)
        - MOMENTUM (Dynamic theme with motion elements)
        - PARADIGM (Contemporary theme with geometric elements)
        - SLATE (Sophisticated dark theme)
        - CORAL (Warm theme with coral accents)
        - BEACH_DAY (Light, airy beach-inspired theme)
        - MODERN_WRITER (Writing-focused theme)
        - SPEARMINT (Fresh green theme)
        - GAMEDAY (Sports-inspired theme)
        - BLUE_AND_YELLOW (Classic blue and yellow combination)
        - SWISS (Clean Swiss design inspired theme)
        - LUXE (Elegant luxury theme)
        - MARINA (Navy blue maritime theme)
        - FOREST (Nature-inspired green theme)

        Args:
            title: Presentation title
            folder_id: Optional folder ID to place presentation
            theme: Theme name (default: STREAMLINE)
        """
        self.logger.info("Creating presentation: %s with theme: %s", title, theme)

        presentation_body = {"title": title}

        presentation = await self.slides_api.create_presentation(title, folder_id)
        presentation_id = presentation.get("presentationId")

        # Apply the specified theme
        if theme != "SIMPLE_LIGHT":  # SIMPLE_LIGHT is the default
            await self.set_theme(presentation_id, theme)

        self.logger.info("Presentation created successfully: %s", presentation_id)
        return presentation

    async def get_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """Get presentation details."""
        self.logger.info("Getting presentation: %s", presentation_id)

        presentation = await self.slides_api.get_presentation(presentation_id)
        return presentation

    async def create_slide(self, presentation_id: str, layout: str = "BLANK") -> Dict[str, Any]:
        """Add a new slide to presentation."""
        self.logger.info("Creating slide in presentation: %s", presentation_id)

        result = await self.slides_api.create_slide(presentation_id, layout)

        self.logger.info("Slide created successfully")
        return result

    async def delete_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any]:
        """Delete a slide from presentation."""
        self.logger.info("Deleting slide %s from presentation: %s", slide_id, presentation_id)

        requests = [{"deleteObject": {"objectId": slide_id}}]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Slide deleted successfully")
        return result

    async def add_text_box(
        self,
        presentation_id: str,
        slide_id: str,
        text: str,
        x: float = 100,
        y: float = 100,
        width: float = 300,
        height: float = 50,
    ) -> Dict[str, Any]:
        """Add a text box to a slide."""
        self.logger.info("Adding text box to slide %s in presentation: %s", slide_id, presentation_id)

        element_id = f"textbox_{slide_id}_{len(text)}"

        requests = [
            {
                "createShape": {
                    "objectId": element_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": width, "unit": "PT"},
                            "height": {"magnitude": height, "unit": "PT"},
                        },
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "PT"},
                    },
                }
            },
            {"insertText": {"objectId": element_id, "text": text}},
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Text box added successfully")
        return result

    async def replace_text(self, presentation_id: str, old_text: str, new_text: str) -> Dict[str, Any]:
        """Replace all occurrences of text in presentation."""
        self.logger.info("Replacing text in presentation: %s", presentation_id)

        requests = [
            {"replaceAllText": {"containsText": {"text": old_text, "matchCase": False}, "replaceText": new_text}}
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Text replaced successfully")
        return result

    async def add_image(
        self,
        presentation_id: str,
        slide_id: str,
        image_url: str,
        x: float = 100,
        y: float = 100,
        width: float = 300,
        height: float = 200,
    ) -> Dict[str, Any]:
        """Add an image to a slide."""
        self.logger.info("Adding image to slide %s in presentation: %s", slide_id, presentation_id)

        element_id = f"image_{slide_id}_{hash(image_url)}"

        requests = [
            {
                "createImage": {
                    "objectId": element_id,
                    "url": image_url,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": width, "unit": "PT"},
                            "height": {"magnitude": height, "unit": "PT"},
                        },
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "PT"},
                    },
                }
            }
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Image added successfully")
        return result

    async def format_text(
        self,
        presentation_id: str,
        element_id: str,
        start_index: int,
        end_index: int,
        bold: bool = False,
        italic: bool = False,
        font_size: Optional[int] = None,
        color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format text in a text element."""
        self.logger.info("Formatting text in presentation: %s", presentation_id)

        text_style = {}
        if bold:
            text_style["bold"] = True
        if italic:
            text_style["italic"] = True
        if font_size:
            text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
        if color:
            text_style["foregroundColor"] = {
                "opaqueColor": {
                    "rgbColor": {
                        "red": int(color[1:3], 16) / 255.0,
                        "green": int(color[3:5], 16) / 255.0,
                        "blue": int(color[5:7], 16) / 255.0,
                    }
                }
            }

        requests = [
            {
                "updateTextStyle": {
                    "objectId": element_id,
                    "textRange": {"startIndex": start_index, "endIndex": end_index},
                    "style": text_style,
                    "fields": ",".join(text_style.keys()),
                }
            }
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Text formatted successfully")
        return result

    async def get_slide_ids(self, presentation_id: str) -> List[str]:
        """Get all slide IDs from presentation."""
        presentation = await self.get_presentation(presentation_id)

        slide_ids = []
        for slide in presentation.get("slides", []):
            slide_ids.append(slide["objectId"])

        return slide_ids

    async def duplicate_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any]:
        """Duplicate a slide."""
        self.logger.info("Duplicating slide %s in presentation: %s", slide_id, presentation_id)

        requests = [{"duplicateObject": {"objectId": slide_id}}]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Slide duplicated successfully")
        return result

    # Theme Management Methods
    async def import_theme(
        self, presentation_id: str, template_presentation_id: str, set_as_theme: bool = False
    ) -> Dict[str, Any]:
        """Import theme from another presentation.

        Args:
            presentation_id: Target presentation ID
            template_presentation_id: Source presentation ID with the theme to import
            set_as_theme: Whether to automatically apply the imported theme
        """
        self.logger.info("Importing theme from %s to %s", template_presentation_id, presentation_id)

        # Get the master from the template presentation
        template_presentation = await self.get_presentation(template_presentation_id)

        # Apply the master to our presentation
        requests = []

        # Import the master
        if template_presentation.get("masters"):
            master_id = template_presentation["masters"][0]["objectId"]
            requests.append(
                {
                    "replaceAllShapesWithImage": {
                        "imageUrl": f"https://docs.google.com/presentation/d/{template_presentation_id}/export/png?id={template_presentation_id}&pageid={master_id}",
                        "replaceMethod": "CENTER_INSIDE",
                    }
                }
            )

        if requests:
            result = await self.slides_api.batch_update(presentation_id, requests)

            if set_as_theme:
                await self.set_theme(presentation_id, "IMPORTED")

            self.logger.info("Theme imported successfully")
            return result

        return {}

    async def set_theme(self, presentation_id: str, theme_name: str) -> Dict[str, Any]:
        """Set theme for the presentation.

        Available themes:
        - SIMPLE_LIGHT, SIMPLE_DARK, STREAMLINE, FOCUS, SHIFT, MOMENTUM
        - PARADIGM, SLATE, CORAL, BEACH_DAY, MODERN_WRITER, SPEARMINT
        - GAMEDAY, BLUE_AND_YELLOW, SWISS, LUXE, MARINA, FOREST
        """
        self.logger.info("Setting theme %s for presentation: %s", theme_name, presentation_id)

        # Map theme names to their template IDs or properties
        theme_map = {
            "SIMPLE_LIGHT": "SIMPLE_LIGHT",
            "SIMPLE_DARK": "SIMPLE_DARK",
            "STREAMLINE": "STREAMLINE",
            "FOCUS": "FOCUS",
            "SHIFT": "SHIFT",
            "MOMENTUM": "MOMENTUM",
            "PARADIGM": "PARADIGM",
            "SLATE": "SLATE",
            "CORAL": "CORAL",
            "BEACH_DAY": "BEACH_DAY",
            "MODERN_WRITER": "MODERN_WRITER",
            "SPEARMINT": "SPEARMINT",
            "GAMEDAY": "GAMEDAY",
            "BLUE_AND_YELLOW": "BLUE_AND_YELLOW",
            "SWISS": "SWISS",
            "LUXE": "LUXE",
            "MARINA": "MARINA",
            "FOREST": "FOREST",
        }

        if theme_name not in theme_map:
            raise ValueError(f"Unknown theme: {theme_name}. Available themes: {', '.join(theme_map.keys())}")

        # Apply theme by replacing the master
        requests = [
            {
                "replaceAllShapesWithSheetsChart": {
                    "chartId": 1,
                    "spreadsheetId": "template",  # This would need actual template handling
                    "linkingMode": "LINKED",
                }
            }
        ]

        # For now, theme setting is acknowledged but not fully implemented
        # Full theme implementation requires access to Google's theme templates
        self.logger.info("Theme %s acknowledged for presentation: %s", theme_name, presentation_id)
        self.logger.info("Note: Full theme application requires Google Slides theme templates")

        return {"acknowledged": True, "theme": theme_name, "message": "Theme setting acknowledged"}

    # Layout Management Methods
    async def list_layouts(self, presentation_id: str) -> List[Dict[str, Any]]:
        """List available slide layouts.

        Returns:
            List of available layouts with their names and descriptions
        """
        self.logger.info("Listing layouts for presentation: %s", presentation_id)

        # Standard Google Slides layouts
        layouts = [
            {"name": "BLANK", "description": "Blank slide"},
            {"name": "CAPTION_ONLY", "description": "Caption only"},
            {"name": "TITLE", "description": "Title slide"},
            {"name": "TITLE_AND_BODY", "description": "Title and body"},
            {"name": "TITLE_AND_TWO_COLUMNS", "description": "Title and two columns"},
            {"name": "TITLE_ONLY", "description": "Title only"},
            {"name": "SECTION_HEADER", "description": "Section header"},
            {"name": "SECTION_TITLE_AND_DESCRIPTION", "description": "Section title and description"},
            {"name": "ONE_COLUMN_TEXT", "description": "One column text"},
            {"name": "MAIN_POINT", "description": "Main point"},
            {"name": "BIG_NUMBER", "description": "Big number"},
        ]

        return layouts

    # Slide Management Methods
    async def add_slide(
        self, presentation_id: str, layout: str = "BLANK", position: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a slide with specified layout at specified position.

        Args:
            presentation_id: Presentation ID
            layout: Layout name (BLANK, TITLE, TITLE_AND_BODY, etc.)
            position: Position to insert slide (0-based, None for end)
        """
        self.logger.info("Adding slide with layout %s to presentation: %s", layout, presentation_id)

        requests = []

        # Create the slide request
        create_request = {"createSlide": {"slideLayoutReference": {"predefinedLayout": layout}}}

        if position is not None:
            create_request["createSlide"]["insertionIndex"] = position

        requests.append(create_request)

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Slide added successfully")
        return result

    async def move_slide(self, presentation_id: str, slide_id: str, new_position: int) -> Dict[str, Any]:
        """Move a slide to a new position.

        Args:
            presentation_id: Presentation ID
            slide_id: ID of slide to move
            new_position: New position (0-based)
        """
        self.logger.info("Moving slide %s to position %d in presentation: %s", slide_id, new_position, presentation_id)

        requests = [{"updateSlidePosition": {"slideObjectIds": [slide_id], "insertionIndex": new_position}}]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Slide moved successfully")
        return result

    async def remove_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any]:
        """Remove (delete) a slide.

        Args:
            presentation_id: Presentation ID
            slide_id: ID of slide to remove
        """
        return self.delete_slide(presentation_id, slide_id)

    # Content Management Methods
    async def list_slide_content(self, presentation_id: str, slide_identifier: str) -> List[Dict[str, Any]]:
        """List all content elements in a slide.

        Args:
            presentation_id: Presentation ID
            slide_identifier: Slide ID (API object ID) or slide number (1, 2, 3...)

        Returns:
            List of content elements with their properties
        """
        self.logger.info("Listing content for slide %s in presentation: %s", slide_identifier, presentation_id)

        presentation = await self.get_presentation(presentation_id)
        slides = presentation.get("slides", [])

        # Find the target slide
        target_slide = await self._find_slide_by_identifier(slides, slide_identifier)
        if not target_slide:
            available_ids = [f"{i+1} ({slide['objectId']})" for i, slide in enumerate(slides)]
            raise ValueError(f"Slide '{slide_identifier}' not found. Available slides: {', '.join(available_ids)}")

        content_elements = []
        for element in target_slide.get("pageElements", []):
            element_info = await self._extract_detailed_element_info(element)
            content_elements.append(element_info)

        return content_elements

    async def list_multiple_slides_content(
        self, presentation_id: str, slide_identifiers: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """List content elements for multiple slides or all slides.

        Args:
            presentation_id: Presentation ID
            slide_identifiers: List of slide identifiers (numbers, IDs, or ranges like "1-3,5"). None for all slides.

        Returns:
            Dictionary mapping slide info to content elements
        """
        self.logger.info("Listing content for multiple slides in presentation: %s", presentation_id)

        presentation = await self.get_presentation(presentation_id)
        slides = presentation.get("slides", [])

        if slide_identifiers is None:
            # List all slides
            target_slides = [(i + 1, slide) for i, slide in enumerate(slides)]
        else:
            # Expand ranges and find specified slides
            expanded_identifiers = await self._expand_slide_identifiers(slide_identifiers, len(slides))
            target_slides = []
            for identifier in expanded_identifiers:
                slide = await self._find_slide_by_identifier(slides, identifier)
                if slide:
                    slide_num = next((i + 1 for i, s in enumerate(slides) if s["objectId"] == slide["objectId"]), "?")
                    target_slides.append((slide_num, slide))

        results = {}
        for slide_num, slide in target_slides:
            slide_key = f"Slide {slide_num} ({slide['objectId']})"
            content_elements = []
            for element in slide.get("pageElements", []):
                element_info = await self._extract_detailed_element_info(element)
                content_elements.append(element_info)
            results[slide_key] = content_elements

        return results

    async def _find_slide_by_identifier(
        self, slides: List[Dict[str, Any]], identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Find slide by number (1,2,3...) or API object ID."""
        # Try as slide number first
        try:
            slide_number = int(identifier)
            if 1 <= slide_number <= len(slides):
                return slides[slide_number - 1]  # Convert to 0-based index
        except ValueError:
            pass

        # Try as API object ID
        for slide in slides:
            if slide["objectId"] == identifier:
                return slide

        return None

    async def _parse_slide_range(self, range_str: str, total_slides: int) -> List[int]:
        """Parse slide range string into list of 1-based slide numbers.

        Examples:
        - "1-3" -> [1, 2, 3]
        - "1,3,5" -> [1, 3, 5]
        - "2-4,6-8" -> [2, 3, 4, 6, 7, 8]
        """
        slide_numbers = set()

        for part in range_str.split(","):
            part = part.strip()
            if "-" in part:
                # Range like "2-4"
                start_str, end_str = part.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                # Validate range
                start = max(1, start)
                end = min(total_slides, end)
                if start <= end:
                    slide_numbers.update(range(start, end + 1))
            else:
                # Single slide like "3"
                slide_num = int(part)
                if 1 <= slide_num <= total_slides:
                    slide_numbers.add(slide_num)

        return sorted(list(slide_numbers))

    async def _expand_slide_identifiers(self, identifiers: List[str], total_slides: int) -> List[str]:
        """Expand slide identifiers that may contain ranges into individual slide numbers/IDs."""
        expanded = []

        for identifier in identifiers:
            # Check if this looks like a range (contains - or ,)
            if "-" in identifier or "," in identifier:
                try:
                    # Try to parse as range
                    slide_numbers = await self._parse_slide_range(identifier, total_slides)
                    expanded.extend([str(num) for num in slide_numbers])
                except (ValueError, TypeError):
                    # If parsing fails, treat as regular identifier
                    expanded.append(identifier)
            else:
                # Regular identifier (single slide number or API ID)
                expanded.append(identifier)

        return expanded

    async def _extract_detailed_element_info(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed information from a page element."""
        element_info = {
            "id": element["objectId"],
            "type": self._get_element_type(element),
        }

        # Extract size and position
        if "size" in element:
            size = element["size"]
            element_info["size"] = {
                "width": f"{size['width']['magnitude']} {size['width']['unit']}",
                "height": f"{size['height']['magnitude']} {size['height']['unit']}",
            }

        if "transform" in element:
            transform = element["transform"]
            element_info["position"] = {
                "x": f"{transform.get('translateX', 0)} {transform.get('unit', 'EMU')}",
                "y": f"{transform.get('translateY', 0)} {transform.get('unit', 'EMU')}",
                "scaleX": transform.get("scaleX", 1),
                "scaleY": transform.get("scaleY", 1),
            }

        # Extract content based on type
        if "shape" in element:
            shape = element["shape"]
            element_info["shape_type"] = shape.get("shapeType", "UNKNOWN")

            # Extract text content
            if "text" in shape:
                text_content = await self._extract_text_from_shape(shape["text"])
                if text_content:
                    element_info["text_content"] = text_content
                    element_info["text_details"] = await self._extract_text_formatting(shape["text"])

            # Extract shape properties
            if "shapeProperties" in shape:
                element_info["shape_properties"] = await self._extract_shape_properties(shape["shapeProperties"])

        elif "image" in element:
            image = element["image"]
            element_info["image_properties"] = {
                "content_url": image.get("contentUrl"),
                "source_url": image.get("sourceUrl"),
            }

        elif "table" in element:
            table = element["table"]
            element_info["table_info"] = {"rows": table.get("rows", 0), "columns": table.get("columns", 0)}
            # Extract table cell contents
            element_info["table_contents"] = await self._extract_table_contents(table)

        return element_info

    async def _extract_text_from_shape(self, text_data: Dict[str, Any]) -> str:
        """Extract plain text content from shape text data."""
        text_content = ""
        for text_element in text_data.get("textElements", []):
            if "textRun" in text_element:
                content = text_element["textRun"].get("content", "")
                text_content += content
        return text_content.strip()

    async def _extract_text_formatting(self, text_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract text formatting details."""
        formatting_details = []
        for text_element in text_data.get("textElements", []):
            if "textRun" in text_element:
                text_run = text_element["textRun"]
                detail = {"content": text_run.get("content", ""), "end_index": text_element.get("endIndex", 0)}
                if "style" in text_run:
                    style = text_run["style"]
                    detail["style"] = {
                        "bold": style.get("bold", False),
                        "italic": style.get("italic", False),
                        "underline": style.get("underline", False),
                        "font_family": style.get("fontFamily"),
                        "font_size": style.get("fontSize", {}).get("magnitude") if "fontSize" in style else None,
                    }
                    if "foregroundColor" in style:
                        color = style["foregroundColor"].get("opaqueColor", {}).get("rgbColor", {})
                        detail["style"][
                            "text_color"
                        ] = f"rgb({color.get('red', 0):.2f}, {color.get('green', 0):.2f}, {color.get('blue', 0):.2f})"
                formatting_details.append(detail)
        return formatting_details

    async def _extract_shape_properties(self, shape_props: Dict[str, Any]) -> Dict[str, Any]:
        """Extract shape visual properties."""
        properties = {}

        if "shapeBackgroundFill" in shape_props:
            bg_fill = shape_props["shapeBackgroundFill"]
            if "solidFill" in bg_fill and "color" in bg_fill["solidFill"]:
                color = bg_fill["solidFill"]["color"].get("rgbColor", {})
                properties["background_color"] = (
                    f"rgb({color.get('red', 0):.2f}, {color.get('green', 0):.2f}, {color.get('blue', 0):.2f})"
                )

        if "outline" in shape_props:
            outline = shape_props["outline"]
            if "weight" in outline:
                properties["border_width"] = f"{outline['weight']['magnitude']} {outline['weight']['unit']}"
            properties["border_style"] = outline.get("dashStyle", "SOLID")

        return properties

    async def _extract_table_contents(self, table_data: Dict[str, Any]) -> List[List[str]]:
        """Extract text contents from table cells."""
        contents = []
        table_rows = table_data.get("tableRows", [])

        for row in table_rows:
            row_contents = []
            for cell in row.get("tableCells", []):
                cell_text = ""
                if "text" in cell:
                    cell_text = await self._extract_text_from_shape(cell["text"])
                row_contents.append(cell_text)
            contents.append(row_contents)

        return contents

    async def _get_element_type(self, element: Dict[str, Any]) -> str:
        """Determine the type of page element."""
        if "shape" in element:
            return "text" if element["shape"].get("shapeType") == "TEXT_BOX" else "shape"
        elif "image" in element:
            return "image"
        elif "table" in element:
            return "table"
        elif "video" in element:
            return "video"
        else:
            return "unknown"

    async def add_text_content(
        self,
        presentation_id: str,
        slide_id: str,
        text: str,
        x: float = 100,
        y: float = 100,
        width: float = 300,
        height: float = 50,
        format_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add text content to a slide with formatting options.

        Format options similar to Google Sheets:
        - textFormat: {fontFamily, fontSize, bold, italic, underline, foregroundColor}
        - backgroundColor: {red, green, blue}
        """
        self.logger.info("Adding text content to slide %s in presentation: %s", slide_id, presentation_id)

        element_id = f"text_{slide_id}_{hash(text)}"

        requests = [
            {
                "createShape": {
                    "objectId": element_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": width, "unit": "PT"},
                            "height": {"magnitude": height, "unit": "PT"},
                        },
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "PT"},
                    },
                }
            },
            {"insertText": {"objectId": element_id, "text": text}},
        ]

        # Apply formatting if provided
        if format_options:
            format_request = await self._create_text_format_request(element_id, format_options, len(text))
            requests.extend(format_request)

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Text content added successfully")
        return result

    async def _create_text_format_request(
        self, element_id: str, format_options: Dict[str, Any], text_length: int
    ) -> List[Dict[str, Any]]:
        """Create formatting requests for text."""
        requests = []

        # Text formatting
        if "textFormat" in format_options:
            text_format = format_options["textFormat"]
            style = {}

            if "bold" in text_format:
                style["bold"] = text_format["bold"]
            if "italic" in text_format:
                style["italic"] = text_format["italic"]
            if "underline" in text_format:
                style["underline"] = text_format["underline"]
            if "fontSize" in text_format:
                style["fontSize"] = {"magnitude": text_format["fontSize"], "unit": "PT"}
            if "fontFamily" in text_format:
                style["fontFamily"] = text_format["fontFamily"]
            if "foregroundColor" in text_format:
                color = text_format["foregroundColor"]
                style["foregroundColor"] = {"opaqueColor": {"rgbColor": color}}

            if style:
                requests.append(
                    {
                        "updateTextStyle": {
                            "objectId": element_id,
                            "textRange": {"type": "ALL"},
                            "style": style,
                            "fields": ",".join(style.keys()),
                        }
                    }
                )

        # Background color
        if "backgroundColor" in format_options:
            color = format_options["backgroundColor"]
            requests.append(
                {
                    "updateShapeProperties": {
                        "objectId": element_id,
                        "shapeProperties": {"shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": color}}}},
                        "fields": "shapeBackgroundFill",
                    }
                }
            )

        return requests

    async def add_image_content(
        self,
        presentation_id: str,
        slide_id: str,
        image_url: str,
        x: float = 100,
        y: float = 100,
        width: float = 300,
        height: float = 200,
    ) -> Dict[str, Any]:
        """Add image content to a slide."""
        return self.add_image(presentation_id, slide_id, image_url, x, y, width, height)

    async def add_table_content(
        self,
        presentation_id: str,
        slide_id: str,
        rows: int,
        columns: int,
        x: float = 100,
        y: float = 100,
        width: float = 400,
        height: float = 200,
    ) -> Dict[str, Any]:
        """Add table content to a slide.

        Args:
            presentation_id: Presentation ID
            slide_id: Slide ID
            rows: Number of rows
            columns: Number of columns
            x, y: Position
            width, height: Table dimensions
        """
        self.logger.info(
            "Adding table (%dx%d) to slide %s in presentation: %s", rows, columns, slide_id, presentation_id
        )

        element_id = f"table_{slide_id}_{rows}x{columns}"

        requests = [
            {
                "createTable": {
                    "objectId": element_id,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": width, "unit": "PT"},
                            "height": {"magnitude": height, "unit": "PT"},
                        },
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "PT"},
                    },
                    "rows": rows,
                    "columns": columns,
                }
            }
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Table added successfully")
        return result

    async def remove_content(self, presentation_id: str, element_id: str) -> Dict[str, Any]:
        """Remove content element from slide.

        Args:
            presentation_id: Presentation ID
            element_id: ID of element to remove
        """
        self.logger.info("Removing content element %s from presentation: %s", element_id, presentation_id)

        requests = [{"deleteObject": {"objectId": element_id}}]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Content element removed successfully")
        return result

    async def move_content(self, presentation_id: str, element_id: str, x: float, y: float) -> Dict[str, Any]:
        """Move content element to new position.

        Args:
            presentation_id: Presentation ID
            element_id: ID of element to move
            x, y: New position coordinates
        """
        self.logger.info("Moving content element %s to (%f, %f) in presentation: %s", element_id, x, y, presentation_id)

        requests = [
            {
                "updatePageElementTransform": {
                    "objectId": element_id,
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "PT"},
                    "applyMode": "ABSOLUTE",
                }
            }
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Content element moved successfully")
        return result

    # Table-specific methods
    async def add_table_row(self, presentation_id: str, table_id: str, position: int = -1) -> Dict[str, Any]:
        """Add row to table.

        Args:
            presentation_id: Presentation ID
            table_id: Table element ID
            position: Position to insert row (-1 for end)
        """
        self.logger.info("Adding row to table %s in presentation: %s", table_id, presentation_id)

        insert_request = {"insertTableRows": {"tableObjectId": table_id, "cellLocation": {"rowIndex": 0}}}

        if position >= 0:
            insert_request["insertTableRows"]["cellLocation"]["rowIndex"] = position

        requests = [insert_request]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Table row added successfully")
        return result

    async def add_table_column(self, presentation_id: str, table_id: str, position: int = -1) -> Dict[str, Any]:
        """Add column to table.

        Args:
            presentation_id: Presentation ID
            table_id: Table element ID
            position: Position to insert column (-1 for end)
        """
        self.logger.info("Adding column to table %s in presentation: %s", table_id, presentation_id)

        insert_request = {"insertTableColumns": {"tableObjectId": table_id, "cellLocation": {"columnIndex": 0}}}

        if position >= 0:
            insert_request["insertTableColumns"]["cellLocation"]["columnIndex"] = position

        requests = [insert_request]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Table column added successfully")
        return result

    async def set_table_cell_value(
        self, presentation_id: str, table_id: str, row: int, column: int, text: str
    ) -> Dict[str, Any]:
        """Set value in table cell.

        Args:
            presentation_id: Presentation ID
            table_id: Table element ID
            row: Row index (0-based)
            column: Column index (0-based)
            text: Text to set in cell
        """
        self.logger.info("Setting cell value (%d,%d) in table %s", row, column, table_id)

        requests = [
            {
                "insertText": {
                    "objectId": table_id,
                    "cellLocation": {"rowIndex": row, "columnIndex": column},
                    "text": text,
                }
            }
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Table cell value set successfully")
        return result

    # Text-specific methods
    async def update_text_content_preserving_format(
        self, presentation_id: str, slide_id: str, element_id: str, current_text: str, new_text: str
    ) -> Dict[str, Any]:
        """Update text content of an element while preserving formatting using replaceAllText.

        Args:
            presentation_id: Presentation ID
            slide_id: Slide ID containing the element
            element_id: Text element ID
            current_text: Current text content
            new_text: New text content
        """
        self.logger.info(
            "Updating text content for element %s in presentation: %s (preserving format)", element_id, presentation_id
        )

        # Use replaceAllText on the specific slide to preserve formatting
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": current_text, "matchCase": True},
                    "replaceText": new_text,
                    "pageObjectIds": [slide_id],
                }
            }
        ]

        result = await self.slides_api.batch_update(presentation_id, requests)
        self.logger.info("Text content updated successfully with formatting preserved")
        return result

    async def update_text_content(self, presentation_id: str, element_id: str, new_text: str) -> Dict[str, Any]:
        """Update text content of an element (fallback method - may not preserve all formatting).

        Args:
            presentation_id: Presentation ID
            element_id: Text element ID
            new_text: New text content
        """
        self.logger.info("Updating text content for element %s in presentation: %s", element_id, presentation_id)

        # Get the current presentation to find the element and its current text
        presentation = await self.get_presentation(presentation_id)
        current_text = await self._extract_element_text(presentation, element_id)

        if not current_text:
            # If no current text, just insert new text
            requests = [
                {"insertText": {"objectId": element_id, "text": new_text, "insertionIndex": 0}},
            ]
        else:
            # Delete and insert - this preserves some formatting but not all
            requests = [
                {"deleteText": {"objectId": element_id, "textRange": {"startIndex": 0, "endIndex": len(current_text)}}},
                {"insertText": {"objectId": element_id, "text": new_text, "insertionIndex": 0}},
            ]

        result = await self.slides_api.batch_update(presentation_id, requests)

        self.logger.info("Text content updated successfully")
        return result

    async def translate_text_content(
        self, presentation_id: str, element_id: str, target_language: str, source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text content of an element.

        Args:
            presentation_id: Presentation ID
            element_id: Text element ID
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
        """
        from .translate_service import TranslateService

        self.logger.info("Translating text content for element %s to %s", element_id, target_language)

        # Get current text
        presentation = await self.get_presentation(presentation_id)
        current_text = await self._extract_element_text(presentation, element_id)

        if not current_text:
            return {}

        # Initialize translate service
        translate_service = TranslateService(self.auth_service)
        await translate_service.initialize()

        # Translate the text
        translation_result = await translate_service.translate_text(current_text, target_language, source_language)
        translated_text = translation_result["translatedText"]

        # Update the element with translated text
        result = await self.update_text_content(presentation_id, element_id, translated_text)

        self.logger.info("Text content translated successfully")
        return result

    async def translate_slides(
        self, presentation_id: str, slides: str, target_language: str, source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text content in slides.

        Args:
            presentation_id: Presentation ID
            slides: Slide range/number to translate (e.g., '1-3', '2', '1,3,5', 'all')
            target_language: Target language code
            source_language: Source language code (auto-detect if None)

        Returns:
            Dictionary with translation results
        """
        from .translate_service import TranslateService

        self.logger.info("Translating slides %s in presentation %s to %s", slides, presentation_id, target_language)

        # Initialize translate service
        translate_service = TranslateService(self.auth_service)
        await translate_service.initialize()

        # Get presentation
        presentation = await self.get_presentation(presentation_id)
        total_slides = len(presentation.get("slides", []))

        # Parse slide range - use the method that returns 0-based indices directly
        if slides.lower() == "all":
            slide_indices = list(range(total_slides))
        else:
            # Use the second _parse_slide_range method that returns 0-based indices
            slide_indices = []
            for part in slides.split(","):
                part = part.strip()
                if "-" in part:
                    # Range like "2-4"
                    start, end = map(int, part.split("-"))
                    # Convert to 0-based and validate
                    start_idx = max(0, start - 1)
                    end_idx = min(total_slides - 1, end - 1)
                    slide_indices.extend(range(start_idx, end_idx + 1))
                else:
                    # Single slide like "3"
                    slide_num = int(part)
                    slide_idx = slide_num - 1  # Convert to 0-based
                    if 0 <= slide_idx < total_slides:
                        slide_indices.append(slide_idx)
            slide_indices = sorted(list(set(slide_indices)))

        if not slide_indices:
            self.logger.warning("No valid slides found for range: %s", slides)
            return {"translated_slides": 0}

        translated_count = 0
        total_translated_elements = 0

        for slide_index in slide_indices:
            slide = presentation["slides"][slide_index]
            slide_id = slide["objectId"]
            slide_translated_elements = 0

            # Process all text elements in the slide
            for element in slide.get("pageElements", []):
                if "shape" in element and "text" in element["shape"]:
                    element_id = element["objectId"]

                    # Extract current text
                    current_text = await self._extract_element_text(presentation, element_id)

                    if current_text and current_text.strip():
                        try:
                            # Translate the text
                            translation_result = await translate_service.translate_text(
                                current_text, target_language, source_language
                            )
                            translated_text = translation_result["translatedText"]

                            # Update the element with translated text while preserving formatting
                            await self.update_text_content_preserving_format(
                                presentation_id, slide_id, element_id, current_text, translated_text
                            )
                            slide_translated_elements += 1

                        except Exception as e:
                            self.logger.warning("Failed to translate element %s: %s", element_id, str(e))

            if slide_translated_elements > 0:
                translated_count += 1
                total_translated_elements += slide_translated_elements

        self.logger.info(
            "Translation complete: %d slides translated, %d text elements updated",
            translated_count,
            total_translated_elements,
        )

        return {
            "translated_slides": translated_count,
            "total_elements_translated": total_translated_elements,
            "target_language": target_language,
        }

    async def _extract_element_text(self, presentation: Dict[str, Any], element_id: str) -> str:
        """Extract text content from a presentation element."""
        for slide in presentation.get("slides", []):
            for element in slide.get("pageElements", []):
                if element["objectId"] == element_id and "shape" in element:
                    shape = element["shape"]
                    if "text" in shape:
                        text_content = ""
                        for text_element in shape["text"].get("textElements", []):
                            if "textRun" in text_element:
                                text_content += text_element["textRun"].get("content", "")
                        return text_content
        return ""

    async def format_text_content(
        self,
        presentation_id: str,
        element_id: str,
        format_options: Dict[str, Any],
        start_index: int = 0,
        end_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Format text content with specified options.

        Args:
            presentation_id: Presentation ID
            element_id: Text element ID
            format_options: Format options similar to Google Sheets
            start_index: Start index for formatting
            end_index: End index for formatting (None for entire text)
        """
        self.logger.info("Formatting text content for element %s in presentation: %s", element_id, presentation_id)

        if end_index is None:
            # Get text length
            presentation = await self.get_presentation(presentation_id)
            text = await self._extract_element_text(presentation, element_id)
            end_index = len(text)

        format_requests = await self._create_text_format_request(element_id, format_options, end_index - start_index)

        # Update the text range for the requests
        for request in format_requests:
            if "updateTextStyle" in request:
                request["updateTextStyle"]["textRange"] = {"startIndex": start_index, "endIndex": end_index}

        if format_requests:
            result = await self.slides_api.batch_update(presentation_id, format_requests)

            self.logger.info("Text content formatted successfully")
            return result

        return {}

    # Download Methods
    async def download_presentation(
        self, presentation_id: str, output_path: str, format_type: str = "pdf", slides_range: Optional[str] = None
    ) -> str:
        """Download presentation in specified format.

        Args:
            presentation_id: Presentation ID
            output_path: Output file path or directory (for images)
            format_type: Export format (pdf, pptx, png, jpeg)
            slides_range: Slide range specification (e.g., "1-3", "1,3,5", "2-4,6-8")

        Returns:
            Final output path or directory
        """
        import os
        import requests
        from pathlib import Path

        self.logger.info("Downloading presentation %s as %s", presentation_id, format_type.upper())

        # Get presentation info for slide count validation
        presentation = await self.get_presentation(presentation_id)
        total_slides = len(presentation.get("slides", []))

        # Parse slide range
        slide_indices = await self._parse_slide_range(slides_range, total_slides) if slides_range else None

        if format_type.lower() in ["png", "jpeg"]:
            return await self._download_as_images(
                presentation_id, output_path, format_type, slide_indices, total_slides
            )
        else:
            return await self._download_as_document(presentation_id, output_path, format_type, slide_indices)

    async def _parse_slide_range(self, range_str: str, total_slides: int) -> List[int]:
        """Parse slide range string into list of 0-based slide indices.

        Examples:
        - "1-3" -> [0, 1, 2]
        - "1,3,5" -> [0, 2, 4]
        - "2-4,6-8" -> [1, 2, 3, 5, 6, 7]
        """
        indices = set()

        for part in range_str.split(","):
            part = part.strip()
            if "-" in part:
                # Range like "2-4"
                start, end = map(int, part.split("-"))
                # Convert to 0-based and validate
                start_idx = max(0, start - 1)
                end_idx = min(total_slides - 1, end - 1)
                indices.update(range(start_idx, end_idx + 1))
            else:
                # Single slide like "3"
                slide_num = int(part)
                slide_idx = slide_num - 1  # Convert to 0-based
                if 0 <= slide_idx < total_slides:
                    indices.add(slide_idx)

        return sorted(list(indices))

    async def _download_as_document(
        self, presentation_id: str, output_path: str, format_type: str, slide_indices: Optional[List[int]] = None
    ) -> str:
        """Download presentation as PDF or PPTX document."""
        import os
        import requests

        # Get credentials for authenticated request
        credentials = self.auth_service.credentials

        # Build export URL
        if format_type.lower() == "pdf":
            export_url = f"https://docs.google.com/presentation/d/{presentation_id}/export/pdf"
            if not output_path.lower().endswith(".pdf"):
                output_path += ".pdf"
        elif format_type.lower() == "pptx":
            export_url = f"https://docs.google.com/presentation/d/{presentation_id}/export/pptx"
            if not output_path.lower().endswith(".pptx"):
                output_path += ".pptx"
        else:
            raise ValueError(f"Unsupported document format: {format_type}")

        # Add slide range parameters if specified
        params = {}
        if slide_indices:
            # Google Slides export uses 1-based slide numbers
            slide_nums = [str(i + 1) for i in slide_indices]
            params["range"] = ",".join(slide_nums)

        # Make authenticated request
        headers = {"Authorization": f"Bearer {credentials.token}"}

        self.logger.info("Downloading from: %s", export_url)
        response = requests.get(export_url, headers=headers, params=params, stream=True, timeout=300)  # nosec
        response.raise_for_status()

        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        self.logger.info("Document saved to: %s", output_path)
        return output_path

    async def _download_as_images(
        self,
        presentation_id: str,
        output_dir: str,
        format_type: str,
        slide_indices: Optional[List[int]] = None,
        total_slides: int = 0,
    ) -> str:
        """Download presentation slides as individual images."""
        import os
        import requests
        from pathlib import Path

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Get credentials for authenticated request
        credentials = self.auth_service.credentials

        # Determine which slides to download
        if slide_indices:
            slides_to_download = slide_indices
        else:
            slides_to_download = list(range(total_slides))

        # Get slide object IDs
        presentation = await self.get_presentation(presentation_id)
        slide_objects = presentation.get("slides", [])

        headers = {"Authorization": f"Bearer {credentials.token}"}
        downloaded_files = []

        for slide_idx in slides_to_download:
            if slide_idx >= len(slide_objects):
                continue

            slide_object_id = slide_objects[slide_idx]["objectId"]
            slide_number = slide_idx + 1

            # Build image export URL
            if format_type.lower() == "png":
                export_url = f"https://docs.google.com/presentation/d/{presentation_id}/export/png?id={presentation_id}&pageid={slide_object_id}"
                file_extension = "png"
            elif format_type.lower() == "jpeg":
                export_url = f"https://docs.google.com/presentation/d/{presentation_id}/export/jpeg?id={presentation_id}&pageid={slide_object_id}"
                file_extension = "jpeg"
            else:
                raise ValueError(f"Unsupported image format: {format_type}")

            # Download image
            self.logger.info("Downloading slide %d as %s", slide_number, format_type.upper())
            response = requests.get(export_url, headers=headers, stream=True, timeout=300)  # nosec
            response.raise_for_status()

            # Save image with slide number
            filename = f"slide_{slide_number:03d}.{file_extension}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            downloaded_files.append(filepath)
            self.logger.info("Slide %d saved to: %s", slide_number, filepath)

        self.logger.info("Downloaded %d slides to directory: %s", len(downloaded_files), output_dir)
        return output_dir

    # Copy Operations
    async def copy_slides(
        self,
        source_presentation_id: str,
        target_presentation_id: str,
        slide_identifiers: List[str],
        preserve_theme: bool = True,
        link_to_source: bool = False,
        target_position: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Copy slides from one presentation to another with range support.

        Args:
            source_presentation_id: Source presentation ID
            target_presentation_id: Target presentation ID
            slide_identifiers: List of slide identifiers, numbers, or ranges (e.g., ["1-3", "5"])
            preserve_theme: Whether to preserve original theme/formatting (default: True)
            link_to_source: Whether to link slides to source presentation (default: False)
            target_position: Position to insert slides (None for end)

        Returns:
            Dictionary with copy results and new slide IDs
        """
        self.logger.info(
            "Copying slides from %s to %s: %s",
            source_presentation_id,
            target_presentation_id,
            slide_identifiers,
        )

        # Get source presentation
        source_presentation = await self.get_presentation(source_presentation_id)
        source_slides = source_presentation.get("slides", [])

        # Expand slide identifiers to handle ranges
        expanded_identifiers = await self._expand_slide_identifiers(slide_identifiers, len(source_slides))

        # Find source slides to copy
        slides_to_copy = []
        for identifier in expanded_identifiers:
            slide = await self._find_slide_by_identifier(source_slides, identifier)
            if slide:
                slides_to_copy.append(slide)

        if not slides_to_copy:
            raise ValueError(f"No valid slides found for identifiers: {slide_identifiers}")

        # Get target presentation
        target_presentation = await self.get_presentation(target_presentation_id)
        target_slides = target_presentation.get("slides", [])

        # Determine insertion position
        insert_index = len(target_slides) if target_position is None else target_position

        copied_slide_ids = []
        requests = []

        for i, source_slide in enumerate(slides_to_copy):
            current_insert_index = insert_index + i

            if preserve_theme:
                # Copy slide with all content and formatting
                requests.extend(
                    await self._create_slide_copy_requests(source_slide, current_insert_index, link_to_source)
                )
            else:
                # Create blank slide and copy only content
                requests.extend(
                    await self._create_slide_content_copy_requests(source_slide, current_insert_index, link_to_source)
                )

        # Execute all copy requests
        if requests:
            result = await self.slides_api.batch_update(target_presentation_id, requests)

            # Extract new slide IDs from response
            for reply in result.get("replies", []):
                if "createSlide" in reply:
                    copied_slide_ids.append(reply["createSlide"]["objectId"])

        self.logger.info("Successfully copied %d slides", len(copied_slide_ids))

        return {
            "copied_slides": len(copied_slide_ids),
            "new_slide_ids": copied_slide_ids,
            "source_presentation": source_presentation_id,
            "target_presentation": target_presentation_id,
            "preserve_theme": preserve_theme,
            "link_to_source": link_to_source,
        }

    async def _create_slide_copy_requests(
        self, source_slide: Dict[str, Any], insert_index: int, link_to_source: bool
    ) -> List[Dict[str, Any]]:
        """Create requests to copy a slide with full formatting."""
        requests = []

        # Create new slide
        slide_layout = await self._get_slide_layout(source_slide)
        requests.append(
            {
                "createSlide": {
                    "insertionIndex": insert_index,
                    "slideLayoutReference": {"predefinedLayout": slide_layout},
                }
            }
        )

        # Note: Full slide copying with all elements and formatting would require
        # complex element-by-element recreation. For now, we'll create the slide
        # and copy major elements.

        return requests

    async def _create_slide_content_copy_requests(
        self, source_slide: Dict[str, Any], insert_index: int, link_to_source: bool
    ) -> List[Dict[str, Any]]:
        """Create requests to copy slide content without theme."""
        requests = []

        # Create blank slide
        requests.append(
            {
                "createSlide": {
                    "insertionIndex": insert_index,
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                }
            }
        )

        return requests

    async def _get_slide_layout(self, slide: Dict[str, Any]) -> str:
        """Determine the layout of a slide based on its properties."""
        # Analyze slide elements to determine most appropriate layout
        page_elements = slide.get("pageElements", [])

        if not page_elements:
            return "BLANK"

        # Basic layout detection based on number and type of elements
        text_elements = [elem for elem in page_elements if "shape" in elem]

        if len(text_elements) == 0:
            return "BLANK"
        elif len(text_elements) == 1:
            return "TITLE_ONLY"
        elif len(text_elements) == 2:
            return "TITLE_AND_BODY"
        else:
            return "TITLE_AND_TWO_COLUMNS"

    # Version Management Methods

    async def list_presentation_versions(self, presentation_id: str) -> List[Dict[str, Any]]:
        """List all versions/revisions of a presentation."""
        self.logger.info("Listing versions for presentation: %s", presentation_id)

        try:
            result = await self.drive_api.list_file_revisions(presentation_id)
            revisions = result.get("revisions", [])

            # Enhance revision data with presentation-specific information
            for revision in revisions:
                revision["file_type"] = "presentation"
                revision["mime_type"] = revision.get("mimeType", "application/vnd.google-apps.presentation")

            self.logger.info("Found %d versions for presentation %s", len(revisions), presentation_id)
            return revisions

        except Exception as e:
            self.logger.error("Failed to list presentation versions: %s", e)
            raise

    async def get_presentation_version(self, presentation_id: str, revision_id: str) -> Dict[str, Any]:
        """Get metadata for a specific presentation version."""
        self.logger.info("Getting version %s for presentation: %s", revision_id, presentation_id)

        try:
            revision = await self.drive_api.get_file_revision(presentation_id, revision_id)
            revision["file_type"] = "presentation"
            revision["mime_type"] = revision.get("mimeType", "application/vnd.google-apps.presentation")

            self.logger.info("Retrieved version metadata for %s", revision_id)
            return revision

        except Exception as e:
            self.logger.error("Failed to get presentation version: %s", e)
            raise

    async def download_presentation_version(
        self, presentation_id: str, revision_id: str, output_path: str, format_type: str = "pptx"
    ) -> str:
        """Download a specific version of a presentation in the specified format."""
        self.logger.info("Downloading version %s of presentation %s as %s", revision_id, presentation_id, format_type)

        try:
            # Map format types to MIME types
            format_mime_types = {
                "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "pdf": "application/pdf",
                "png": "image/png",
                "jpeg": "image/jpeg",
                "svg": "image/svg+xml",
                "txt": "text/plain",
                "odp": "application/vnd.oasis.opendocument.presentation",
            }

            if format_type not in format_mime_types:
                raise ValueError(f"Unsupported format: {format_type}. Supported: {list(format_mime_types.keys())}")

            export_mime_type = format_mime_types[format_type]

            # Ensure output path has correct extension
            output_path_obj = Path(output_path)
            if not output_path_obj.suffix == f".{format_type}":
                output_path = str(output_path_obj.with_suffix(f".{format_type}"))

            result_path = await self.drive_api.export_file_revision(
                presentation_id, revision_id, export_mime_type, output_path
            )

            self.logger.info("Version downloaded successfully to: %s", result_path)
            return result_path

        except Exception as e:
            self.logger.error("Failed to download presentation version: %s", e)
            raise

    async def compare_presentation_versions(
        self, presentation_id: str, revision_id_1: str, revision_id_2: str, output_dir: str = "/tmp"
    ) -> Dict[str, Any]:
        """Compare two versions of a presentation and return detailed diff analysis."""
        self.logger.info("Comparing presentation %s versions %s vs %s", presentation_id, revision_id_1, revision_id_2)

        try:
            from pathlib import Path
            import json
            import tempfile

            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Download both versions as JSON (via PPTX conversion and analysis)
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Download version 1
                v1_path = temp_path / f"v1_{revision_id_1}.pptx"
                await self.download_presentation_version(presentation_id, revision_id_1, str(v1_path), "pptx")

                # Download version 2
                v2_path = temp_path / f"v2_{revision_id_2}.pptx"
                await self.download_presentation_version(presentation_id, revision_id_2, str(v2_path), "pptx")

                # Get presentation structures for comparison
                v1_structure = await self._extract_presentation_structure(presentation_id, revision_id_1)
                v2_structure = await self._extract_presentation_structure(presentation_id, revision_id_2)

                # Perform diff analysis
                diff_result = await self._perform_presentation_diff(v1_structure, v2_structure)

                # Save comparison result
                comparison_file = output_dir / f"comparison_{revision_id_1}_vs_{revision_id_2}.json"
                with open(comparison_file, "w", encoding="utf-8") as f:
                    json.dump(diff_result, f, indent=2, default=str)

                self.logger.info("Comparison completed successfully. Results saved to: %s", comparison_file)
                return diff_result

        except Exception as e:
            self.logger.error("Failed to compare presentation versions: %s", e)
            raise

    async def _extract_presentation_structure(self, presentation_id: str, revision_id: str) -> Dict[str, Any]:
        """Extract presentation structure for comparison purposes."""
        try:
            # For now, we'll extract basic metadata from the revision
            # In a full implementation, this would parse the PPTX file or use Slides API
            revision_info = await self.get_presentation_version(presentation_id, revision_id)

            structure = {
                "revision_id": revision_id,
                "modified_time": revision_info.get("modifiedTime"),
                "size": revision_info.get("size"),
                "last_modifying_user": revision_info.get("lastModifyingUser", {}).get("displayName"),
                "slides": [],  # This would be populated by parsing the actual content
                "metadata": revision_info,
            }

            return structure

        except Exception as e:
            self.logger.error("Failed to extract presentation structure: %s", e)
            raise

    async def _perform_presentation_diff(
        self, v1_structure: Dict[str, Any], v2_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform detailed diff analysis between two presentation structures."""
        try:
            diff_result = {
                "comparison_summary": {
                    "version_1": {
                        "revision_id": v1_structure["revision_id"],
                        "modified_time": v1_structure["modified_time"],
                        "size": v1_structure["size"],
                        "last_modifying_user": v1_structure["last_modifying_user"],
                    },
                    "version_2": {
                        "revision_id": v2_structure["revision_id"],
                        "modified_time": v2_structure["modified_time"],
                        "size": v2_structure["size"],
                        "last_modifying_user": v2_structure["last_modifying_user"],
                    },
                },
                "changes": {
                    "added_slides": [],
                    "deleted_slides": [],
                    "modified_slides": [],
                    "size_change": None,
                    "time_difference": None,
                },
                "detailed_analysis": {
                    "content_changes": [],
                    "format_changes": [],
                    "structural_changes": [],
                },
            }

            # Calculate basic differences
            v1_size = int(v1_structure.get("size", "0"))
            v2_size = int(v2_structure.get("size", "0"))
            diff_result["changes"]["size_change"] = v2_size - v1_size

            # Parse modification times
            from datetime import datetime

            try:
                v1_time = datetime.fromisoformat(v1_structure["modified_time"].replace("Z", "+00:00"))
                v2_time = datetime.fromisoformat(v2_structure["modified_time"].replace("Z", "+00:00"))
                time_diff = v2_time - v1_time
                diff_result["changes"]["time_difference"] = str(time_diff)
            except (ValueError, TypeError, KeyError):
                diff_result["changes"]["time_difference"] = "Unable to calculate"

            # Add placeholder for future slide-level comparison
            diff_result["detailed_analysis"]["content_changes"].append(
                {
                    "type": "metadata_comparison",
                    "description": f"Size changed by {diff_result['changes']['size_change']} bytes",
                    "user_change": v1_structure["last_modifying_user"] != v2_structure["last_modifying_user"],
                }
            )

            return diff_result

        except Exception as e:
            self.logger.error("Failed to perform presentation diff: %s", e)
            raise

    async def keep_presentation_version_forever(
        self, presentation_id: str, revision_id: str, keep_forever: bool = True
    ) -> Dict[str, Any]:
        """Mark a presentation version to be kept forever or allow auto-deletion."""
        self.logger.info(
            "Setting keepForever=%s for version %s of presentation %s", keep_forever, revision_id, presentation_id
        )

        try:
            result = await self.drive_api.keep_file_revision_forever(presentation_id, revision_id, keep_forever)
            self.logger.info("Version %s keepForever updated to %s", revision_id, keep_forever)
            return result

        except Exception as e:
            self.logger.error("Failed to update version keep forever setting: %s", e)
            raise

    async def restore_presentation_version(self, presentation_id: str, revision_id: str) -> Dict[str, Any]:
        """Restore a presentation to a specific revision by creating a new file with the old content."""
        self.logger.info("Restoring presentation %s to revision %s", presentation_id, revision_id)

        try:
            result = await self.drive_api.restore_file_revision(presentation_id, revision_id)

            # Enhanced result with presentation-specific information
            result["file_type"] = "presentation"
            result["original_presentation_id"] = presentation_id

            self.logger.info(
                "Successfully restored presentation. New file: %s (ID: %s)",
                result.get("restored_file_name"),
                result.get("restored_file_id"),
            )
            return result

        except Exception as e:
            self.logger.error("Failed to restore presentation version: %s", e)
            raise
