"""Google Sheets service wrapper."""

import logging
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
