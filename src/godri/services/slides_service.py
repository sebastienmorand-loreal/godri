"""Google Slides service wrapper."""

import logging
from typing import Dict, Any, List, Optional
from .auth_service import AuthService


class SlidesService:
    """Google Slides operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.drive_service = None

    async def initialize(self):
        """Initialize the Slides service."""
        await self.auth_service.authenticate()
        self.service = self.auth_service.get_service("slides", "v1")
        self.drive_service = self.auth_service.get_service("drive", "v3")
        self.logger.info("Slides service initialized")

    def create_presentation(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Google Slides presentation."""
        self.logger.info("Creating presentation: %s", title)

        presentation_body = {"title": title}

        presentation = self.service.presentations().create(body=presentation_body).execute()

        presentation_id = presentation.get("presentationId")

        if folder_id:
            self.drive_service.files().update(
                fileId=presentation_id, addParents=folder_id, fields="id, parents"
            ).execute()
            self.logger.info("Presentation moved to folder: %s", folder_id)

        self.logger.info("Presentation created successfully: %s", presentation_id)
        return presentation

    def get_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """Get presentation details."""
        self.logger.info("Getting presentation: %s", presentation_id)

        presentation = self.service.presentations().get(presentationId=presentation_id).execute()

        return presentation

    def create_slide(self, presentation_id: str, layout: str = "BLANK") -> Dict[str, Any]:
        """Add a new slide to presentation."""
        self.logger.info("Creating slide in presentation: %s", presentation_id)

        requests = [{"createSlide": {"slideLayoutReference": {"predefinedLayout": layout}}}]

        result = (
            self.service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        self.logger.info("Slide created successfully")
        return result

    def delete_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any]:
        """Delete a slide from presentation."""
        self.logger.info("Deleting slide %s from presentation: %s", slide_id, presentation_id)

        requests = [{"deleteObject": {"objectId": slide_id}}]

        result = (
            self.service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        self.logger.info("Slide deleted successfully")
        return result

    def add_text_box(
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

        result = (
            self.service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        self.logger.info("Text box added successfully")
        return result

    def replace_text(self, presentation_id: str, old_text: str, new_text: str) -> Dict[str, Any]:
        """Replace all occurrences of text in presentation."""
        self.logger.info("Replacing text in presentation: %s", presentation_id)

        requests = [
            {"replaceAllText": {"containsText": {"text": old_text, "matchCase": False}, "replaceText": new_text}}
        ]

        result = (
            self.service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        self.logger.info("Text replaced successfully")
        return result

    def add_image(
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

        result = (
            self.service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        self.logger.info("Image added successfully")
        return result

    def format_text(
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

        result = (
            self.service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        self.logger.info("Text formatted successfully")
        return result

    def get_slide_ids(self, presentation_id: str) -> List[str]:
        """Get all slide IDs from presentation."""
        presentation = self.get_presentation(presentation_id)

        slide_ids = []
        for slide in presentation.get("slides", []):
            slide_ids.append(slide["objectId"])

        return slide_ids

    def duplicate_slide(self, presentation_id: str, slide_id: str) -> Dict[str, Any]:
        """Duplicate a slide."""
        self.logger.info("Duplicating slide %s in presentation: %s", slide_id, presentation_id)

        requests = [{"duplicateObject": {"objectId": slide_id}}]

        result = (
            self.service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        self.logger.info("Slide duplicated successfully")
        return result
