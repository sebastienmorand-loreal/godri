"""Google Slides API client with async aiohttp."""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from .google_api_client import GoogleApiClient


class SlidesApiClient:
    """Async Google Slides API client."""

    def __init__(self, api_client: GoogleApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://slides.googleapis.com/v1"

    async def create_presentation(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Google Slides presentation."""
        self.logger.info(f"Creating presentation: {title}")

        presentation_metadata = {"title": title}
        url = f"{self.base_url}/presentations"

        result = await self.api_client.make_request("POST", url, data=presentation_metadata)

        presentation_id = result.get("presentationId")
        self.logger.info(f"Presentation created successfully: {presentation_id}")

        # If folder_id specified, move presentation to folder using Drive API
        if folder_id:
            drive_url = "https://www.googleapis.com/drive/v3"

            # Get current parents
            file_info_url = f"{drive_url}/files/{presentation_id}"
            file_info = await self.api_client.make_request("GET", file_info_url, params={"fields": "parents"})
            current_parents = file_info.get("parents", [])

            # Move to new folder
            move_url = f"{drive_url}/files/{presentation_id}"
            move_params = {"addParents": folder_id, "removeParents": ",".join(current_parents), "fields": "id, parents"}
            await self.api_client.make_request("PATCH", move_url, params=move_params)
            self.logger.info(f"Presentation moved to folder: {folder_id}")

        return result

    async def get_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """Get presentation content and metadata."""
        self.logger.info(f"Getting presentation: {presentation_id}")

        url = f"{self.base_url}/presentations/{presentation_id}"

        return await self.api_client.make_request("GET", url)

    async def batch_update(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch updates on presentation."""
        self.logger.info(f"Batch updating presentation: {presentation_id} with {len(requests)} requests")

        update_data = {"requests": requests}
        url = f"{self.base_url}/presentations/{presentation_id}:batchUpdate"

        result = await self.api_client.make_request("POST", url, data=update_data)
        self.logger.info(f"Batch update completed successfully")
        return result

    async def create_slide(
        self, presentation_id: str, layout: str = "BLANK", insertion_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new slide."""
        self.logger.info(f"Creating slide with layout '{layout}' in presentation: {presentation_id}")

        slide_id = f"slide_{len(str(presentation_id))}_new"

        create_request = {"createSlide": {"objectId": slide_id, "slideLayoutReference": {"predefinedLayout": layout}}}

        if insertion_index is not None:
            create_request["createSlide"]["insertionIndex"] = insertion_index

        requests = [create_request]
        result = await self.batch_update(presentation_id, requests)

        return result.get("replies", [{}])[0].get("createSlide", {})

    async def delete_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any]:
        """Delete a slide."""
        self.logger.info(f"Deleting slide {slide_id} from presentation: {presentation_id}")

        requests = [{"deleteObject": {"objectId": slide_id}}]

        return await self.batch_update(presentation_id, requests)

    async def duplicate_slide(
        self, presentation_id: str, slide_id: str, insertion_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Duplicate a slide."""
        self.logger.info(f"Duplicating slide {slide_id} in presentation: {presentation_id}")

        duplicate_request = {"duplicateObject": {"objectId": slide_id}}

        if insertion_index is not None:
            duplicate_request["duplicateObject"]["insertionIndex"] = insertion_index

        requests = [duplicate_request]
        result = await self.batch_update(presentation_id, requests)

        return result.get("replies", [{}])[0].get("duplicateObject", {})

    async def update_slide_position(self, presentation_id: str, slide_id: str, new_index: int) -> Dict[str, Any]:
        """Move slide to new position."""
        self.logger.info(f"Moving slide {slide_id} to position {new_index} in presentation: {presentation_id}")

        requests = [{"updateSlidesPosition": {"slideObjectIds": [slide_id], "insertionIndex": new_index}}]

        return await self.batch_update(presentation_id, requests)

    async def create_text_box(
        self,
        presentation_id: str,
        slide_id: str,
        text: str,
        x: float,
        y: float,
        width: float,
        height: float,
        element_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a text box on a slide."""
        self.logger.info(f"Creating text box on slide {slide_id} in presentation: {presentation_id}")

        if not element_id:
            element_id = f"textbox_{slide_id}_{int(x)}_{int(y)}"

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

        return await self.batch_update(presentation_id, requests)

    async def create_image(
        self,
        presentation_id: str,
        slide_id: str,
        image_url: str,
        x: float,
        y: float,
        width: float,
        height: float,
        element_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an image on a slide."""
        self.logger.info(f"Creating image on slide {slide_id} in presentation: {presentation_id}")

        if not element_id:
            element_id = f"image_{slide_id}_{int(x)}_{int(y)}"

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

        return await self.batch_update(presentation_id, requests)

    async def create_table(
        self,
        presentation_id: str,
        slide_id: str,
        rows: int,
        columns: int,
        x: float,
        y: float,
        width: float,
        height: float,
        element_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a table on a slide."""
        self.logger.info(f"Creating {rows}x{columns} table on slide {slide_id} in presentation: {presentation_id}")

        if not element_id:
            element_id = f"table_{slide_id}_{rows}_{columns}"

        requests = [
            {
                "createTable": {
                    "objectId": element_id,
                    "rows": rows,
                    "columns": columns,
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

        return await self.batch_update(presentation_id, requests)

    async def update_text_style(
        self,
        presentation_id: str,
        element_id: str,
        style: Dict[str, Any],
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update text style in an element."""
        self.logger.info(f"Updating text style for element {element_id} in presentation: {presentation_id}")

        text_range = {"type": "ALL"}
        if start_index is not None and end_index is not None:
            text_range = {"type": "FIXED_RANGE", "startIndex": start_index, "endIndex": end_index}

        requests = [
            {
                "updateTextStyle": {
                    "objectId": element_id,
                    "textRange": text_range,
                    "style": style,
                    "fields": ",".join(style.keys()),
                }
            }
        ]

        return await self.batch_update(presentation_id, requests)

    async def insert_text(self, presentation_id: str, element_id: str, text: str, index: int = 0) -> Dict[str, Any]:
        """Insert text into an element."""
        self.logger.info(f"Inserting text into element {element_id} in presentation: {presentation_id}")

        requests = [{"insertText": {"objectId": element_id, "text": text, "insertionIndex": index}}]

        return await self.batch_update(presentation_id, requests)

    async def replace_text(
        self, presentation_id: str, old_text: str, new_text: str, match_case: bool = False
    ) -> Dict[str, Any]:
        """Replace text throughout the presentation."""
        self.logger.info(f"Replacing text '{old_text}' with '{new_text}' in presentation: {presentation_id}")

        requests = [
            {"replaceAllText": {"containsText": {"text": old_text, "matchCase": match_case}, "replaceText": new_text}}
        ]

        return await self.batch_update(presentation_id, requests)

    async def update_element_transform(
        self, presentation_id: str, element_id: str, transform: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update element position and scale."""
        self.logger.info(f"Updating transform for element {element_id} in presentation: {presentation_id}")

        requests = [
            {"updatePageElementTransform": {"objectId": element_id, "transform": transform, "applyMode": "ABSOLUTE"}}
        ]

        return await self.batch_update(presentation_id, requests)

    async def delete_element(self, presentation_id: str, element_id: str) -> Dict[str, Any]:
        """Delete an element from a slide."""
        self.logger.info(f"Deleting element {element_id} from presentation: {presentation_id}")

        requests = [{"deleteObject": {"objectId": element_id}}]

        return await self.batch_update(presentation_id, requests)

    async def get_slide_content(self, presentation_id: str, slide_id: str) -> List[Dict[str, Any]]:
        """Get detailed content information for a slide."""
        self.logger.info(f"Getting content for slide {slide_id} in presentation: {presentation_id}")

        presentation = await self.get_presentation(presentation_id)
        slides = presentation.get("slides", [])

        target_slide = None
        for slide in slides:
            if slide.get("objectId") == slide_id:
                target_slide = slide
                break

        if not target_slide:
            self.logger.warning(f"Slide {slide_id} not found")
            return []

        elements = []
        page_elements = target_slide.get("pageElements", [])

        for element in page_elements:
            element_info = {"id": element.get("objectId"), "type": self._get_element_type(element)}

            # Add size and position info
            if "size" in element:
                size = element["size"]
                element_info["size"] = {
                    "width": size.get("width", {}).get("magnitude", 0),
                    "height": size.get("height", {}).get("magnitude", 0),
                }

            if "transform" in element:
                transform = element["transform"]
                element_info["position"] = {
                    "x": transform.get("translateX", 0),
                    "y": transform.get("translateY", 0),
                    "scaleX": transform.get("scaleX", 1),
                    "scaleY": transform.get("scaleY", 1),
                }

            # Extract content based on element type
            if "shape" in element:
                shape = element["shape"]
                element_info["shape_type"] = shape.get("shapeType")

                if "text" in shape:
                    text_elements = shape["text"].get("textElements", [])
                    text_content = ""
                    text_details = []

                    for text_elem in text_elements:
                        if "textRun" in text_elem:
                            run = text_elem["textRun"]
                            content = run.get("content", "")
                            text_content += content

                            text_detail = {"content": content}
                            if "style" in run:
                                style = run["style"]
                                text_detail["style"] = {
                                    "bold": style.get("bold", False),
                                    "italic": style.get("italic", False),
                                    "underline": style.get("underline", False),
                                    "font_family": style.get("fontFamily"),
                                    "font_size": style.get("fontSize", {}).get("magnitude"),
                                    "text_color": self._extract_color(style.get("foregroundColor")),
                                }
                            text_details.append(text_detail)

                    element_info["text_content"] = text_content.strip()
                    element_info["text_details"] = text_details

                # Shape properties
                shape_props = shape.get("shapeProperties", {})
                if shape_props:
                    element_info["shape_properties"] = {
                        "background_color": self._extract_color(
                            shape_props.get("shapeBackgroundFill", {}).get("solidFill", {}).get("color")
                        ),
                        "border_width": shape_props.get("outline", {}).get("weight", {}).get("magnitude"),
                        "border_style": shape_props.get("outline", {}).get("dashStyle", "SOLID"),
                    }

            elif "table" in element:
                table = element["table"]
                table_rows = table.get("tableRows", [])
                element_info["table_info"] = {
                    "rows": len(table_rows),
                    "columns": len(table_rows[0].get("tableCells", [])) if table_rows else 0,
                }

                # Extract table content
                table_contents = []
                for row in table_rows:
                    row_contents = []
                    for cell in row.get("tableCells", []):
                        cell_text = ""
                        for text_elem in cell.get("text", {}).get("textElements", []):
                            if "textRun" in text_elem:
                                cell_text += text_elem["textRun"].get("content", "")
                        row_contents.append(cell_text.strip())
                    table_contents.append(row_contents)
                element_info["table_contents"] = table_contents

            elif "image" in element:
                image = element["image"]
                element_info["image_properties"] = {
                    "content_url": image.get("contentUrl"),
                    "source_url": image.get("sourceUrl"),
                }

            elements.append(element_info)

        return elements

    def _get_element_type(self, element: Dict[str, Any]) -> str:
        """Determine element type from element data."""
        if "shape" in element:
            return "shape"
        elif "table" in element:
            return "table"
        elif "image" in element:
            return "image"
        elif "video" in element:
            return "video"
        elif "line" in element:
            return "line"
        else:
            return "unknown"

    def _extract_color(self, color_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract color information from API response."""
        if not color_data:
            return None

        if "rgbColor" in color_data:
            rgb = color_data["rgbColor"]
            r = int(rgb.get("red", 0) * 255)
            g = int(rgb.get("green", 0) * 255)
            b = int(rgb.get("blue", 0) * 255)
            return f"#{r:02x}{g:02x}{b:02x}"

        return None

    async def export_presentation(self, presentation_id: str, export_format: str = "pdf") -> bytes:
        """Export presentation to different formats."""
        self.logger.info(f"Exporting presentation {presentation_id} as {export_format}")

        # Use Drive API for export
        drive_url = "https://www.googleapis.com/drive/v3"

        # Map formats to MIME types
        format_mapping = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "png": "image/png",
            "jpeg": "image/jpeg",
            "svg": "image/svg+xml",
            "txt": "text/plain",
        }

        mime_type = format_mapping.get(export_format.lower())
        if not mime_type:
            raise ValueError(f"Unsupported export format: {export_format}")

        export_url = f"{drive_url}/files/{presentation_id}/export"
        params = {"mimeType": mime_type}

        result = await self.api_client.make_request("GET", export_url, params=params)

        # Handle binary content
        if isinstance(result, dict) and "content" in result:
            return result["content"]
        else:
            raise ValueError("Failed to export presentation - no content received")

    async def copy_slides(
        self,
        source_presentation_id: str,
        destination_presentation_id: str,
        slide_ids: List[str],
        insertion_index: Optional[int] = None,
    ) -> List[str]:
        """Copy slides from one presentation to another."""
        self.logger.info(
            f"Copying {len(slide_ids)} slides from {source_presentation_id} to {destination_presentation_id}"
        )

        copied_slide_ids = []

        for i, slide_id in enumerate(slide_ids):
            # Get slide content from source
            source_presentation = await self.get_presentation(source_presentation_id)
            source_slides = source_presentation.get("slides", [])

            source_slide = None
            for slide in source_slides:
                if slide.get("objectId") == slide_id:
                    source_slide = slide
                    break

            if not source_slide:
                self.logger.warning(f"Source slide {slide_id} not found")
                continue

            # Create new slide in destination
            target_index = insertion_index + i if insertion_index is not None else None
            new_slide = await self.create_slide(destination_presentation_id, "BLANK", target_index)
            new_slide_id = new_slide.get("objectId")

            if not new_slide_id:
                self.logger.error(f"Failed to create slide in destination")
                continue

            # Copy elements from source slide to new slide
            requests = []
            for element in source_slide.get("pageElements", []):
                element_id = element.get("objectId")
                if not element_id:
                    continue

                # Create copy of element with new ID
                new_element_id = f"{element_id}_copy_{new_slide_id}"

                # Handle different element types
                if "shape" in element:
                    shape = element["shape"]
                    create_request = {
                        "createShape": {
                            "objectId": new_element_id,
                            "shapeType": shape.get("shapeType", "TEXT_BOX"),
                            "elementProperties": {
                                "pageObjectId": new_slide_id,
                                "size": element.get("size", {}),
                                "transform": element.get("transform", {}),
                            },
                        }
                    }
                    requests.append(create_request)

                    # Copy text content if present
                    if "text" in shape:
                        text_content = ""
                        for text_elem in shape["text"].get("textElements", []):
                            if "textRun" in text_elem:
                                text_content += text_elem["textRun"].get("content", "")

                        if text_content:
                            requests.append({"insertText": {"objectId": new_element_id, "text": text_content}})

                elif "image" in element:
                    image = element["image"]
                    if "contentUrl" in image:
                        requests.append(
                            {
                                "createImage": {
                                    "objectId": new_element_id,
                                    "url": image["contentUrl"],
                                    "elementProperties": {
                                        "pageObjectId": new_slide_id,
                                        "size": element.get("size", {}),
                                        "transform": element.get("transform", {}),
                                    },
                                }
                            }
                        )

                elif "table" in element:
                    table = element["table"]
                    table_rows = table.get("tableRows", [])
                    if table_rows:
                        rows = len(table_rows)
                        cols = len(table_rows[0].get("tableCells", []))

                        requests.append(
                            {
                                "createTable": {
                                    "objectId": new_element_id,
                                    "rows": rows,
                                    "columns": cols,
                                    "elementProperties": {
                                        "pageObjectId": new_slide_id,
                                        "size": element.get("size", {}),
                                        "transform": element.get("transform", {}),
                                    },
                                }
                            }
                        )

            # Execute all copy requests
            if requests:
                await self.batch_update(destination_presentation_id, requests)

            copied_slide_ids.append(new_slide_id)

        self.logger.info(f"Successfully copied {len(copied_slide_ids)} slides")
        return copied_slide_ids

    async def apply_theme(self, presentation_id: str, theme_presentation_id: str) -> Dict[str, Any]:
        """Apply theme from another presentation."""
        self.logger.info(f"Applying theme from {theme_presentation_id} to {presentation_id}")

        requests = [
            {
                "replaceAllShapesWithImage": {
                    "imageUrl": f"https://docs.google.com/presentation/d/{theme_presentation_id}/export/png?id={theme_presentation_id}&pageid=g1",
                    "replaceMethod": "CENTER_INSIDE",
                }
            }
        ]

        return await self.batch_update(presentation_id, requests)
