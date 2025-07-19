"""Google Forms service wrapper."""

import logging
from typing import List, Dict, Optional, Any, Union
from .auth_service import AuthService
from .translate_service import TranslateService


class FormsService:
    """Google Forms operations."""

    def __init__(self, auth_service: AuthService, translate_service: Optional[TranslateService] = None):
        self.auth_service = auth_service
        self.translate_service = translate_service
        self.logger = logging.getLogger(__name__)
        self.service = None

    async def initialize(self):
        """Initialize the Forms service."""
        await self.auth_service.authenticate()
        self.service = self.auth_service.get_service("forms", "v1")
        self.logger.info("Forms service initialized")

    def get_form(self, form_id: str) -> Dict[str, Any]:
        """Get complete form structure including questions and sections.

        Args:
            form_id: Google Form ID

        Returns:
            Dictionary containing complete form structure
        """
        self.logger.info("Getting form structure: %s", form_id)

        form = self.service.forms().get(formId=form_id).execute()

        # Process and organize the form structure
        processed_form = self._process_form_structure(form)

        self.logger.info("Form retrieved successfully with %d items", len(processed_form.get("items", [])))
        return processed_form

    def get_questions(self, form_id: str, section_filter: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all questions from a form organized by sections.

        Args:
            form_id: Google Form ID
            section_filter: Optional section number (1-based) to filter questions.
                           If provided, only questions from that section are returned.
                           If None, all questions are returned.

        Returns:
            List of questions with section information
        """
        self.logger.info("Getting all questions from form: %s", form_id)

        form = self.get_form(form_id)
        questions = []
        current_section = {"title": "Default Section", "description": "", "index": 0}
        question_number = 1

        for item in form.get("items", []):
            if "pageBreakItem" in item:
                # This is a section break
                page_break = item.get("pageBreakItem", {})
                # Calculate correct section index: first pageBreak creates section 1, second creates section 2, etc.
                section_index = len([q for q in questions if q.get("is_section_break")]) + 1
                current_section = {
                    "title": item.get("title", f"Section {section_index + 1}"),  # +1 for display purposes
                    "description": item.get("description", ""),
                    "index": section_index,
                    "go_to_action": page_break.get("goToAction"),
                    "go_to_section_id": page_break.get("goToSectionId"),
                }
                questions.append(
                    {
                        "is_section_break": True,
                        "section_info": current_section,
                        "item_id": item.get("itemId"),
                    }
                )
            elif self._is_question_item(item):
                # This is a question
                question = self._process_question_item(item, current_section, question_number)
                questions.append(question)
                question_number += 1

        # Apply section filter if specified
        if section_filter is not None:
            if section_filter < 1:
                raise ValueError("Section numbers must be 1-based (>= 1)")

            # Convert 1-based section number to 0-based section index
            target_section_index = section_filter - 1
            filtered_questions = []

            for question in questions:
                if question.get("is_section_break"):
                    # Keep section breaks to maintain structure
                    filtered_questions.append(question)
                elif question.get("section", {}).get("index") == target_section_index:
                    # Keep questions from target section
                    filtered_questions.append(question)

            questions = filtered_questions
            self.logger.info("Filtered to section %d: %d items returned", section_filter, len(questions))
        else:
            self.logger.info("Retrieved %d items (%d questions) from form", len(questions), question_number - 1)

        return questions

    def get_question(self, form_id: str, question_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific question by its number.

        Args:
            form_id: Google Form ID
            question_number: Question number (1-based)

        Returns:
            Question details or None if not found
        """
        if question_number < 1:
            raise ValueError("Question numbers must be 1-based (>= 1)")

        self.logger.info("Getting question %d from form: %s", question_number, form_id)

        questions = self.get_questions(form_id)
        actual_questions = [q for q in questions if not q.get("is_section_break")]

        if 1 <= question_number <= len(actual_questions):
            question = actual_questions[question_number - 1]
            self.logger.info("Question %d retrieved successfully", question_number)
            return question

        self.logger.warning("Question %d not found (form has %d questions)", question_number, len(actual_questions))
        return None

    def get_section_questions(self, form_id: str, section_number: int) -> List[Dict[str, Any]]:
        """Get all questions from a specific section.

        Args:
            form_id: Google Form ID
            section_number: Section number (1-based)

        Returns:
            List of questions in the section
        """
        if section_number < 1:
            raise ValueError("Section numbers must be 1-based (>= 1)")

        # Convert 1-based to 0-based for internal processing
        section_index = section_number - 1
        self.logger.info("Getting questions from section %d (1-based) in form: %s", section_number, form_id)

        questions = self.get_questions(form_id)
        section_questions = [
            q for q in questions if not q.get("is_section_break") and q.get("section", {}).get("index") == section_index
        ]

        self.logger.info("Found %d questions in section %d", len(section_questions), section_number)
        return section_questions

    def get_sections(self, form_id: str) -> List[Dict[str, Any]]:
        """Get all sections from a form.

        Args:
            form_id: Google Form ID

        Returns:
            List of sections with their navigation options
        """
        self.logger.info("Getting all sections from form: %s", form_id)

        questions = self.get_questions(form_id)
        sections = []

        # Add default section if there are questions before the first page break
        first_break_index = next((i for i, q in enumerate(questions) if q.get("is_section_break")), len(questions))
        if first_break_index > 0:
            sections.append(
                {
                    "index": 0,
                    "title": "Default Section",
                    "description": "",
                    "question_count": first_break_index,
                    "go_to_action": None,
                    "go_to_section_id": None,
                }
            )

        # Add explicit sections
        for item in questions:
            if item.get("is_section_break"):
                section_info = item.get("section_info", {})
                section_questions = self.get_section_questions(form_id, section_info.get("index", 0) + 1)
                sections.append(
                    {
                        "index": section_info.get("index", 0),
                        "title": section_info.get("title", ""),
                        "description": section_info.get("description", ""),
                        "question_count": len(section_questions),
                        "go_to_action": section_info.get("go_to_action"),
                        "go_to_section_id": section_info.get("go_to_section_id"),
                        "item_id": item.get("item_id"),
                    }
                )

        self.logger.info("Found %d sections in form", len(sections))
        return sections

    def add_section(
        self,
        form_id: str,
        title: str,
        description: str = "",
        position: str = "end",
        section_number: Optional[int] = None,
        question_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a new section to the form.

        Args:
            form_id: Google Form ID
            title: Section title
            description: Section description
            position: Position relative to reference ("before", "after", "end")
            section_number: Section number for positioning (1-based, required if not "end")
            question_number: Question number within section for positioning (1-based, required if not "end")

        Returns:
            Created section information
        """
        self.logger.info("Adding section '%s' to form: %s", title, form_id)

        # Create page break item
        new_item = {"title": title, "description": description, "pageBreakItem": {}}

        # Determine insertion location using new index calculation method
        if position == "end":
            location = {"index": 0}  # End of form
        else:
            if section_number is None or question_number is None:
                raise ValueError("section_number and question_number are required when position is not 'end'")

            if section_number < 1 or question_number < 1:
                raise ValueError("Section and question numbers must be 1-based (>= 1)")

            index = self._calculate_index_location(
                form_id, section_number=section_number, question_number=question_number, position=position
            )
            location = {"index": index}

        # Create the section
        request = {"createItem": {"item": new_item, "location": location}}

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Section '%s' added successfully", title)
        return response

    def add_question(
        self,
        form_id: str,
        question_data: Dict[str, Any],
        section_number: int = 1,
        position: str = "end",
        reference_question: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a new question to the form.

        Args:
            form_id: Google Form ID
            question_data: Question configuration
            section_number: Target section number (1-based)
            position: Position relative to reference ("before", "after", "end")
            reference_question: Question number for positioning (if not "end")

        Returns:
            Created question information
        """
        if section_number < 1:
            raise ValueError("Section numbers must be 1-based (>= 1)")
        if reference_question is not None and reference_question < 1:
            raise ValueError("Reference question numbers must be 1-based (>= 1)")

        # Convert 1-based to 0-based for internal processing
        section_index = section_number - 1
        self.logger.info("Adding question to section %d (1-based) in form: %s", section_number, form_id)

        # Create question item from question_data
        new_item = self._build_question_item(question_data)

        # Use new pageBreak-based location calculation
        if position == "end":
            # Add to end of specified section
            index = self._calculate_index_location(form_id, section_number=section_number, position_in_section="end")
        elif position in ["before", "after"] and reference_question is not None:
            # reference_question is already the question number within the specified section (1-based)
            index = self._calculate_index_location(
                form_id, section_number=section_number, question_number=reference_question, position=position
            )
        else:
            # Fallback to end of form
            index = self._calculate_index_location(form_id)

        location = {"index": index}

        # Create the question
        request = {"createItem": {"item": new_item, "location": location}}

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Question added successfully")
        return response

    def update_question(self, form_id: str, question_number: int, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing question.

        Args:
            form_id: Google Form ID
            question_number: Question number to update (1-based)
            question_data: New question configuration

        Returns:
            Update response
        """
        if question_number < 1:
            raise ValueError("Question numbers must be 1-based (>= 1)")

        self.logger.info("Updating question %d (1-based) in form: %s", question_number, form_id)

        # Get current question to find its item ID
        current_question = self.get_question(form_id, question_number)
        if not current_question:
            raise ValueError(f"Question {question_number} not found")

        item_id = current_question["item_id"]
        updated_item = self._build_question_item(question_data)
        updated_item["itemId"] = item_id

        # Get the current item position from the form structure
        form = self.get_form(form_id)
        items = form.get("items", [])
        item_position = next((i for i, item in enumerate(items) if item.get("itemId") == item_id), 0)

        # The location should be at the request level for updateItem
        request = {
            "updateItem": {
                "item": updated_item,
                "location": {"index": item_position},
                "updateMask": "title,description,questionItem",
            }
        }

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Question %d updated successfully", question_number)
        return response

    def update_question_by_section(
        self, form_id: str, section_number: int, question_number_in_section: int, question_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a question by section and question number within that section.

        Args:
            form_id: Google Form ID
            section_number: Section number (1-based)
            question_number_in_section: Question number within the section (1-based)
            question_data: New question configuration

        Returns:
            Update response
        """
        if section_number < 1:
            raise ValueError("Section numbers must be 1-based (>= 1)")
        if question_number_in_section < 1:
            raise ValueError("Question numbers must be 1-based (>= 1)")

        self.logger.info(
            "Updating question %d in section %d in form: %s", question_number_in_section, section_number, form_id
        )

        # Use new method to get exact index for finding the item
        index = self._calculate_index_location(
            form_id, section_number=section_number, question_number=question_number_in_section, position="exact"
        )

        # Get raw form to find item_id at this index
        form = self.service.forms().get(formId=form_id).execute()
        items = form.get("items", [])

        if index >= len(items):
            raise ValueError(f"Question {question_number_in_section} not found in section {section_number}")

        target_item = items[index]
        if not self._is_question_item(target_item):
            raise ValueError(f"Item at position is not a question")

        item_id = target_item.get("itemId")
        if not item_id:
            raise ValueError("Question item has no itemId")

        # Build updated question item
        updated_item = self._build_question_item(question_data)
        updated_item["itemId"] = item_id

        # Update the question
        request = {"updateItem": {"item": updated_item, "updateMask": "*"}}

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Question %d in section %d updated successfully", question_number_in_section, section_number)
        return response

    def update_section(
        self,
        form_id: str,
        section_number: int,
        title: str,
        description: str = "",
        go_to_action: Optional[str] = None,
        go_to_section_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing section.

        Args:
            form_id: Google Form ID
            section_number: Section number to update (1-based)
            title: New section title
            description: New section description
            go_to_action: Navigation action after this section
            go_to_section_id: Target section ID for navigation

        Returns:
            Update response
        """
        if section_number < 1:
            raise ValueError("Section numbers must be 1-based (>= 1)")

        # Convert 1-based to 0-based for internal processing
        section_index = section_number - 1
        self.logger.info("Updating section %d (1-based) in form: %s", section_number, form_id)

        # Get current sections to find the target section
        sections = self.get_sections(form_id)
        target_section = next((s for s in sections if s["index"] == section_index), None)
        if not target_section:
            raise ValueError(f"Section {section_index} not found")

        item_id = target_section.get("item_id")
        if not item_id:
            raise ValueError(f"Section {section_index} has no item_id (may be default section)")

        # Build updated section item
        updated_item = {"itemId": item_id, "title": title, "description": description, "pageBreakItem": {}}

        if go_to_action:
            updated_item["pageBreakItem"]["goToAction"] = go_to_action
        if go_to_section_id:
            updated_item["pageBreakItem"]["goToSectionId"] = go_to_section_id

        # Update the section
        request = {"updateItem": {"item": updated_item, "updateMask": "*"}}

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Section %d updated successfully", section_index)
        return response

    def remove_question(self, form_id: str, question_number: int) -> Dict[str, Any]:
        """Remove a question from the form.

        Args:
            form_id: Google Form ID
            question_number: Question number to remove (1-based)

        Returns:
            Removal response
        """
        if question_number < 1:
            raise ValueError("Question numbers must be 1-based (>= 1)")

        self.logger.info("Removing question %d (1-based) from form: %s", question_number, form_id)

        # Get current question to find its section and position
        current_question = self.get_question(form_id, question_number)
        if not current_question:
            raise ValueError(f"Question {question_number} not found")

        # Find the section and question number within that section
        ref_section = current_question.get("section", {}).get("index", 0) + 1  # Convert to 1-based

        # Find question number within that section
        questions = self.get_questions(form_id)
        actual_questions = [q for q in questions if not q.get("is_section_break")]
        section_questions = [
            q
            for q in actual_questions
            if q.get("section", {}).get("index") == current_question.get("section", {}).get("index")
        ]
        question_in_section = next(
            (i + 1 for i, q in enumerate(section_questions) if q.get("question_number") == question_number), 1
        )

        # Use new method to get exact index
        index = self._calculate_index_location(
            form_id, section_number=ref_section, question_number=question_in_section, position="exact"
        )

        # Remove the question
        request = {"deleteItem": {"location": {"index": index}}}

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Question %d removed successfully", question_number)
        return response

    def remove_question_by_section(
        self, form_id: str, section_number: int, question_number_in_section: int
    ) -> Dict[str, Any]:
        """Remove a question by section and question number within that section.

        Args:
            form_id: Google Form ID
            section_number: Section number (1-based)
            question_number_in_section: Question number within the section (1-based)

        Returns:
            Removal response
        """
        if section_number < 1:
            raise ValueError("Section numbers must be 1-based (>= 1)")
        if question_number_in_section < 1:
            raise ValueError("Question numbers must be 1-based (>= 1)")

        self.logger.info(
            "Removing question %d from section %d in form: %s", question_number_in_section, section_number, form_id
        )

        # Use new method to get exact index
        index = self._calculate_index_location(
            form_id, section_number=section_number, question_number=question_number_in_section, position="exact"
        )

        # Remove the question
        request = {"deleteItem": {"location": {"index": index}}}

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Question %d from section %d removed successfully", question_number_in_section, section_number)
        return response

    def remove_section(self, form_id: str, section_number: int) -> Dict[str, Any]:
        """Remove a section and all its questions.

        Args:
            form_id: Google Form ID
            section_number: Section number to remove (1-based)

        Returns:
            Removal response
        """
        if section_number < 1:
            raise ValueError("Section numbers must be 1-based (>= 1)")

        # Convert 1-based to 0-based for internal processing
        section_index = section_number - 1
        self.logger.info("Removing section %d (1-based) and its questions from form: %s", section_number, form_id)

        # Get section questions first
        section_questions = self.get_section_questions(form_id, section_number)
        sections = self.get_sections(form_id)
        target_section = next((s for s in sections if s["index"] == section_index), None)

        if not target_section:
            raise ValueError(f"Section {section_index} not found")

        # Build batch requests to remove all questions in section and the section itself
        requests = []

        # Remove questions in reverse order to maintain indices
        for question in reversed(section_questions):
            requests.append({"deleteItem": {"location": {"index": question.get("position_index", 0)}}})

        # Remove the section page break if it has an item_id
        if target_section.get("item_id"):
            # Find the section's position index
            questions = self.get_questions(form_id)
            section_item = next((q for q in questions if q.get("item_id") == target_section["item_id"]), None)
            if section_item:
                requests.append({"deleteItem": {"location": {"index": section_item.get("position_index", 0)}}})

        if requests:
            batch_request = {"requests": requests}
            response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()
            self.logger.info("Section %d and %d questions removed successfully", section_number, len(section_questions))
            return response
        else:
            self.logger.info("No items to remove for section %d", section_number)
            return {"replies": []}

    async def translate_question(
        self,
        form_id: str,
        question_number: int,
        target_language: str,
        translate_answers: bool = True,
        source_language: str = "",
    ) -> Dict[str, Any]:
        """Translate a question and optionally its answers.

        Args:
            form_id: Google Form ID
            question_number: Question number to translate (1-based)
            target_language: Target language code
            translate_answers: Whether to translate answer options
            source_language: Source language (auto-detected if empty)

        Returns:
            Translation results and updated question
        """
        if question_number < 1:
            raise ValueError("Question numbers must be 1-based (>= 1)")

        if not self.translate_service:
            raise ValueError(
                "TranslateService not available. Initialize FormsService with translate_service parameter."
            )

        self.logger.info("Translating question %d (1-based) to %s", question_number, target_language)

        # Get current question
        question = self.get_question(form_id, question_number)
        if not question:
            raise ValueError(f"Question {question_number} not found")

        # Translate question title and description
        title_translation = self.translate_service.translate_text(
            question.get("title", ""), target_language, source_language
        )
        translated_title = title_translation.get("translatedText", question.get("title", ""))

        translated_description = ""
        if question.get("description"):
            desc_translation = self.translate_service.translate_text(
                question["description"], target_language, source_language
            )
            translated_description = desc_translation.get("translatedText", question["description"])

        # Translate answer options if requested
        translated_options = []
        if translate_answers and question.get("question_item", {}).get("question", {}).get("choiceQuestion"):
            choice_question = question["question_item"]["question"]["choiceQuestion"]
            if "options" in choice_question:
                for option in choice_question["options"]:
                    if "value" in option:
                        option_translation = self.translate_service.translate_text(
                            option["value"], target_language, source_language
                        )
                        translated_value = option_translation.get("translatedText", option["value"])
                        translated_options.append({"original": option["value"], "translated": translated_value})

        # Build updated question data
        updated_question_data = {
            "title": translated_title,
            "description": translated_description,
            "question_type": question.get("question_type"),
            "required": question.get("required", False),
        }

        # Add translated options if applicable
        if translated_options:
            updated_question_data["options"] = [opt["translated"] for opt in translated_options]

        # Update the question with translations
        update_response = self.update_question(form_id, question_number, updated_question_data)

        result = {
            "question_number": question_number,
            "translations": {
                "title": {"original": question.get("title", ""), "translated": translated_title},
                "description": (
                    {"original": question.get("description", ""), "translated": translated_description}
                    if question.get("description")
                    else None
                ),
                "options": translated_options if translated_options else None,
            },
            "update_response": update_response,
        }

        self.logger.info("Question %d translated successfully", question_number)
        return result

    async def move_question(
        self,
        form_id: str,
        source_section_number: int,
        source_question_number: int,
        target_section_number: int,
        target_question_number: int,
        position: str = "before",
    ) -> Dict[str, Any]:
        """Move a question from one position to another.

        Args:
            form_id: Google Form ID
            source_section_number: Source section number (1-based)
            source_question_number: Source question number within section (1-based)
            target_section_number: Target section number (1-based)
            target_question_number: Target question number within section (1-based)
            position: Position relative to target ("before", "after")

        Returns:
            Move operation response
        """
        if source_section_number < 1 or source_question_number < 1:
            raise ValueError("Source section and question numbers must be 1-based (>= 1)")
        if target_section_number < 1 or target_question_number < 1:
            raise ValueError("Target section and question numbers must be 1-based (>= 1)")

        self.logger.info(
            "Moving question %d from section %d to section %d, question %d (%s)",
            source_question_number,
            source_section_number,
            target_section_number,
            target_question_number,
            position,
        )

        # Get source question details
        source_questions = self.get_questions(form_id, section_filter=source_section_number)
        source_questions_only = [q for q in source_questions if not q.get("is_section_break")]

        if not source_questions_only or source_question_number > len(source_questions_only):
            raise ValueError(f"Source question {source_question_number} not found in section {source_section_number}")

        source_question = source_questions_only[source_question_number - 1]
        source_item_id = source_question["item_id"]

        # Get the current item position from the form structure
        form = self.get_form(form_id)
        items = form.get("items", [])
        source_index = next((i for i, item in enumerate(items) if item.get("itemId") == source_item_id), 0)

        # Calculate target location
        target_index = self._calculate_index_location(
            form_id, section_number=target_section_number, question_number=target_question_number, position=position
        )

        # Move the question
        request = {
            "moveItem": {
                "originalLocation": {"index": source_index},
                "newLocation": {"index": target_index},
            }
        }

        batch_request = {"requests": [request]}
        response = self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

        self.logger.info("Question moved successfully")
        return response

    def _get_section_items(self, form_id: str, section_number: int) -> List[Dict[str, Any]]:
        """Get all items (section break + questions) that belong to a specific section.

        Args:
            form_id: Google Form ID
            section_number: Section number (1-based)

        Returns:
            List of items (form items) that belong to the section, including the section break itself
        """
        form = self.get_form(form_id)
        items = form.get("items", [])

        # Use _calculate_index_location to find precise section boundaries
        if section_number == 1:
            # Default section: from start until first pageBreakItem
            start_index = 0
            end_index = self._calculate_index_location(form_id, section_number=1, position_in_section="end")
        else:
            # Other sections: from pageBreakItem to end of section
            start_index = self._calculate_index_location(
                form_id, section_number=section_number, position_in_section="start"
            )
            end_index = self._calculate_index_location(
                form_id, section_number=section_number, position_in_section="end"
            )

        # Extract items in this range
        section_items = items[start_index:end_index]

        self.logger.debug(
            "Section %d items: start_index=%d, end_index=%d, item_count=%d",
            section_number,
            start_index,
            end_index,
            len(section_items),
        )

        return section_items

    def _get_section_item_indices(self, form_id: str, section_number: int) -> List[int]:
        """Get indices of all items (section break + questions) that belong to a specific section.

        Args:
            form_id: Google Form ID
            section_number: Section number (1-based)

        Returns:
            List of indices that belong to the section, including the section break itself
        """
        form = self.get_form(form_id)
        items = form.get("items", [])

        # Use _calculate_index_location to find precise section boundaries
        if section_number == 1:
            # Default section: from start until first pageBreakItem
            start_index = 0
            end_index = self._calculate_index_location(form_id, section_number=1, position_in_section="end")
        else:
            # Other sections: from pageBreakItem to end of section
            start_index = self._calculate_index_location(
                form_id, section_number=section_number, position_in_section="start"
            )
            end_index = self._calculate_index_location(
                form_id, section_number=section_number, position_in_section="end"
            )

        # Return the range of indices
        section_indices = list(range(start_index, end_index))

        self.logger.debug(
            "Section %d indices: start_index=%d, end_index=%d, indices=%s",
            section_number,
            start_index,
            end_index,
            section_indices,
        )

        return section_indices

    def _get_sections_list(self, form_id: str) -> List[Dict[str, Any]]:
        """Get list of all sections in the form."""
        form = self.service.forms().get(formId=form_id).execute()
        items = form.get("items", [])

        sections = []
        current_section = 1

        # First section (Default) always exists
        sections.append({"section_number": 1, "title": "Default Section"})

        for item in items:
            if "pageBreakItem" in item:
                current_section += 1
                page_break = item.get("pageBreakItem", {})
                sections.append(
                    {"section_number": current_section, "title": item.get("title", f"Section {current_section}")}
                )

        return sections

    async def move_section(
        self,
        form_id: str,
        source_section_number: int,
        target_section_number: int,
        position: str = "before",
    ) -> Dict[str, Any]:
        """Move a section to a new position relative to another section.

        This moves the entire section including its section break and all questions.

        Args:
            form_id: Google Form ID
            source_section_number: Source section number (1-based)
            target_section_number: Target section number (1-based)
            position: Position relative to target section ("before", "after")

        Returns:
            Move operation response
        """
        # Get form structure
        form = self.service.forms().get(formId=form_id).execute()
        items = form.get("items", [])

        self.logger.debug("Form has %d items", len(items))

        # Get the indices of all items in the source section
        source_section_index = (
            self._calculate_index_location(form_id, source_section_number, position_in_section="start") - 1
        )

        # Get the items for the source section (actually we just need the number of items)
        source_items = self._get_section_items(form_id, source_section_number)

        # Calculate destination index
        if position == "after":
            if target_section_number == len(self._get_sections_list(form_id)):
                # Moving after the last section
                destination_index = len(items) - 1
            else:
                # Moving after target section but not the last one - go before the next section
                next_section_number = target_section_number + 1
                destination_index = self._calculate_index_location(form_id, next_section_number, position="start") - 1
        else:  # position == "before"
            if target_section_number == 1:
                # Moving before first section
                destination_index = 0
            else:
                # Moving before target section
                destination_index = (
                    self._calculate_index_location(form_id, target_section_number, position_in_section="start") - 1
                )

        self.logger.debug("Source section index: %s", source_section_index)
        self.logger.debug("Destination index: %d", destination_index)
        print("Source section index: %s", source_section_index)
        print("Destination index: %d", destination_index)

        # Create move requests for all items in the section
        requests = []

        # Move items one by one to the destination
        # After moving the first item, subsequent items shift down, so they all use the same original index
        for _ in range(len(source_items) + 1):
            # Use the first item's index for all moves since items shift after each move
            requests.append(
                {
                    "moveItem": {
                        "originalLocation": {"index": source_section_index},
                        "newLocation": {"index": destination_index},
                    }
                }
            )

        self.logger.debug("Move requests: %s", requests)

        # Execute batch update
        batch_request = {"requests": requests}
        print(batch_request)
        return self.service.forms().batchUpdate(formId=form_id, body=batch_request).execute()

    def _process_form_structure(self, form: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw form data into organized structure."""
        return {
            "form_id": form.get("formId"),
            "title": form.get("info", {}).get("title", ""),
            "description": form.get("info", {}).get("description", ""),
            "document_title": form.get("info", {}).get("documentTitle", ""),
            "items": form.get("items", []),
            "settings": form.get("settings", {}),
            "revisionId": form.get("revisionId"),
            "responderUri": form.get("responderUri"),
            "linkedSheetId": form.get("linkedSheetId"),
        }

    def _is_question_item(self, item: Dict[str, Any]) -> bool:
        """Check if an item is a question (not a section break or other item type)."""
        return item.get("questionItem") is not None

    def _process_question_item(
        self, item: Dict[str, Any], current_section: Dict[str, Any], question_number: int
    ) -> Dict[str, Any]:
        """Process a question item into organized structure."""
        question_item = item.get("questionItem", {})
        question = question_item.get("question", {})

        # Determine question type
        question_type = "unknown"
        if question.get("choiceQuestion"):
            question_type = "choice"
        elif question.get("textQuestion"):
            question_type = "text"
        elif question.get("scaleQuestion"):
            question_type = "scale"
        elif question.get("dateQuestion"):
            question_type = "date"
        elif question.get("timeQuestion"):
            question_type = "time"
        elif question.get("fileUploadQuestion"):
            question_type = "file_upload"
        elif question.get("rowQuestion"):
            question_type = "grid"

        # Extract choice options if applicable
        choices = []
        go_to_actions = {}
        if question.get("choiceQuestion"):
            choice_question = question["choiceQuestion"]
            for i, option in enumerate(choice_question.get("options", [])):
                choice_data = {
                    "value": option.get("value", ""),
                    "image": option.get("image"),
                }

                # Check for navigation actions
                if option.get("goToAction") or option.get("goToSectionId"):
                    go_to_actions[i] = {"action": option.get("goToAction"), "section_id": option.get("goToSectionId")}

                choices.append(choice_data)

        return {
            "question_number": question_number,
            "item_id": item.get("itemId"),
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "question_type": question_type,
            "required": question_item.get("required", False),
            "question_item": question_item,
            "choices": choices if choices else None,
            "choice_navigation": go_to_actions if go_to_actions else None,
            "section": current_section,
            "position_index": item.get("positionIndex", 0),
        }

    def _calculate_index_location(
        self,
        form_id: str,
        section_number: Optional[int] = None,
        question_number: Optional[int] = None,
        position: str = "exact",
        position_in_section: str = "end",
    ) -> int:
        """Calculate exact index location in items[] array using pageBreak logic.

        This method works with the raw form items[] array and counts pageBreakItem elements
        to find sections, then calculates the exact array index for API operations.

        Args:
            form_id: Google Form ID
            section_number: Target section number (1-based, None for form-level operations)
            question_number: Specific question number within section (1-based, None for section operations)
            position: Position type ("exact", "before", "after", "end")
            position_in_section: Position within section ("start", "end") when question_number is None

        Returns:
            Exact index in the items[] array for API operations

        Examples:
            # Get index of question 2 in section 3
            _calculate_index_location(form_id, section_number=3, question_number=2, position="exact")

            # Get index to insert at end of section 5
            _calculate_index_location(form_id, section_number=5, position_in_section="end")

            # Get index to insert after question 3 in section 2
            _calculate_index_location(form_id, section_number=2, question_number=3, position="after")
        """
        # Get raw form structure
        form = self.service.forms().get(formId=form_id).execute()
        items = form.get("items", [])

        if not items:
            return 0

        # If no section specified, return end of form
        if section_number is None:
            return len(items) if position == "after" else 0

        # Validate section number
        if section_number < 1:
            raise ValueError("Section numbers must be 1-based (>= 1)")

        # Find target section by counting pageBreaks
        page_breaks_found = 0
        section_start_index = 0
        section_end_index = len(items)

        for i, item in enumerate(items):
            if "pageBreakItem" in item:
                page_breaks_found += 1

                if page_breaks_found == section_number - 1:
                    # Found the pageBreak that starts our target section
                    section_start_index = i + 1  # Section starts after the pageBreak
                elif page_breaks_found == section_number:
                    # Found the pageBreak that ends our target section
                    section_end_index = i
                    break

        # Section 1 special case: no pageBreak before it
        if section_number == 1:
            section_start_index = 0
            # Find first pageBreak to determine section 1 end
            for i, item in enumerate(items):
                if "pageBreakItem" in item:
                    section_end_index = i
                    break

        # Validate section exists
        if section_number > 1 and page_breaks_found < section_number - 1:
            raise ValueError(f"Section {section_number} not found (only {page_breaks_found + 1} sections exist)")

        # If no specific question requested, return section position
        if question_number is None:
            if position_in_section == "start":
                return section_start_index
            elif position_in_section == "end":
                return section_end_index
            else:
                raise ValueError(f"Invalid position_in_section: {position_in_section}")

        # Find specific question within the section
        if question_number < 1:
            raise ValueError("Question numbers must be 1-based (>= 1)")

        questions_found = 0
        for i in range(section_start_index, section_end_index):
            item = items[i]

            # Skip pageBreaks and non-question items
            if "pageBreakItem" in item or not self._is_question_item(item):
                continue

            questions_found += 1

            if questions_found == question_number:
                # Found the target question
                if position == "exact":
                    return i
                elif position == "before":
                    return i
                elif position == "after":
                    return i + 1
                elif position == "end":
                    return section_end_index
                else:
                    raise ValueError(f"Invalid position: {position}")

        # Question not found in section
        if position == "end" or position_in_section == "end":
            return section_end_index
        else:
            raise ValueError(
                f"Question {question_number} not found in section {section_number} (only {questions_found} questions exist)"
            )

    def _calculate_insertion_location(
        self, form_id: str, position: str, reference_question: Optional[int] = None, section_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Legacy method - use _calculate_index_location for new code."""
        try:
            if position == "end" and section_index is not None:
                section_number = section_index + 1  # Convert 0-based to 1-based
                index = self._calculate_index_location(
                    form_id, section_number=section_number, position_in_section="end"
                )
            elif reference_question is not None:
                # This is more complex - need to find which section the reference question is in
                # For now, fallback to original logic but this should be refactored
                questions = self.get_questions(form_id)
                actual_questions = [q for q in questions if not q.get("is_section_break")]

                if reference_question < 1 or reference_question > len(actual_questions):
                    raise ValueError(f"Reference question {reference_question} not found")

                # Find section of reference question and use new method
                ref_question = actual_questions[reference_question - 1]
                ref_section = ref_question.get("section", {}).get("index", 0) + 1  # Convert to 1-based

                # Find question number within that section
                section_questions = [
                    q
                    for q in actual_questions
                    if q.get("section", {}).get("index") == ref_question.get("section", {}).get("index")
                ]
                question_in_section = next(
                    (i + 1 for i, q in enumerate(section_questions) if q.get("question_number") == reference_question),
                    1,
                )

                index = self._calculate_index_location(
                    form_id, section_number=ref_section, question_number=question_in_section, position=position
                )
            else:
                index = 0  # End of form

            return {"index": index}

        except Exception as e:
            self.logger.warning("Fallback to end of form due to error: %s", e)
            return {"index": 0}

    def _build_question_item(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a question item from question data."""
        item = {
            "title": question_data.get("title", ""),
            "description": question_data.get("description", ""),
            "questionItem": {
                "question": {},
            },
        }

        # Add required field only if it's True, as the API might not accept false values
        if question_data.get("required", False):
            item["questionItem"]["required"] = True

        question_type = question_data.get("question_type", "text")
        question = item["questionItem"]["question"]

        if question_type == "text":
            question["textQuestion"] = {"paragraph": question_data.get("paragraph", False)}
        elif question_type == "choice":
            choice_question = {"type": question_data.get("choice_type", "RADIO"), "options": []}

            for option_text in question_data.get("options", []):
                choice_question["options"].append({"value": option_text})

            question["choiceQuestion"] = choice_question
        elif question_type == "scale":
            question["scaleQuestion"] = {
                "low": question_data.get("scale_low", 1),
                "high": question_data.get("scale_high", 5),
                "lowLabel": question_data.get("scale_low_label", ""),
                "highLabel": question_data.get("scale_high_label", ""),
            }
        elif question_type == "date":
            question["dateQuestion"] = {
                "includeTime": question_data.get("include_time", False),
                "includeYear": question_data.get("include_year", True),
            }
        elif question_type == "time":
            question["timeQuestion"] = {"duration": question_data.get("duration", False)}
        elif question_type == "file_upload":
            question["fileUploadQuestion"] = {
                "folderId": question_data.get("folder_id"),
                "types": question_data.get("file_types", []),
                "maxFiles": question_data.get("max_files", 1),
                "maxFileSize": question_data.get("max_file_size"),
            }

        return item
