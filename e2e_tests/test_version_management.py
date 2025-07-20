#!/usr/bin/env python3
"""
End-to-end tests for version management functionality.

These tests verify the complete version management feature across
Google Slides, Docs, and Sheets services including:
- Version listing
- Version comparison with diff strategies
- Version download functionality  
- Keep forever functionality

Prerequisites:
- Google API credentials configured
- Internet connection for API calls
- Valid Google Workspace file IDs for testing
"""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from godri.services.auth_service_new import AuthService
from godri.services.slides_service import SlidesService
from godri.services.docs_service import DocsService
from godri.services.sheets_service import SheetsService

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VersionManagementE2ETests:
    """End-to-end tests for version management functionality."""

    def __init__(self):
        self.auth_service = None
        self.slides_service = None
        self.docs_service = None
        self.sheets_service = None
        
        # Test file IDs - these should be replaced with actual test file IDs
        # For now, we'll create test files or use placeholder IDs
        self.test_presentation_id = None
        self.test_document_id = None
        self.test_spreadsheet_id = None

    async def setup(self):
        """Initialize services for testing."""
        logger.info("Setting up version management E2E tests...")
        
        try:
            # Initialize authentication
            self.auth_service = AuthService()
            
            # Initialize services
            self.slides_service = SlidesService(self.auth_service)
            self.docs_service = DocsService(self.auth_service)
            self.sheets_service = SheetsService(self.auth_service)
            
            # Initialize all services
            await self.slides_service.initialize()
            await self.docs_service.initialize()
            await self.sheets_service.initialize()
            
            logger.info("Services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup services: {e}")
            return False

    async def create_test_files(self):
        """Create test files for version management testing."""
        logger.info("Creating test files...")
        
        try:
            # Create test presentation
            presentation = await self.slides_service.create_presentation("Version Test Presentation", None, "STREAMLINE")
            self.test_presentation_id = presentation["presentationId"]
            logger.info(f"Created test presentation: {self.test_presentation_id}")
            
            # Create test document
            document = await self.docs_service.create_document("Version Test Document", None)
            self.test_document_id = document["documentId"]
            logger.info(f"Created test document: {self.test_document_id}")
            
            # Create test spreadsheet
            spreadsheet = await self.sheets_service.create_spreadsheet("Version Test Spreadsheet", None)
            self.test_spreadsheet_id = spreadsheet["spreadsheetId"]
            logger.info(f"Created test spreadsheet: {self.test_spreadsheet_id}")
            
            # Add some content to generate version history
            await self._add_initial_content()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create test files: {e}")
            return False

    async def _add_initial_content(self):
        """Add initial content to test files to create version history."""
        logger.info("Adding initial content to test files...")
        
        try:
            # Add content to presentation
            slide_ids = await self.slides_service.get_slide_ids(self.test_presentation_id)
            if slide_ids:
                await self.slides_service.add_text_box(
                    self.test_presentation_id, 
                    slide_ids[0], 
                    "Initial version content"
                )
            
            # Add content to document
            await self.docs_service.insert_text(self.test_document_id, "Initial document content")
            
            # Add content to spreadsheet
            await self.sheets_service.update_values(
                self.test_spreadsheet_id, 
                "Sheet1!A1:B2", 
                [["Header 1", "Header 2"], ["Value 1", "Value 2"]]
            )
            
            logger.info("Initial content added successfully")
            
        except Exception as e:
            logger.error(f"Failed to add initial content: {e}")
            raise

    async def test_slides_version_listing(self):
        """Test listing versions for Google Slides presentation."""
        logger.info("Testing slides version listing...")
        
        try:
            versions = await self.slides_service.list_presentation_versions(self.test_presentation_id)
            
            # Verify we got versions
            assert len(versions) > 0, "No versions found for presentation"
            
            # Verify version structure
            for version in versions:
                assert "id" in version, "Version missing ID"
                assert "modifiedTime" in version, "Version missing modified time"
                assert "file_type" in version, "Version missing file type"
                assert version["file_type"] == "presentation", "Incorrect file type"
            
            logger.info(f"✅ Successfully retrieved {len(versions)} presentation versions")
            return True
            
        except Exception as e:
            logger.error(f"❌ Slides version listing test failed: {e}")
            return False

    async def test_docs_version_listing(self):
        """Test listing versions for Google Docs document."""
        logger.info("Testing docs version listing...")
        
        try:
            versions = await self.docs_service.list_document_versions(self.test_document_id)
            
            # Verify we got versions
            assert len(versions) > 0, "No versions found for document"
            
            # Verify version structure
            for version in versions:
                assert "id" in version, "Version missing ID"
                assert "modifiedTime" in version, "Version missing modified time"
                assert "file_type" in version, "Version missing file type"
                assert version["file_type"] == "document", "Incorrect file type"
            
            logger.info(f"✅ Successfully retrieved {len(versions)} document versions")
            return True
            
        except Exception as e:
            logger.error(f"❌ Docs version listing test failed: {e}")
            return False

    async def test_sheets_version_listing(self):
        """Test listing versions for Google Sheets spreadsheet."""
        logger.info("Testing sheets version listing...")
        
        try:
            versions = await self.sheets_service.list_spreadsheet_versions(self.test_spreadsheet_id)
            
            # Verify we got versions
            assert len(versions) > 0, "No versions found for spreadsheet"
            
            # Verify version structure
            for version in versions:
                assert "id" in version, "Version missing ID"
                assert "modifiedTime" in version, "Version missing modified time"
                assert "file_type" in version, "Version missing file type"
                assert version["file_type"] == "spreadsheet", "Incorrect file type"
            
            logger.info(f"✅ Successfully retrieved {len(versions)} spreadsheet versions")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sheets version listing test failed: {e}")
            return False

    async def test_slides_version_comparison(self):
        """Test comparing two versions of a presentation."""
        logger.info("Testing slides version comparison...")
        
        try:
            # Get available versions
            versions = await self.slides_service.list_presentation_versions(self.test_presentation_id)
            
            if len(versions) < 2:
                # Create additional version by modifying content
                slide_ids = await self.slides_service.get_slide_ids(self.test_presentation_id)
                if slide_ids:
                    await self.slides_service.add_text_box(
                        self.test_presentation_id,
                        slide_ids[0],
                        "Modified content for version comparison"
                    )
                
                # Wait a moment for version to be created
                await asyncio.sleep(2)
                versions = await self.slides_service.list_presentation_versions(self.test_presentation_id)
            
            if len(versions) >= 2:
                # Compare two most recent versions
                revision_1 = versions[0]["id"]
                revision_2 = versions[1]["id"]
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    comparison_result = await self.slides_service.compare_presentation_versions(
                        self.test_presentation_id, revision_1, revision_2, temp_dir
                    )
                
                # Verify comparison result structure
                assert "comparison_summary" in comparison_result, "Missing comparison summary"
                assert "changes" in comparison_result, "Missing changes section"
                assert "detailed_analysis" in comparison_result, "Missing detailed analysis"
                
                logger.info("✅ Successfully compared presentation versions")
                return True
            else:
                logger.warning("⚠️ Not enough versions to test comparison")
                return True
            
        except Exception as e:
            logger.error(f"❌ Slides version comparison test failed: {e}")
            return False

    async def test_docs_version_comparison(self):
        """Test comparing two versions of a document."""
        logger.info("Testing docs version comparison...")
        
        try:
            # Get available versions
            versions = await self.docs_service.list_document_versions(self.test_document_id)
            
            if len(versions) < 2:
                # Create additional version by modifying content
                await self.docs_service.append_text(self.test_document_id, "\nModified content for version comparison")
                
                # Wait a moment for version to be created
                await asyncio.sleep(2)
                versions = await self.docs_service.list_document_versions(self.test_document_id)
            
            if len(versions) >= 2:
                # Compare two most recent versions
                revision_1 = versions[0]["id"]
                revision_2 = versions[1]["id"]
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    comparison_result = await self.docs_service.compare_document_versions(
                        self.test_document_id, revision_1, revision_2, temp_dir
                    )
                
                # Verify comparison result structure
                assert "comparison_summary" in comparison_result, "Missing comparison summary"
                assert "changes" in comparison_result, "Missing changes section"
                assert "detailed_analysis" in comparison_result, "Missing detailed analysis"
                
                logger.info("✅ Successfully compared document versions")
                return True
            else:
                logger.warning("⚠️ Not enough versions to test comparison")
                return True
            
        except Exception as e:
            logger.error(f"❌ Docs version comparison test failed: {e}")
            return False

    async def test_sheets_version_comparison(self):
        """Test comparing two versions of a spreadsheet."""
        logger.info("Testing sheets version comparison...")
        
        try:
            # Get available versions
            versions = await self.sheets_service.list_spreadsheet_versions(self.test_spreadsheet_id)
            
            if len(versions) < 2:
                # Create additional version by modifying content
                await self.sheets_service.update_values(
                    self.test_spreadsheet_id,
                    "Sheet1!A3:B3",
                    [["Modified 1", "Modified 2"]]
                )
                
                # Wait a moment for version to be created
                await asyncio.sleep(2)
                versions = await self.sheets_service.list_spreadsheet_versions(self.test_spreadsheet_id)
            
            if len(versions) >= 2:
                # Compare two most recent versions
                revision_1 = versions[0]["id"]
                revision_2 = versions[1]["id"]
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    comparison_result = await self.sheets_service.compare_spreadsheet_versions(
                        self.test_spreadsheet_id, revision_1, revision_2, temp_dir
                    )
                
                # Verify comparison result structure
                assert "comparison_summary" in comparison_result, "Missing comparison summary"
                assert "changes" in comparison_result, "Missing changes section"
                assert "detailed_analysis" in comparison_result, "Missing detailed analysis"
                
                logger.info("✅ Successfully compared spreadsheet versions")
                return True
            else:
                logger.warning("⚠️ Not enough versions to test comparison")
                return True
            
        except Exception as e:
            logger.error(f"❌ Sheets version comparison test failed: {e}")
            return False

    async def test_version_download(self):
        """Test downloading specific versions of files."""
        logger.info("Testing version download functionality...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Test presentation download
                presentations_versions = await self.slides_service.list_presentation_versions(self.test_presentation_id)
                if presentations_versions:
                    revision_id = presentations_versions[0]["id"]
                    output_path = temp_path / "test_presentation.pptx"
                    
                    downloaded_path = await self.slides_service.download_presentation_version(
                        self.test_presentation_id, revision_id, str(output_path), "pptx"
                    )
                    
                    assert Path(downloaded_path).exists(), "Presentation download failed"
                    logger.info("✅ Successfully downloaded presentation version")
                
                # Test document download
                documents_versions = await self.docs_service.list_document_versions(self.test_document_id)
                if documents_versions:
                    revision_id = documents_versions[0]["id"]
                    output_path = temp_path / "test_document.docx"
                    
                    downloaded_path = await self.docs_service.download_document_version(
                        self.test_document_id, revision_id, str(output_path), "docx"
                    )
                    
                    assert Path(downloaded_path).exists(), "Document download failed"
                    logger.info("✅ Successfully downloaded document version")
                
                # Test spreadsheet download
                spreadsheets_versions = await self.sheets_service.list_spreadsheet_versions(self.test_spreadsheet_id)
                if spreadsheets_versions:
                    revision_id = spreadsheets_versions[0]["id"]
                    output_path = temp_path / "test_spreadsheet.xlsx"
                    
                    downloaded_path = await self.sheets_service.download_spreadsheet_version(
                        self.test_spreadsheet_id, revision_id, str(output_path), "xlsx"
                    )
                    
                    assert Path(downloaded_path).exists(), "Spreadsheet download failed"
                    logger.info("✅ Successfully downloaded spreadsheet version")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Version download test failed: {e}")
            return False

    async def test_keep_forever_functionality(self):
        """Test keep forever functionality for versions."""
        logger.info("Testing keep forever functionality...")
        
        try:
            # Test for presentation
            presentations_versions = await self.slides_service.list_presentation_versions(self.test_presentation_id)
            if presentations_versions:
                revision_id = presentations_versions[0]["id"]
                
                # Set keep forever
                result = await self.slides_service.keep_presentation_version_forever(
                    self.test_presentation_id, revision_id, True
                )
                assert result is not None, "Keep forever operation failed"
                
                # Unset keep forever
                result = await self.slides_service.keep_presentation_version_forever(
                    self.test_presentation_id, revision_id, False
                )
                assert result is not None, "Unset keep forever operation failed"
                
                logger.info("✅ Successfully tested keep forever for presentations")
            
            # Test for documents
            documents_versions = await self.docs_service.list_document_versions(self.test_document_id)
            if documents_versions:
                revision_id = documents_versions[0]["id"]
                
                # Set keep forever
                result = await self.docs_service.keep_document_version_forever(
                    self.test_document_id, revision_id, True
                )
                assert result is not None, "Keep forever operation failed"
                
                # Unset keep forever
                result = await self.docs_service.keep_document_version_forever(
                    self.test_document_id, revision_id, False
                )
                assert result is not None, "Unset keep forever operation failed"
                
                logger.info("✅ Successfully tested keep forever for documents")
            
            # Test for spreadsheets
            spreadsheets_versions = await self.sheets_service.list_spreadsheet_versions(self.test_spreadsheet_id)
            if spreadsheets_versions:
                revision_id = spreadsheets_versions[0]["id"]
                
                # Set keep forever
                result = await self.sheets_service.keep_spreadsheet_version_forever(
                    self.test_spreadsheet_id, revision_id, True
                )
                assert result is not None, "Keep forever operation failed"
                
                # Unset keep forever
                result = await self.sheets_service.keep_spreadsheet_version_forever(
                    self.test_spreadsheet_id, revision_id, False
                )
                assert result is not None, "Unset keep forever operation failed"
                
                logger.info("✅ Successfully tested keep forever for spreadsheets")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Keep forever functionality test failed: {e}")
            return False

    async def cleanup(self):
        """Clean up test files."""
        logger.info("Cleaning up test files...")
        
        try:
            # Delete test files
            if self.test_presentation_id:
                await self.slides_service.drive_api.delete_file(self.test_presentation_id)
                logger.info(f"Deleted test presentation: {self.test_presentation_id}")
            
            if self.test_document_id:
                await self.docs_service.drive_api.delete_file(self.test_document_id)
                logger.info(f"Deleted test document: {self.test_document_id}")
            
            if self.test_spreadsheet_id:
                await self.sheets_service.drive_api.delete_file(self.test_spreadsheet_id)
                logger.info(f"Deleted test spreadsheet: {self.test_spreadsheet_id}")
            
            logger.info("✅ Cleanup completed successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup encountered errors: {e}")

    async def run_all_tests(self):
        """Run all version management tests."""
        logger.info("🚀 Starting Version Management E2E Tests")
        
        total_tests = 0
        passed_tests = 0
        
        # Setup
        if not await self.setup():
            logger.error("❌ Setup failed - aborting tests")
            return False
        
        # Create test files
        if not await self.create_test_files():
            logger.error("❌ Test file creation failed - aborting tests")
            return False
        
        try:
            # Define all tests
            tests = [
                ("Slides Version Listing", self.test_slides_version_listing),
                ("Docs Version Listing", self.test_docs_version_listing),
                ("Sheets Version Listing", self.test_sheets_version_listing),
                ("Slides Version Comparison", self.test_slides_version_comparison),
                ("Docs Version Comparison", self.test_docs_version_comparison),
                ("Sheets Version Comparison", self.test_sheets_version_comparison),
                ("Version Download", self.test_version_download),
                ("Keep Forever Functionality", self.test_keep_forever_functionality),
            ]
            
            # Run each test
            for test_name, test_func in tests:
                total_tests += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*60}")
                
                try:
                    if await test_func():
                        passed_tests += 1
                        logger.info(f"✅ {test_name}: PASSED")
                    else:
                        logger.error(f"❌ {test_name}: FAILED")
                except Exception as e:
                    logger.error(f"❌ {test_name}: FAILED with exception: {e}")
        
        finally:
            # Always cleanup
            await self.cleanup()
        
        # Results summary
        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 Test Results Summary")
        logger.info(f"{'='*60}")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success rate: {(passed_tests / total_tests * 100):.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED!")
            return True
        else:
            logger.error(f"💥 {total_tests - passed_tests} TESTS FAILED")
            return False


async def main():
    """Main test execution function."""
    test_runner = VersionManagementE2ETests()
    success = await test_runner.run_all_tests()
    
    if success:
        logger.info("✅ Version Management E2E Tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Version Management E2E Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())