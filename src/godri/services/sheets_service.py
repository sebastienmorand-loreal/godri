"""Google Sheets service wrapper."""

import logging
from typing import Dict, Any, List, Optional, Union
from .auth_service import AuthService


class SheetsService:
    """Google Sheets operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.service = None
        self.drive_service = None

    async def initialize(self):
        """Initialize the Sheets service."""
        await self.auth_service.authenticate()
        self.service = self.auth_service.get_service("sheets", "v4")
        self.drive_service = self.auth_service.get_service("drive", "v3")
        self.logger.info("Sheets service initialized")

    def create_spreadsheet(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Google Spreadsheet."""
        self.logger.info("Creating spreadsheet: %s", title)

        spreadsheet_body = {"properties": {"title": title}}

        spreadsheet = self.service.spreadsheets().create(body=spreadsheet_body).execute()

        spreadsheet_id = spreadsheet.get("spreadsheetId")

        if folder_id:
            self.drive_service.files().update(
                fileId=spreadsheet_id, addParents=folder_id, fields="id, parents"
            ).execute()
            self.logger.info("Spreadsheet moved to folder: %s", folder_id)

        self.logger.info("Spreadsheet created successfully: %s", spreadsheet_id)
        return spreadsheet

    def get_spreadsheet(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Get spreadsheet metadata."""
        self.logger.info("Getting spreadsheet: %s", spreadsheet_id)

        spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

        return spreadsheet

    def get_values(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """Get values from a range."""
        self.logger.info("Getting values from %s in spreadsheet: %s", range_name, spreadsheet_id)

        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

        values = result.get("values", [])
        self.logger.info("Retrieved %d rows", len(values))

        return values

    def update_values(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "RAW"
    ) -> Dict[str, Any]:
        """Update values in a range."""
        self.logger.info("Updating values in %s for spreadsheet: %s", range_name, spreadsheet_id)

        body = {"values": values}

        result = (
            self.service.spreadsheets()
            .values()
            .update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption=value_input_option, body=body)
            .execute()
        )

        self.logger.info("Updated %d cells", result.get("updatedCells", 0))
        return result

    def append_values(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "RAW"
    ) -> Dict[str, Any]:
        """Append values to a sheet."""
        self.logger.info("Appending values to %s in spreadsheet: %s", range_name, spreadsheet_id)

        body = {"values": values}

        result = (
            self.service.spreadsheets()
            .values()
            .append(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption=value_input_option, body=body)
            .execute()
        )

        self.logger.info("Appended %d rows", len(values))
        return result

    def clear_values(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Clear values in a range."""
        self.logger.info("Clearing values in %s for spreadsheet: %s", range_name, spreadsheet_id)

        result = self.service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=range_name).execute()

        self.logger.info("Values cleared successfully")
        return result

    def create_sheet(self, spreadsheet_id: str, sheet_title: str) -> Dict[str, Any]:
        """Add a new sheet to spreadsheet."""
        self.logger.info("Creating sheet '%s' in spreadsheet: %s", sheet_title, spreadsheet_id)

        body = {"requests": [{"addSheet": {"properties": {"title": sheet_title}}}]}

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Sheet created successfully")
        return result

    def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        """Delete a sheet from spreadsheet."""
        self.logger.info("Deleting sheet %d from spreadsheet: %s", sheet_id, spreadsheet_id)

        body = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Sheet deleted successfully")
        return result

    def format_cells(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        format_options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format cells in a range."""
        self.logger.info("Formatting cells in spreadsheet: %s", spreadsheet_id)

        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col,
                        },
                        "cell": {"userEnteredFormat": format_options},
                        "fields": "userEnteredFormat",
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Cells formatted successfully")
        return result

    def get_sheet_id_by_name(self, spreadsheet_id: str, sheet_name: str) -> Optional[int]:
        """Get sheet ID by name."""
        spreadsheet = self.get_spreadsheet(spreadsheet_id)

        for sheet in spreadsheet.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                return sheet["properties"]["sheetId"]

        return None

    def set_column_width(
        self, spreadsheet_id: str, sheet_id: int, start_col: int, end_col: int, width: int
    ) -> Dict[str, Any]:
        """Set column width."""
        self.logger.info("Setting column width in spreadsheet: %s", spreadsheet_id)

        body = {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": start_col,
                            "endIndex": end_col,
                        },
                        "properties": {"pixelSize": width},
                        "fields": "pixelSize",
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Column width set successfully")
        return result
