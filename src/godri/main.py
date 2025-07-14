"""Google Drive CLI main application."""

import asyncio
import argparse
import sys
import logging
import os
from pathlib import Path
from typing import Optional

# Add the src directory to the path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from godri.config.logging_config import setup_logging
from godri.services.auth_service import AuthService
from godri.services.drive_service import DriveService
from godri.services.docs_service import DocsService
from godri.services.sheets_service import SheetsService
from godri.services.slides_service import SlidesService
from godri.services.translate_service import TranslateService


class GodriCLI:
    """Main CLI application."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.auth_service = None
        self.drive_service = None
        self.docs_service = None
        self.sheets_service = None
        self.slides_service = None
        self.translate_service = None

    async def initialize_services(self):
        """Initialize all services."""
        self.auth_service = AuthService()
        self.drive_service = DriveService(self.auth_service)
        self.docs_service = DocsService(self.auth_service)
        self.sheets_service = SheetsService(self.auth_service)
        self.slides_service = SlidesService(self.auth_service)
        self.translate_service = TranslateService(self.auth_service)

        await self.drive_service.initialize()
        await self.docs_service.initialize()
        await self.sheets_service.initialize()
        await self.slides_service.initialize()
        await self.translate_service.initialize()

    async def handle_auth(self, args):
        """Handle authentication command."""
        try:
            if args.force:
                # Delete existing token to force re-authentication
                import os

                token_file = os.path.expanduser("~/.godri-token.json")
                if os.path.exists(token_file):
                    os.remove(token_file)
                    print("Existing token deleted. Starting fresh authentication...")

            await self.auth_service.authenticate()
            print("Authentication successful!")
        except Exception as e:
            self.logger.error("Authentication failed: %s", str(e))
            sys.exit(1)

    async def handle_search(self, args):
        """Handle file search command."""
        if args.name:
            results = self.drive_service.search_by_name(args.name, args.mime_type)
        else:
            results = self.drive_service.search_files(args.query, args.limit)

        if not results:
            print("No files found.")
            return

        print(f"Found {len(results)} files:")
        for file in results:
            print(f"  - {file['name']} (ID: {file['id']}, Type: {file.get('mimeType', 'Unknown')})")

    async def handle_upload(self, args):
        """Handle file upload command."""
        try:
            result = await self.drive_service.upload_file(args.file_path, args.folder_id, args.name)
            print(f"File uploaded successfully!")
            print(f"  - ID: {result['id']}")
            print(f"  - Name: {result['name']}")
            print(f"  - Link: {result.get('webViewLink', 'N/A')}")
        except Exception as e:
            self.logger.error("Upload failed: %s", str(e))
            sys.exit(1)

    async def handle_download(self, args):
        """Handle file download command."""
        try:
            if args.smart:
                result = await self.drive_service.download_file_smart(args.file_id, args.output_path)
            else:
                result = await self.drive_service.download_file(args.file_id, args.output_path)
            print(f"File downloaded successfully to: {result}")
        except Exception as e:
            self.logger.error("Download failed: %s", str(e))
            sys.exit(1)

    async def handle_create_folder(self, args):
        """Handle folder creation command."""
        try:
            result = self.drive_service.create_folder(args.name, args.parent_id)
            print(f"Folder created successfully!")
            print(f"  - ID: {result['id']}")
            print(f"  - Name: {result['name']}")
            print(f"  - Link: {result.get('webViewLink', 'N/A')}")
        except Exception as e:
            self.logger.error("Folder creation failed: %s", str(e))
            sys.exit(1)

    async def handle_delete(self, args):
        """Handle file/folder deletion command."""
        try:
            success = self.drive_service.delete_file(args.file_id)
            if success:
                print("File/folder deleted successfully!")
            else:
                print("Failed to delete file/folder.")
                sys.exit(1)
        except Exception as e:
            self.logger.error("Deletion failed: %s", str(e))
            sys.exit(1)

    async def handle_create_doc(self, args):
        """Handle Google Doc creation command."""
        try:
            result = self.docs_service.create_document(args.title, args.folder_id)
            print(f"Document created successfully!")
            print(f"  - ID: {result['documentId']}")
            print(f"  - Title: {result['title']}")

            if args.content:
                if args.markdown:
                    self.docs_service.insert_markdown_text(result["documentId"], args.content)
                    print("Markdown content added to document with formatting.")
                else:
                    self.docs_service.insert_text(result["documentId"], args.content)
                    print("Content added to document.")
        except Exception as e:
            self.logger.error("Document creation failed: %s", str(e))
            sys.exit(1)

    async def handle_create_sheet(self, args):
        """Handle Google Sheet creation command."""
        try:
            result = self.sheets_service.create_spreadsheet(args.title, args.folder_id)
            print(f"Spreadsheet created successfully!")
            print(f"  - ID: {result['spreadsheetId']}")
            print(f"  - Title: {result['properties']['title']}")
        except Exception as e:
            self.logger.error("Spreadsheet creation failed: %s", str(e))
            sys.exit(1)

    async def handle_create_slides(self, args):
        """Handle Google Slides creation command."""
        try:
            theme = getattr(args, "theme", "STREAMLINE")
            result = self.slides_service.create_presentation(args.title, args.folder_id, theme)
            print(f"Presentation created successfully!")
            print(f"  - ID: {result['presentationId']}")
            print(f"  - Title: {result['title']}")
            print(f"  - Theme: {theme}")
        except Exception as e:
            self.logger.error("Presentation creation failed: %s", str(e))
            sys.exit(1)

    async def handle_translate(self, args):
        """Handle text translation command."""
        try:
            result = self.translate_service.translate_text(args.text, args.target_language, args.source_language)
            print(f"Translation:")
            print(f"  - Original: {args.text}")
            print(f"  - Translated: {result['translatedText']}")
            if result.get("detectedSourceLanguage"):
                print(f"  - Detected source: {result['detectedSourceLanguage']}")
        except Exception as e:
            self.logger.error("Translation failed: %s", str(e))
            sys.exit(1)

    async def handle_read_doc(self, args):
        """Handle reading Google Doc content."""
        try:
            if args.plain_text:
                content = self.docs_service.get_document_text(args.document_id)
                print(content)
            else:
                document = self.docs_service.get_document(args.document_id)
                print(f"Document: {document.get('title', 'Untitled')}")
                print(f"ID: {args.document_id}")
                print("=" * 50)
                content = self.docs_service.get_document_text(args.document_id)
                print(content)
        except Exception as e:
            self.logger.error("Failed to read document: %s", str(e))
            sys.exit(1)

    async def handle_update_doc(self, args):
        """Handle updating Google Doc content."""
        try:
            if args.replace:
                # Replace entire document content
                if args.markdown:
                    self.docs_service.set_markdown_content(args.document_id, args.content)
                    print("Document content replaced with markdown formatting.")
                else:
                    self.docs_service.set_document_content(args.document_id, args.content)
                    print("Document content replaced.")
            else:
                # Insert/append content
                if args.markdown:
                    if args.index == 1:
                        # Append to end if index is 1 (default)
                        document = self.docs_service.get_document(args.document_id)
                        end_index = document.get("body", {}).get("content", [{}])[-1].get("endIndex", 1) - 1
                        self.docs_service.insert_markdown_text(args.document_id, args.content, end_index)
                    else:
                        self.docs_service.insert_markdown_text(args.document_id, args.content, args.index)
                    print("Markdown content added to document with formatting.")
                else:
                    if args.index == 1:
                        # Append to end if index is 1 (default)
                        self.docs_service.append_text(args.document_id, args.content)
                    else:
                        self.docs_service.insert_text(args.document_id, args.content, args.index)
                    print("Content added to document.")
        except Exception as e:
            self.logger.error("Failed to update document: %s", str(e))
            sys.exit(1)

    async def handle_read_sheet(self, args):
        """Handle reading Google Sheet content."""
        try:
            if args.range:
                values = self.sheets_service.get_values(args.spreadsheet_id, args.range)
                print(f"Data from range '{args.range}':")
            else:
                values = self.sheets_service.read_entire_sheet(args.spreadsheet_id, args.sheet_name)
                sheet_name = args.sheet_name or "first sheet"
                print(f"Data from {sheet_name}:")

            if not values:
                print("No data found.")
                return

            if args.json:
                import json

                print(json.dumps(values, indent=2))
            else:
                print(f"Found {len(values)} rows:")
                for i, row in enumerate(values[: args.limit] if args.limit else values):
                    print(f"Row {i+1}: {row}")
                if args.limit and len(values) > args.limit:
                    print(f"... and {len(values) - args.limit} more rows (use --limit to show more)")
        except Exception as e:
            self.logger.error("Failed to read sheet: %s", str(e))
            sys.exit(1)

    async def handle_set_values(self, args):
        """Handle setting values in Google Sheet."""
        try:
            # Parse values - support JSON array or comma-separated
            if args.values.startswith("["):
                import json

                values = json.loads(args.values)
            else:
                # Split by comma and create single row
                values = [v.strip() for v in args.values.split(",")]

            result = self.sheets_service.set_values_in_range(args.spreadsheet_id, args.range, values)
            print(f"Values set successfully in range '{args.range}'")
            print(f"Updated {result.get('updatedCells', 0)} cells")
        except Exception as e:
            self.logger.error("Failed to set values: %s", str(e))
            sys.exit(1)

    async def handle_set_formula(self, args):
        """Handle setting formula in Google Sheet."""
        try:
            result = self.sheets_service.set_formula(args.spreadsheet_id, args.range, args.formula)
            print(f"Formula set successfully in range '{args.range}'")
            print(f"Updated {result.get('updatedCells', 0)} cells")
        except Exception as e:
            self.logger.error("Failed to set formula: %s", str(e))
            sys.exit(1)

    async def handle_format_cells(self, args):
        """Handle formatting cells in Google Sheet."""
        try:
            if hasattr(args, "source_range") and args.source_range:
                # Copy formatting from source range
                result = await self.sheets_service.copy_format(args.spreadsheet_id, args.source_range, args.range)
                print(f"Formatting copied from '{args.source_range}' to '{args.range}' successfully")
            else:
                # Apply custom formatting from JSON
                import json

                format_options = json.loads(args.format_options)
                result = self.sheets_service.format_range(args.spreadsheet_id, args.range, format_options)
                print(f"Formatting applied successfully to range '{args.range}'")
        except Exception as e:
            self.logger.error("Failed to format cells: %s", str(e))
            sys.exit(1)

    async def handle_list_sheets(self, args):
        """Handle listing sheets in Google Spreadsheet."""
        try:
            sheets = self.sheets_service.list_sheets(args.spreadsheet_id)

            if not sheets:
                print("No sheets found.")
                return

            print(f"Found {len(sheets)} sheets:")
            for sheet in sheets:
                status = " [HIDDEN]" if sheet["hidden"] else ""
                grid = sheet.get("gridProperties", {})
                size_info = ""
                if grid:
                    rows = grid.get("rowCount", "unknown")
                    cols = grid.get("columnCount", "unknown")
                    size_info = f" ({rows}x{cols})"

                print(f"  - '{sheet['title']}' (ID: {sheet['sheetId']}, Index: {sheet['index']}){size_info}{status}")
        except Exception as e:
            self.logger.error("Failed to list sheets: %s", str(e))
            sys.exit(1)

    async def handle_manage_sheet(self, args):
        """Handle sheet management operations."""
        try:
            if args.action == "create":
                result = self.sheets_service.create_sheet(args.spreadsheet_id, args.sheet_name)
                print(f"Sheet '{args.sheet_name}' created successfully")

            elif args.action == "delete":
                sheet_id = self.sheets_service.get_sheet_id_by_name(args.spreadsheet_id, args.sheet_name)
                if sheet_id is None:
                    print(f"Sheet '{args.sheet_name}' not found")
                    sys.exit(1)

                result = self.sheets_service.delete_sheet(args.spreadsheet_id, sheet_id)
                print(f"Sheet '{args.sheet_name}' deleted successfully")

            elif args.action == "hide":
                sheet_id = self.sheets_service.get_sheet_id_by_name(args.spreadsheet_id, args.sheet_name)
                if sheet_id is None:
                    print(f"Sheet '{args.sheet_name}' not found")
                    sys.exit(1)

                result = self.sheets_service.hide_sheet(args.spreadsheet_id, sheet_id)
                print(f"Sheet '{args.sheet_name}' hidden successfully")

            elif args.action == "unhide":
                sheet_id = self.sheets_service.get_sheet_id_by_name(args.spreadsheet_id, args.sheet_name)
                if sheet_id is None:
                    print(f"Sheet '{args.sheet_name}' not found")
                    sys.exit(1)

                result = self.sheets_service.unhide_sheet(args.spreadsheet_id, sheet_id)
                print(f"Sheet '{args.sheet_name}' unhidden successfully")

        except Exception as e:
            self.logger.error("Failed to manage sheet: %s", str(e))
            sys.exit(1)

    async def handle_add_row(self, args):
        """Handle adding row(s) to spreadsheet."""
        try:
            # Get sheet ID if sheet name provided, otherwise use first sheet
            if args.sheet_name:
                sheet_id = self.sheets_service.get_sheet_id_by_name(args.spreadsheet_id, args.sheet_name)
                if sheet_id is None:
                    print(f"Sheet '{args.sheet_name}' not found")
                    sys.exit(1)
            else:
                # Use first sheet
                sheets = self.sheets_service.list_sheets(args.spreadsheet_id)
                if not sheets:
                    print("No sheets found in spreadsheet")
                    sys.exit(1)
                sheet_id = sheets[0]["sheetId"]
                args.sheet_name = sheets[0]["title"]

            # Convert 1-based row number to 0-based index
            row_index = args.row_number - 1

            result = self.sheets_service.insert_row(args.spreadsheet_id, sheet_id, row_index, args.count)
            sheet_name = args.sheet_name or "default sheet"
            print(f"Inserted {args.count} row(s) at position {args.row_number} in sheet '{sheet_name}'")

        except Exception as e:
            self.logger.error("Failed to add row: %s", str(e))
            sys.exit(1)

    async def handle_remove_row(self, args):
        """Handle removing row(s) from spreadsheet."""
        try:
            # Get sheet ID if sheet name provided, otherwise use first sheet
            if args.sheet_name:
                sheet_id = self.sheets_service.get_sheet_id_by_name(args.spreadsheet_id, args.sheet_name)
                if sheet_id is None:
                    print(f"Sheet '{args.sheet_name}' not found")
                    sys.exit(1)
            else:
                # Use first sheet
                sheets = self.sheets_service.list_sheets(args.spreadsheet_id)
                if not sheets:
                    print("No sheets found in spreadsheet")
                    sys.exit(1)
                sheet_id = sheets[0]["sheetId"]
                args.sheet_name = sheets[0]["title"]

            # Convert 1-based row number to 0-based index
            row_index = args.row_number - 1

            result = self.sheets_service.delete_row(args.spreadsheet_id, sheet_id, row_index, args.count)
            sheet_name = args.sheet_name or "default sheet"
            print(f"Deleted {args.count} row(s) starting at position {args.row_number} in sheet '{sheet_name}'")

        except Exception as e:
            self.logger.error("Failed to remove row: %s", str(e))
            sys.exit(1)

    async def handle_add_column(self, args):
        """Handle adding column(s) to spreadsheet."""
        try:
            # Get sheet ID if sheet name provided, otherwise use first sheet
            if args.sheet_name:
                sheet_id = self.sheets_service.get_sheet_id_by_name(args.spreadsheet_id, args.sheet_name)
                if sheet_id is None:
                    print(f"Sheet '{args.sheet_name}' not found")
                    sys.exit(1)
            else:
                # Use first sheet
                sheets = self.sheets_service.list_sheets(args.spreadsheet_id)
                if not sheets:
                    print("No sheets found in spreadsheet")
                    sys.exit(1)
                sheet_id = sheets[0]["sheetId"]
                args.sheet_name = sheets[0]["title"]

            # Convert column letter to 0-based index
            column_index = self.sheets_service._convert_column_letter_to_index(args.column_letter)

            result = self.sheets_service.insert_column(args.spreadsheet_id, sheet_id, column_index, args.count)
            sheet_name = args.sheet_name or "default sheet"
            print(f"Inserted {args.count} column(s) at position {args.column_letter} in sheet '{sheet_name}'")

        except Exception as e:
            self.logger.error("Failed to add column: %s", str(e))
            sys.exit(1)

    async def handle_remove_column(self, args):
        """Handle removing column(s) from spreadsheet."""
        try:
            # Get sheet ID if sheet name provided, otherwise use first sheet
            if args.sheet_name:
                sheet_id = self.sheets_service.get_sheet_id_by_name(args.spreadsheet_id, args.sheet_name)
                if sheet_id is None:
                    print(f"Sheet '{args.sheet_name}' not found")
                    sys.exit(1)
            else:
                # Use first sheet
                sheets = self.sheets_service.list_sheets(args.spreadsheet_id)
                if not sheets:
                    print("No sheets found in spreadsheet")
                    sys.exit(1)
                sheet_id = sheets[0]["sheetId"]
                args.sheet_name = sheets[0]["title"]

            # Convert column letter to 0-based index
            column_index = self.sheets_service._convert_column_letter_to_index(args.column_letter)

            result = self.sheets_service.delete_column(args.spreadsheet_id, sheet_id, column_index, args.count)
            sheet_name = args.sheet_name or "default sheet"
            print(f"Deleted {args.count} column(s) starting at position {args.column_letter} in sheet '{sheet_name}'")

        except Exception as e:
            self.logger.error("Failed to remove column: %s", str(e))
            sys.exit(1)

    # New hierarchical command handlers
    async def handle_drive(self, args):
        """Handle drive subcommands."""
        if args.drive_command == "search":
            await self.handle_search(args)
        elif args.drive_command == "upload":
            await self.handle_upload(args)
        elif args.drive_command == "download":
            await self.handle_download(args)
        elif args.drive_command == "folder":
            await self.handle_drive_folder(args)

    async def handle_drive_folder(self, args):
        """Handle drive folder subcommands."""
        if args.folder_action == "create":
            await self.handle_create_folder(args)
        elif args.folder_action == "delete":
            await self.handle_delete(args)

    async def handle_docs(self, args):
        """Handle docs subcommands."""
        if args.docs_command == "create-document":
            await self.handle_create_doc(args)
        elif args.docs_command == "read":
            await self.handle_read_doc(args)
        elif args.docs_command == "update":
            await self.handle_update_doc(args)
        elif args.docs_command == "translate":
            await self.handle_translate_doc(args)

    async def handle_sheets(self, args):
        """Handle sheets subcommands."""
        if args.sheets_command == "create-document":
            await self.handle_create_sheet(args)
        elif args.sheets_command == "read":
            await self.handle_list_sheets(args)
        elif args.sheets_command == "hide":
            args.action = "hide"
            await self.handle_manage_sheet(args)
        elif args.sheets_command == "unhide":
            args.action = "unhide"
            await self.handle_manage_sheet(args)
        elif args.sheets_command == "create":
            args.action = "create"
            await self.handle_manage_sheet(args)
        elif args.sheets_command == "delete":
            args.action = "delete"
            await self.handle_manage_sheet(args)
        elif args.sheets_command == "values":
            await self.handle_sheet_values(args)
        elif args.sheets_command == "columns":
            await self.handle_sheet_columns(args)
        elif args.sheets_command == "rows":
            await self.handle_sheet_rows(args)
        elif args.sheets_command == "translate":
            await self.handle_translate_sheet(args)

    async def handle_sheet_values(self, args):
        """Handle sheet values subcommands."""
        if args.values_action == "set":
            if hasattr(args, "formula") and args.formula:
                # Convert values to formula format for set_formula
                args.formula = args.values
                await self.handle_set_formula(args)
            else:
                await self.handle_set_values(args)

            # Apply formatting if provided
            if hasattr(args, "format") and args.format:
                args.format_options = args.format
                await self.handle_format_cells(args)
        elif args.values_action == "read":
            await self.handle_read_sheet(args)
        elif args.values_action == "format":
            await self.handle_format_cells(args)

    async def handle_sheet_columns(self, args):
        """Handle sheet columns subcommands."""
        if args.columns_action == "add":
            await self.handle_add_column(args)
        elif args.columns_action == "remove":
            await self.handle_remove_column(args)

    async def handle_sheet_rows(self, args):
        """Handle sheet rows subcommands."""
        if args.rows_action == "add":
            await self.handle_add_row(args)
        elif args.rows_action == "remove":
            await self.handle_remove_row(args)

    async def handle_slides(self, args):
        """Handle slides subcommands."""
        if args.slides_command == "create-document":
            await self.handle_create_slides(args)
        elif args.slides_command == "themes":
            await self.handle_slides_themes(args)
        elif args.slides_command == "layout":
            await self.handle_slides_layout(args)
        elif args.slides_command == "add":
            await self.handle_slides_add(args)
        elif args.slides_command == "move":
            await self.handle_slides_move(args)
        elif args.slides_command == "remove":
            await self.handle_slides_remove(args)
        elif args.slides_command == "content":
            await self.handle_slides_content(args)

    async def handle_translate_doc(self, args):
        """Handle document translation."""
        try:
            start_index = getattr(args, "start_index", 1)
            end_index = getattr(args, "end_index", None)

            result = await self.docs_service.translate_document(
                args.document_id, args.target_language, getattr(args, "source_language", None), start_index, end_index
            )

            if result:
                print(f"Document translated successfully to {args.target_language}")
                print(f"Translation completed")
            else:
                print("No content was translated")

        except Exception as e:
            self.logger.error("Failed to translate document: %s", str(e))
            sys.exit(1)

    async def handle_translate_sheet(self, args):
        """Handle sheet range translation."""
        try:
            result = await self.sheets_service.translate_range(
                args.spreadsheet_id, args.range, args.target_language, getattr(args, "source_language", None)
            )

            if result:
                updated_cells = result.get("updatedCells", 0)
                print(f"Range '{args.range}' translated successfully to {args.target_language}")
                print(f"Updated {updated_cells} cells")
            else:
                print("No content was translated in the specified range")

        except Exception as e:
            self.logger.error("Failed to translate sheet range: %s", str(e))
            sys.exit(1)

    async def handle_slides_themes(self, args):
        """Handle slides themes subcommands."""
        try:
            if args.themes_action == "import":
                result = self.slides_service.import_theme(
                    args.presentation_id, args.template_id, getattr(args, "set", False)
                )
                print(f"Theme imported successfully from presentation {args.template_id}")
                if getattr(args, "set", False):
                    print("Theme automatically applied to presentation")
            elif args.themes_action == "set":
                result = self.slides_service.set_theme(args.presentation_id, args.theme_name)
                print(f"Theme '{args.theme_name}' applied successfully to presentation {args.presentation_id}")
        except Exception as e:
            self.logger.error("Failed to manage theme: %s", str(e))
            sys.exit(1)

    async def handle_slides_layout(self, args):
        """Handle slides layout subcommands."""
        try:
            if args.layout_action == "list":
                layouts = self.slides_service.list_layouts(args.presentation_id)
                print(f"Available layouts for presentation {args.presentation_id}:")
                for layout in layouts:
                    print(f"  - {layout['name']}: {layout['description']}")
        except Exception as e:
            self.logger.error("Failed to list layouts: %s", str(e))
            sys.exit(1)

    async def handle_slides_add(self, args):
        """Handle adding slides."""
        try:
            result = self.slides_service.add_slide(args.presentation_id, args.layout, getattr(args, "position", None))
            print(f"Slide added successfully with layout '{args.layout}'")
            if hasattr(args, "position") and args.position is not None:
                print(f"Inserted at position {args.position}")
            else:
                print("Added at the end")
        except Exception as e:
            self.logger.error("Failed to add slide: %s", str(e))
            sys.exit(1)

    async def handle_slides_move(self, args):
        """Handle moving slides."""
        try:
            result = self.slides_service.move_slide(args.presentation_id, args.slide_id, args.position)
            print(f"Slide {args.slide_id} moved to position {args.position}")
        except Exception as e:
            self.logger.error("Failed to move slide: %s", str(e))
            sys.exit(1)

    async def handle_slides_remove(self, args):
        """Handle removing slides."""
        try:
            result = self.slides_service.remove_slide(args.presentation_id, args.slide_id)
            print(f"Slide {args.slide_id} removed successfully")
        except Exception as e:
            self.logger.error("Failed to remove slide: %s", str(e))
            sys.exit(1)

    async def handle_slides_content(self, args):
        """Handle slides content subcommands."""
        try:
            if args.content_action == "add":
                await self.handle_slides_content_add(args)
            elif args.content_action == "list":
                await self.handle_slides_content_list(args)
            elif args.content_action == "remove":
                await self.handle_slides_content_remove(args)
            elif args.content_action == "move":
                await self.handle_slides_content_move(args)
        except Exception as e:
            self.logger.error("Failed to manage content: %s", str(e))
            sys.exit(1)

    async def handle_slides_content_add(self, args):
        """Handle adding content to slides."""
        format_options = None
        if hasattr(args, "format") and args.format:
            import json

            format_options = json.loads(args.format)

        if args.content_type == "text":
            result = self.slides_service.add_text_content(
                args.presentation_id,
                args.slide_id,
                args.content,
                args.x,
                args.y,
                args.width,
                args.height,
                format_options,
            )
            print(f"Text content added to slide {args.slide_id}")
        elif args.content_type == "image":
            result = self.slides_service.add_image_content(
                args.presentation_id, args.slide_id, args.content, args.x, args.y, args.width, args.height
            )
            print(f"Image content added to slide {args.slide_id}")
        elif args.content_type == "table":
            # Parse ROWSxCOLS format
            if "x" in args.content.lower():
                rows, cols = map(int, args.content.lower().split("x"))
                result = self.slides_service.add_table_content(
                    args.presentation_id, args.slide_id, rows, cols, args.x, args.y, args.width, args.height
                )
                print(f"Table ({rows}x{cols}) added to slide {args.slide_id}")
            else:
                raise ValueError("Table content must be in format 'ROWSxCOLS' (e.g., '3x4')")

    async def handle_slides_content_list(self, args):
        """Handle listing content in slides."""
        content_elements = self.slides_service.list_slide_content(args.presentation_id, args.slide_id)
        if not content_elements:
            print(f"No content found in slide {args.slide_id}")
            return

        print(f"Content in slide {args.slide_id}:")
        for element in content_elements:
            print(f"  - ID: {element['id']}, Type: {element['type']}")

    async def handle_slides_content_remove(self, args):
        """Handle removing content from slides."""
        result = self.slides_service.remove_content(args.presentation_id, args.element_id)
        print(f"Content element {args.element_id} removed successfully")

    async def handle_slides_content_move(self, args):
        """Handle moving content on slides."""
        result = self.slides_service.move_content(args.presentation_id, args.element_id, args.x, args.y)
        print(f"Content element {args.element_id} moved to position ({args.x}, {args.y})")

    def create_parser(self):
        """Create argument parser with hierarchical command structure."""
        parser = argparse.ArgumentParser(description="Google Drive CLI tool", prog="godri")
        parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # AUTH command
        auth_parser = subparsers.add_parser("auth", help="Authenticate with Google APIs")
        auth_parser.add_argument("--force", action="store_true", help="Force re-authentication (delete existing token)")

        # DRIVE command with subcommands
        drive_parser = subparsers.add_parser("drive", help="Google Drive operations")
        drive_subparsers = drive_parser.add_subparsers(dest="drive_command", help="Drive operations")

        # drive search
        drive_search_parser = drive_subparsers.add_parser("search", help="Search for files")
        drive_search_group = drive_search_parser.add_mutually_exclusive_group(required=True)
        drive_search_group.add_argument("--query", "-q", help="Search query")
        drive_search_group.add_argument("--name", "-n", help="Search by file name")
        drive_search_parser.add_argument("--mime-type", "-t", help="Filter by MIME type")
        drive_search_parser.add_argument("--limit", "-l", type=int, default=20, help="Maximum results")

        # drive upload
        drive_upload_parser = drive_subparsers.add_parser("upload", help="Upload a file")
        drive_upload_parser.add_argument("file_path", help="Path to file to upload")
        drive_upload_parser.add_argument("--folder-id", "-f", help="Parent folder ID")
        drive_upload_parser.add_argument("--name", "-n", help="Custom file name")

        # drive download
        drive_download_parser = drive_subparsers.add_parser("download", help="Download a file")
        drive_download_parser.add_argument("file_id", help="File ID to download")
        drive_download_parser.add_argument("output_path", help="Output file path")
        drive_download_parser.add_argument(
            "--smart",
            "-s",
            action="store_true",
            help="Smart download: convert Google Workspace files to Office formats",
        )

        # drive folder
        drive_folder_parser = drive_subparsers.add_parser("folder", help="Folder operations")
        folder_subparsers = drive_folder_parser.add_subparsers(dest="folder_action", help="Folder actions")

        # drive folder create
        folder_create_parser = folder_subparsers.add_parser("create", help="Create a folder")
        folder_create_parser.add_argument("name", help="Folder name")
        folder_create_parser.add_argument("--parent-id", "-p", help="Parent folder ID")

        # drive folder delete
        folder_delete_parser = folder_subparsers.add_parser("delete", help="Delete a folder")
        folder_delete_parser.add_argument("file_id", help="Folder ID to delete")

        # DOCS command with subcommands
        docs_parser = subparsers.add_parser("docs", help="Google Docs operations")
        docs_subparsers = docs_parser.add_subparsers(dest="docs_command", help="Docs operations")

        # docs create-document
        docs_create_parser = docs_subparsers.add_parser("create-document", help="Create a Google Doc")
        docs_create_parser.add_argument("title", help="Document title")
        docs_create_parser.add_argument("--folder-id", "-f", help="Folder ID")
        docs_create_parser.add_argument("--content", "-c", help="Initial content")
        docs_create_parser.add_argument("--markdown", "-m", action="store_true", help="Parse content as markdown")

        # docs read
        docs_read_parser = docs_subparsers.add_parser("read", help="Read Google Doc content")
        docs_read_parser.add_argument("document_id", help="Document ID to read")
        docs_read_parser.add_argument(
            "--plain-text", "-p", action="store_true", help="Output only plain text without headers"
        )

        # docs update
        docs_update_parser = docs_subparsers.add_parser("update", help="Update Google Doc content")
        docs_update_parser.add_argument("document_id", help="Document ID to update")
        docs_update_parser.add_argument("content", help="Content to add/replace")
        docs_update_parser.add_argument("--markdown", "-m", action="store_true", help="Parse content as markdown")
        docs_update_parser.add_argument(
            "--replace", "-r", action="store_true", help="Replace entire document content (default: append)"
        )
        docs_update_parser.add_argument(
            "--index", "-i", type=int, default=1, help="Insert position (ignored if --replace)"
        )

        # docs translate
        docs_translate_parser = docs_subparsers.add_parser("translate", help="Translate Google Doc content")
        docs_translate_parser.add_argument("document_id", help="Document ID to translate")
        docs_translate_parser.add_argument("target_language", help="Target language code (e.g., 'fr', 'es')")
        docs_translate_parser.add_argument(
            "--source-language", "-s", help="Source language code (auto-detect if not specified)"
        )
        docs_translate_parser.add_argument(
            "--start-index", type=int, default=1, help="Start index for translation range"
        )
        docs_translate_parser.add_argument(
            "--end-index", type=int, help="End index for translation range (entire document if not specified)"
        )

        # SHEETS command with subcommands
        sheets_parser = subparsers.add_parser("sheets", help="Google Sheets operations")
        sheets_subparsers = sheets_parser.add_subparsers(dest="sheets_command", help="Sheets operations")

        # sheets create-document
        sheets_create_parser = sheets_subparsers.add_parser("create-document", help="Create a Google Sheet")
        sheets_create_parser.add_argument("title", help="Spreadsheet title")
        sheets_create_parser.add_argument("--folder-id", "-f", help="Folder ID")

        # sheets read
        sheets_read_parser = sheets_subparsers.add_parser("read", help="List all sheets in spreadsheet")
        sheets_read_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")

        # sheets hide
        sheets_hide_parser = sheets_subparsers.add_parser("hide", help="Hide a sheet")
        sheets_hide_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        sheets_hide_parser.add_argument("sheet_name", help="Sheet name")

        # sheets unhide
        sheets_unhide_parser = sheets_subparsers.add_parser("unhide", help="Unhide a sheet")
        sheets_unhide_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        sheets_unhide_parser.add_argument("sheet_name", help="Sheet name")

        # sheets create
        sheets_create_sheet_parser = sheets_subparsers.add_parser("create", help="Create a new sheet")
        sheets_create_sheet_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        sheets_create_sheet_parser.add_argument("sheet_name", help="Sheet name")

        # sheets delete
        sheets_delete_parser = sheets_subparsers.add_parser("delete", help="Delete a sheet")
        sheets_delete_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        sheets_delete_parser.add_argument("sheet_name", help="Sheet name")

        # sheets values
        sheets_values_parser = sheets_subparsers.add_parser("values", help="Sheet values operations")
        values_subparsers = sheets_values_parser.add_subparsers(dest="values_action", help="Values actions")

        # sheets values set
        values_set_parser = values_subparsers.add_parser("set", help="Set values in cells")
        values_set_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        values_set_parser.add_argument("range", help="Range to set values (e.g., 'A1', 'Sheet1!A1:B2')")
        values_set_parser.add_argument("values", help="Values to set (comma-separated or JSON array)")
        values_set_parser.add_argument("--formula", action="store_true", help="Treat values as formula")
        values_set_parser.add_argument("--format", help="Format options as JSON")

        # sheets values read
        values_read_parser = values_subparsers.add_parser("read", help="Read sheet data")
        values_read_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        values_read_parser.add_argument("--sheet-name", "-s", help="Sheet name (default: first sheet)")
        values_read_parser.add_argument("--range", "-r", help="Specific range to read (e.g., 'A1:C10')")
        values_read_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
        values_read_parser.add_argument("--limit", "-l", type=int, help="Limit number of rows displayed")

        # sheets values format
        values_format_parser = values_subparsers.add_parser(
            "format", help="Format cells with JSON options or copy from another range"
        )
        values_format_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        values_format_parser.add_argument("range", help="Range to format")
        format_group = values_format_parser.add_mutually_exclusive_group(required=True)
        format_group.add_argument(
            "--format-options",
            help="""Format options as JSON. Examples:
