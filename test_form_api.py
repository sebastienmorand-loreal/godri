#!/usr/bin/env python3
"""Test script to fetch form data and save to JSON file."""

import json
import asyncio
import logging
from pathlib import Path
from src.godri.services.auth_service import AuthService
from src.godri.services.forms_service import FormsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FORM_ID = "1nqeMn4J6fWNR1EZZ5DAGyC0U1Si-wcca-WNCc5BuT0c"
OUTPUT_FILE = "interventional_pulmonology_form.json"


async def main():
    """Fetch form data and save to JSON file."""
    try:
        # Initialize services
        logger.info("Initializing authentication service...")
        auth_service = AuthService()
        await auth_service.authenticate()
        
        logger.info("Initializing forms service...")
        forms_service = FormsService(auth_service)
        await forms_service.initialize()
        
        # Get complete form structure
        logger.info(f"Fetching form data for ID: {FORM_ID}")
        form_data = forms_service.get_form(FORM_ID)
        
        # Get questions for detailed structure
        logger.info("Fetching questions data...")
        questions_data = forms_service.get_questions(FORM_ID)
        
        # Get sections data
        logger.info("Fetching sections data...")
        sections_data = forms_service.get_sections(FORM_ID)
        
        # Combine all data
        complete_form_data = {
            "form_metadata": form_data,
            "questions": questions_data,
            "sections": sections_data,
            "export_timestamp": "2025-07-19T03:40:00Z",
            "form_id": FORM_ID
        }
        
        # Save to JSON file
        output_path = Path(OUTPUT_FILE)
        logger.info(f"Saving form data to {output_path.absolute()}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(complete_form_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Form data successfully saved to {output_path.absolute()}")
        logger.info(f"File size: {output_path.stat().st_size:,} bytes")
        
        # Print summary
        form_title = form_data.get("info", {}).get("title", "Unknown")
        total_questions = len(questions_data.get("questions", []))
        total_sections = len(sections_data.get("sections", []))
        
        print(f"\n📋 Form Export Summary:")
        print(f"Title: {form_title}")
        print(f"Form ID: {FORM_ID}")
        print(f"Total Questions: {total_questions}")
        print(f"Total Sections: {total_sections}")
        print(f"Output File: {output_path.absolute()}")
        
    except Exception as e:
        logger.error(f"❌ Error fetching form data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())