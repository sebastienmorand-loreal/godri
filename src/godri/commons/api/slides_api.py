"""Google Slides API wrapper using aiogoogle for full async operations."""

import logging
from typing import Optional, Dict, Any, List, Union

from .google_api_client import GoogleApiClient


class SlidesApiClient:
    """Async Google Slides API client using aiogoogle."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Slides API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self._service = None

    async def _get_service(self):
        """Get or create Slides service."""
        if self._service is None:
            self._service = await self.api_client.discover_service("slides", "v1")
        return self._service

    async def get_presentation(self, presentation_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get presentation metadata and content.

        Args:
            presentation_id: Google Slides presentation ID
            fields: Comma-separated list of fields to return

        Returns:
            Presentation data
        """
        service = await self._get_service()

        params = {"presentationId": presentation_id}
        if fields:
            params["fields"] = fields

        return await self.api_client.execute_request(service, "presentations.get", **params)

    async def create_presentation(self, title: str) -> Dict[str, Any]:
        """Create a new presentation.

        Args:
            title: Presentation title

        Returns:
            Created presentation metadata
        """
        service = await self._get_service()

        body = {"title": title}

        return await self.api_client.execute_request(service, "presentations.create", body=body)

    async def batch_update(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on presentation.

        Args:
            presentation_id: Google Slides presentation ID
            requests: List of update requests

        Returns:
            Update response
        """
        service = await self._get_service()

        body = {"requests": requests}

        return await self.api_client.execute_request(
            service, "presentations.batchUpdate", presentationId=presentation_id, body=body
        )

    async def create_slide(
        self,
        presentation_id: str,
        layout_id: Optional[str] = None,
        slide_index: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new slide in the presentation.

        Args:
            presentation_id: Google Slides presentation ID
            layout_id: Layout ID for the new slide
            slide_index: Index where to insert the slide
            object_id: Custom object ID for the slide

        Returns:
            Create slide response
        """
        request = {"createSlide": {}}

        if layout_id:
            request["createSlide"]["slideLayoutReference"] = {"layoutId": layout_id}

        if slide_index is not None:
            request["createSlide"]["insertionIndex"] = slide_index

        if object_id:
            request["createSlide"]["objectId"] = object_id

        return await self.batch_update(presentation_id, [request])

    async def duplicate_slide(
        self, presentation_id: str, slide_object_id: str, slide_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Duplicate a slide within the presentation.

        Args:
            presentation_id: Google Slides presentation ID
            slide_object_id: Object ID of the slide to duplicate
            slide_index: Index where to insert the duplicated slide

        Returns:
            Duplicate slide response
        """
        request = {"duplicateObject": {"objectId": slide_object_id}}

        if slide_index is not None:
            request["duplicateObject"]["insertionIndex"] = slide_index

        return await self.batch_update(presentation_id, [request])

    async def delete_slide(self, presentation_id: str, slide_object_id: str) -> Dict[str, Any]:
        """Delete a slide from the presentation.

        Args:
            presentation_id: Google Slides presentation ID
            slide_object_id: Object ID of the slide to delete

        Returns:
            Delete slide response
        """
        request = {"deleteObject": {"objectId": slide_object_id}}

        return await self.batch_update(presentation_id, [request])

    async def replace_text(self, presentation_id: str, old_text: str, new_text: str) -> Dict[str, Any]:
        """Replace text throughout the presentation.

        Args:
            presentation_id: Google Slides presentation ID
            old_text: Text to find and replace
            new_text: Replacement text

        Returns:
            Replace text response
        """
        request = {"replaceAllText": {"containsText": {"text": old_text, "matchCase": False}, "replaceText": new_text}}

        return await self.batch_update(presentation_id, [request])

    async def create_text_box(
        self,
        presentation_id: str,
        slide_object_id: str,
        text: str,
        x: float,
        y: float,
        width: float,
        height: float,
        object_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a text box on a slide.

        Args:
            presentation_id: Google Slides presentation ID
            slide_object_id: Object ID of the slide
            text: Text content
            x: X coordinate in EMU (English Metric Units)
            y: Y coordinate in EMU
            width: Width in EMU
            height: Height in EMU
            object_id: Custom object ID for the text box

        Returns:
            Create text box response
        """
        element_properties = {
            "pageObjectId": slide_object_id,
            "size": {"width": {"magnitude": width, "unit": "EMU"}, "height": {"magnitude": height, "unit": "EMU"}},
            "transform": {
                "scaleX": 1.0,
                "scaleY": 1.0,
                "translateX": x,
                "translateY": y,
                "unit": "EMU",
            },
        }

        if object_id:
            element_properties["objectId"] = object_id

        requests = [
            {"createShape": {"elementProperties": element_properties, "shapeType": "TEXT_BOX"}},
            {"insertText": {"objectId": object_id or "TEXT_BOX", "text": text}},
        ]

        return await self.batch_update(presentation_id, requests)

    async def create_image(
        self,
        presentation_id: str,
        slide_object_id: str,
        image_url: str,
        x: float,
        y: float,
        width: float,
        height: float,
        object_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an image on a slide.

        Args:
            presentation_id: Google Slides presentation ID
            slide_object_id: Object ID of the slide
            image_url: URL of the image
            x: X coordinate in EMU
            y: Y coordinate in EMU
            width: Width in EMU
            height: Height in EMU
            object_id: Custom object ID for the image

        Returns:
            Create image response
        """
        element_properties = {
            "pageObjectId": slide_object_id,
            "size": {"width": {"magnitude": width, "unit": "EMU"}, "height": {"magnitude": height, "unit": "EMU"}},
            "transform": {
                "scaleX": 1.0,
                "scaleY": 1.0,
                "translateX": x,
                "translateY": y,
                "unit": "EMU",
            },
        }

        if object_id:
            element_properties["objectId"] = object_id

        request = {"createImage": {"elementProperties": element_properties, "url": image_url}}

        return await self.batch_update(presentation_id, [request])

    async def create_shape(
        self,
        presentation_id: str,
        slide_object_id: str,
        shape_type: str,
        x: float,
        y: float,
        width: float,
        height: float,
        object_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a shape on a slide.

        Args:
            presentation_id: Google Slides presentation ID
            slide_object_id: Object ID of the slide
            shape_type: Type of shape (e.g., "RECTANGLE", "ELLIPSE")
            x: X coordinate in EMU
            y: Y coordinate in EMU
            width: Width in EMU
            height: Height in EMU
            object_id: Custom object ID for the shape

        Returns:
            Create shape response
        """
        element_properties = {
            "pageObjectId": slide_object_id,
            "size": {"width": {"magnitude": width, "unit": "EMU"}, "height": {"magnitude": height, "unit": "EMU"}},
            "transform": {
                "scaleX": 1.0,
                "scaleY": 1.0,
                "translateX": x,
                "translateY": y,
                "unit": "EMU",
            },
        }

        if object_id:
            element_properties["objectId"] = object_id

        request = {"createShape": {"elementProperties": element_properties, "shapeType": shape_type}}

        return await self.batch_update(presentation_id, [request])

    async def update_text_style(
        self,
        presentation_id: str,
        object_id: str,
        text_range: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update text style for a text element.

        Args:
            presentation_id: Google Slides presentation ID
            object_id: Object ID of the text element
            text_range: Range of text to style (optional, entire text if None)
            style: Text style properties

        Returns:
            Update text style response
        """
        request = {"updateTextStyle": {"objectId": object_id}}

        if text_range:
            request["updateTextStyle"]["textRange"] = text_range

        if style:
            request["updateTextStyle"]["style"] = style
            request["updateTextStyle"]["fields"] = ",".join(style.keys())

        return await self.batch_update(presentation_id, [request])

    async def update_shape_properties(
        self, presentation_id: str, object_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update shape properties.

        Args:
            presentation_id: Google Slides presentation ID
            object_id: Object ID of the shape
            properties: Shape properties to update

        Returns:
            Update shape properties response
        """
        request = {
            "updateShapeProperties": {
                "objectId": object_id,
                "shapeProperties": properties,
                "fields": ",".join(properties.keys()),
            }
        }

        return await self.batch_update(presentation_id, [request])

    async def move_object(
        self, presentation_id: str, object_id: str, x: float, y: float, scale_x: float = 1.0, scale_y: float = 1.0
    ) -> Dict[str, Any]:
        """Move and optionally scale an object on a slide.

        Args:
            presentation_id: Google Slides presentation ID
            object_id: Object ID to move
            x: New X coordinate in EMU
            y: New Y coordinate in EMU
            scale_x: Scale factor for X axis
            scale_y: Scale factor for Y axis

        Returns:
            Update page element transform response
        """
        request = {
            "updatePageElementTransform": {
                "objectId": object_id,
                "transform": {
                    "scaleX": scale_x,
                    "scaleY": scale_y,
                    "translateX": x,
                    "translateY": y,
                    "unit": "EMU",
                },
                "applyMode": "ABSOLUTE",
            }
        }

        return await self.batch_update(presentation_id, [request])

    async def resize_object(self, presentation_id: str, object_id: str, width: float, height: float) -> Dict[str, Any]:
        """Resize an object on a slide.

        Args:
            presentation_id: Google Slides presentation ID
            object_id: Object ID to resize
            width: New width in EMU
            height: New height in EMU

        Returns:
            Update page element size response
        """
        request = {
            "updatePageElementSize": {
                "objectId": object_id,
                "size": {"width": {"magnitude": width, "unit": "EMU"}, "height": {"magnitude": height, "unit": "EMU"}},
            }
        }

        return await self.batch_update(presentation_id, [request])

    async def get_thumbnails(
        self, presentation_id: str, thumbnail_properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get thumbnails for all slides in the presentation.

        Args:
            presentation_id: Google Slides presentation ID
            thumbnail_properties: Properties for thumbnail generation

        Returns:
            Thumbnails response
        """
        service = await self._get_service()

        params = {"presentationId": presentation_id}
        if thumbnail_properties:
            params.update(thumbnail_properties)

        return await self.api_client.execute_request(service, "presentations.pages.getThumbnail", **params)

    def emu_to_points(self, emu: float) -> float:
        """Convert EMU (English Metric Units) to points.

        Args:
            emu: Value in EMU

        Returns:
            Value in points
        """
        return emu / 12700

    def points_to_emu(self, points: float) -> float:
        """Convert points to EMU (English Metric Units).

        Args:
            points: Value in points

        Returns:
            Value in EMU
        """
        return points * 12700

    def inches_to_emu(self, inches: float) -> float:
        """Convert inches to EMU (English Metric Units).

        Args:
            inches: Value in inches

        Returns:
            Value in EMU
        """
        return inches * 914400

    def emu_to_inches(self, emu: float) -> float:
        """Convert EMU (English Metric Units) to inches.

        Args:
            emu: Value in EMU

        Returns:
            Value in inches
        """
        return emu / 914400
