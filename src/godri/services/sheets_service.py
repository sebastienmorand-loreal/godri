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

    def _clean_formula_string(self, formula: str) -> str:
        """Clean and prepare a formula string for Google Sheets.

        Args:
            formula: Raw formula string that may have quotes or other issues

        Returns:
            Cleaned formula string ready for Google Sheets API
        """
        if not formula:
            return formula

        # Strip whitespace
        formula = formula.strip()

        # Remove leading/trailing quotes that can cause issues
        if (formula.startswith('"') and formula.endswith('"')) or (formula.startswith("'") and formula.endswith("'")):
            formula = formula[1:-1]

        # Remove any leading quotes that would prevent formula execution
        formula = formula.lstrip("'\"")

        # Ensure formula starts with =
        if formula and not formula.startswith("="):
            formula = "=" + formula

        return formula

    def set_formulas_in_range(
        self, spreadsheet_id: str, range_name: str, formulas: Union[str, List[List[str]]]
    ) -> Dict[str, Any]:
        """Set formulas in a cell or range.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: A1 notation range (e.g., 'A1', 'A1:C3')
            formulas: Single formula string or List[List] of formulas for table format

        Examples:
            Single formula: formulas = "SUM(A1:A10)"
            Formula table: formulas = [["=A1+B1", "=A1*2"], ["=A2+B2", "=A2*2"]]
        """
        self.logger.info("Setting formulas in %s for spreadsheet: %s", range_name, spreadsheet_id)

        if isinstance(formulas, str):
            # Single formula
            cleaned_formula = self._clean_formula_string(formulas)
            body = {"values": [[cleaned_formula]]}
        else:
            # List of lists of formulas
            formatted_formulas = []
            for row in formulas:
                formatted_row = []
                for formula in row:
                    cleaned_formula = self._clean_formula_string(formula)
                    formatted_row.append(cleaned_formula)
                formatted_formulas.append(formatted_row)
            body = {"values": formatted_formulas}

        result = (
            self.service.spreadsheets()
            .values()
            .update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption="USER_ENTERED", body=body)
            .execute()
        )

        self.logger.info("Formulas set successfully")
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

    def rename_sheet(self, spreadsheet_id: str, sheet_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a sheet by name.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_name: Current name of the sheet to rename
            new_name: New name for the sheet

        Returns:
            Dictionary with operation results

        Raises:
            ValueError: If sheet with sheet_name is not found
        """
        self.logger.info("Renaming sheet '%s' to '%s' in spreadsheet: %s", sheet_name, new_name, spreadsheet_id)

        # Get sheet ID by name
        sheet_id = self.get_sheet_id_by_name(spreadsheet_id, sheet_name)
        if sheet_id is None:
            raise ValueError(f"Sheet '{sheet_name}' not found in spreadsheet")

        return self.rename_sheet_by_id(spreadsheet_id, sheet_id, new_name)

    def rename_sheet_by_id(self, spreadsheet_id: str, sheet_id: int, new_name: str) -> Dict[str, Any]:
        """Rename a sheet by ID.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_id: ID of the sheet to rename
            new_name: New name for the sheet

        Returns:
            Dictionary with operation results
        """
        self.logger.info("Renaming sheet ID %d to '%s' in spreadsheet: %s", sheet_id, new_name, spreadsheet_id)

        body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "title": new_name},
                        "fields": "title",
                    }
                }
            ]
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Sheet renamed successfully to '%s'", new_name)
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

    # Copy Operations
    def copy_sheet(
        self,
        source_spreadsheet_id: str,
        target_spreadsheet_id: str,
        source_sheet_name: str,
        target_sheet_name: Optional[str] = None,
        preserve_formatting: bool = True,
    ) -> Dict[str, Any]:
        """Copy a sheet from one spreadsheet to another.

        Args:
            source_spreadsheet_id: Source spreadsheet ID
            target_spreadsheet_id: Target spreadsheet ID
            source_sheet_name: Name of sheet to copy
            target_sheet_name: Name for new sheet (default: source name with suffix)
            preserve_formatting: Whether to preserve cell formatting (default: True)

        Returns:
            Dictionary with copy results and new sheet info
        """
        self.logger.info(
            "Copying sheet '%s' from %s to %s",
            source_sheet_name,
            source_spreadsheet_id,
            target_spreadsheet_id,
        )

        # Get source sheet ID
        source_sheet_id = self.get_sheet_id_by_name(source_spreadsheet_id, source_sheet_name)
        if source_sheet_id is None:
            raise ValueError(f"Sheet '{source_sheet_name}' not found in source spreadsheet")

        # Determine target sheet name
        if target_sheet_name is None:
            target_sheet_name = f"{source_sheet_name} (Copy)"

        # Check if target sheet name already exists and make it unique
        target_sheets = self.list_sheets(target_spreadsheet_id)
        existing_names = [sheet["title"] for sheet in target_sheets]

        original_target_name = target_sheet_name
        counter = 1
        while target_sheet_name in existing_names:
            target_sheet_name = f"{original_target_name} ({counter})"
            counter += 1

        try:
            # Step 1: Copy the sheet structure using Google Sheets API
            copy_request = {
                "destinationSpreadsheetId": target_spreadsheet_id,
            }

            result = (
                self.service.spreadsheets()
                .sheets()
                .copyTo(
                    spreadsheetId=source_spreadsheet_id,
                    sheetId=source_sheet_id,
                    body=copy_request,
                )
                .execute()
            )

            new_sheet_id = result["sheetId"]
            copied_sheet_title = result["title"]

            # Step 2: Rename the copied sheet if needed
            if copied_sheet_title != target_sheet_name:
                rename_request = {
                    "requests": [
                        {
                            "updateSheetProperties": {
                                "properties": {
                                    "sheetId": new_sheet_id,
                                    "title": target_sheet_name,
                                },
                                "fields": "title",
                            }
                        }
                    ]
                }

                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=target_spreadsheet_id, body=rename_request
                ).execute()

            self.logger.info(
                "Successfully copied sheet '%s' to '%s' (ID: %d)",
                source_sheet_name,
                target_sheet_name,
                new_sheet_id,
            )

            return {
                "source_spreadsheet": source_spreadsheet_id,
                "target_spreadsheet": target_spreadsheet_id,
                "source_sheet": source_sheet_name,
                "target_sheet": target_sheet_name,
                "new_sheet_id": new_sheet_id,
                "preserve_formatting": preserve_formatting,
            }

        except Exception as e:
            self.logger.error("Failed to copy sheet: %s", str(e))
            raise

    def copy_multiple_sheets(
        self,
        source_spreadsheet_id: str,
        target_spreadsheet_id: str,
        sheet_names: List[str],
        preserve_formatting: bool = True,
    ) -> Dict[str, Any]:
        """Copy multiple sheets from one spreadsheet to another.

        Args:
            source_spreadsheet_id: Source spreadsheet ID
            target_spreadsheet_id: Target spreadsheet ID
            sheet_names: List of sheet names to copy
            preserve_formatting: Whether to preserve cell formatting (default: True)

        Returns:
            Dictionary with copy results for all sheets
        """
        self.logger.info(
            "Copying %d sheets from %s to %s",
            len(sheet_names),
            source_spreadsheet_id,
            target_spreadsheet_id,
        )

        results = []
        for sheet_name in sheet_names:
            try:
                result = self.copy_sheet(
                    source_spreadsheet_id,
                    target_spreadsheet_id,
                    sheet_name,
                    preserve_formatting=preserve_formatting,
                )
                results.append(result)
            except Exception as e:
                self.logger.error("Failed to copy sheet '%s': %s", sheet_name, str(e))
                results.append(
                    {
                        "source_sheet": sheet_name,
                        "error": str(e),
                        "success": False,
                    }
                )

        successful_copies = len([r for r in results if "error" not in r])

        self.logger.info(
            "Sheet copying completed: %d successful, %d failed",
            successful_copies,
            len(results) - successful_copies,
        )

        return {
            "source_spreadsheet": source_spreadsheet_id,
            "target_spreadsheet": target_spreadsheet_id,
            "results": results,
            "successful_copies": successful_copies,
            "total_sheets": len(sheet_names),
            "preserve_formatting": preserve_formatting,
        }

    # Copy and Paste Operations
    def copy_range_values(
        self,
        spreadsheet_id: str,
        source_range: str,
        destination_range: str,
        copy_type: str = "all",
        paste_type: str = "PASTE_NORMAL",
    ) -> Dict[str, Any]:
        """Copy values from source range to destination range using Google Sheets API.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            source_range: Source range in A1 notation (e.g., 'A1:C3', 'Sheet1!A1:C3')
            destination_range: Destination range in A1 notation (e.g., 'E1:G3', 'Sheet2!E1:G3')
            copy_type: What to copy - 'values', 'formulas', 'formats', 'all' (default: 'all')
            paste_type: Paste operation type (default: 'PASTE_NORMAL')

        Returns:
            Dictionary with operation results

        Raises:
            ValueError: If copy_type is invalid
        """
        self.logger.info(
            "Copying %s from range %s to %s in spreadsheet: %s",
            copy_type,
            source_range,
            destination_range,
            spreadsheet_id,
        )

        # Validate copy_type
        valid_copy_types = ["values", "formulas", "formats", "all"]
        if copy_type not in valid_copy_types:
            raise ValueError(f"Invalid copy_type '{copy_type}'. Must be one of: {valid_copy_types}")

        # Map copy_type to paste_type
        paste_type_mapping = {
            "values": "PASTE_VALUES",
            "formulas": "PASTE_FORMULA",
            "formats": "PASTE_FORMAT",
            "all": "PASTE_NORMAL",
        }

        actual_paste_type = paste_type_mapping.get(copy_type, paste_type)

        # Use copyPaste request in batchUpdate
        body = {
            "requests": [
                {
                    "copyPaste": {
                        "source": {"sheetId": self._get_sheet_id_from_range(spreadsheet_id, source_range)},
                        "destination": {"sheetId": self._get_sheet_id_from_range(spreadsheet_id, destination_range)},
                        "pasteType": actual_paste_type,
                    }
                }
            ]
        }

        # Add range specifications if needed
        source_grid_range = self._convert_a1_to_grid_range(spreadsheet_id, source_range)
        destination_grid_range = self._convert_a1_to_grid_range(spreadsheet_id, destination_range)

        body["requests"][0]["copyPaste"]["source"].update(source_grid_range)
        body["requests"][0]["copyPaste"]["destination"].update(destination_grid_range)

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        self.logger.info("Range copied successfully from %s to %s", source_range, destination_range)

        return {
            "spreadsheet_id": spreadsheet_id,
            "source_range": source_range,
            "destination_range": destination_range,
            "copy_type": copy_type,
            "paste_type": actual_paste_type,
            "replies": result.get("replies", []),
        }

    def _get_sheet_id_from_range(self, spreadsheet_id: str, range_name: str) -> int:
        """Extract sheet ID from a range string."""
        if "!" in range_name:
            sheet_name = range_name.split("!")[0]
            return self.get_sheet_id_by_name(spreadsheet_id, sheet_name)
        else:
            # Default to first sheet if no sheet specified
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            return spreadsheet["sheets"][0]["properties"]["sheetId"]

    def _convert_a1_to_grid_range(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Convert A1 notation to GridRange format for API requests."""
        import re

        # Extract sheet name and range parts
        if "!" in range_name:
            sheet_name, cell_range = range_name.split("!", 1)
        else:
            cell_range = range_name

        # Parse cell range (e.g., 'A1:C3' or 'A1')
        if ":" in cell_range:
            start_cell, end_cell = cell_range.split(":")
        else:
            start_cell = end_cell = cell_range

        def parse_cell(cell: str) -> Dict[str, int]:
            """Parse cell reference like 'A1' into row/column indices."""
            match = re.match(r"([A-Z]+)(\d+)", cell.upper())
            if not match:
                raise ValueError(f"Invalid cell reference: {cell}")

            col_letters, row_num = match.groups()

            # Convert column letters to 0-based index
            col_index = 0
            for char in col_letters:
                col_index = col_index * 26 + (ord(char) - ord("A") + 1)
            col_index -= 1  # Convert to 0-based

            row_index = int(row_num) - 1  # Convert to 0-based

            return {"row": row_index, "col": col_index}

        start_indices = parse_cell(start_cell)
        end_indices = parse_cell(end_cell)

        grid_range = {
            "startRowIndex": start_indices["row"],
            "endRowIndex": end_indices["row"] + 1,  # End is exclusive
            "startColumnIndex": start_indices["col"],
            "endColumnIndex": end_indices["col"] + 1,  # End is exclusive
        }

        return grid_range

    # CSV Import Operations
    def import_csv_file(
        self,
        csv_file_path: str,
        spreadsheet_id: Optional[str] = None,
        sheet_name: str = "Sheet1",
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import CSV file to Google Sheets using Drive API conversion.

        Args:
            csv_file_path: Path to local CSV file
            spreadsheet_id: Target spreadsheet ID (creates new if None)
            sheet_name: Target sheet name (for new spreadsheets)
            folder_id: Optional folder ID for new spreadsheets

        Returns:
            Dictionary with import results and spreadsheet info
        """
        import os

        self.logger.info("Importing CSV file: %s", csv_file_path)

        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

        if spreadsheet_id:
            # Import to existing spreadsheet
            return self._import_csv_to_existing_sheet(csv_file_path, spreadsheet_id, sheet_name)
        else:
            # Create new spreadsheet from CSV
            return self._create_spreadsheet_from_csv(csv_file_path, sheet_name, folder_id)

    def import_csv_data(
        self, csv_data: str, spreadsheet_id: str, sheet_name: str = "Sheet1", start_range: str = "A1"
    ) -> Dict[str, Any]:
        """Import CSV data string to Google Sheets using Sheets API.

        Args:
            csv_data: CSV content as string
            spreadsheet_id: Target spreadsheet ID
            sheet_name: Target sheet name
            start_range: Starting cell range (e.g., 'A1')

        Returns:
            Dictionary with import results
        """
        import csv
        import io

        self.logger.info("Importing CSV data to sheet: %s", sheet_name)

        # Parse CSV data
        csv_reader = csv.reader(io.StringIO(csv_data))
        rows = list(csv_reader)

        if not rows:
            raise ValueError("CSV data is empty")

        # Convert to the format expected by Sheets API
        values = []
        for row in rows:
            values.append(row)

        # Determine the range for the data
        end_col_letter = self._number_to_column_letter(len(values[0]))
        end_row = len(values)
        range_name = f"{sheet_name}!{start_range}:{end_col_letter}{end_row}"

        # Clear existing content in the range first
        self.clear_range(spreadsheet_id, range_name)

        # Import the data
        result = self.set_values_in_range(spreadsheet_id, range_name, values)

        self.logger.info("CSV data imported successfully: %d rows, %d columns", len(values), len(values[0]))

        return {
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "range": range_name,
            "rows_imported": len(values),
            "columns_imported": len(values[0]),
            "cells_updated": result.get("updatedCells", 0),
        }

    def _create_spreadsheet_from_csv(
        self, csv_file_path: str, sheet_name: str, folder_id: Optional[str]
    ) -> Dict[str, Any]:
        """Create new spreadsheet from CSV file using Drive API."""
        import os

        file_name = os.path.basename(csv_file_path)
        title = os.path.splitext(file_name)[0]

        # Upload CSV file and convert to Google Sheets
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }

        if folder_id:
            file_metadata["parents"] = [folder_id]

        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(csv_file_path, mimetype="text/csv")

        file = (
            self.drive_service.files().create(body=file_metadata, media_body=media, fields="id,name,mimeType").execute()
        )

        spreadsheet_id = file.get("id")

        self.logger.info("Created new spreadsheet from CSV: %s", spreadsheet_id)

        return {
            "spreadsheet_id": spreadsheet_id,
            "name": file.get("name"),
            "created_from_csv": True,
            "original_file": csv_file_path,
        }

    def _import_csv_to_existing_sheet(self, csv_file_path: str, spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
        """Import CSV file to existing spreadsheet sheet."""
        # Read CSV file
        with open(csv_file_path, "r", encoding="utf-8") as f:
            csv_data = f.read()

        # Use the CSV data import method
        return self.import_csv_data(csv_data, spreadsheet_id, sheet_name)

    def _number_to_column_letter(self, num: int) -> str:
        """Convert column number to letter (1->A, 2->B, 26->Z, 27->AA)."""
        letter = ""
        while num > 0:
            num -= 1
            letter = chr(num % 26 + ord("A")) + letter
            num //= 26
        return letter

    def clear_range(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Clear content in a specific range."""
        self.logger.info("Clearing range: %s", range_name)

        result = (
            self.service.spreadsheets()
            .values()
            .clear(spreadsheetId=spreadsheet_id, range=range_name, body={})
            .execute()
        )

        self.logger.info("Range cleared successfully")
        return result

    def get_range_details(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        """Get comprehensive details about a range including formulas, values, formatting, and errors.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: A1 notation range (e.g., 'A1', 'A1:C3', 'Sheet1!B2:D4')

        Returns:
            Dictionary containing detailed information about each cell in the range
        """
        self.logger.info("Getting range details for %s in spreadsheet: %s", range_name, spreadsheet_id)

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

        # Get detailed sheet data including all cell properties
        fields = (
            "sheets(properties(title,sheetId),"
            "data(rowData(values("
            "formattedValue,userEnteredValue,effectiveValue,effectiveFormat,"
            "userEnteredFormat,hyperlink,note,textFormatRuns"
            "))))"
        )

        spreadsheet = (
            self.service.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                ranges=[range_name],
                fields=fields,
                includeGridData=True,
            )
            .execute()
        )

        # Process the response to extract detailed cell information
        result = {
            "range": range_name,
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "cells": [],
        }

        if "sheets" in spreadsheet and spreadsheet["sheets"]:
            sheet = spreadsheet["sheets"][0]
            if "data" in sheet and sheet["data"]:
                data = sheet["data"][0]
                if "rowData" in data:
                    for row_idx, row_data in enumerate(data["rowData"]):
                        if "values" in row_data:
                            for col_idx, cell_data in enumerate(row_data["values"]):
                                cell_info = self._extract_cell_details(
                                    cell_data, start_row + row_idx, start_col + col_idx
                                )
                                result["cells"].append(cell_info)

        self.logger.info("Retrieved details for %d cells", len(result["cells"]))
        return result

    def _extract_cell_details(self, cell_data: Dict[str, Any], row: int, col: int) -> Dict[str, Any]:
        """Extract detailed information from a single cell data object.

        Args:
            cell_data: Raw cell data from Sheets API
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Dictionary with comprehensive cell information
        """
        # Convert column index to letter (0->A, 1->B, etc.)
        col_letter = self._number_to_column_letter(col + 1)
        cell_address = f"{col_letter}{row + 1}"

        cell_info = {
            "address": cell_address,
            "row": row + 1,  # 1-based for user display
            "column": col + 1,  # 1-based for user display
            "column_letter": col_letter,
            "type": "empty",
            "display_value": "",
            "effective_value": None,
            "user_entered_value": None,
            "formula": None,
            "is_formula": False,
            "has_error": False,
            "error_type": None,
            "error_message": None,
            "format": {},
            "hyperlink": None,
            "note": None,
        }

        if not cell_data:
            return cell_info

        # Extract display value (what user sees)
        if "formattedValue" in cell_data:
            cell_info["display_value"] = cell_data["formattedValue"]
            cell_info["type"] = "value"

        # Extract effective value (calculated result)
        if "effectiveValue" in cell_data:
            effective = cell_data["effectiveValue"]
            cell_info["effective_value"] = effective

            # Determine value type
            if "errorValue" in effective:
                cell_info["type"] = "error"
                cell_info["has_error"] = True
                error = effective["errorValue"]
                cell_info["error_type"] = error.get("type", "UNKNOWN_ERROR")
                cell_info["error_message"] = error.get("message", "Unknown error")
            elif "numberValue" in effective:
                cell_info["type"] = "number"
            elif "stringValue" in effective:
                cell_info["type"] = "string"
            elif "boolValue" in effective:
                cell_info["type"] = "boolean"

        # Extract user entered value (raw input)
        if "userEnteredValue" in cell_data:
            user_entered = cell_data["userEnteredValue"]
            cell_info["user_entered_value"] = user_entered

            # Check if it's a formula
            if "formulaValue" in user_entered:
                cell_info["formula"] = user_entered["formulaValue"]
                cell_info["is_formula"] = True
                cell_info["type"] = "formula"

        # Extract formatting
        if "effectiveFormat" in cell_data:
            cell_info["format"] = self._extract_format_details(cell_data["effectiveFormat"])

        # Extract hyperlink
        if "hyperlink" in cell_data:
            cell_info["hyperlink"] = cell_data["hyperlink"]

        # Extract note/comment
        if "note" in cell_data:
            cell_info["note"] = cell_data["note"]

        return cell_info

    def _extract_format_details(self, format_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract formatting details from effectiveFormat data.

        Args:
            format_data: effectiveFormat object from Sheets API

        Returns:
            Dictionary with formatting information
        """
        format_info = {}

        # Number format
        if "numberFormat" in format_data:
            number_format = format_data["numberFormat"]
            format_info["number_format"] = {
                "type": number_format.get("type", "TEXT"),
                "pattern": number_format.get("pattern", ""),
            }

        # Text format
        if "textFormat" in format_data:
            text_format = format_data["textFormat"]
            format_info["text_format"] = {
                "bold": text_format.get("bold", False),
                "italic": text_format.get("italic", False),
                "underline": text_format.get("underline", False),
                "strikethrough": text_format.get("strikethrough", False),
                "font_family": text_format.get("fontFamily", ""),
                "font_size": text_format.get("fontSize", 10),
            }

            # Text color
            if "foregroundColor" in text_format:
                color = text_format["foregroundColor"]
                format_info["text_color"] = {
                    "red": color.get("red", 0),
                    "green": color.get("green", 0),
                    "blue": color.get("blue", 0),
                    "alpha": color.get("alpha", 1),
                }

        # Background color
        if "backgroundColor" in format_data:
            bg_color = format_data["backgroundColor"]
            format_info["background_color"] = {
                "red": bg_color.get("red", 1),
                "green": bg_color.get("green", 1),
                "blue": bg_color.get("blue", 1),
                "alpha": bg_color.get("alpha", 1),
            }

        # Borders
        if "borders" in format_data:
            format_info["borders"] = format_data["borders"]

        # Horizontal alignment
        if "horizontalAlignment" in format_data:
            format_info["horizontal_alignment"] = format_data["horizontalAlignment"]

        # Vertical alignment
        if "verticalAlignment" in format_data:
            format_info["vertical_alignment"] = format_data["verticalAlignment"]

        return format_info