Font: '{"textFormat":{"fontFamily":"Arial"}}'
Bold: '{"textFormat":{"bold":true}}'
Italic: '{"textFormat":{"italic":true}}'
Underline: '{"textFormat":{"underline":true}}'
Font size: '{"textFormat":{"fontSize":14}}'
Text color: '{"textFormat":{"foregroundColor":{"red":1.0,"green":0.0,"blue":0.0}}}'
Background: '{"backgroundColor":{"red":1.0,"green":0.8,"blue":0.8}}'
Combined: '{"textFormat":{"bold":true,"fontFamily":"Calibri","fontSize":12,"foregroundColor":{"red":0.2,"green":0.2,"blue":0.8}},"backgroundColor":{"red":0.9,"green":0.9,"blue":1.0}}'""",
        )
        format_group.add_argument("--from", dest="source_range", help="Copy formatting from this range")

        # sheets columns
        sheets_columns_parser = sheets_subparsers.add_parser("columns", help="Column operations")
        columns_subparsers = sheets_columns_parser.add_subparsers(dest="columns_action", help="Column actions")

        # sheets columns add
        columns_add_parser = columns_subparsers.add_parser("add", help="Add column(s)")
        columns_add_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        columns_add_parser.add_argument("column_letter", help="Column letter to insert at")
        columns_add_parser.add_argument("--count", "-c", type=int, default=1, help="Number of columns to insert")
        columns_add_parser.add_argument("--sheet-name", "-s", help="Sheet name (default: first sheet)")

        # sheets columns remove
        columns_remove_parser = columns_subparsers.add_parser("remove", help="Remove column(s)")
        columns_remove_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        columns_remove_parser.add_argument("column_letter", help="Column letter to delete")
        columns_remove_parser.add_argument("--count", "-c", type=int, default=1, help="Number of columns to delete")
        columns_remove_parser.add_argument("--sheet-name", "-s", help="Sheet name (default: first sheet)")

        # sheets rows
        sheets_rows_parser = sheets_subparsers.add_parser("rows", help="Row operations")
        rows_subparsers = sheets_rows_parser.add_subparsers(dest="rows_action", help="Row actions")

        # sheets rows add
        rows_add_parser = rows_subparsers.add_parser("add", help="Add row(s)")
        rows_add_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        rows_add_parser.add_argument("row_number", type=int, help="Row number to insert at (1-based)")
        rows_add_parser.add_argument("--count", "-c", type=int, default=1, help="Number of rows to insert")
        rows_add_parser.add_argument("--sheet-name", "-s", help="Sheet name (default: first sheet)")

        # sheets rows remove
        rows_remove_parser = rows_subparsers.add_parser("remove", help="Remove row(s)")
        rows_remove_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        rows_remove_parser.add_argument("row_number", type=int, help="Row number to delete (1-based)")
        rows_remove_parser.add_argument("--count", "-c", type=int, default=1, help="Number of rows to delete")
        rows_remove_parser.add_argument("--sheet-name", "-s", help="Sheet name (default: first sheet)")

        # sheets translate
        sheets_translate_parser = sheets_subparsers.add_parser("translate", help="Translate sheet range content")
        sheets_translate_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
        sheets_translate_parser.add_argument("range", help="Range to translate (e.g., 'A1:C10', 'Sheet1!A1:B5')")
        sheets_translate_parser.add_argument("target_language", help="Target language code (e.g., 'fr', 'es')")
        sheets_translate_parser.add_argument(
            "--source-language", "-s", help="Source language code (auto-detect if not specified)"
        )

        # SLIDES command
        slides_parser = subparsers.add_parser("slides", help="Google Slides operations")
        slides_subparsers = slides_parser.add_subparsers(dest="slides_command", help="Slides operations")

        # slides create-document
        slides_create_parser = slides_subparsers.add_parser(
            "create-document", help="Create a Google Slides presentation"
        )
        slides_create_parser.add_argument("title", help="Presentation title")
        slides_create_parser.add_argument("--folder-id", "-f", help="Folder ID")
        slides_create_parser.add_argument(
            "--theme",
            "-t",
            default="STREAMLINE",
            help="Presentation theme (SIMPLE_LIGHT, SIMPLE_DARK, STREAMLINE, FOCUS, SHIFT, MOMENTUM, PARADIGM, SLATE, CORAL, BEACH_DAY, MODERN_WRITER, SPEARMINT, GAMEDAY, BLUE_AND_YELLOW, SWISS, LUXE, MARINA, FOREST)",
        )

        # slides themes
        slides_themes_parser = slides_subparsers.add_parser("themes", help="Theme management")
        themes_subparsers = slides_themes_parser.add_subparsers(dest="themes_action", help="Theme actions")

        # slides themes import
        themes_import_parser = themes_subparsers.add_parser("import", help="Import theme from another presentation")
        themes_import_parser.add_argument("presentation_id", help="Target presentation ID")
        themes_import_parser.add_argument("template_id", help="Source presentation ID with theme to import")
        themes_import_parser.add_argument("--set", action="store_true", help="Automatically apply the imported theme")

        # slides themes set
        themes_set_parser = themes_subparsers.add_parser("set", help="Set theme for presentation")
        themes_set_parser.add_argument("presentation_id", help="Presentation ID")
        themes_set_parser.add_argument(
            "theme_name",
            help="Theme name (SIMPLE_LIGHT, SIMPLE_DARK, STREAMLINE, FOCUS, SHIFT, MOMENTUM, PARADIGM, SLATE, CORAL, BEACH_DAY, MODERN_WRITER, SPEARMINT, GAMEDAY, BLUE_AND_YELLOW, SWISS, LUXE, MARINA, FOREST)",
        )

        # slides layout
        slides_layout_parser = slides_subparsers.add_parser("layout", help="Layout operations")
        layout_subparsers = slides_layout_parser.add_subparsers(dest="layout_action", help="Layout actions")

        # slides layout list
        layout_list_parser = layout_subparsers.add_parser("list", help="List available layouts")
        layout_list_parser.add_argument("presentation_id", help="Presentation ID")

        # slides add
        slides_add_parser = slides_subparsers.add_parser("add", help="Add a slide")
        slides_add_parser.add_argument("presentation_id", help="Presentation ID")
        slides_add_parser.add_argument(
            "--layout",
            "-l",
            default="BLANK",
            help="Slide layout (BLANK, CAPTION_ONLY, TITLE, TITLE_AND_BODY, TITLE_AND_TWO_COLUMNS, TITLE_ONLY, SECTION_HEADER, SECTION_TITLE_AND_DESCRIPTION, ONE_COLUMN_TEXT, MAIN_POINT, BIG_NUMBER)",
        )
        slides_add_parser.add_argument(
            "--position", "-p", type=int, help="Position to insert slide (0-based, end if not specified)"
        )

        # slides move
        slides_move_parser = slides_subparsers.add_parser("move", help="Move a slide")
        slides_move_parser.add_argument("presentation_id", help="Presentation ID")
        slides_move_parser.add_argument("slide_id", help="Slide ID to move")
        slides_move_parser.add_argument("position", type=int, help="New position (0-based)")

        # slides remove
        slides_remove_parser = slides_subparsers.add_parser("remove", help="Remove a slide")
        slides_remove_parser.add_argument("presentation_id", help="Presentation ID")
        slides_remove_parser.add_argument("slide_id", help="Slide ID to remove")

        # slides content
        slides_content_parser = slides_subparsers.add_parser("content", help="Content management")
        content_subparsers = slides_content_parser.add_subparsers(dest="content_action", help="Content actions")

        # slides content add
        content_add_parser = content_subparsers.add_parser("add", help="Add content to slide")
        content_add_parser.add_argument("presentation_id", help="Presentation ID")
        content_add_parser.add_argument("slide_id", help="Slide ID")
        content_add_parser.add_argument(
            "content_type", choices=["text", "image", "table"], help="Type of content to add"
        )
        content_add_parser.add_argument(
            "content", help="Content data (text string, image URL, or 'ROWSxCOLS' for table)"
        )
        content_add_parser.add_argument("--x", type=float, default=100, help="X position")
        content_add_parser.add_argument("--y", type=float, default=100, help="Y position")
        content_add_parser.add_argument("--width", type=float, default=300, help="Width")
        content_add_parser.add_argument("--height", type=float, default=200, help="Height")
        content_add_parser.add_argument("--format", help="Format options as JSON (similar to sheets formatting)")

        # slides content list
        content_list_parser = content_subparsers.add_parser("list", help="List content in slide")
        content_list_parser.add_argument("presentation_id", help="Presentation ID")
        content_list_parser.add_argument("slide_id", help="Slide ID")

        # slides content remove
        content_remove_parser = content_subparsers.add_parser("remove", help="Remove content from slide")
        content_remove_parser.add_argument("presentation_id", help="Presentation ID")
        content_remove_parser.add_argument("element_id", help="Element ID to remove")

        # slides content move
        content_move_parser = content_subparsers.add_parser("move", help="Move content on slide")
        content_move_parser.add_argument("presentation_id", help="Presentation ID")
        content_move_parser.add_argument("element_id", help="Element ID to move")
        content_move_parser.add_argument("x", type=float, help="New X position")
        content_move_parser.add_argument("y", type=float, help="New Y position")

        # TRANSLATE command
        translate_parser = subparsers.add_parser("translate", help="Translate text")
        translate_parser.add_argument("text", help="Text to translate")
        translate_parser.add_argument("target_language", help="Target language code (e.g., 'fr', 'es')")
        translate_parser.add_argument("--source-language", "-s", help="Source language code")

        return parser

    async def run(self, args=None):
        """Run the CLI application."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        if not parsed_args.command:
            parser.print_help()
            return

        try:
            await self.initialize_services()
        except Exception as e:
            self.logger.error("Service initialization failed: %s", str(e))
            sys.exit(1)

        command_handlers = {
            "auth": self.handle_auth,
            "drive": self.handle_drive,
            "docs": self.handle_docs,
            "sheets": self.handle_sheets,
            "slides": self.handle_slides,
            "translate": self.handle_translate,
        }

        handler = command_handlers.get(parsed_args.command)
        if handler:
            await handler(parsed_args)
        else:
            print(f"Unknown command: {parsed_args.command}")
            sys.exit(1)


async def main():
    """Main entry point."""
    setup_logging()
    cli = GodriCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
