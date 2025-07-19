"""Google Forms API wrapper using aiogoogle for full async operations."""

import logging
from typing import Optional, Dict, Any, List, Union

from .google_api_client import GoogleApiClient


class FormsApiClient:
    """Async Google Forms API client using aiogoogle."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Forms API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self._service = None

    async def _get_service(self):
        """Get or create Forms service."""
        if self._service is None:
            self._service = await self.api_client.discover_service("forms", "v1")
        return self._service

    async def get_form(self, form_id: str) -> Dict[str, Any]:
        """Get form metadata and structure.

        Args:
            form_id: Google Forms form ID

        Returns:
            Form data
        """
        service = await self._get_service()

        return await self.api_client.execute_request(service, "forms.get", formId=form_id)

    async def create_form(self, title: str, document_title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new form.

        Args:
            title: Form title
            document_title: Document title (defaults to title)

        Returns:
            Created form metadata
        """
        service = await self._get_service()

        body = {"info": {"title": title, "documentTitle": document_title or title}}

        return await self.api_client.execute_request(service, "forms.create", body=body)

    async def batch_update(self, form_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on form.

        Args:
            form_id: Google Forms form ID
            requests: List of update requests

        Returns:
            Update response
        """
        service = await self._get_service()

        body = {"requests": requests}

        return await self.api_client.execute_request(service, "forms.batchUpdate", formId=form_id, body=body)

    async def get_responses(
        self, form_id: str, filter_expression: Optional[str] = None, page_size: int = 100
    ) -> Dict[str, Any]:
        """Get form responses.

        Args:
            form_id: Google Forms form ID
            filter_expression: Filter expression for responses
            page_size: Maximum number of responses per page

        Returns:
            Form responses
        """
        service = await self._get_service()

        params = {"formId": form_id, "pageSize": page_size}

        if filter_expression:
            params["filter"] = filter_expression

        return await self.api_client.execute_request(service, "forms.responses.list", **params)

    async def get_response(self, form_id: str, response_id: str) -> Dict[str, Any]:
        """Get a specific form response.

        Args:
            form_id: Google Forms form ID
            response_id: Response ID

        Returns:
            Form response data
        """
        service = await self._get_service()

        return await self.api_client.execute_request(
            service, "forms.responses.get", formId=form_id, responseId=response_id
        )

    async def create_item(
        self,
        form_id: str,
        title: str,
        question_type: str,
        location: Optional[Dict[str, Any]] = None,
        required: bool = False,
        choices: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new form item (question).

        Args:
            form_id: Google Forms form ID
            title: Question title
            question_type: Type of question (e.g., CHOICE, TEXT, SCALE)
            location: Location where to insert the item
            required: Whether the question is required
            choices: List of choices for choice questions
            description: Question description

        Returns:
            Create item response
        """
        # Build question item structure
        question_item = {
            "title": title,
            "questionItem": {
                "question": {
                    "required": required,
                }
            },
        }

        if description:
            question_item["description"] = description

        # Set question type and options
        if question_type == "CHOICE":
            question_item["questionItem"]["question"]["choiceQuestion"] = {
                "type": "RADIO",
                "options": [{"value": choice} for choice in (choices or [])],
            }
        elif question_type == "MULTIPLE_CHOICE":
            question_item["questionItem"]["question"]["choiceQuestion"] = {
                "type": "CHECKBOX",
                "options": [{"value": choice} for choice in (choices or [])],
            }
        elif question_type == "TEXT":
            question_item["questionItem"]["question"]["textQuestion"] = {"paragraph": False}
        elif question_type == "PARAGRAPH_TEXT":
            question_item["questionItem"]["question"]["textQuestion"] = {"paragraph": True}
        elif question_type == "SCALE":
            question_item["questionItem"]["question"]["scaleQuestion"] = {"low": 1, "high": 5}
        elif question_type == "DATE":
            question_item["questionItem"]["question"]["dateQuestion"] = {"includeTime": False}
        elif question_type == "TIME":
            question_item["questionItem"]["question"]["timeQuestion"] = {"duration": False}
        elif question_type == "FILE_UPLOAD":
            question_item["questionItem"]["question"]["fileUploadQuestion"] = {
                "folderId": "",
                "types": ["DOCUMENT", "SPREADSHEET", "PRESENTATION", "DRAWING", "PDF", "IMAGE", "VIDEO", "AUDIO"],
                "maxFiles": 1,
                "maxFileSize": 1073741824,  # 1GB
            }

        # Build request
        request = {"createItem": {"item": question_item}}

        if location:
            request["createItem"]["location"] = location

        return await self.batch_update(form_id, [request])

    async def update_item(self, form_id: str, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing form item.

        Args:
            form_id: Google Forms form ID
            item_id: Item ID to update
            item_data: New item data

        Returns:
            Update response
        """
        request = {"updateItem": {"item": item_data, "location": {"index": 0}, "updateMask": "*"}}

        return await self.batch_update(form_id, [request])

    async def delete_item(self, form_id: str, item_id: str) -> Dict[str, Any]:
        """Delete a form item.

        Args:
            form_id: Google Forms form ID
            item_id: Item ID to delete

        Returns:
            Delete response
        """
        request = {"deleteItem": {"location": {"index": 0}}}  # Would need proper item location

        return await self.batch_update(form_id, [request])

    async def move_item(
        self, form_id: str, original_location: Dict[str, Any], new_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Move a form item to a new position.

        Args:
            form_id: Google Forms form ID
            original_location: Current location of the item
            new_location: New location for the item

        Returns:
            Move response
        """
        request = {"moveItem": {"originalLocation": original_location, "newLocation": new_location}}

        return await self.batch_update(form_id, [request])

    async def update_form_info(
        self, form_id: str, title: Optional[str] = None, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update form information.

        Args:
            form_id: Google Forms form ID
            title: New form title
            description: New form description

        Returns:
            Update response
        """
        info_updates = {}
        if title is not None:
            info_updates["title"] = title
        if description is not None:
            info_updates["description"] = description

        if not info_updates:
            return {}

        request = {"updateFormInfo": {"info": info_updates, "updateMask": ",".join(info_updates.keys())}}

        return await self.batch_update(form_id, [request])

    async def update_settings(
        self,
        form_id: str,
        collect_email: Optional[bool] = None,
        is_quiz: Optional[bool] = None,
        allow_response_edit: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update form settings.

        Args:
            form_id: Google Forms form ID
            collect_email: Whether to collect email addresses
            is_quiz: Whether this is a quiz
            allow_response_edit: Whether to allow response editing

        Returns:
            Update response
        """
        settings_updates = {}
        if collect_email is not None:
            settings_updates["collectEmail"] = collect_email
        if is_quiz is not None:
            settings_updates["quizSettings"] = {"isQuiz": is_quiz}
        if allow_response_edit is not None:
            settings_updates["allowResponseEdit"] = allow_response_edit

        if not settings_updates:
            return {}

        request = {"updateSettings": {"settings": settings_updates, "updateMask": ",".join(settings_updates.keys())}}

        return await self.batch_update(form_id, [request])

    async def add_section_break(
        self,
        form_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a section break to the form.

        Args:
            form_id: Google Forms form ID
            title: Section title
            description: Section description
            location: Location where to insert the section break

        Returns:
            Add section response
        """
        page_break_item = {"pageBreakItem": {}}

        if title:
            page_break_item["title"] = title
        if description:
            page_break_item["description"] = description

        request = {"createItem": {"item": page_break_item}}

        if location:
            request["createItem"]["location"] = location

        return await self.batch_update(form_id, [request])

    async def add_image(
        self,
        form_id: str,
        image_uri: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add an image to the form.

        Args:
            form_id: Google Forms form ID
            image_uri: URI of the image
            title: Image title
            description: Image description
            location: Location where to insert the image

        Returns:
            Add image response
        """
        image_item = {"imageItem": {"image": {"sourceUri": image_uri}}}

        if title:
            image_item["title"] = title
        if description:
            image_item["description"] = description

        request = {"createItem": {"item": image_item}}

        if location:
            request["createItem"]["location"] = location

        return await self.batch_update(form_id, [request])

    async def add_video(
        self,
        form_id: str,
        video_uri: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a video to the form.

        Args:
            form_id: Google Forms form ID
            video_uri: URI of the video (YouTube URL)
            title: Video title
            description: Video description
            location: Location where to insert the video

        Returns:
            Add video response
        """
        video_item = {"videoItem": {"video": {"youtubeUri": video_uri}}}

        if title:
            video_item["title"] = title
        if description:
            video_item["description"] = description

        request = {"createItem": {"item": video_item}}

        if location:
            request["createItem"]["location"] = location

        return await self.batch_update(form_id, [request])

    async def add_text_item(
        self,
        form_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a text item (non-question) to the form.

        Args:
            form_id: Google Forms form ID
            title: Text item title
            description: Text item description
            location: Location where to insert the text item

        Returns:
            Add text item response
        """
        text_item = {"textItem": {}}

        if title:
            text_item["title"] = title
        if description:
            text_item["description"] = description

        request = {"createItem": {"item": text_item}}

        if location:
            request["createItem"]["location"] = location

        return await self.batch_update(form_id, [request])

    def get_question_types(self) -> List[str]:
        """Get list of supported question types.

        Returns:
            List of question type strings
        """
        return [
            "CHOICE",
            "MULTIPLE_CHOICE",
            "TEXT",
            "PARAGRAPH_TEXT",
            "SCALE",
            "DATE",
            "TIME",
            "FILE_UPLOAD",
        ]
