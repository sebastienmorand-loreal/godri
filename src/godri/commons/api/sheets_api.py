"""Google Sheets API wrapper using aiogoogle for full async operations."""

import logging
from typing import Optional, Dict, Any, List, Union

from .google_api_client import GoogleApiClient


class SheetsApiClient:
    """Async Google Sheets API client using aiogoogle."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Sheets API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self._service = None

    async def _get_service(self):
        """Get or create Sheets service."""
        if self._service is None:
            self._service = await self.api_client.discover_service("sheets", "v4")
        return self._service

    async def get_spreadsheet(
        self, spreadsheet_id: str, ranges: Optional[List[str]] = None, include_grid_data: bool = False
    ) -> Dict[str, Any]:
        """Get spreadsheet metadata and data.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            ranges: Optional list of ranges to include
            include_grid_data: Whether to include grid data

        Returns:
            Spreadsheet data
        """
        service = await self._get_service()

        params = {"spreadsheetId": spreadsheet_id, "includeGridData": include_grid_data}

        if ranges:
            params["ranges"] = ranges

        return await self.api_client.execute_request(service, "spreadsheets.get", **params)

    async def create_spreadsheet(self, title: str, sheets: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a new spreadsheet.

        Args:
            title: Spreadsheet title
            sheets: Optional list of sheet definitions

        Returns:
            Created spreadsheet metadata
        """
        service = await self._get_service()

        body = {"properties": {"title": title}}

        if sheets:
            body["sheets"] = sheets

        return await self.api_client.execute_request(service, "spreadsheets.create", body=body)

    async def get_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        value_render_option: str = "FORMATTED_VALUE",
        date_time_render_option: str = "SERIAL_NUMBER",
        major_dimension: str = "ROWS",
    ) -> Dict[str, Any]:
        """Get values from a range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: Range in A1 notation
            value_render_option: How values should be rendered
            date_time_render_option: How date/time values should be rendered
            major_dimension: Major dimension for values

        Returns:
            Values data
        """
        service = await self._get_service()

        return await self.api_client.execute_request(
            service,
            "spreadsheets.values.get",
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueRenderOption=value_render_option,
            dateTimeRenderOption=date_time_render_option,
            majorDimension=major_dimension,
        )

    async def update_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "RAW",
        major_dimension: str = "ROWS",
    ) -> Dict[str, Any]:
        """Update values in a range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: Range in A1 notation
            values: 2D array of values
            value_input_option: How values should be interpreted (RAW or USER_ENTERED)
            major_dimension: Major dimension for values

        Returns:
            Update response
        """
        service = await self._get_service()

        body = {"values": values, "majorDimension": major_dimension}

        return await self.api_client.execute_request(
            service,
            "spreadsheets.values.update",
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body,
        )

    async def batch_get_values(
        self, spreadsheet_id: str, ranges: List[str], value_render_option: str = "FORMATTED_VALUE"
    ) -> Dict[str, Any]:
        """Get values from multiple ranges.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            ranges: List of ranges in A1 notation
            value_render_option: How values should be rendered

        Returns:
            Batch values response
        """
        service = await self._get_service()

        return await self.api_client.execute_request(
            service,
            "spreadsheets.values.batchGet",
            spreadsheetId=spreadsheet_id,
            ranges=ranges,
            valueRenderOption=value_render_option,
        )

    async def batch_update_values(
        self, spreadsheet_id: str, value_ranges: List[Dict[str, Any]], value_input_option: str = "RAW"
    ) -> Dict[str, Any]:
        """Update values in multiple ranges.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            value_ranges: List of value range objects
            value_input_option: How values should be interpreted

        Returns:
            Batch update response
        """
        service = await self._get_service()

        body = {"valueInputOption": value_input_option, "data": value_ranges}

        return await self.api_client.execute_request(
            service, "spreadsheets.values.batchUpdate", spreadsheetId=spreadsheet_id, body=body
        )

    async def append_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "RAW",
        insert_data_option: str = "OVERWRITE",
    ) -> Dict[str, Any]:
        """Append values to a range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: Range in A1 notation
            values: 2D array of values to append
            value_input_option: How values should be interpreted
            insert_data_option: How to insert new data

        Returns:
            Append response
        """
        service = await self._get_service()

        body = {"values": values, "majorDimension": "ROWS"}

        return await self.api_client.execute_request(
            service,
            "spreadsheets.values.append",
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option,
            body=body,
        )

    async def clear_values(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Clear values in a range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: Range in A1 notation

        Returns:
            Clear response
        """
        service = await self._get_service()

        return await self.api_client.execute_request(
            service, "spreadsheets.values.clear", spreadsheetId=spreadsheet_id, range=range_name, body={}
        )

    async def batch_update(self, spreadsheet_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            requests: List of update requests

        Returns:
            Update response
        """
        service = await self._get_service()

        body = {"requests": requests}

        return await self.api_client.execute_request(
            service, "spreadsheets.batchUpdate", spreadsheetId=spreadsheet_id, body=body
        )

    async def copy_to(self, spreadsheet_id: str, sheet_id: int, destination_spreadsheet_id: str) -> Dict[str, Any]:
        """Copy sheet to another spreadsheet.

        Args:
            spreadsheet_id: Source spreadsheet ID
            sheet_id: Source sheet ID
            destination_spreadsheet_id: Target spreadsheet ID

        Returns:
            Copy response
        """
        service = await self._get_service()

        body = {"destinationSpreadsheetId": destination_spreadsheet_id}

        return await self.api_client.execute_request(
            service, "spreadsheets.sheets.copyTo", spreadsheetId=spreadsheet_id, sheetId=sheet_id, body=body
        )

    async def add_sheet(self, spreadsheet_id: str, title: str, index: Optional[int] = None) -> Dict[str, Any]:
        """Add a new sheet to the spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            title: Sheet title
            index: Sheet index position

        Returns:
            Add sheet response
        """
        properties = {"title": title}
        if index is not None:
            properties["index"] = index

        requests = [{"addSheet": {"properties": properties}}]

        return await self.batch_update(spreadsheet_id, requests)

    async def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        """Delete a sheet from the spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_id: Sheet ID to delete

        Returns:
            Delete sheet response
        """
        requests = [{"deleteSheet": {"sheetId": sheet_id}}]

        return await self.batch_update(spreadsheet_id, requests)

    async def duplicate_sheet(
        self, spreadsheet_id: str, source_sheet_id: int, new_sheet_name: str, insert_sheet_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Duplicate a sheet within the spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            source_sheet_id: Source sheet ID to duplicate
            new_sheet_name: Name for the new sheet
            insert_sheet_index: Index where to insert the new sheet

        Returns:
            Duplicate sheet response
        """
        request = {"duplicateSheet": {"sourceSheetId": source_sheet_id, "newSheetName": new_sheet_name}}

        if insert_sheet_index is not None:
            request["duplicateSheet"]["insertSheetIndex"] = insert_sheet_index

        requests = [request]

        return await self.batch_update(spreadsheet_id, requests)

    async def format_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        format_options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format a range of cells.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: Range in A1 notation
            format_options: Cell format options

        Returns:
            Format response
        """
        # Convert A1 notation to grid range
        grid_range = self._a1_to_grid_range(range_name)

        requests = [{"repeatCell": {"range": grid_range, "cell": {"userEnteredFormat": format_options}, "fields": "*"}}]

        return await self.batch_update(spreadsheet_id, requests)

    async def set_column_width(
        self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int, width: int
    ) -> Dict[str, Any]:
        """Set column width for a range of columns.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_id: Sheet ID
            start_index: Start column index (0-based)
            end_index: End column index (0-based, exclusive)
            width: Column width in pixels

        Returns:
            Update response
        """
        requests = [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": start_index,
                        "endIndex": end_index,
                    },
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    async def set_row_height(
        self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int, height: int
    ) -> Dict[str, Any]:
        """Set row height for a range of rows.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_id: Sheet ID
            start_index: Start row index (0-based)
            end_index: End row index (0-based, exclusive)
            height: Row height in pixels

        Returns:
            Update response
        """
        requests = [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": start_index,
                        "endIndex": end_index,
                    },
                    "properties": {"pixelSize": height},
                    "fields": "pixelSize",
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    def _a1_to_grid_range(self, range_name: str) -> Dict[str, Any]:
        """Convert A1 notation to grid range format.

        Args:
            range_name: Range in A1 notation (e.g., "A1:B2", "Sheet1!A1:B2")

        Returns:
            Grid range dictionary
        """
        # Basic implementation - this could be more sophisticated
        parts = range_name.split("!")
        if len(parts) == 2:
            sheet_name, cell_range = parts
        else:
            sheet_name = None
            cell_range = parts[0]

        # Parse cell range (simplified implementation)
        if ":" in cell_range:
            start_cell, end_cell = cell_range.split(":")
        else:
            start_cell = end_cell = cell_range

        # Convert to grid coordinates (this is a simplified implementation)
        grid_range = {}
        if sheet_name:
            # Would need to look up sheet ID from sheet name
            pass

        return grid_range
