#!/usr/bin/env python3
"""
End-to-end tests for CLI version management commands.

These tests verify the CLI interface for version management functionality
by running actual CLI commands and validating their outputs.
"""

import asyncio
import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CLIVersionCommandsE2ETests:
    """End-to-end tests for CLI version management commands."""

    def __init__(self):
        self.test_presentation_id = None
        self.test_document_id = None
        self.test_spreadsheet_id = None

    def run_cli_command(self, command_args):
        """Run a CLI command and return the result."""
        try:
            # Run the command
            result = subprocess.run(
                ["godri"] + command_args,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            logger.error("Command timed out")
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    async def create_test_files(self):
        """Create test files using CLI commands."""
        logger.info("Creating test files via CLI...")
        
        try:
            # Create test presentation
            result = self.run_cli_command([
                "slides", "create", 
                "CLI Version Test Presentation"
            ])
            
            if result["returncode"] == 0:
                # Extract presentation ID from output
                output = result["stdout"]
                if "presentationId" in output:
                    # Parse JSON-like output to extract ID
                    import re
                    match = re.search(r"'presentationId': '([^']+)'", output)
                    if match:
                        self.test_presentation_id = match.group(1)
                        logger.info(f"Created test presentation: {self.test_presentation_id}")
            
            # Create test document
            result = self.run_cli_command([
                "docs", "create",
                "CLI Version Test Document"
            ])
            
            if result["returncode"] == 0:
                output = result["stdout"]
                if "documentId" in output:
                    match = re.search(r"'documentId': '([^']+)'", output)
                    if match:
                        self.test_document_id = match.group(1)
                        logger.info(f"Created test document: {self.test_document_id}")
            
            # Create test spreadsheet
            result = self.run_cli_command([
                "sheets", "create",
                "CLI Version Test Spreadsheet"
            ])
            
            if result["returncode"] == 0:
                output = result["stdout"]
                if "spreadsheetId" in output:
                    match = re.search(r"'spreadsheetId': '([^']+)'", output)
                    if match:
                        self.test_spreadsheet_id = match.group(1)
                        logger.info(f"Created test spreadsheet: {self.test_spreadsheet_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create test files: {e}")
            return False

    def test_slides_versions_list_command(self):
        """Test 'godri slides versions list' command."""
        logger.info("Testing 'godri slides versions list' command...")
        
        if not self.test_presentation_id:
            logger.warning("No test presentation ID available")
            return False
        
        try:
            result = self.run_cli_command([
                "slides", "versions", "list",
                self.test_presentation_id
            ])
            
            # Check command executed successfully
            if result["returncode"] != 0:
                logger.error(f"Command failed: {result['stderr']}")
                return False
            
            # Verify output contains version information
            output = result["stdout"]
            if "versions" not in output.lower() and "revision" not in output.lower():
                logger.error("Output doesn't contain version information")
                return False
            
            logger.info("✅ Slides versions list command successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Slides versions list command test failed: {e}")
            return False

    def test_docs_versions_list_command(self):
        """Test 'godri docs versions list' command."""
        logger.info("Testing 'godri docs versions list' command...")
        
        if not self.test_document_id:
            logger.warning("No test document ID available")
            return False
        
        try:
            result = self.run_cli_command([
                "docs", "versions", "list",
                self.test_document_id
            ])
            
            # Check command executed successfully
            if result["returncode"] != 0:
                logger.error(f"Command failed: {result['stderr']}")
                return False
            
            # Verify output contains version information
            output = result["stdout"]
            if "versions" not in output.lower() and "revision" not in output.lower():
                logger.error("Output doesn't contain version information")
                return False
            
            logger.info("✅ Docs versions list command successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Docs versions list command test failed: {e}")
            return False

    def test_sheets_versions_list_command(self):
        """Test 'godri sheets versions list' command."""
        logger.info("Testing 'godri sheets versions list' command...")
        
        if not self.test_spreadsheet_id:
            logger.warning("No test spreadsheet ID available")
            return False
        
        try:
            result = self.run_cli_command([
                "sheets", "versions", "list",
                self.test_spreadsheet_id
            ])
            
            # Check command executed successfully
            if result["returncode"] != 0:
                logger.error(f"Command failed: {result['stderr']}")
                return False
            
            # Verify output contains version information
            output = result["stdout"]
            if "versions" not in output.lower() and "revision" not in output.lower():
                logger.error("Output doesn't contain version information")
                return False
            
            logger.info("✅ Sheets versions list command successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sheets versions list command test failed: {e}")
            return False

    def test_version_comparison_commands(self):
        """Test version comparison commands."""
        logger.info("Testing version comparison commands...")
        
        # We'll test with placeholder revision IDs since we may not have multiple versions
        # In a real test environment, you would use actual revision IDs
        
        try:
            # Test slides comparison help
            result = self.run_cli_command([
                "slides", "versions", "compare", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Slides compare help command failed")
                return False
            
            # Test docs comparison help
            result = self.run_cli_command([
                "docs", "versions", "compare", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Docs compare help command failed")
                return False
            
            # Test sheets comparison help
            result = self.run_cli_command([
                "sheets", "versions", "compare", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Sheets compare help command failed")
                return False
            
            logger.info("✅ Version comparison commands help successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Version comparison commands test failed: {e}")
            return False

    def test_version_download_commands(self):
        """Test version download commands."""
        logger.info("Testing version download commands...")
        
        try:
            # Test slides download help
            result = self.run_cli_command([
                "slides", "versions", "download", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Slides download help command failed")
                return False
            
            # Test docs download help
            result = self.run_cli_command([
                "docs", "versions", "download", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Docs download help command failed")
                return False
            
            # Test sheets download help
            result = self.run_cli_command([
                "sheets", "versions", "download", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Sheets download help command failed")
                return False
            
            logger.info("✅ Version download commands help successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Version download commands test failed: {e}")
            return False

    def test_keep_forever_commands(self):
        """Test keep forever commands."""
        logger.info("Testing keep forever commands...")
        
        try:
            # Test slides keep-forever help
            result = self.run_cli_command([
                "slides", "versions", "keep-forever", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Slides keep-forever help command failed")
                return False
            
            # Test docs keep-forever help
            result = self.run_cli_command([
                "docs", "versions", "keep-forever", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Docs keep-forever help command failed")
                return False
            
            # Test sheets keep-forever help
            result = self.run_cli_command([
                "sheets", "versions", "keep-forever", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Sheets keep-forever help command failed")
                return False
            
            logger.info("✅ Keep forever commands help successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Keep forever commands test failed: {e}")
            return False

    def test_general_help_commands(self):
        """Test help commands for version functionality."""
        logger.info("Testing general help commands...")
        
        try:
            # Test main slides versions help
            result = self.run_cli_command([
                "slides", "versions", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Slides versions help failed")
                return False
            
            output = result["stdout"]
            expected_commands = ["list", "get", "download", "compare", "keep-forever"]
            for cmd in expected_commands:
                if cmd not in output:
                    logger.error(f"Missing {cmd} command in slides versions help")
                    return False
            
            # Test main docs versions help
            result = self.run_cli_command([
                "docs", "versions", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Docs versions help failed")
                return False
            
            # Test main sheets versions help
            result = self.run_cli_command([
                "sheets", "versions", "--help"
            ])
            
            if result["returncode"] != 0:
                logger.error("Sheets versions help failed")
                return False
            
            logger.info("✅ General help commands successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ General help commands test failed: {e}")
            return False

    def cleanup(self):
        """Clean up test files."""
        logger.info("Cleaning up test files...")
        
        try:
            # Delete test files using CLI
            if self.test_presentation_id:
                result = self.run_cli_command([
                    "drive", "delete", self.test_presentation_id
                ])
                if result["returncode"] == 0:
                    logger.info(f"Deleted test presentation: {self.test_presentation_id}")
                else:
                    logger.warning(f"Failed to delete presentation: {result['stderr']}")
            
            if self.test_document_id:
                result = self.run_cli_command([
                    "drive", "delete", self.test_document_id
                ])
                if result["returncode"] == 0:
                    logger.info(f"Deleted test document: {self.test_document_id}")
                else:
                    logger.warning(f"Failed to delete document: {result['stderr']}")
            
            if self.test_spreadsheet_id:
                result = self.run_cli_command([
                    "drive", "delete", self.test_spreadsheet_id
                ])
                if result["returncode"] == 0:
                    logger.info(f"Deleted test spreadsheet: {self.test_spreadsheet_id}")
                else:
                    logger.warning(f"Failed to delete spreadsheet: {result['stderr']}")
            
            logger.info("✅ CLI cleanup completed")
            
        except Exception as e:
            logger.warning(f"⚠️ CLI cleanup encountered errors: {e}")

    def run_all_tests(self):
        """Run all CLI version management tests."""
        logger.info("🚀 Starting CLI Version Management E2E Tests")
        
        total_tests = 0
        passed_tests = 0
        
        try:
            # Create test files
            if not self.create_test_files():
                logger.error("❌ Test file creation failed - continuing with available files")
            
            # Define all tests
            tests = [
                ("General Help Commands", self.test_general_help_commands),
                ("Slides Versions List Command", self.test_slides_versions_list_command),
                ("Docs Versions List Command", self.test_docs_versions_list_command),
                ("Sheets Versions List Command", self.test_sheets_versions_list_command),
                ("Version Comparison Commands", self.test_version_comparison_commands),
                ("Version Download Commands", self.test_version_download_commands),
                ("Keep Forever Commands", self.test_keep_forever_commands),
            ]
            
            # Run each test
            for test_name, test_func in tests:
                total_tests += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*60}")
                
                try:
                    if test_func():
                        passed_tests += 1
                        logger.info(f"✅ {test_name}: PASSED")
                    else:
                        logger.error(f"❌ {test_name}: FAILED")
                except Exception as e:
                    logger.error(f"❌ {test_name}: FAILED with exception: {e}")
        
        finally:
            # Always cleanup
            self.cleanup()
        
        # Results summary
        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 CLI Test Results Summary")
        logger.info(f"{'='*60}")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success rate: {(passed_tests / total_tests * 100):.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL CLI TESTS PASSED!")
            return True
        else:
            logger.error(f"💥 {total_tests - passed_tests} CLI TESTS FAILED")
            return False


def main():
    """Main test execution function."""
    test_runner = CLIVersionCommandsE2ETests()
    success = test_runner.run_all_tests()
    
    if success:
        logger.info("✅ CLI Version Management E2E Tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ CLI Version Management E2E Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()