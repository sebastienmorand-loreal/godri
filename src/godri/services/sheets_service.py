"""Google Sheets service wrapper."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from ..commons.api.google_api_client import GoogleApiClient
from ..commons.api.sheets_api import SheetsApiClient
from ..commons.api.drive_api import DriveApiClient
from .auth_service_new import AuthService


class SheetsService:
    """Google Sheets operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.sheets_api = None
        self.drive_api = None

    async def initialize(self):
        """Initialize the Sheets service."""
        credentials = await self.auth_service.authenticate()
        if not credentials:
            raise ValueError("Failed to authenticate with Google Sheets")

        api_client = GoogleApiClient(credentials)
        await api_client.initialize()
        self.sheets_api = SheetsApiClient(api_client)
        self.drive_api = DriveApiClient(api_client)
        self.logger.info("Sheets service initialized")

    async def create_spreadsheet(
        self, title: str, folder_id: Optional[str] = None, sheet_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Google Spreadsheet."""
        self.logger.info("Creating spreadsheet: %s", title)

        spreadsheet = await self.sheets_api.create_spreadsheet(title, folder_id, sheet_names)
        spreadsheet_id = spreadsheet.get("spreadsheetId")

        self.logger.info("Spreadsheet created successfully: %s", spreadsheet_id)
        return spreadsheet

    async def get_spreadsheet(self, spreadsheet_id: str, include_grid_data: bool = False) -> Dict[str, Any]:
        """Get spreadsheet metadata."""
        self.logger.info("Getting spreadsheet: %s", spreadsheet_id)

        spreadsheet = await self.sheets_api.get_spreadsheet(spreadsheet_id, include_grid_data)
        return spreadsheet

    async def get_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        value_render_option: str = "FORMATTED_VALUE",
        date_time_render_option: str = "SERIAL_NUMBER",
    ) -> List[List[str]]:
        """Get values from a specific range."""
        self.logger.info("Getting values from range: %s in spreadsheet: %s", range_name, spreadsheet_id)

        values = await self.sheets_api.get_values(
            spreadsheet_id, range_name, value_render_option, date_time_render_option
        )
        self.logger.info("Retrieved %d rows of data", len(values))
        return values

    async def update_values(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """Update values in a specific range."""
        self.logger.info("Updating values in range: %s", range_name)

        result = await self.sheets_api.update_values(spreadsheet_id, range_name, values, value_input_option)
        self.logger.info("Updated %d cells", result.get("updatedCells", 0))
        return result

    async def append_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
        insert_data_option: str = "INSERT_ROWS",
    ) -> Dict[str, Any]:
        """Append values to a sheet."""
        self.logger.info("Appending values to range: %s", range_name)

        result = await self.sheets_api.append_values(
            spreadsheet_id, range_name, values, value_input_option, insert_data_option
        )
        self.logger.info("Appended data successfully")
        return result

    async def batch_get_values(
        self, spreadsheet_id: str, ranges: List[str], value_render_option: str = "FORMATTED_VALUE"
    ) -> List[Dict[str, Any]]:
        """Get values from multiple ranges."""
        self.logger.info("Getting values from %d ranges", len(ranges))

        result = await self.sheets_api.batch_get_values(spreadsheet_id, ranges, value_render_option)
        self.logger.info("Retrieved data from %d ranges", len(result))
        return result

    async def batch_update_values(
        self, spreadsheet_id: str, value_ranges: List[Dict[str, Any]], value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """Update multiple ranges of values."""
        self.logger.info("Batch updating %d ranges", len(value_ranges))

        result = await self.sheets_api.batch_update_values(spreadsheet_id, value_ranges, value_input_option)
        self.logger.info("Batch update completed successfully")
        return result

    async def clear_values(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Clear values in a range."""
        self.logger.info("Clearing values in range: %s", range_name)

        result = await self.sheets_api.clear_values(spreadsheet_id, range_name)
        self.logger.info("Values cleared successfully")
        return result

    async def add_sheet(
        self,
        spreadsheet_id: str,
        title: str,
        index: Optional[int] = None,
        row_count: int = 1000,
        column_count: int = 26,
    ) -> Dict[str, Any]:
        """Add a new sheet to spreadsheet."""
        self.logger.info("Adding sheet '%s' to spreadsheet: %s", title, spreadsheet_id)

        result = await self.sheets_api.add_sheet(spreadsheet_id, title, index, row_count, column_count)
        self.logger.info("Sheet added successfully: %s", title)
        return result

    async def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        """Delete a sheet from spreadsheet."""
        self.logger.info("Deleting sheet %d from spreadsheet: %s", sheet_id, spreadsheet_id)

        result = await self.sheets_api.delete_sheet(spreadsheet_id, sheet_id)
        self.logger.info("Sheet deleted successfully")
        return result

    async def copy_sheet_to(
        self, source_spreadsheet_id: str, sheet_id: int, destination_spreadsheet_id: str
    ) -> Dict[str, Any]:
        """Copy sheet to another spreadsheet."""
        self.logger.info("Copying sheet %d from %s to %s", sheet_id, source_spreadsheet_id, destination_spreadsheet_id)

        result = await self.sheets_api.copy_sheet_to(source_spreadsheet_id, sheet_id, destination_spreadsheet_id)
        self.logger.info("Sheet copied successfully")
        return result

    async def format_cells(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_column: int,
        end_column: int,
        cell_format: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format cells in a range."""
        self.logger.info("Formatting cells in sheet %d", sheet_id)

        result = await self.sheets_api.format_cells(
            spreadsheet_id, sheet_id, start_row, end_row, start_column, end_column, cell_format
        )
        self.logger.info("Cells formatted successfully")
        return result

    async def set_column_width(
        self, spreadsheet_id: str, sheet_id: int, start_column: int, end_column: int, width: int
    ) -> Dict[str, Any]:
        """Set column width."""
        self.logger.info("Setting column width for columns %d-%d", start_column, end_column)

        result = await self.sheets_api.set_column_width(spreadsheet_id, sheet_id, start_column, end_column, width)
        self.logger.info("Column width set successfully")
        return result

    async def set_row_height(
        self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, height: int
    ) -> Dict[str, Any]:
        """Set row height."""
        self.logger.info("Setting row height for rows %d-%d", start_row, end_row)

        result = await self.sheets_api.set_row_height(spreadsheet_id, sheet_id, start_row, end_row, height)
        self.logger.info("Row height set successfully")
        return result

    async def translate_range(
        self, spreadsheet_id: str, range_name: str, target_language: str, source_language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Translate text in a range of cells."""
        self.logger.info("Translating range %s to %s", range_name, target_language)

        result = await self.sheets_api.translate_range(spreadsheet_id, range_name, target_language, source_language)

        if result:
            self.logger.info("Range translated successfully")
        else:
            self.logger.warning("Translation failed or no translatable content found")

        return result

    async def copy_paste(
        self,
        spreadsheet_id: str,
        source_sheet_id: int,
        source_start_row: int,
        source_end_row: int,
        source_start_col: int,
        source_end_col: int,
        dest_sheet_id: int,
        dest_start_row: int,
        dest_start_col: int,
        paste_type: str = "PASTE_NORMAL",
    ) -> Dict[str, Any]:
        """Copy and paste data between ranges."""
        self.logger.info("Copying data from sheet %d to sheet %d", source_sheet_id, dest_sheet_id)

        result = await self.sheets_api.copy_paste(
            spreadsheet_id,
            source_sheet_id,
            source_start_row,
            source_end_row,
            source_start_col,
            source_end_col,
            dest_sheet_id,
            dest_start_row,
            dest_start_col,
            paste_type,
        )
        self.logger.info("Copy paste operation completed successfully")
        return result

    async def insert_rows(self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int) -> Dict[str, Any]:
        """Insert rows in a sheet."""
        self.logger.info("Inserting rows %d-%d in sheet %d", start_index, end_index, sheet_id)

        result = await self.sheets_api.insert_rows(spreadsheet_id, sheet_id, start_index, end_index)
        self.logger.info("Rows inserted successfully")
        return result

    async def insert_columns(
        self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int
    ) -> Dict[str, Any]:
        """Insert columns in a sheet."""
        self.logger.info("Inserting columns %d-%d in sheet %d", start_index, end_index, sheet_id)

        result = await self.sheets_api.insert_columns(spreadsheet_id, sheet_id, start_index, end_index)
        self.logger.info("Columns inserted successfully")
        return result

    async def delete_rows(self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int) -> Dict[str, Any]:
        """Delete rows from a sheet."""
        self.logger.info("Deleting rows %d-%d from sheet %d", start_index, end_index, sheet_id)

        result = await self.sheets_api.delete_rows(spreadsheet_id, sheet_id, start_index, end_index)
        self.logger.info("Rows deleted successfully")
        return result

    async def delete_columns(
        self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int
    ) -> Dict[str, Any]:
        """Delete columns from a sheet."""
        self.logger.info("Deleting columns %d-%d from sheet %d", start_index, end_index, sheet_id)

        result = await self.sheets_api.delete_columns(spreadsheet_id, sheet_id, start_index, end_index)
        self.logger.info("Columns deleted successfully")
        return result

    async def batch_update(self, spreadsheet_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch updates on spreadsheet."""
        self.logger.info("Executing batch update with %d requests", len(requests))

        result = await self.sheets_api.batch_update(spreadsheet_id, requests)
        self.logger.info("Batch update completed successfully")
        return result

    # Version Management Methods

    async def list_spreadsheet_versions(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """List all versions/revisions of a spreadsheet."""
        self.logger.info("Listing versions for spreadsheet: %s", spreadsheet_id)

        try:
            result = await self.drive_api.list_file_revisions(spreadsheet_id)
            revisions = result.get("revisions", [])

            # Enhance revision data with spreadsheet-specific information
            for revision in revisions:
                revision["file_type"] = "spreadsheet"
                revision["mime_type"] = revision.get("mimeType", "application/vnd.google-apps.spreadsheet")

            self.logger.info("Found %d versions for spreadsheet %s", len(revisions), spreadsheet_id)
            return revisions

        except Exception as e:
            self.logger.error("Failed to list spreadsheet versions: %s", e)
            raise

    async def get_spreadsheet_version(self, spreadsheet_id: str, revision_id: str) -> Dict[str, Any]:
        """Get metadata for a specific spreadsheet version."""
        self.logger.info("Getting version %s for spreadsheet: %s", revision_id, spreadsheet_id)

        try:
            revision = await self.drive_api.get_file_revision(spreadsheet_id, revision_id)
            revision["file_type"] = "spreadsheet"
            revision["mime_type"] = revision.get("mimeType", "application/vnd.google-apps.spreadsheet")

            self.logger.info("Retrieved version metadata for %s", revision_id)
            return revision

        except Exception as e:
            self.logger.error("Failed to get spreadsheet version: %s", e)
            raise

    async def download_spreadsheet_version(
        self, spreadsheet_id: str, revision_id: str, output_path: str, format_type: str = "xlsx"
    ) -> str:
        """Download a specific version of a spreadsheet in the specified format."""
        self.logger.info("Downloading version %s of spreadsheet %s as %s", revision_id, spreadsheet_id, format_type)

        try:
            # Map format types to MIME types
            format_mime_types = {
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "pdf": "application/pdf",
                "csv": "text/csv",
                "tsv": "text/tab-separated-values",
                "html": "text/html",
                "ods": "application/vnd.oasis.opendocument.spreadsheet",
                "zip": "application/zip",
            }

            if format_type not in format_mime_types:
                raise ValueError(f"Unsupported format: {format_type}. Supported: {list(format_mime_types.keys())}")

            export_mime_type = format_mime_types[format_type]

            # Ensure output path has correct extension
            output_path_obj = Path(output_path)
            if not output_path_obj.suffix == f".{format_type}":
                output_path = str(output_path_obj.with_suffix(f".{format_type}"))

            result_path = await self.drive_api.export_file_revision(
                spreadsheet_id, revision_id, export_mime_type, output_path
            )

            self.logger.info("Version downloaded successfully to: %s", result_path)
            return result_path

        except Exception as e:
            self.logger.error("Failed to download spreadsheet version: %s", e)
            raise

    async def compare_spreadsheet_versions(
        self, spreadsheet_id: str, revision_id_1: str, revision_id_2: str, output_dir: str = "/tmp"
    ) -> Dict[str, Any]:
        """Compare two versions of a spreadsheet and return detailed diff analysis."""
        self.logger.info("Comparing spreadsheet %s versions %s vs %s", spreadsheet_id, revision_id_1, revision_id_2)

        try:
            import json
            import tempfile
            import csv

            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Download both versions as CSV for comparison
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Download version 1 as CSV
                v1_path = temp_path / f"v1_{revision_id_1}.csv"
                await self.download_spreadsheet_version(spreadsheet_id, revision_id_1, str(v1_path), "csv")

                # Download version 2 as CSV
                v2_path = temp_path / f"v2_{revision_id_2}.csv"
                await self.download_spreadsheet_version(spreadsheet_id, revision_id_2, str(v2_path), "csv")

                # Read the CSV content
                with open(v1_path, "r", encoding="utf-8") as f:
                    v1_reader = csv.reader(f)
                    v1_data = list(v1_reader)

                with open(v2_path, "r", encoding="utf-8") as f:
                    v2_reader = csv.reader(f)
                    v2_data = list(v2_reader)

                # Get revision metadata
                v1_metadata = await self.get_spreadsheet_version(spreadsheet_id, revision_id_1)
                v2_metadata = await self.get_spreadsheet_version(spreadsheet_id, revision_id_2)

                # Perform diff analysis
                diff_result = await self._perform_spreadsheet_diff(v1_data, v2_data, v1_metadata, v2_metadata)

                # Save comparison result
                comparison_file = output_dir / f"comparison_{revision_id_1}_vs_{revision_id_2}.json"
                with open(comparison_file, "w", encoding="utf-8") as f:
                    json.dump(diff_result, f, indent=2, default=str)

                self.logger.info("Comparison completed successfully. Results saved to: %s", comparison_file)
                return diff_result

        except Exception as e:
            self.logger.error("Failed to compare spreadsheet versions: %s", e)
            raise

    async def _perform_spreadsheet_diff(
        self,
        v1_data: List[List[str]],
        v2_data: List[List[str]],
        v1_metadata: Dict[str, Any],
        v2_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform detailed diff analysis between two spreadsheet contents."""
        try:
            from datetime import datetime

            diff_result = {
                "comparison_summary": {
                    "version_1": {
                        "revision_id": v1_metadata["id"],
                        "modified_time": v1_metadata.get("modifiedTime"),
                        "size": v1_metadata.get("size"),
                        "last_modifying_user": v1_metadata.get("lastModifyingUser", {}).get("displayName"),
                        "row_count": len(v1_data),
                        "column_count": max(len(row) for row in v1_data) if v1_data else 0,
                    },
                    "version_2": {
                        "revision_id": v2_metadata["id"],
                        "modified_time": v2_metadata.get("modifiedTime"),
                        "size": v2_metadata.get("size"),
                        "last_modifying_user": v2_metadata.get("lastModifyingUser", {}).get("displayName"),
                        "row_count": len(v2_data),
                        "column_count": max(len(row) for row in v2_data) if v2_data else 0,
                    },
                },
                "changes": {
                    "row_count_change": len(v2_data) - len(v1_data),
                    "column_count_change": (max(len(row) for row in v2_data) if v2_data else 0)
                    - (max(len(row) for row in v1_data) if v1_data else 0),
                    "size_change": None,
                    "time_difference": None,
                },
                "detailed_analysis": {
                    "added_rows": [],
                    "deleted_rows": [],
                    "modified_cells": [],
                    "summary": {},
                },
            }

            # Calculate basic differences
            v1_size = int(v1_metadata.get("size", "0"))
            v2_size = int(v2_metadata.get("size", "0"))
            diff_result["changes"]["size_change"] = v2_size - v1_size

            # Parse modification times
            try:
                v1_time = datetime.fromisoformat(v1_metadata["modifiedTime"].replace("Z", "+00:00"))
                v2_time = datetime.fromisoformat(v2_metadata["modifiedTime"].replace("Z", "+00:00"))
                time_diff = v2_time - v1_time
                diff_result["changes"]["time_difference"] = str(time_diff)
            except (ValueError, TypeError, KeyError):
                diff_result["changes"]["time_difference"] = "Unable to calculate"

            # Analyze cell-by-cell differences
            max_rows = max(len(v1_data), len(v2_data))
            max_cols = max(
                max(len(row) for row in v1_data) if v1_data else 0, max(len(row) for row in v2_data) if v2_data else 0
            )

            cell_changes = 0
            for row_idx in range(max_rows):
                v1_row = v1_data[row_idx] if row_idx < len(v1_data) else []
                v2_row = v2_data[row_idx] if row_idx < len(v2_data) else []

                for col_idx in range(max_cols):
                    v1_cell = v1_row[col_idx] if col_idx < len(v1_row) else ""
                    v2_cell = v2_row[col_idx] if col_idx < len(v2_row) else ""

                    if v1_cell != v2_cell:
                        cell_changes += 1
                        diff_result["detailed_analysis"]["modified_cells"].append(
                            {
                                "row": row_idx + 1,  # 1-based indexing for user readability
                                "column": col_idx + 1,
                                "old_value": v1_cell,
                                "new_value": v2_cell,
                            }
                        )

            # Detect added/deleted rows
            if len(v2_data) > len(v1_data):
                for row_idx in range(len(v1_data), len(v2_data)):
                    diff_result["detailed_analysis"]["added_rows"].append(
                        {
                            "row": row_idx + 1,
                            "content": v2_data[row_idx] if row_idx < len(v2_data) else [],
                        }
                    )

            if len(v1_data) > len(v2_data):
                for row_idx in range(len(v2_data), len(v1_data)):
                    diff_result["detailed_analysis"]["deleted_rows"].append(
                        {
                            "row": row_idx + 1,
                            "content": v1_data[row_idx] if row_idx < len(v1_data) else [],
                        }
                    )

            diff_result["detailed_analysis"]["summary"] = {
                "total_cell_changes": cell_changes,
                "rows_added": len(diff_result["detailed_analysis"]["added_rows"]),
                "rows_deleted": len(diff_result["detailed_analysis"]["deleted_rows"]),
            }

            return diff_result

        except Exception as e:
            self.logger.error("Failed to perform spreadsheet diff: %s", e)
            raise

    async def keep_spreadsheet_version_forever(
        self, spreadsheet_id: str, revision_id: str, keep_forever: bool = True
    ) -> Dict[str, Any]:
        """Mark a spreadsheet version to be kept forever or allow auto-deletion."""
        self.logger.info(
            "Setting keepForever=%s for version %s of spreadsheet %s", keep_forever, revision_id, spreadsheet_id
        )

        try:
            result = await self.drive_api.keep_file_revision_forever(spreadsheet_id, revision_id, keep_forever)
            self.logger.info("Version %s keepForever updated to %s", revision_id, keep_forever)
            return result

        except Exception as e:
            self.logger.error("Failed to update version keep forever setting: %s", e)
            raise

    async def restore_spreadsheet_version(self, spreadsheet_id: str, revision_id: str) -> Dict[str, Any]:
        """Restore a spreadsheet to a specific revision by creating a new file with the old content."""
        self.logger.info("Restoring spreadsheet %s to revision %s", spreadsheet_id, revision_id)

        try:
            result = await self.drive_api.restore_file_revision(spreadsheet_id, revision_id)

            # Enhanced result with spreadsheet-specific information
            result["file_type"] = "spreadsheet"
            result["original_spreadsheet_id"] = spreadsheet_id

            self.logger.info(
                "Successfully restored spreadsheet. New file: %s (ID: %s)",
                result.get("restored_file_name"),
                result.get("restored_file_id"),
            )
            return result

        except Exception as e:
            self.logger.error("Failed to restore spreadsheet version: %s", e)
            raise
