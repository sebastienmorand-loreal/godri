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
            result = self.slides_service.create_presentation(args.title, args.folder_id)
            print(f"Presentation created successfully!")
            print(f"  - ID: {result['presentationId']}")
            print(f"  - Title: {result['title']}")
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

    def create_parser(self):
        """Create argument parser."""
        parser = argparse.ArgumentParser(description="Google Drive CLI tool", prog="godri")

        parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        auth_parser = subparsers.add_parser("auth", help="Authenticate with Google APIs")

        search_parser = subparsers.add_parser("search", help="Search for files")
        search_group = search_parser.add_mutually_exclusive_group(required=True)
        search_group.add_argument("--query", "-q", help="Search query")
        search_group.add_argument("--name", "-n", help="Search by file name")
        search_parser.add_argument("--mime-type", "-t", help="Filter by MIME type")
        search_parser.add_argument("--limit", "-l", type=int, default=20, help="Maximum results")

        upload_parser = subparsers.add_parser("upload", help="Upload a file")
        upload_parser.add_argument("file_path", help="Path to file to upload")
        upload_parser.add_argument("--folder-id", "-f", help="Parent folder ID")
        upload_parser.add_argument("--name", "-n", help="Custom file name")

        download_parser = subparsers.add_parser("download", help="Download a file")
        download_parser.add_argument("file_id", help="File ID to download")
        download_parser.add_argument("output_path", help="Output file path")

        folder_parser = subparsers.add_parser("create-folder", help="Create a folder")
        folder_parser.add_argument("name", help="Folder name")
        folder_parser.add_argument("--parent-id", "-p", help="Parent folder ID")

        delete_parser = subparsers.add_parser("delete", help="Delete a file or folder")
        delete_parser.add_argument("file_id", help="File/folder ID to delete")

        doc_parser = subparsers.add_parser("create-doc", help="Create a Google Doc")
        doc_parser.add_argument("title", help="Document title")
        doc_parser.add_argument("--folder-id", "-f", help="Folder ID")
        doc_parser.add_argument("--content", "-c", help="Initial content")

        sheet_parser = subparsers.add_parser("create-sheet", help="Create a Google Sheet")
        sheet_parser.add_argument("title", help="Spreadsheet title")
        sheet_parser.add_argument("--folder-id", "-f", help="Folder ID")

        slides_parser = subparsers.add_parser("create-slides", help="Create a Google Slides presentation")
        slides_parser.add_argument("title", help="Presentation title")
        slides_parser.add_argument("--folder-id", "-f", help="Folder ID")

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
            "search": self.handle_search,
            "upload": self.handle_upload,
            "download": self.handle_download,
            "create-folder": self.handle_create_folder,
            "delete": self.handle_delete,
            "create-doc": self.handle_create_doc,
            "create-sheet": self.handle_create_sheet,
            "create-slides": self.handle_create_slides,
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
