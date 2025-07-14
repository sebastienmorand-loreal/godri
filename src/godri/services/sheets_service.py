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

    def read_entire_sheet(self, spreadsheet_id: str, sheet_name: str = None) -> List[List[Any]]:
        """Read all data from a sheet."""
        if sheet_name:
            range_name = f"{sheet_name}"
        else:
            # Get first sheet if no name specified
            spreadsheet = self.get_spreadsheet(spreadsheet_id)
            if not spreadsheet.get("sheets"):
                return []
            sheet_name = spreadsheet["sheets"][0]["properties"]["title"]
            range_name = sheet_name

        self.logger.info("Reading entire sheet '%s' from spreadsheet: %s", sheet_name, spreadsheet_id)

        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

        values = result.get("values", [])
        self.logger.info("Retrieved %d rows from sheet '%s'", len(values), sheet_name)
        return values

    def set_formula(self, spreadsheet_id: str, range_name: str, formula: str) -> Dict[str, Any]:
        """Set a formula in a cell or range."""
        self.logger.info("Setting formula in %s for spreadsheet: %s", range_name, spreadsheet_id)

        # Ensure formula starts with =
        if not formula.startswith("="):
            formula = "=" + formula

        body = {"values": [[formula]]}

        result = (
            self.service.spreadsheets()
            .values()
            .update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption="USER_ENTERED", body=body)
            .execute()
        )

        self.logger.info("Formula set successfully")
        return result

    def set_values_in_range(
        self, spreadsheet_id: str, range_name: str, values: Union[str, int, float, List[List[Any]]]
    ) -> Dict[str, Any]:
        """Set values in a cell or range."""
        self.logger.info("Setting values in %s for spreadsheet: %s", range_name, spreadsheet_id)

        # Convert single value to 2D array format
        if isinstance(values, (str, int, float)):
            body = {"values": [[values]]}
        elif isinstance(values, list) and len(values) > 0 and not isinstance(values[0], list):
            # Single row of values
            body = {"values": [values]}
        else:
            # Already in 2D format
            body = {"values": values}

        result = (
            self.service.spreadsheets()
            .values()
            .update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption="RAW", body=body)
            .execute()
        )

        self.logger.info("Values set successfully")
        return result

    def list_sheets(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """List all sheets in a spreadsheet."""
        self.logger.info("Listing sheets in spreadsheet: %s", spreadsheet_id)

        spreadsheet = self.get_spreadsheet(spreadsheet_id)
        sheets_info = []

        for sheet in spreadsheet.get("sheets", []):
            props = sheet["properties"]
            sheets_info.append(
                {
                    "title": props["title"],
                    "sheetId": props["sheetId"],
                    "index": props["index"],
                    "hidden": props.get("hidden", False),
                    "gridProperties": props.get("gridProperties", {}),
                }
            )

        self.logger.info("Found %d sheets", len(sheets_info))
        return sheets_info

    def hide_sheet(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        """Hide a sheet."""
        self.logger.info("Hiding sheet %d in spreadsheet: %s", sheet_id, spreadsheet_id)

        body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "hidden": True},
                        "fields": "hidden",
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Sheet hidden successfully")
        return result

    def unhide_sheet(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        """Unhide a sheet."""
        self.logger.info("Unhiding sheet %d in spreadsheet: %s", sheet_id, spreadsheet_id)

        body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "hidden": False},
                        "fields": "hidden",
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Sheet unhidden successfully")
        return result

    def format_range(self, spreadsheet_id: str, range_name: str, format_options: Dict[str, Any]) -> Dict[str, Any]:
        """Format a range using A1 notation with comprehensive formatting options.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: A1 notation range (e.g., 'A1:B5', 'Sheet1!C2:D10')
            format_options: Dictionary with formatting options

        Format Options Examples:

        Text Formatting:
            - Font family: {"textFormat": {"fontFamily": "Arial"}}
            - Font family: {"textFormat": {"fontFamily": "Calibri"}}
            - Font family: {"textFormat": {"fontFamily": "Times New Roman"}}
            - Font family: {"textFormat": {"fontFamily": "Roboto"}}
            - Bold: {"textFormat": {"bold": true}}
            - Italic: {"textFormat": {"italic": true}}
            - Underline: {"textFormat": {"underline": true}}
            - Strikethrough: {"textFormat": {"strikethrough": true}}
            - Font size: {"textFormat": {"fontSize": 14}}

        Colors (RGB values 0.0-1.0):
            - Text color (red): {"textFormat": {"foregroundColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}}
            - Text color (blue): {"textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 1.0}}}
            - Text color (green): {"textFormat": {"foregroundColor": {"red": 0.0, "green": 0.8, "blue": 0.0}}}
            - Background (yellow): {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 0.0}}
            - Background (light blue): {"backgroundColor": {"red": 0.8, "green": 0.9, "blue": 1.0}}
            - Background (light gray): {"backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}}

        Combined Examples:
            - Header style: {"textFormat": {"bold": true, "fontFamily": "Arial", "fontSize": 12}, "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8}}
            - Error text: {"textFormat": {"bold": true, "foregroundColor": {"red": 1.0, "green": 0.0, "blue": 0.0}}, "backgroundColor": {"red": 1.0, "green": 0.9, "blue": 0.9}}
            - Success text: {"textFormat": {"italic": true, "foregroundColor": {"red": 0.0, "green": 0.6, "blue": 0.0}}, "backgroundColor": {"red": 0.9, "green": 1.0, "blue": 0.9}}

        Borders:
            - All borders: {"borders": {"top": {"style": "SOLID", "width": 1}, "bottom": {"style": "SOLID", "width": 1}, "left": {"style": "SOLID", "width": 1}, "right": {"style": "SOLID", "width": 1}}}
            - Thick bottom border: {"borders": {"bottom": {"style": "SOLID", "width": 3}}}

        Alignment:
            - Center: {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}
            - Right align: {"horizontalAlignment": "RIGHT"}
            - Left align: {"horizontalAlignment": "LEFT"}

        Number Format:
            - Currency: {"numberFormat": {"type": "CURRENCY", "pattern": "\"$\"#,##0.00"}}
            - Percentage: {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}}
            - Date: {"numberFormat": {"type": "DATE", "pattern": "mm/dd/yyyy"}}
        """
        self.logger.info("Formatting range %s in spreadsheet: %s", range_name, spreadsheet_id)

        # Parse the range to get sheet name and range
        if "!" in range_name:
            sheet_name, cell_range = range_name.split("!", 1)
        else:
            # Get first sheet if no sheet specified
            spreadsheet = self.get_spreadsheet(spreadsheet_id)
            sheet_name = spreadsheet["sheets"][0]["properties"]["title"]
            cell_range = range_name

        sheet_id = self.get_sheet_id_by_name(spreadsheet_id, sheet_name)
        if sheet_id is None:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        # Convert A1 notation to grid coordinates
        start_row, start_col, end_row, end_col = self._parse_a1_notation(cell_range)

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

        self.logger.info("Range formatted successfully")
        return result

    def _parse_a1_notation(self, range_str: str) -> tuple:
        """Parse A1 notation to grid coordinates (0-indexed)."""
        import re

        # Handle single cell (e.g., "A1") or range (e.g., "A1:B5")
        if ":" in range_str:
            start_cell, end_cell = range_str.split(":")
        else:
            start_cell = end_cell = range_str

        def parse_cell(cell):
            match = re.match(r"([A-Z]+)(\d+)", cell.upper())
            if not match:
                raise ValueError(f"Invalid cell reference: {cell}")

            col_letters, row_num = match.groups()

            # Convert column letters to 0-indexed number
            col_num = 0
            for char in col_letters:
                col_num = col_num * 26 + (ord(char) - ord("A") + 1)
            col_num -= 1  # Convert to 0-indexed

            row_num = int(row_num) - 1  # Convert to 0-indexed

            return row_num, col_num

        start_row, start_col = parse_cell(start_cell)
        end_row, end_col = parse_cell(end_cell)

        # End indices are exclusive in the API
        return start_row, start_col, end_row + 1, end_col + 1

    def insert_row(self, spreadsheet_id: str, sheet_id: int, row_index: int, count: int = 1) -> Dict[str, Any]:
        """Insert row(s) at specified index."""
        self.logger.info("Inserting %d row(s) at index %d in sheet %d", count, row_index, sheet_id)

        body = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": row_index,
                            "endIndex": row_index + count,
                        },
                        "inheritFromBefore": False,
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Row(s) inserted successfully")
        return result

    def delete_row(self, spreadsheet_id: str, sheet_id: int, row_index: int, count: int = 1) -> Dict[str, Any]:
        """Delete row(s) starting at specified index."""
        self.logger.info("Deleting %d row(s) starting at index %d in sheet %d", count, row_index, sheet_id)

        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": row_index,
                            "endIndex": row_index + count,
                        }
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Row(s) deleted successfully")
        return result

    def insert_column(self, spreadsheet_id: str, sheet_id: int, column_index: int, count: int = 1) -> Dict[str, Any]:
        """Insert column(s) at specified index."""
        self.logger.info("Inserting %d column(s) at index %d in sheet %d", count, column_index, sheet_id)

        body = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": column_index,
                            "endIndex": column_index + count,
                        },
                        "inheritFromBefore": False,
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Column(s) inserted successfully")
        return result

    def delete_column(self, spreadsheet_id: str, sheet_id: int, column_index: int, count: int = 1) -> Dict[str, Any]:
        """Delete column(s) starting at specified index."""
        self.logger.info("Deleting %d column(s) starting at index %d in sheet %d", count, column_index, sheet_id)

        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": column_index,
                            "endIndex": column_index + count,
                        }
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Column(s) deleted successfully")
        return result

    def _convert_column_letter_to_index(self, column_letter: str) -> int:
        """Convert column letter (A, B, C, ..., AA, AB, etc.) to 0-based index."""
        column_letter = column_letter.upper()
        result = 0
        for char in column_letter:
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result - 1

    def _convert_index_to_column_letter(self, index: int) -> str:
        """Convert 0-based column index to column letter."""
        result = ""
        while index >= 0:
            result = chr(ord("A") + (index % 26)) + result
            index = index // 26 - 1
        return result

    async def translate_range(
        self, spreadsheet_id: str, range_name: str, target_language: str, source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate values in a range while preserving formulas and formatting."""
        from .translate_service import TranslateService
        import re

        self.logger.info("Translating range %s in spreadsheet: %s to %s", range_name, spreadsheet_id, target_language)

        # Initialize translate service
        translate_service = TranslateService(self.auth_service)
        await translate_service.initialize()

        # Get current values, formulas, and formatting
        try:
            # Get values (calculated results)
            values_result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name, valueRenderOption="UNFORMATTED_VALUE")
                .execute()
            )
            values = values_result.get("values", [])

            # Get formulas (raw formulas)
            formulas_result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name, valueRenderOption="FORMULA")
                .execute()
            )
            formulas = formulas_result.get("values", [])

            # Get cell formatting data
            sheet_data_result = (
                self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, ranges=[range_name], includeGridData=True)
                .execute()
            )

            # Extract formatting from the first sheet's grid data
            formatting_data = None
            if sheet_data_result.get("sheets") and sheet_data_result["sheets"][0].get("data"):
                formatting_data = sheet_data_result["sheets"][0]["data"][0].get("rowData", [])

        except Exception as e:
            self.logger.error("Failed to get range data: %s", str(e))
            raise

        if not values and not formulas:
            self.logger.info("No data found in range")
            return {}

        # Ensure formulas array matches values dimensions
        max_rows = max(len(values), len(formulas)) if values or formulas else 0
        max_cols = max(
            max(len(row) for row in values) if values else 0, max(len(row) for row in formulas) if formulas else 0
        )

        # Pad arrays to same dimensions
        while len(values) < max_rows:
            values.append([])
        while len(formulas) < max_rows:
            formulas.append([])

        for i in range(max_rows):
            while len(values[i]) < max_cols:
                values[i].append("")
            while len(formulas[i]) < max_cols:
                formulas[i].append("")

        # Process each cell
        translated_values = []
        for row_idx, (value_row, formula_row) in enumerate(zip(values, formulas)):
            translated_row = []
            for col_idx, (cell_value, cell_formula) in enumerate(zip(value_row, formula_row)):
                translated_cell = self._translate_cell_content(
                    cell_value, cell_formula, translate_service, target_language, source_language
                )
                translated_row.append(translated_cell)
            translated_values.append(translated_row)

        # Update the range with translated values using batch update to preserve formatting
        try:
            # Parse range to get sheet info
            sheet_id, start_row, start_col, end_row, end_col = self._parse_range_for_formatting(
                spreadsheet_id, range_name
            )

            # Prepare batch update requests
            requests = []

            # First, update values
            for row_idx, row_values in enumerate(translated_values):
                for col_idx, cell_value in enumerate(row_values):
                    if cell_value:  # Only update non-empty cells
                        cell_row = start_row + row_idx
                        cell_col = start_col + col_idx

                        # Create update request for this cell
                        requests.append(
                            {
                                "updateCells": {
                                    "range": {
                                        "sheetId": sheet_id,
                                        "startRowIndex": cell_row,
                                        "endRowIndex": cell_row + 1,
                                        "startColumnIndex": cell_col,
                                        "endColumnIndex": cell_col + 1,
                                    },
                                    "rows": [
                                        {
                                            "values": [
                                                {
                                                    "userEnteredValue": (
                                                        {"stringValue": cell_value}
                                                        if isinstance(cell_value, str)
                                                        and not cell_value.startswith("=")
                                                        else {"formulaValue": cell_value}
                                                    ),
                                                    "userEnteredFormat": (
                                                        self._get_preserved_format(formatting_data, row_idx, col_idx)
                                                        if formatting_data
                                                        else {}
                                                    ),
                                                }
                                            ]
                                        }
                                    ],
                                    "fields": "userEnteredValue,userEnteredFormat",
                                }
                            }
                        )

            # Execute batch update
            if requests:
                result = (
                    self.service.spreadsheets()
                    .batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests})
                    .execute()
                )

                self.logger.info(
                    "Range translation completed with formatting preserved. Processed %d requests", len(requests)
                )
                return result
            else:
                self.logger.info("No cells to update")
                return {}

        except Exception as e:
            self.logger.error("Failed to update translated values with formatting: %s", str(e))
            # Fallback to simple value update without formatting
            self.logger.info("Falling back to simple value update")
            result = (
                self.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body={"values": translated_values},
                )
                .execute()
            )
            return result

    def _translate_cell_content(
        self,
        cell_value: str,
        cell_formula: str,
        translate_service,
        target_language: str,
        source_language: Optional[str] = None,
    ) -> str:
        """Translate content of a single cell, handling formulas intelligently."""
        import re

        # If cell is empty, return as-is
        if not cell_value and not cell_formula:
            return ""

        # If it's a formula, translate only string literals within it
        if cell_formula and cell_formula.startswith("="):
            self.logger.debug("Processing formula: %s", cell_formula)
            return self._translate_formula_strings(cell_formula, translate_service, target_language, source_language)

        # If it's a regular text value, translate it
        if isinstance(cell_value, str) and cell_value.strip():
            # Skip if it looks like a number, date, or other non-text data
            if self._is_translatable_text(cell_value):
                try:
                    translation_result = translate_service.translate_text(cell_value, target_language, source_language)
                    translated_text = translation_result["translatedText"]
                    self.logger.debug("Translated cell: '%s' -> '%s'", cell_value, translated_text)
                    return translated_text
                except Exception as e:
                    self.logger.error("Failed to translate cell value '%s': %s", cell_value, str(e))
                    return cell_value

        # Return original value for non-translatable content
        return cell_value

    def _translate_formula_strings(
        self, formula: str, translate_service, target_language: str, source_language: Optional[str] = None
    ) -> str:
        """Translate string literals within a formula while preserving formula structure."""
        import re

        # Pattern to match string literals in formulas (quoted strings)
        string_pattern = r'"([^"]*)"'

        def translate_match(match):
            original_string = match.group(1)
            if self._is_translatable_text(original_string):
                try:
                    translation_result = translate_service.translate_text(
                        original_string, target_language, source_language
                    )
                    translated_string = translation_result["translatedText"]
                    self.logger.debug("Translated formula string: '%s' -> '%s'", original_string, translated_string)
                    return f'"{translated_string}"'
                except Exception as e:
                    self.logger.error("Failed to translate formula string '%s': %s", original_string, str(e))
                    return match.group(0)  # Return original quoted string
            return match.group(0)  # Return original quoted string

        # Replace all string literals in the formula
        translated_formula = re.sub(string_pattern, translate_match, formula)
        return translated_formula

    def _is_translatable_text(self, text: str) -> bool:
        """Determine if text should be translated (exclude numbers, dates, etc.)."""
        import re

        if not text or not text.strip():
            return False

        text = text.strip()

        # Skip pure numbers
        try:
            float(text.replace(",", "").replace("$", "").replace("%", ""))
            return False
        except ValueError:
            pass

        # Skip dates (basic patterns)
        date_patterns = [
            r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$",  # MM/DD/YYYY or similar
            r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$",  # YYYY/MM/DD or similar
            r"^\w{3}\s+\d{1,2},?\s+\d{4}$",  # Jan 1, 2024
        ]

        for pattern in date_patterns:
            if re.match(pattern, text):
                return False

        # Skip very short text (likely abbreviations or codes)
        if len(text) < 2:
            return False

        # Skip text that's mostly special characters or numbers
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars < len(text) * 0.5:  # Less than 50% alphabetic characters
            return False

        return True

    def _parse_range_for_formatting(self, spreadsheet_id: str, range_name: str) -> tuple:
        """Parse range and return sheet_id, start_row, start_col, end_row, end_col."""
        # Parse the range to get sheet name and cell range
        if "!" in range_name:
            sheet_name, cell_range = range_name.split("!", 1)
        else:
            # Get first sheet if no sheet specified
            spreadsheet = self.get_spreadsheet(spreadsheet_id)
            sheet_name = spreadsheet["sheets"][0]["properties"]["title"]
            cell_range = range_name

        sheet_id = self.get_sheet_id_by_name(spreadsheet_id, sheet_name)
        if sheet_id is None:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        # Convert A1 notation to grid coordinates
        start_row, start_col, end_row, end_col = self._parse_a1_notation(cell_range)

        return sheet_id, start_row, start_col, end_row, end_col

    def _get_preserved_format(
        self, formatting_data: List[Dict[str, Any]], row_idx: int, col_idx: int
    ) -> Dict[str, Any]:
        """Extract and return the formatting for a specific cell."""
        if not formatting_data or row_idx >= len(formatting_data):
            return {}

        row_data = formatting_data[row_idx]
        if not row_data.get("values") or col_idx >= len(row_data["values"]):
            return {}

        cell_data = row_data["values"][col_idx]
        return cell_data.get("userEnteredFormat", {})

    async def copy_format(self, spreadsheet_id: str, source_range: str, target_range: str) -> Dict[str, Any]:
        """Copy formatting from source range to target range."""
        self.logger.info("Copying format from %s to %s in spreadsheet: %s", source_range, target_range, spreadsheet_id)

        try:
            # Get source formatting
            source_data_result = (
                self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, ranges=[source_range], includeGridData=True)
                .execute()
            )

            if not source_data_result.get("sheets") or not source_data_result["sheets"][0].get("data"):
                raise ValueError(f"No formatting data found for source range: {source_range}")

            source_formatting = source_data_result["sheets"][0]["data"][0].get("rowData", [])

            if not source_formatting:
                raise ValueError(f"No formatting found in source range: {source_range}")

            # Parse target range
            target_sheet_id, target_start_row, target_start_col, target_end_row, target_end_col = (
                self._parse_range_for_formatting(spreadsheet_id, target_range)
            )

            # Parse source range to understand dimensions
            source_sheet_id, source_start_row, source_start_col, source_end_row, source_end_col = (
                self._parse_range_for_formatting(spreadsheet_id, source_range)
            )

            # Calculate dimensions
            source_rows = source_end_row - source_start_row
            source_cols = source_end_col - source_start_col
            target_rows = target_end_row - target_start_row
            target_cols = target_end_col - target_start_col

            # Prepare batch update requests
            requests = []

            # Apply formatting to each cell in target range
            for target_row_idx in range(target_rows):
                for target_col_idx in range(target_cols):
                    # Calculate corresponding source cell (with wrapping if needed)
                    source_row_idx = target_row_idx % source_rows
                    source_col_idx = target_col_idx % source_cols

                    # Get source format
                    source_format = self._get_preserved_format(source_formatting, source_row_idx, source_col_idx)

                    if source_format:  # Only apply if there's formatting to copy
                        cell_row = target_start_row + target_row_idx
                        cell_col = target_start_col + target_col_idx

                        requests.append(
                            {
                                "updateCells": {
                                    "range": {
                                        "sheetId": target_sheet_id,
                                        "startRowIndex": cell_row,
                                        "endRowIndex": cell_row + 1,
                                        "startColumnIndex": cell_col,
                                        "endColumnIndex": cell_col + 1,
                                    },
                                    "rows": [{"values": [{"userEnteredFormat": source_format}]}],
                                    "fields": "userEnteredFormat",
                                }
                            }
                        )

            # Execute batch update
            if requests:
                result = (
                    self.service.spreadsheets()
                    .batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests})
                    .execute()
                )

                self.logger.info("Format copying completed. Processed %d cells", len(requests))
                return result
            else:
                self.logger.info("No formatting to copy")
                return {}

        except Exception as e:
            self.logger.error("Failed to copy formatting: %s", str(e))
            raise
