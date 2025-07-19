"""Google Sheets API client with async aiohttp."""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from .google_api_client import GoogleApiClient


class SheetsApiClient:
    """Async Google Sheets API client."""

    def __init__(self, api_client: GoogleApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://sheets.googleapis.com/v4"

    async def create_spreadsheet(
        self, title: str, folder_id: Optional[str] = None, sheet_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Google Spreadsheet."""
        self.logger.info(f"Creating spreadsheet: {title}")

        sheets_data = []
        if sheet_names:
            for i, sheet_name in enumerate(sheet_names):
                sheets_data.append({"properties": {"title": sheet_name, "index": i, "sheetType": "GRID"}})
        else:
            # Default sheet
            sheets_data.append({"properties": {"title": "Sheet1", "index": 0, "sheetType": "GRID"}})

        spreadsheet_metadata = {"properties": {"title": title}, "sheets": sheets_data}

        url = f"{self.base_url}/spreadsheets"
        result = await self.api_client.make_request("POST", url, data=spreadsheet_metadata)

        spreadsheet_id = result.get("spreadsheetId")
        self.logger.info(f"Spreadsheet created successfully: {spreadsheet_id}")

        # If folder_id specified, move spreadsheet to folder using Drive API
        if folder_id:
            drive_url = "https://www.googleapis.com/drive/v3"

            # Get current parents
            file_info_url = f"{drive_url}/files/{spreadsheet_id}"
            file_info = await self.api_client.make_request("GET", file_info_url, params={"fields": "parents"})
            current_parents = file_info.get("parents", [])

            # Move to new folder
            move_url = f"{drive_url}/files/{spreadsheet_id}"
            move_params = {"addParents": folder_id, "removeParents": ",".join(current_parents), "fields": "id, parents"}
            await self.api_client.make_request("PATCH", move_url, params=move_params)
            self.logger.info(f"Spreadsheet moved to folder: {folder_id}")

        return result

    async def get_spreadsheet(self, spreadsheet_id: str, include_grid_data: bool = False) -> Dict[str, Any]:
        """Get spreadsheet metadata and structure."""
        self.logger.info(f"Getting spreadsheet: {spreadsheet_id}")

        params = {"includeGridData": str(include_grid_data).lower()}
        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}"

        return await self.api_client.make_request("GET", url, params=params)

    async def get_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        value_render_option: str = "FORMATTED_VALUE",
        date_time_render_option: str = "SERIAL_NUMBER",
    ) -> List[List[str]]:
        """Get values from a specific range."""
        self.logger.info(f"Getting values from range: {range_name} in spreadsheet: {spreadsheet_id}")

        params = {"valueRenderOption": value_render_option, "dateTimeRenderOption": date_time_render_option}
        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}/values/{range_name}"

        result = await self.api_client.make_request("GET", url, params=params)
        return result.get("values", [])

    async def batch_get_values(
        self, spreadsheet_id: str, ranges: List[str], value_render_option: str = "FORMATTED_VALUE"
    ) -> List[Dict[str, Any]]:
        """Get values from multiple ranges."""
        self.logger.info(f"Getting values from {len(ranges)} ranges in spreadsheet: {spreadsheet_id}")

        params = {"ranges": ranges, "valueRenderOption": value_render_option}
        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}/values:batchGet"

        result = await self.api_client.make_request("GET", url, params=params)
        return result.get("valueRanges", [])

    async def update_values(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]], value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """Update values in a specific range."""
        self.logger.info(f"Updating values in range: {range_name} in spreadsheet: {spreadsheet_id}")

        update_data = {"range": range_name, "majorDimension": "ROWS", "values": values}

        params = {"valueInputOption": value_input_option}
        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}/values/{range_name}"

        return await self.api_client.make_request("PUT", url, params=params, data=update_data)

    async def batch_update_values(
        self, spreadsheet_id: str, value_ranges: List[Dict[str, Any]], value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """Update multiple ranges of values."""
        self.logger.info(f"Batch updating {len(value_ranges)} ranges in spreadsheet: {spreadsheet_id}")

        update_data = {"valueInputOption": value_input_option, "data": value_ranges}

        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}/values:batchUpdate"

        return await self.api_client.make_request("POST", url, data=update_data)

    async def append_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
        insert_data_option: str = "INSERT_ROWS",
    ) -> Dict[str, Any]:
        """Append values to a sheet."""
        self.logger.info(f"Appending values to range: {range_name} in spreadsheet: {spreadsheet_id}")

        append_data = {"range": range_name, "majorDimension": "ROWS", "values": values}

        params = {"valueInputOption": value_input_option, "insertDataOption": insert_data_option}
        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}/values/{range_name}:append"

        return await self.api_client.make_request("POST", url, params=params, data=append_data)

    async def batch_update(self, spreadsheet_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch updates on spreadsheet."""
        self.logger.info(f"Batch updating spreadsheet: {spreadsheet_id} with {len(requests)} requests")

        update_data = {"requests": requests}
        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}:batchUpdate"

        result = await self.api_client.make_request("POST", url, data=update_data)
        self.logger.info(f"Batch update completed successfully")
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
        self.logger.info(f"Adding sheet '{title}' to spreadsheet: {spreadsheet_id}")

        sheet_properties = {
            "title": title,
            "sheetType": "GRID",
            "gridProperties": {"rowCount": row_count, "columnCount": column_count},
        }

        if index is not None:
            sheet_properties["index"] = index

        requests = [{"addSheet": {"properties": sheet_properties}}]

        result = await self.batch_update(spreadsheet_id, requests)
        return result.get("replies", [{}])[0].get("addSheet", {})

    async def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        """Delete a sheet from spreadsheet."""
        self.logger.info(f"Deleting sheet {sheet_id} from spreadsheet: {spreadsheet_id}")

        requests = [{"deleteSheet": {"sheetId": sheet_id}}]

        return await self.batch_update(spreadsheet_id, requests)

    async def update_sheet_properties(
        self, spreadsheet_id: str, sheet_id: int, properties: Dict[str, Any], fields: str
    ) -> Dict[str, Any]:
        """Update sheet properties."""
        self.logger.info(f"Updating properties for sheet {sheet_id} in spreadsheet: {spreadsheet_id}")

        requests = [{"updateSheetProperties": {"properties": {"sheetId": sheet_id, **properties}, "fields": fields}}]

        return await self.batch_update(spreadsheet_id, requests)

    async def copy_sheet_to(
        self, source_spreadsheet_id: str, sheet_id: int, destination_spreadsheet_id: str
    ) -> Dict[str, Any]:
        """Copy sheet to another spreadsheet."""
        self.logger.info(f"Copying sheet {sheet_id} from {source_spreadsheet_id} to {destination_spreadsheet_id}")

        copy_data = {"destinationSpreadsheetId": destination_spreadsheet_id}
        url = f"{self.base_url}/spreadsheets/{source_spreadsheet_id}/sheets/{sheet_id}:copyTo"

        return await self.api_client.make_request("POST", url, data=copy_data)

    async def insert_rows(self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int) -> Dict[str, Any]:
        """Insert rows in a sheet."""
        self.logger.info(f"Inserting rows {start_index}-{end_index} in sheet {sheet_id}")

        requests = [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": start_index,
                        "endIndex": end_index,
                    }
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    async def insert_columns(
        self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int
    ) -> Dict[str, Any]:
        """Insert columns in a sheet."""
        self.logger.info(f"Inserting columns {start_index}-{end_index} in sheet {sheet_id}")

        requests = [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": start_index,
                        "endIndex": end_index,
                    }
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    async def delete_rows(self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int) -> Dict[str, Any]:
        """Delete rows from a sheet."""
        self.logger.info(f"Deleting rows {start_index}-{end_index} in sheet {sheet_id}")

        requests = [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": start_index,
                        "endIndex": end_index,
                    }
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    async def delete_columns(
        self, spreadsheet_id: str, sheet_id: int, start_index: int, end_index: int
    ) -> Dict[str, Any]:
        """Delete columns from a sheet."""
        self.logger.info(f"Deleting columns {start_index}-{end_index} in sheet {sheet_id}")

        requests = [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": start_index,
                        "endIndex": end_index,
                    }
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

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
        self.logger.info(f"Formatting cells ({start_row},{start_column}):({end_row},{end_column}) in sheet {sheet_id}")

        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_column,
                        "endColumnIndex": end_column,
                    },
                    "cell": {"userEnteredFormat": cell_format},
                    "fields": "userEnteredFormat",
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

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
        self.logger.info(f"Copying data from sheet {source_sheet_id} to sheet {dest_sheet_id}")

        requests = [
            {
                "copyPaste": {
                    "source": {
                        "sheetId": source_sheet_id,
                        "startRowIndex": source_start_row,
                        "endRowIndex": source_end_row,
                        "startColumnIndex": source_start_col,
                        "endColumnIndex": source_end_col,
                    },
                    "destination": {
                        "sheetId": dest_sheet_id,
                        "rowIndex": dest_start_row,
                        "columnIndex": dest_start_col,
                    },
                    "pasteType": paste_type,
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    async def set_column_width(
        self, spreadsheet_id: str, sheet_id: int, start_column: int, end_column: int, width: int
    ) -> Dict[str, Any]:
        """Set column width."""
        self.logger.info(f"Setting columns {start_column}-{end_column} width to {width} in sheet {sheet_id}")

        requests = [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": start_column,
                        "endIndex": end_column,
                    },
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    async def set_row_height(
        self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, height: int
    ) -> Dict[str, Any]:
        """Set row height."""
        self.logger.info(f"Setting rows {start_row}-{end_row} height to {height} in sheet {sheet_id}")

        requests = [
            {
                "updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": start_row, "endIndex": end_row},
                    "properties": {"pixelSize": height},
                    "fields": "pixelSize",
                }
            }
        ]

        return await self.batch_update(spreadsheet_id, requests)

    async def clear_values(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Clear values in a range."""
        self.logger.info(f"Clearing values in range: {range_name} in spreadsheet: {spreadsheet_id}")

        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}/values/{range_name}:clear"

        return await self.api_client.make_request("POST", url, data={})

    async def batch_clear_values(self, spreadsheet_id: str, ranges: List[str]) -> Dict[str, Any]:
        """Clear values in multiple ranges."""
        self.logger.info(f"Clearing values in {len(ranges)} ranges in spreadsheet: {spreadsheet_id}")

        clear_data = {"ranges": ranges}
        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}/values:batchClear"

        return await self.api_client.make_request("POST", url, data=clear_data)

    async def get_spreadsheet_values(
        self, spreadsheet_id: str, ranges: Optional[List[str]] = None, include_grid_data: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive spreadsheet data."""
        self.logger.info(f"Getting comprehensive data for spreadsheet: {spreadsheet_id}")

        params = {"includeGridData": str(include_grid_data).lower()}
        if ranges:
            params["ranges"] = ranges

        url = f"{self.base_url}/spreadsheets/{spreadsheet_id}"

        return await self.api_client.make_request("GET", url, params=params)

    def _column_letter_to_index(self, column_letter: str) -> int:
        """Convert column letter(s) to 0-based index."""
        result = 0
        for char in column_letter.upper():
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result - 1

    def _index_to_column_letter(self, index: int) -> str:
        """Convert 0-based index to column letter(s)."""
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord("A")) + result
            index = index // 26 - 1
        return result

    async def translate_range(
        self, spreadsheet_id: str, range_name: str, target_language: str, source_language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Translate text in a range of cells."""
        self.logger.info(f"Translating range {range_name} to {target_language} in spreadsheet: {spreadsheet_id}")

        # Get current values
        values = await self.get_values(spreadsheet_id, range_name)

        if not values:
            self.logger.warning("No values found in range")
            return None

        # Collect all text to translate
        text_to_translate = []
        text_positions = []

        for row_idx, row in enumerate(values):
            for col_idx, cell_value in enumerate(row):
                if isinstance(cell_value, str) and cell_value.strip():
                    # Skip if it looks like a formula or number
                    if not (cell_value.startswith("=") or cell_value.replace(".", "").replace(",", "").isdigit()):
                        text_to_translate.append(cell_value.strip())
                        text_positions.append((row_idx, col_idx))

        if not text_to_translate:
            self.logger.warning("No translatable text found in range")
            return None

        # Translate using Google Translate API
        translate_url = "https://translation.googleapis.com/language/translate/v2"
        translate_data = {"q": text_to_translate, "target": target_language, "format": "text"}

        if source_language:
            translate_data["source"] = source_language

        translation_result = await self.api_client.make_request("POST", translate_url, data=translate_data)
        translations = translation_result.get("data", {}).get("translations", [])

        if not translations:
            self.logger.error("Translation failed - no results returned")
            return None

        # Update values with translations
        updated_values = [row[:] for row in values]  # Deep copy

        for i, (row_idx, col_idx) in enumerate(text_positions):
            if i < len(translations):
                translated_text = translations[i]["translatedText"]
                # Extend row if necessary
                while len(updated_values[row_idx]) <= col_idx:
                    updated_values[row_idx].append("")
                updated_values[row_idx][col_idx] = translated_text

        # Update the spreadsheet
        result = await self.update_values(spreadsheet_id, range_name, updated_values)
        self.logger.info(f"Range translated successfully - {len(translations)} cells updated")

        return result
