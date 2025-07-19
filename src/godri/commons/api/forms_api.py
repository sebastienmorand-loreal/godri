"""Google Forms API client with async aiohttp."""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from .google_api_client import GoogleApiClient


class FormsApiClient:
    """Async Google Forms API client."""

    def __init__(self, api_client: GoogleApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://forms.googleapis.com/v1"

    async def create_form(
        self, title: str, description: Optional[str] = None, folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new Google Form."""
        self.logger.info(f"Creating form: {title}")

        form_metadata = {"info": {"title": title}}

        if description:
            form_metadata["info"]["description"] = description

        url = f"{self.base_url}/forms"
        result = await self.api_client.make_request("POST", url, data=form_metadata)

        form_id = result.get("formId")
        self.logger.info(f"Form created successfully: {form_id}")

        # If folder_id specified, move form to folder using Drive API
        if folder_id:
            drive_url = "https://www.googleapis.com/drive/v3"

            # Get current parents
            file_info_url = f"{drive_url}/files/{form_id}"
            file_info = await self.api_client.make_request("GET", file_info_url, params={"fields": "parents"})
            current_parents = file_info.get("parents", [])

            # Move to new folder
            move_url = f"{drive_url}/files/{form_id}"
            move_params = {"addParents": folder_id, "removeParents": ",".join(current_parents), "fields": "id, parents"}
            await self.api_client.make_request("PATCH", move_url, params=move_params)
            self.logger.info(f"Form moved to folder: {folder_id}")

        return result

    async def get_form(self, form_id: str) -> Dict[str, Any]:
        """Get form structure and content."""
        self.logger.info(f"Getting form: {form_id}")

        url = f"{self.base_url}/forms/{form_id}"

        return await self.api_client.make_request("GET", url)

    async def batch_update(self, form_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch updates on form."""
        self.logger.info(f"Batch updating form: {form_id} with {len(requests)} requests")

        update_data = {"requests": requests}
        url = f"{self.base_url}/forms/{form_id}:batchUpdate"

        result = await self.api_client.make_request("POST", url, data=update_data)
        self.logger.info(f"Batch update completed successfully")
        return result

    async def update_form_info(
        self,
        form_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        document_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update basic form information."""
        self.logger.info(f"Updating form info: {form_id}")

        info_updates = {}
        if title is not None:
            info_updates["title"] = title
        if description is not None:
            info_updates["description"] = description
        if document_title is not None:
            info_updates["documentTitle"] = document_title

        if not info_updates:
            self.logger.warning("No updates provided for form info")
            return {}

        requests = [{"updateFormInfo": {"info": info_updates, "updateMask": ",".join(info_updates.keys())}}]

        return await self.batch_update(form_id, requests)

    async def create_item(
        self, form_id: str, item_data: Dict[str, Any], location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new item (question or section) in form."""
        self.logger.info(f"Creating item in form: {form_id}")

        create_request = {"createItem": {"item": item_data}}

        if location:
            create_request["createItem"]["location"] = location

        requests = [create_request]
        result = await self.batch_update(form_id, requests)

        return result.get("replies", [{}])[0].get("createItem", {})

    async def update_item(
        self, form_id: str, item_id: str, item_data: Dict[str, Any], update_mask: str
    ) -> Dict[str, Any]:
        """Update an existing item in form."""
        self.logger.info(f"Updating item {item_id} in form: {form_id}")

        requests = [{"updateItem": {"item": {"itemId": item_id, **item_data}, "updateMask": update_mask}}]

        return await self.batch_update(form_id, requests)

    async def delete_item(self, form_id: str, item_id: str) -> Dict[str, Any]:
        """Delete an item from form."""
        self.logger.info(f"Deleting item {item_id} from form: {form_id}")

        requests = [{"deleteItem": {"location": {"index": 0}}}]  # Will be updated based on actual position

        return await self.batch_update(form_id, requests)

    async def move_item(
        self, form_id: str, original_location: Dict[str, Any], new_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Move an item to a new position in form."""
        self.logger.info(f"Moving item in form: {form_id}")

        requests = [{"moveItem": {"originalLocation": original_location, "newLocation": new_location}}]

        return await self.batch_update(form_id, requests)

    async def add_text_question(
        self,
        form_id: str,
        title: str,
        description: Optional[str] = None,
        required: bool = False,
        location_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a text question to form."""
        self.logger.info(f"Adding text question '{title}' to form: {form_id}")

        question_item = {"title": title, "questionItem": {"question": {"required": required, "textQuestion": {}}}}

        if description:
            question_item["description"] = description

        location = None
        if location_index is not None:
            location = {"index": location_index}

        return await self.create_item(form_id, question_item, location)

    async def add_choice_question(
        self,
        form_id: str,
        title: str,
        options: List[str],
        question_type: str = "RADIO",
        description: Optional[str] = None,
        required: bool = False,
        location_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a choice question (radio/checkbox) to form."""
        self.logger.info(f"Adding {question_type} choice question '{title}' to form: {form_id}")

        choice_options = []
        for option_text in options:
            choice_options.append({"value": option_text})

        question_item = {
            "title": title,
            "questionItem": {
                "question": {"required": required, "choiceQuestion": {"type": question_type, "options": choice_options}}
            },
        }

        if description:
            question_item["description"] = description

        location = None
        if location_index is not None:
            location = {"index": location_index}

        return await self.create_item(form_id, question_item, location)

    async def add_scale_question(
        self,
        form_id: str,
        title: str,
        low_value: int = 1,
        high_value: int = 5,
        low_label: Optional[str] = None,
        high_label: Optional[str] = None,
        description: Optional[str] = None,
        required: bool = False,
        location_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a scale question to form."""
        self.logger.info(f"Adding scale question '{title}' to form: {form_id}")

        scale_question = {"low": low_value, "high": high_value}

        if low_label:
            scale_question["lowLabel"] = low_label
        if high_label:
            scale_question["highLabel"] = high_label

        question_item = {
            "title": title,
            "questionItem": {"question": {"required": required, "scaleQuestion": scale_question}},
        }

        if description:
            question_item["description"] = description

        location = None
        if location_index is not None:
            location = {"index": location_index}

        return await self.create_item(form_id, question_item, location)

    async def add_date_question(
        self,
        form_id: str,
        title: str,
        include_time: bool = False,
        include_year: bool = True,
        description: Optional[str] = None,
        required: bool = False,
        location_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a date question to form."""
        self.logger.info(f"Adding date question '{title}' to form: {form_id}")

        date_question = {"includeTime": include_time, "includeYear": include_year}

        question_item = {
            "title": title,
            "questionItem": {"question": {"required": required, "dateQuestion": date_question}},
        }

        if description:
            question_item["description"] = description

        location = None
        if location_index is not None:
            location = {"index": location_index}

        return await self.create_item(form_id, question_item, location)

    async def add_time_question(
        self,
        form_id: str,
        title: str,
        duration: bool = False,
        description: Optional[str] = None,
        required: bool = False,
        location_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a time question to form."""
        self.logger.info(f"Adding time question '{title}' to form: {form_id}")

        time_question = {"duration": duration}

        question_item = {
            "title": title,
            "questionItem": {"question": {"required": required, "timeQuestion": time_question}},
        }

        if description:
            question_item["description"] = description

        location = None
        if location_index is not None:
            location = {"index": location_index}

        return await self.create_item(form_id, question_item, location)

    async def add_file_upload_question(
        self,
        form_id: str,
        title: str,
        allowed_types: Optional[List[str]] = None,
        max_files: int = 1,
        max_file_size: Optional[int] = None,
        description: Optional[str] = None,
        required: bool = False,
        location_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a file upload question to form."""
        self.logger.info(f"Adding file upload question '{title}' to form: {form_id}")

        file_upload_question = {"maxFiles": max_files}

        if allowed_types:
            file_upload_question["types"] = allowed_types
        if max_file_size:
            file_upload_question["maxFileSize"] = max_file_size

        question_item = {
            "title": title,
            "questionItem": {"question": {"required": required, "fileUploadQuestion": file_upload_question}},
        }

        if description:
            question_item["description"] = description

        location = None
        if location_index is not None:
            location = {"index": location_index}

        return await self.create_item(form_id, question_item, location)

    async def add_section_break(
        self, form_id: str, title: str, description: Optional[str] = None, location_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a section break to form."""
        self.logger.info(f"Adding section break '{title}' to form: {form_id}")

        section_item = {"title": title, "pageBreakItem": {}}

        if description:
            section_item["description"] = description

        location = None
        if location_index is not None:
            location = {"index": location_index}

        return await self.create_item(form_id, section_item, location)

    async def get_form_responses(self, form_id: str, filter_criteria: Optional[str] = None) -> Dict[str, Any]:
        """Get responses to a form."""
        self.logger.info(f"Getting responses for form: {form_id}")

        params = {}
        if filter_criteria:
            params["filter"] = filter_criteria

        url = f"{self.base_url}/forms/{form_id}/responses"

        return await self.api_client.make_request("GET", url, params=params)

    async def get_specific_response(self, form_id: str, response_id: str) -> Dict[str, Any]:
        """Get a specific response to a form."""
        self.logger.info(f"Getting response {response_id} for form: {form_id}")

        url = f"{self.base_url}/forms/{form_id}/responses/{response_id}"

        return await self.api_client.make_request("GET", url)

    def get_questions_from_form(self, form_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract questions from form data structure."""
        questions = []
        items = form_data.get("items", [])

        question_number = 1
        for i, item in enumerate(items):
            item_id = item.get("itemId", "")
            title = item.get("title", "")
            description = item.get("description", "")

            # Check if this is a section break (page break)
            if "pageBreakItem" in item:
                questions.append(
                    {
                        "item_index": i,
                        "item_id": item_id,
                        "title": title,
                        "description": description,
                        "is_section_break": True,
                        "question_number": None,
                        "question_type": "section_break",
                        "required": False,
                        "choices": None,
                    }
                )
            elif "questionItem" in item:
                question_item = item["questionItem"]
                question = question_item.get("question", {})
                required = question.get("required", False)

                # Determine question type and extract choices if applicable
                question_type = "text"
                choices = None

                if "textQuestion" in question:
                    question_type = "text"
                elif "choiceQuestion" in question:
                    choice_q = question["choiceQuestion"]
                    if choice_q.get("type") == "RADIO":
                        question_type = "choice"
                    elif choice_q.get("type") == "CHECKBOX":
                        question_type = "checkbox"
                    else:
                        question_type = "choice"

                    choices = []
                    for option in choice_q.get("options", []):
                        choices.append(
                            {
                                "value": option.get("value", ""),
                                "image": option.get("image", {}).get("contentUri") if "image" in option else None,
                            }
                        )

                elif "scaleQuestion" in question:
                    question_type = "scale"
                elif "dateQuestion" in question:
                    question_type = "date"
                elif "timeQuestion" in question:
                    question_type = "time"
                elif "fileUploadQuestion" in question:
                    question_type = "file_upload"

                questions.append(
                    {
                        "item_index": i,
                        "item_id": item_id,
                        "title": title,
                        "description": description,
                        "is_section_break": False,
                        "question_number": question_number,
                        "question_type": question_type,
                        "required": required,
                        "choices": choices,
                    }
                )
                question_number += 1
            else:
                # Other item types (text, image, etc.)
                questions.append(
                    {
                        "item_index": i,
                        "item_id": item_id,
                        "title": title,
                        "description": description,
                        "is_section_break": False,
                        "question_number": None,
                        "question_type": "other",
                        "required": False,
                        "choices": None,
                    }
                )

        return questions

    def get_sections_from_form(self, form_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sections from form data structure."""
        sections = []
        items = form_data.get("items", [])

        current_section = {
            "index": 1,
            "title": "Main Section",
            "description": "",
            "question_count": 0,
            "start_item_index": 0,
            "end_item_index": len(items) - 1 if items else 0,
        }

        section_index = 1
        question_count = 0

        for i, item in enumerate(items):
            if "pageBreakItem" in item:
                # End current section
                current_section["question_count"] = question_count
                current_section["end_item_index"] = i - 1 if i > 0 else 0
                sections.append(current_section)

                # Start new section
                section_index += 1
                current_section = {
                    "index": section_index,
                    "title": item.get("title", f"Section {section_index}"),
                    "description": item.get("description", ""),
                    "question_count": 0,
                    "start_item_index": i + 1,
                    "end_item_index": len(items) - 1,
                }
                question_count = 0

            elif "questionItem" in item:
                question_count += 1

        # Add the last section
        current_section["question_count"] = question_count
        sections.append(current_section)

        return sections

    async def translate_question(
        self,
        form_id: str,
        item_id: str,
        target_language: str,
        source_language: Optional[str] = None,
        translate_answers: bool = True,
    ) -> Dict[str, Any]:
        """Translate a question and optionally its answer options."""
        self.logger.info(f"Translating question {item_id} to {target_language} in form: {form_id}")

        # Get current form data
        form_data = await self.get_form(form_id)

        # Find the item to translate
        target_item = None
        for item in form_data.get("items", []):
            if item.get("itemId") == item_id:
                target_item = item
                break

        if not target_item:
            raise ValueError(f"Item {item_id} not found in form")

        # Prepare texts to translate
        texts_to_translate = []
        text_map = {}

        # Title
        title = target_item.get("title", "")
        if title.strip():
            texts_to_translate.append(title)
            text_map["title"] = len(texts_to_translate) - 1

        # Description
        description = target_item.get("description", "")
        if description.strip():
            texts_to_translate.append(description)
            text_map["description"] = len(texts_to_translate) - 1

        # Answer options if it's a choice question
        choices_indices = []
        if translate_answers and "questionItem" in target_item:
            question = target_item["questionItem"].get("question", {})
            if "choiceQuestion" in question:
                options = question["choiceQuestion"].get("options", [])
                for option in options:
                    value = option.get("value", "")
                    if value.strip():
                        texts_to_translate.append(value)
                        choices_indices.append(len(texts_to_translate) - 1)

        if not texts_to_translate:
            self.logger.warning("No text found to translate")
            return {"translations": {"title": None, "description": None, "options": []}}

        # Translate using Google Translate API
        translate_url = "https://translation.googleapis.com/language/translate/v2"
        translate_data = {"q": texts_to_translate, "target": target_language, "format": "text"}

        if source_language:
            translate_data["source"] = source_language

        translation_result = await self.api_client.make_request("POST", translate_url, data=translate_data)
        translations = translation_result.get("data", {}).get("translations", [])

        if not translations:
            raise ValueError("Translation failed - no results returned")

        # Apply translations
        updates = {}

        # Update title
        if "title" in text_map:
            translated_title = translations[text_map["title"]]["translatedText"]
            updates["title"] = translated_title

        # Update description
        if "description" in text_map:
            translated_description = translations[text_map["description"]]["translatedText"]
            updates["description"] = translated_description

        # Update choice options
        if choices_indices and "questionItem" in target_item:
            question_item = target_item["questionItem"].copy()
            choice_question = question_item["question"]["choiceQuestion"].copy()
            new_options = []

            for i, option in enumerate(choice_question.get("options", [])):
                new_option = option.copy()
                if i < len(choices_indices):
                    choice_index = choices_indices[i]
                    if choice_index < len(translations):
                        new_option["value"] = translations[choice_index]["translatedText"]
                new_options.append(new_option)

            choice_question["options"] = new_options
            question_item["question"]["choiceQuestion"] = choice_question
            updates["questionItem"] = question_item

        # Update the form
        if updates:
            update_fields = []
            if "title" in updates:
                update_fields.append("title")
            if "description" in updates:
                update_fields.append("description")
            if "questionItem" in updates:
                update_fields.append("questionItem.question.choiceQuestion.options")

            await self.update_item(form_id, item_id, updates, ",".join(update_fields))

        # Prepare response with translation details
        translation_response = {
            "translations": {
                "title": (
                    {
                        "original": title,
                        "translated": (
                            translations[text_map["title"]]["translatedText"] if "title" in text_map else None
                        ),
                    }
                    if "title" in text_map
                    else None
                ),
                "description": (
                    {
                        "original": description,
                        "translated": (
                            translations[text_map["description"]]["translatedText"]
                            if "description" in text_map
                            else None
                        ),
                    }
                    if "description" in text_map
                    else None
                ),
                "options": [],
            }
        }

        # Add option translations
        if choices_indices and "questionItem" in target_item:
            original_options = target_item["questionItem"]["question"]["choiceQuestion"].get("options", [])
            for i, choice_index in enumerate(choices_indices):
                if i < len(original_options) and choice_index < len(translations):
                    translation_response["translations"]["options"].append(
                        {
                            "original": original_options[i].get("value", ""),
                            "translated": translations[choice_index]["translatedText"],
                        }
                    )

        self.logger.info(f"Question translated successfully")
        return translation_response
