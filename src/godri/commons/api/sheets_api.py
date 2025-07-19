"""Google Sheets API wrapper using async HTTP client."""

import logging
from typing import Optional, Dict, Any, List
from .google_api_client import GoogleApiClient


class SheetsApiClient:
    """Async Google Sheets API client."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Sheets API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.base_url = "/sheets/v4"

    async def get_spreadsheet(self, spreadsheet_id: str, ranges: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get spreadsheet metadata and data.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            ranges: Optional list of ranges to include

        Returns:
            Spreadsheet data
        """
        params = {}
        if ranges:
            params["ranges"] = ranges

        return await self.api_client.get(f"{self.base_url}/spreadsheets/{spreadsheet_id}", params=params)

    async def create_spreadsheet(self, title: str) -> Dict[str, Any]:
        """Create a new spreadsheet.

        Args:
            title: Spreadsheet title

        Returns:
            Created spreadsheet metadata
        """
        body = {"properties": {"title": title}}
        return await self.api_client.post(f"{self.base_url}/spreadsheets", json_data=body)

    async def get_values(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Get values from a range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: Range in A1 notation

        Returns:
            Values data
        """
        return await self.api_client.get(f"{self.base_url}/spreadsheets/{spreadsheet_id}/values/{range_name}")

    async def update_values(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "RAW"
    ) -> Dict[str, Any]:
        """Update values in a range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: Range in A1 notation
            values: 2D array of values
            value_input_option: How values should be interpreted (RAW or USER_ENTERED)

        Returns:
            Update response
        """
        body = {"values": values, "majorDimension": "ROWS"}
        params = {"valueInputOption": value_input_option}

        return await self.api_client.put(
            f"{self.base_url}/spreadsheets/{spreadsheet_id}/values/{range_name}", json_data=body, params=params
        )

    async def batch_update(self, spreadsheet_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch update on spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            requests: List of update requests

        Returns:
            Update response
        """
        body = {"requests": requests}
        return await self.api_client.post(f"{self.base_url}/spreadsheets/{spreadsheet_id}:batchUpdate", json_data=body)

    async def copy_to(self, spreadsheet_id: str, sheet_id: int, destination_spreadsheet_id: str) -> Dict[str, Any]:
        """Copy sheet to another spreadsheet.

        Args:
            spreadsheet_id: Source spreadsheet ID
            sheet_id: Source sheet ID
            destination_spreadsheet_id: Target spreadsheet ID

        Returns:
            Copy response
        """
        body = {"destinationSpreadsheetId": destination_spreadsheet_id}
        return await self.api_client.post(
            f"{self.base_url}/spreadsheets/{spreadsheet_id}/sheets/{sheet_id}:copyTo", json_data=body
        )
