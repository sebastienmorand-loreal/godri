"""MCP Server implementation for Godri."""

import asyncio
import json
import logging
from typing import List, Optional
import os
from mcp.server.fastmcp import FastMCP
from .auth_service_new import AuthService
from .drive_service import DriveService
from .docs_service import DocsService
from .sheets_service import SheetsService
from .slides_service import SlidesService
from .translate_service import TranslateService
from .speech_service import SpeechService
from .forms_service import FormsService

# Initialize FastMCP server
mcp = FastMCP("Godri")

# Global services - will be initialized on first use
auth_service: Optional[AuthService] = None
drive_service: Optional[DriveService] = None
docs_service: Optional[DocsService] = None
sheets_service: Optional[SheetsService] = None
slides_service: Optional[SlidesService] = None
translate_service: Optional[TranslateService] = None
speech_service: Optional[SpeechService] = None
forms_service: Optional[FormsService] = None

logger = logging.getLogger(__name__)


def _convert_color_to_rgb(color: str) -> dict:
    """Convert color (hex, name, or RGB) to Google Sheets API RGB format (0.0-1.0)."""
    import re

    # Common color names to RGB
    color_names = {
        "white": (1.0, 1.0, 1.0),
        "black": (0.0, 0.0, 0.0),
        "red": (1.0, 0.0, 0.0),
        "green": (0.0, 0.8, 0.0),
        "blue": (0.0, 0.0, 1.0),
        "yellow": (1.0, 1.0, 0.0),
        "cyan": (0.0, 1.0, 1.0),
        "magenta": (1.0, 0.0, 1.0),
        "orange": (1.0, 0.65, 0.0),
        "purple": (0.5, 0.0, 0.5),
        "pink": (1.0, 0.75, 0.8),
        "brown": (0.65, 0.16, 0.16),
        "gray": (0.5, 0.5, 0.5),
        "grey": (0.5, 0.5, 0.5),
        "lightgray": (0.83, 0.83, 0.83),
        "lightgrey": (0.83, 0.83, 0.83),
        "darkgray": (0.66, 0.66, 0.66),
        "darkgrey": (0.66, 0.66, 0.66),
    }

    color_lower = color.lower().strip()

    # Check if it's a named color
    if color_lower in color_names:
        r, g, b = color_names[color_lower]
        return {"red": r, "green": g, "blue": b}

    # Check if it's a hex color
    hex_match = re.match(r"^#?([0-9a-fA-F]{6})$", color.strip())
    if hex_match:
        hex_color = hex_match.group(1)
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return {"red": r, "green": g, "blue": b}

    # Default to black if color not recognized
    return {"red": 0.0, "green": 0.0, "blue": 0.0}


async def initialize_services():
    """Initialize all Google services."""
    global auth_service, drive_service, docs_service, sheets_service, slides_service, translate_service, speech_service, forms_service

    if auth_service is not None:
        return  # Already initialized

    # Initialize with new async auth service
    auth_service = AuthService()
    drive_service = DriveService(auth_service)
    docs_service = DocsService(auth_service)
    sheets_service = SheetsService(auth_service)
    slides_service = SlidesService(auth_service)
    translate_service = TranslateService(auth_service)
    speech_service = SpeechService(auth_service)
    forms_service = FormsService(auth_service, translate_service)

    await drive_service.initialize()
    await docs_service.initialize()
    await sheets_service.initialize()
    await slides_service.initialize()
    await translate_service.initialize()
    await speech_service.initialize()
    await forms_service.initialize()

    logger.info("All services initialized for MCP server")


# Drive tools
@mcp.tool(name="drive_search")
async def drive_search(query: str = "", name: str = "", mime_type: str = "", limit: int = 20) -> str:
    """Search for files in Google Drive. Use query for general search or name for exact filename matching. Optionally filter by MIME type."""
    await initialize_services()

    if name:
        result = await drive_service.search_by_name(name, mime_type)
    else:
        result = await drive_service.search_files(query, limit)

    return str(result)


@mcp.tool(name="drive_upload")
async def drive_upload(file_path: str, folder_id: str = "", name: str = "") -> str:
    """Upload a local file to Google Drive. Optionally specify a parent folder ID and custom name."""
    await initialize_services()

    result = await drive_service.upload_file(file_path, folder_id if folder_id else None, name if name else None)
    return str(result)


@mcp.tool(name="drive_download")
async def drive_download(file_id: str, output_path: str, smart: bool = False) -> str:
    """Download a file from Google Drive. Use smart=True for automatic format conversion of Google Workspace files."""
    await initialize_services()

    if smart:
        result = await drive_service.download_file_smart(file_id, output_path)
    else:
        result = await drive_service.download_file(file_id, output_path)
    return f"File downloaded successfully to: {result}"


@mcp.tool(name="drive_folder_create")
async def drive_folder_create(name: str, parent_id: str = "") -> str:
    """Create a new folder in Google Drive. Optionally specify a parent folder ID."""
    await initialize_services()

    result = await drive_service.create_folder(name, parent_id if parent_id else None)
    return str(result)


@mcp.tool(name="drive_folder_delete")
async def drive_folder_delete(file_id: str) -> str:
    """Delete a file or folder from Google Drive by its ID."""
    await initialize_services()

    success = await drive_service.delete_file(file_id)
    return "File/folder deleted successfully!" if success else "Failed to delete file/folder."


# Docs tools
@mcp.tool(name="docs_createdocument")
async def docs_createdocument(title: str, folder_id: str = "", content: str = "", markdown: bool = False) -> str:
    """Create a new Google Doc with specified title. Optionally add initial content and specify if content is markdown."""
    await initialize_services()

    result = await docs_service.create_document(title, folder_id if folder_id else None)

    if content:
        if markdown:
            await docs_service.insert_markdown_text(result["documentId"], content)
        else:
            await docs_service.insert_text(result["documentId"], content)

    return str(result)


@mcp.tool(name="docs_read")
async def docs_read(document_id: str, plain_text: bool = False) -> str:
    """Read content from a Google Doc. Set plain_text=True to get only text without formatting."""
    await initialize_services()

    if plain_text:
        return await docs_service.get_document_text(document_id)
    else:
        document = await docs_service.get_document(document_id)
        content = await docs_service.get_document_text(document_id)
        return f"Document: {document.get('title', 'Untitled')}\nContent:\n{content}"


@mcp.tool(name="docs_update")
async def docs_update(
    document_id: str, content: str, markdown: bool = False, replace: bool = False, index: int = 1
) -> str:
    """Update Google Doc content. Set replace=True to replace entire document, otherwise content is appended. Use index to specify insertion position."""
    await initialize_services()

    if replace:
        if markdown:
            docs_service.set_markdown_content(document_id, content)
        else:
            docs_service.set_document_content(document_id, content)
        return "Document content replaced successfully."
    else:
        if markdown:
            if index == 1:
                document = docs_service.get_document(document_id)
                end_index = document.get("body", {}).get("content", [{}])[-1].get("endIndex", 1) - 1
                docs_service.insert_markdown_text(document_id, content, end_index)
            else:
                docs_service.insert_markdown_text(document_id, content, index)
        else:
            if index == 1:
                docs_service.append_text(document_id, content)
            else:
                docs_service.insert_text(document_id, content, index)
        return "Content added to document successfully."


@mcp.tool(name="docs_translate")
async def docs_translate(
    document_id: str, target_language: str, source_language: str = "", start_index: int = 1, end_index: int = 0
) -> str:
    """Translate Google Doc content to target language. Optionally specify source language and text range for partial translation."""
    await initialize_services()

    result = await docs_service.translate_document(
        document_id,
        target_language,
        source_language if source_language else None,
        start_index,
        end_index if end_index > 0 else None,
    )

    return f"Document translated successfully to {target_language}" if result else "No content was translated"


# Sheets tools
@mcp.tool(name="sheets_createdocument")
async def sheets_createdocument(title: str, folder_id: str = "") -> str:
    """Create a new Google Spreadsheet with specified title. Optionally specify parent folder ID."""
    await initialize_services()

    result = await sheets_service.create_spreadsheet(title, folder_id if folder_id else None)
    return str(result)


@mcp.tool(name="sheets_read")
async def sheets_read(spreadsheet_id: str) -> str:
    """List all sheets in a Google Spreadsheet with their properties."""
    await initialize_services()

    result = await sheets_service.list_sheets(spreadsheet_id)
    return str(result)


@mcp.tool(name="sheets_create")
async def sheets_create(spreadsheet_id: str, sheet_name: str) -> str:
    """Create a new sheet within an existing Google Spreadsheet."""
    await initialize_services()

    result = await sheets_service.create_sheet(spreadsheet_id, sheet_name)
    return f"Sheet '{sheet_name}' created successfully"


@mcp.tool(name="sheets_delete")
async def sheets_delete(spreadsheet_id: str, sheet_name: str) -> str:
    """Delete a sheet from a Google Spreadsheet by name."""
    await initialize_services()

    sheet_id = sheets_service.get_sheet_id_by_name(spreadsheet_id, sheet_name)
    if sheet_id is None:
        return f"Sheet '{sheet_name}' not found"

    sheets_service.delete_sheet(spreadsheet_id, sheet_id)
    return f"Sheet '{sheet_name}' deleted successfully"


@mcp.tool(name="sheets_hide")
async def sheets_hide(spreadsheet_id: str, sheet_name: str) -> str:
    """Hide a sheet in a Google Spreadsheet."""
    await initialize_services()

    sheet_id = sheets_service.get_sheet_id_by_name(spreadsheet_id, sheet_name)
    if sheet_id is None:
        return f"Sheet '{sheet_name}' not found"

    sheets_service.hide_sheet(spreadsheet_id, sheet_id)
    return f"Sheet '{sheet_name}' hidden successfully"


@mcp.tool(name="sheets_unhide")
async def sheets_unhide(spreadsheet_id: str, sheet_name: str) -> str:
    """Unhide a sheet in a Google Spreadsheet."""
    await initialize_services()

    sheet_id = sheets_service.get_sheet_id_by_name(spreadsheet_id, sheet_name)
    if sheet_id is None:
        return f"Sheet '{sheet_name}' not found"

    sheets_service.unhide_sheet(spreadsheet_id, sheet_id)
    return f"Sheet '{sheet_name}' unhidden successfully"


@mcp.tool(name="sheets_values_read")
async def sheets_values_read(
    spreadsheet_id: str, sheet_name: str = "", range_name: str = "", as_json: bool = True
) -> str:
    """Read data from a Google Sheet. Specify sheet_name for entire sheet or range_name for specific range (e.g., 'A1:C10').

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet_name: Name of the sheet to read (for entire sheet)
        range_name: A1 notation range (e.g., 'A1:C10', 'Sheet1!B2:D5')
        as_json: Return structured JSON format (default True) or plain string

    Returns:
        JSON-formatted table data as List[List] or plain string representation
    """
    await initialize_services()

    if range_name:
        values = sheets_service.get_values(spreadsheet_id, range_name)
    else:
        values = sheets_service.read_entire_sheet(spreadsheet_id, sheet_name)

    if not values:
        return "No data found."

    if as_json:
        import json

        return json.dumps(values, ensure_ascii=False, indent=2)
    else:
        return str(values)


@mcp.tool(name="sheets_values_set")
async def sheets_values_set(spreadsheet_id: str, range_name: str, values: str) -> str:
    """Set VALUES (not formulas) in Google Sheet cells. For formulas, use sheets_set_formula instead.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        range_name: A1 notation range (e.g., 'A1:C3', 'Sheet1!B2:D4')
        values: Table data as JSON List[List] (e.g., '[["A1","B1"],["A2","B2"]]') or comma-separated for single row

    Examples:
        Single row: values = "Value1,Value2,Value3"
        Multiple rows: values = '[["Row1Col1","Row1Col2"],["Row2Col1","Row2Col2"]]'
        Numbers and text: values = '[["Name","Age","Score"],["John","25","95.5"]]'

    Note:
        This tool sets LITERAL VALUES only. Any text starting with "=" will be treated as text, not a formula.
        To set formulas, use the sheets_set_formula tool instead.

    Returns:
        Success message with number of updated cells
    """
    await initialize_services()

    # Parse values - support JSON List[List] or comma-separated for single row
    if values.startswith("["):
        import json

        try:
            parsed_values = json.loads(values)
            # Ensure it's a list of lists
            if parsed_values and not isinstance(parsed_values[0], list):
                parsed_values = [parsed_values]  # Convert single row to List[List]
        except json.JSONDecodeError:
            return 'Error: Invalid JSON format. Use format like \'[["A1","B1"],["A2","B2"]]\' for table data.'
    else:
        # Single row comma-separated
        parsed_values = [v.strip() for v in values.split(",")]

    # Always set as values (not formulas) - uses RAW input option
    result = await sheets_service.set_values_in_range(spreadsheet_id, range_name, parsed_values)

    return f"Values set successfully in range '{range_name}'. Updated {result.get('updatedCells', 0)} cells"


@mcp.tool(name="sheets_set_formula")
async def sheets_set_formula(spreadsheet_id: str, range_name: str, formulas: str) -> str:
    """Set FORMULAS (not values) in Google Sheet cells. For literal values, use sheets_values_set instead.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        range_name: A1 notation range (e.g., 'A1', 'A1:C3', 'Sheet1!B2:D4')
        formulas: Single formula or JSON List[List] of formulas for table format

    Examples:
        Single formula: formulas = "SUM(A1:A10)"
        Formula with quotes: formulas = "'B8/1073741824" (quotes are automatically cleaned)
        Multiple formulas: formulas = '[["=A1+B1","=A1*2"],["=A2+B2","=A2*2"]]'
        Complex formulas: formulas = '[["=VLOOKUP(A1,Sheet2!A:B,2,FALSE)","=IF(B1>0,\"Positive\",\"Negative\")"]]'

    Note:
        This tool sets FORMULAS that will be calculated by Google Sheets.
        - Leading quotes (', ") are automatically removed to prevent display issues
        - Formulas are automatically prefixed with "=" if not provided
        - Use sheets_values_set for literal text/numbers
        - Supports both single formulas and formula tables

    Returns:
        Success message with number of updated cells
    """
    await initialize_services()

    # Parse formulas - support single formula or JSON List[List] for table format
    if formulas.startswith("["):
        import json

        try:
            parsed_formulas = json.loads(formulas)
            # Ensure it's a list of lists
            if parsed_formulas and not isinstance(parsed_formulas[0], list):
                parsed_formulas = [parsed_formulas]  # Convert single row to List[List]
            result = await sheets_service.set_formulas_in_range(spreadsheet_id, range_name, parsed_formulas)
        except json.JSONDecodeError:
            return 'Error: Invalid JSON format. Use format like \'[["=A1+B1","=A1*2"]]\' for formula tables.'
    else:
        # Single formula
        result = await sheets_service.set_formulas_in_range(spreadsheet_id, range_name, formulas)

    return f"Formulas set successfully in range '{range_name}'. Updated {result.get('updatedCells', 0)} cells"


@mcp.tool(name="sheets_translate")
async def sheets_translate(
    spreadsheet_id: str, range_name: str, target_language: str, source_language: str = ""
) -> str:
    """Translate content in a Google Sheet range to target language."""
    await initialize_services()

    result = await sheets_service.translate_range(
        spreadsheet_id, range_name, target_language, source_language if source_language else None
    )

    if result:
        updated_cells = result.get("updatedCells", 0)
        return f"Range '{range_name}' translated successfully to {target_language}. Updated {updated_cells} cells"
    else:
        return "No content was translated in the specified range"


@mcp.tool(name="sheets_values_copy")
async def sheets_values_copy(
    spreadsheet_id: str, source_range: str, destination_range: str, copy_type: str = "all"
) -> str:
    """Copy values, formulas, formats, or all between ranges in Google Sheets.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        source_range: Source range in A1 notation (e.g., 'A1:C3', 'Sheet1!A1:C3')
        destination_range: Destination range in A1 notation (e.g., 'E1:G3', 'Sheet2!E1:G3')
        copy_type: What to copy - 'values', 'formulas', 'formats', 'all' (default: 'all')

    Examples:
        Copy all: copy_type='all' (copies values, formulas, and formatting)
        Values only: copy_type='values' (copies only the calculated values)
        Formulas only: copy_type='formulas' (copies formulas, maintains references)
        Formats only: copy_type='formats' (copies only formatting, no content)

    Returns:
        Success message with copy operation details
    """
    await initialize_services()

    try:
        result = await sheets_service.copy_range_values(spreadsheet_id, source_range, destination_range, copy_type)

        return f"✅ Range '{source_range}' copied to '{destination_range}' successfully\nCopy type: {result['copy_type']} (paste type: {result['paste_type']})"

    except Exception as e:
        return f"❌ Error copying range: {str(e)}"


# Slides tools
@mcp.tool(name="slides_createdocument")
async def slides_createdocument(title: str, folder_id: str = "", theme: str = "STREAMLINE") -> str:
    """Create a new Google Slides presentation with specified title and theme. Available themes: SIMPLE_LIGHT, SIMPLE_DARK, STREAMLINE, FOCUS, etc."""
    await initialize_services()

    result = await slides_service.create_presentation(title, folder_id if folder_id else None, theme)
    return str(result)


@mcp.tool(name="slides_download")
async def slides_download(presentation_id: str, format_type: str = "pdf", output_path: str = "") -> str:
    """Download Google Slides presentation in specified format (pdf, pptx, png, jpeg). For images, output_path should be a directory."""
    await initialize_services()

    result = await slides_service.download_presentation(presentation_id, format_type, output_path)
    return str(result)


@mcp.tool(name="slides_add")
async def slides_add(presentation_id: str, layout: str = "BLANK", position: int = -1) -> str:
    """Add a new slide to presentation. Available layouts: BLANK, TITLE, TITLE_AND_BODY, etc. Position -1 adds at end."""
    await initialize_services()

    pos = None if position == -1 else position
    result = await slides_service.add_slide(presentation_id, layout, pos)
    return "Slide added successfully"


@mcp.tool(name="slides_remove")
async def slides_remove(presentation_id: str, slide_id: str) -> str:
    """Remove a slide from presentation by slide ID."""
    await initialize_services()

    result = await slides_service.remove_slide(presentation_id, slide_id)
    return f"Slide {slide_id} removed successfully"


@mcp.tool(name="slides_content_add")
async def slides_content_add(
    presentation_id: str,
    slide_id: str,
    content_type: str,
    content: str,
    x: float = 100,
    y: float = 100,
    width: float = 300,
    height: float = 200,
) -> str:
    """Add content to a slide. content_type: 'text', 'image', or 'table'. For table, content should be 'ROWSxCOLS' format (e.g., '3x4')."""
    await initialize_services()

    if content_type == "text":
        result = await slides_service.add_text_content(presentation_id, slide_id, content, x, y, width, height)
        return f"Text content added to slide {slide_id}"
    elif content_type == "image":
        result = await slides_service.add_image_content(presentation_id, slide_id, content, x, y, width, height)
        return f"Image content added to slide {slide_id}"
    elif content_type == "table":
        if "x" in content.lower():
            rows, cols = map(int, content.lower().split("x"))
            result = await slides_service.add_table_content(presentation_id, slide_id, rows, cols, x, y, width, height)
            return f"Table ({rows}x{cols}) added to slide {slide_id}"
        else:
            return "Table content must be in format 'ROWSxCOLS' (e.g., '3x4')"
    else:
        return f"Unknown content type: {content_type}"


@mcp.tool(name="slides_content_list")
async def slides_content_list(presentation_id: str, slide_identifiers: str = "", all_slides: bool = False) -> str:
    """List content elements in slide(s). Use slide_identifiers for specific slides (numbers, IDs, or ranges like '1-3,5' or '2' or '1,3,5'), or all_slides=True for all slides.
    Returns detailed content including text, images, tables with formatting, size, and position information."""
    await initialize_services()

    try:
        if all_slides or not slide_identifiers:
            # List content for all slides
            results = slides_service.list_multiple_slides_content(presentation_id)
            if not results:
                return "No slides found in presentation"

            output = []
            for slide_key, content_elements in results.items():
                output.append(f"=== {slide_key} ===")
                if not content_elements:
                    output.append("  No content elements found")
                else:
                    for i, element in enumerate(content_elements):
                        output.append(f"  Element {i+1}:")
                        output.append(f"    ID: {element['id']}")
                        output.append(f"    Type: {element['type']}")

                        if "size" in element:
                            size = element["size"]
                            output.append(f"    Size: {size['width']} x {size['height']}")

                        if "position" in element:
                            pos = element["position"]
                            output.append(f"    Position: ({pos['x']}, {pos['y']})")

                        if "text_content" in element and element["text_content"]:
                            output.append(f"    Text: \"{element['text_content']}\"")

                        if "shape_type" in element:
                            output.append(f"    Shape: {element['shape_type']}")

                        if "table_info" in element:
                            table_info = element["table_info"]
                            output.append(f"    Table: {table_info['rows']} rows x {table_info['columns']} columns")
                            if "table_contents" in element:
                                for row_idx, row in enumerate(element["table_contents"]):
                                    row_text = " | ".join(cell.strip() if cell.strip() else "(empty)" for cell in row)
                                    output.append(f"      Row {row_idx+1}: {row_text}")

                        if "image_properties" in element:
                            img_props = element["image_properties"]
                            output.append(f"    Image: {img_props.get('content_url', 'N/A')}")

                        output.append("")  # Empty line between elements
                output.append("")  # Empty line between slides

            return "\n".join(output)
        else:
            # Parse slide identifiers to support ranges and multiple slides
            identifiers = [id.strip() for id in slide_identifiers.split(",")]

            # Use multiple slides handler to support ranges
            results = slides_service.list_multiple_slides_content(presentation_id, identifiers)
            if not results:
                return "No content found for specified slides"

            output = []
            for slide_key, content_elements in results.items():
                output.append(f"=== {slide_key} ===")
                if not content_elements:
                    output.append("  No content elements found")
                else:
                    for i, element in enumerate(content_elements):
                        output.append(f"  Element {i+1}:")
                        output.append(f"    ID: {element['id']}")
                        output.append(f"    Type: {element['type']}")

                        if "size" in element:
                            size = element["size"]
                            output.append(f"    Size: {size['width']} x {size['height']}")

                        if "position" in element:
                            pos = element["position"]
                            output.append(f"    Position: ({pos['x']}, {pos['y']})")

                        if "text_content" in element and element["text_content"]:
                            output.append(f"    Text: \"{element['text_content']}\"")

                            if "text_details" in element:
                                for j, detail in enumerate(element["text_details"]):
                                    if detail["content"].strip():
                                        style_info = ""
                                        if "style" in detail:
                                            style = detail["style"]
                                            style_parts = []
                                            if style.get("bold"):
                                                style_parts.append("bold")
                                            if style.get("italic"):
                                                style_parts.append("italic")
                                            if style.get("font_family"):
                                                style_parts.append(f"font:{style['font_family']}")
                                            if style.get("font_size"):
                                                style_parts.append(f"size:{style['font_size']}")
                                            if style_parts:
                                                style_info = f" ({', '.join(style_parts)})"
                                        output.append(f"      Text {j+1}: \"{detail['content'].strip()}\"{style_info}")

                        if "shape_type" in element:
                            output.append(f"    Shape: {element['shape_type']}")
                            if "shape_properties" in element and element["shape_properties"]:
                                props = element["shape_properties"]
                                if "background_color" in props:
                                    output.append(f"    Background: {props['background_color']}")

                        if "table_info" in element:
                            table_info = element["table_info"]
                            output.append(f"    Table: {table_info['rows']} rows x {table_info['columns']} columns")
                            if "table_contents" in element:
                                output.append(f"    Contents:")
                                for row_idx, row in enumerate(element["table_contents"]):
                                    row_text = " | ".join(cell.strip() if cell.strip() else "(empty)" for cell in row)
                                    output.append(f"      Row {row_idx+1}: {row_text}")

                        if "image_properties" in element:
                            img_props = element["image_properties"]
                            output.append(f"    Image:")
                            if img_props.get("content_url"):
                                output.append(f"      Content URL: {img_props['content_url']}")
                            if img_props.get("source_url"):
                                output.append(f"      Source URL: {img_props['source_url']}")

                        output.append("")  # Empty line between elements
                output.append("")  # Empty line between slides

            return "\n".join(output)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Failed to list slide content: {e}"


# Copy tools
@mcp.tool(name="slides_copy")
async def slides_copy(
    source_presentation_id: str,
    target_presentation_id: str,
    slide_identifiers: str,
    preserve_theme: bool = True,
    link_to_source: bool = False,
    target_position: int = -1,
) -> str:
    """Copy slides from one presentation to another. slide_identifiers can be numbers, IDs, or ranges (e.g., '1-3,5', '2', '1,3,5').
    Set preserve_theme=False to use target presentation theme. Set link_to_source=True to link slides to source. Position -1 adds at end.
    """
    await initialize_services()

    # Parse slide identifiers into list
    identifiers = [id.strip() for id in slide_identifiers.split(",")]

    result = await slides_service.copy_slides(
        source_presentation_id,
        target_presentation_id,
        identifiers,
        preserve_theme=preserve_theme,
        link_to_source=link_to_source,
        target_position=None if target_position == -1 else target_position,
    )

    return f"Successfully copied {result['copied_slides']} slides. New slide IDs: {', '.join(result['new_slide_ids'])}"


@mcp.tool(name="sheets_copy")
async def sheets_copy(
    source_spreadsheet_id: str,
    target_spreadsheet_id: str,
    sheet_names: str,
    target_name: str = "",
    preserve_formatting: bool = True,
) -> str:
    """Copy sheets from one spreadsheet to another. sheet_names is comma-separated list of sheet names to copy.
    For single sheet copy, optionally specify target_name. Set preserve_formatting=False to ignore formatting."""
    await initialize_services()

    # Parse sheet names into list
    names = [name.strip() for name in sheet_names.split(",")]

    if len(names) == 1 and target_name:
        # Single sheet copy with custom name
        result = await sheets_service.copy_sheet(
            source_spreadsheet_id,
            target_spreadsheet_id,
            names[0],
            target_sheet_name=target_name,
            preserve_formatting=preserve_formatting,
        )
        return f"Successfully copied sheet '{result['source_sheet']}' to '{result['target_sheet']}' (ID: {result['new_sheet_id']})"
    else:
        # Multiple sheets copy
        result = await sheets_service.copy_multiple_sheets(
            source_spreadsheet_id, target_spreadsheet_id, names, preserve_formatting=preserve_formatting
        )

        output = [f"Sheet copy operation completed:"]
        output.append(f"Total sheets: {result['total_sheets']}")
        output.append(f"Successful copies: {result['successful_copies']}")
        output.append(f"Failed copies: {result['total_sheets'] - result['successful_copies']}")

        for sheet_result in result["results"]:
            if "error" in sheet_result:
                output.append(f"  ❌ {sheet_result['source_sheet']}: {sheet_result['error']}")
            else:
                output.append(f"  ✅ {sheet_result['source_sheet']} → {sheet_result['target_sheet']}")

        return "\n".join(output)


# Sheets formatting tools
@mcp.tool(name="sheets_format_range")
async def sheets_format_range(
    spreadsheet_id: str,
    range_name: str,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    font_family: str = "",
    font_size: int = 0,
    text_color: str = "",
    background_color: str = "",
    horizontal_align: str = "",
    vertical_align: str = "",
    borders: str = "",
    number_format: str = "",
) -> str:
    """Apply formatting to a range in Google Sheets using A1 notation.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        range_name: A1 notation range (e.g., 'A1:C3', 'Sheet1!B2:D4', 'A:A' for entire column, '1:1' for entire row)
        bold: Make text bold
        italic: Make text italic
        underline: Add underline
        strikethrough: Add strikethrough
        font_family: Font family name (e.g., 'Arial', 'Times New Roman')
        font_size: Font size in points
        text_color: Text color (hex like '#FF0000' or name like 'red')
        background_color: Background color (hex like '#FFFF00' or name like 'yellow')
        horizontal_align: Horizontal alignment ('LEFT', 'CENTER', 'RIGHT')
        vertical_align: Vertical alignment ('TOP', 'MIDDLE', 'BOTTOM')
        borders: Border style ('all', 'thick', 'none')
        number_format: Number format pattern (e.g., '$#,##0.00', '0.00%', 'mm/dd/yyyy')

    Examples:
        Header row: bold=True, background_color='lightgray', horizontal_align='CENTER'
        Currency column: number_format='$#,##0.00'
        Entire column bold: range_name='A:A', bold=True

    Returns:
        Success message confirming formatting application
    """
    await initialize_services()

    # Build format options dictionary using proper Google Sheets API format
    format_options = {}

    # Text formatting
    if bold or italic or underline or strikethrough or font_family or font_size or text_color:
        text_format = {}
        if bold:
            text_format["bold"] = True
        if italic:
            text_format["italic"] = True
        if underline:
            text_format["underline"] = True
        if strikethrough:
            text_format["strikethrough"] = True
        if font_family:
            text_format["fontFamily"] = font_family
        if font_size > 0:
            text_format["fontSize"] = font_size
        if text_color:
            # Convert color to RGB format
            rgb_color = _convert_color_to_rgb(text_color)
            text_format["foregroundColor"] = rgb_color
        format_options["textFormat"] = text_format

    # Background color
    if background_color:
        rgb_color = _convert_color_to_rgb(background_color)
        format_options["backgroundColor"] = rgb_color

    # Alignment
    if horizontal_align:
        format_options["horizontalAlignment"] = horizontal_align.upper()
    if vertical_align:
        format_options["verticalAlignment"] = vertical_align.upper()

    # Borders
    if borders:
        if borders.lower() == "all":
            format_options["borders"] = {
                "top": {"style": "SOLID", "width": 1},
                "bottom": {"style": "SOLID", "width": 1},
                "left": {"style": "SOLID", "width": 1},
                "right": {"style": "SOLID", "width": 1},
            }
        elif borders.lower() == "thick":
            format_options["borders"] = {
                "top": {"style": "SOLID", "width": 3},
                "bottom": {"style": "SOLID", "width": 3},
                "left": {"style": "SOLID", "width": 3},
                "right": {"style": "SOLID", "width": 3},
            }
        elif borders.lower() == "none":
            format_options["borders"] = {
                "top": {"style": "NONE"},
                "bottom": {"style": "NONE"},
                "left": {"style": "NONE"},
                "right": {"style": "NONE"},
            }

    # Number format
    if number_format:
        format_options["numberFormat"] = {"pattern": number_format}

    if not format_options:
        return "No formatting options specified. Please provide at least one formatting parameter."

    try:
        result = await sheets_service.format_range(spreadsheet_id, range_name, format_options)
        return f"Formatting applied successfully to range '{range_name}'"
    except Exception as e:
        return f"Error applying formatting: {str(e)}"


@mcp.tool(name="sheets_copy_format")
async def sheets_copy_format(spreadsheet_id: str, source_range: str, target_range: str) -> str:
    """Copy formatting from one range to another in Google Sheets.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        source_range: A1 notation source range (e.g., 'A1:C3', 'Sheet1!B2:D4')
        target_range: A1 notation target range (e.g., 'E1:G3', 'Sheet2!F2:H4')

    Examples:
        Copy header formatting: source_range='A1:D1', target_range='A5:D5'
        Copy table formatting: source_range='Sheet1!A1:C10', target_range='Sheet2!A1:C10'

    Note:
        If source and target ranges have different sizes, formatting will be applied with wrapping/clipping as needed.

    Returns:
        Success message confirming format copy operation
    """
    await initialize_services()

    try:
        result = await sheets_service.copy_format(spreadsheet_id, source_range, target_range)
        return f"Formatting copied successfully from '{source_range}' to '{target_range}'"
    except Exception as e:
        return f"Error copying formatting: {str(e)}"


@mcp.tool(name="sheets_set_column_width")
async def sheets_set_column_width(
    spreadsheet_id: str, sheet_name: str, start_column: str, end_column: str, width: int
) -> str:
    """Set column width(s) in Google Sheets.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet_name: Name of the sheet
        start_column: Starting column letter (e.g., 'A')
        end_column: Ending column letter (e.g., 'C') - use same as start_column for single column
        width: Width in pixels

    Examples:
        Single column: start_column='A', end_column='A', width=150
        Multiple columns: start_column='B', end_column='D', width=100

    Returns:
        Success message confirming column width change
    """
    await initialize_services()

    try:
        # Get sheet ID
        sheet_id = sheets_service.get_sheet_id_by_name(spreadsheet_id, sheet_name)
        if sheet_id is None:
            return f"Error: Sheet '{sheet_name}' not found"

        # Convert column letters to indices (A=0, B=1, etc.)
        start_col_index = ord(start_column.upper()) - ord("A")
        end_col_index = ord(end_column.upper()) - ord("A")

        result = await sheets_service.set_column_width(spreadsheet_id, sheet_id, start_col_index, end_col_index, width)

        if start_column == end_column:
            return f"Column '{start_column}' width set to {width} pixels"
        else:
            return f"Columns '{start_column}' to '{end_column}' width set to {width} pixels"
    except Exception as e:
        return f"Error setting column width: {str(e)}"


# CSV Import tools
@mcp.tool(name="sheets_import_csv_file")
async def sheets_import_csv_file(
    csv_file_path: str, spreadsheet_id: str = "", sheet_name: str = "Sheet1", folder_id: str = ""
) -> str:
    """Import a CSV file to Google Sheets.

    Args:
        csv_file_path: Path to local CSV file to import
        spreadsheet_id: Target spreadsheet ID (creates new spreadsheet if empty)
        sheet_name: Target sheet name (default: Sheet1)
        folder_id: Folder ID for new spreadsheet (if creating new)

    Examples:
        Import to new spreadsheet: csv_file_path="/path/to/data.csv"
        Import to existing sheet: csv_file_path="/path/to/data.csv", spreadsheet_id="abc123", sheet_name="Data"

    Returns:
        Success message with import details and spreadsheet information
    """
    await initialize_services()

    try:
        result = await sheets_service.import_csv_file(
            csv_file_path, spreadsheet_id if spreadsheet_id else None, sheet_name, folder_id if folder_id else None
        )

        if result.get("created_from_csv"):
            return f"✅ Created new spreadsheet '{result['name']}' from CSV file\nSpreadsheet ID: {result['spreadsheet_id']}\nOriginal file: {result['original_file']}"
        else:
            return f"✅ CSV file imported successfully to sheet '{result['sheet_name']}'\nRange: {result['range']}\nImported {result['rows_imported']} rows and {result['columns_imported']} columns\nUpdated {result['cells_updated']} cells"
    except Exception as e:
        return f"❌ Error importing CSV file: {str(e)}"


@mcp.tool(name="sheets_import_csv_data")
async def sheets_import_csv_data(
    spreadsheet_id: str, csv_data: str, sheet_name: str = "Sheet1", start_range: str = "A1"
) -> str:
    """Import CSV data string to Google Sheets.

    Args:
        spreadsheet_id: Target spreadsheet ID
        csv_data: CSV content as string (e.g., "Name,Age\nJohn,25\nJane,30")
        sheet_name: Target sheet name (default: Sheet1)
        start_range: Starting cell range for import (default: A1)

    Examples:
        Simple data: csv_data="Name,Age\nJohn,25\nJane,30", spreadsheet_id="abc123"
        Specific location: csv_data="Product,Price\nApple,1.50", start_range="B5"

    Returns:
        Success message with import details
    """
    await initialize_services()

    try:
        result = await sheets_service.import_csv_data(csv_data, spreadsheet_id, sheet_name, start_range)

        return f"✅ CSV data imported successfully to sheet '{result['sheet_name']}'\nRange: {result['range']}\nImported {result['rows_imported']} rows and {result['columns_imported']} columns\nUpdated {result['cells_updated']} cells"
    except Exception as e:
        return f"❌ Error importing CSV data: {str(e)}"


@mcp.tool(name="sheets_rename")
async def sheets_rename(spreadsheet_id: str, sheet_name: str, new_name: str) -> str:
    """Rename a sheet in Google Sheets.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet_name: Current name of the sheet to rename
        new_name: New name for the sheet

    Examples:
        Rename sheet: spreadsheet_id="abc123", sheet_name="Sheet1", new_name="Data Sheet"
        Rename with spaces: sheet_name="Old Name", new_name="New Name"

    Returns:
        Success message confirming the sheet rename operation
    """
    await initialize_services()

    try:
        result = await sheets_service.rename_sheet(spreadsheet_id, sheet_name, new_name)
        return f"✅ Sheet '{sheet_name}' renamed to '{new_name}' successfully"
    except Exception as e:
        return f"❌ Error renaming sheet: {str(e)}"


# Comprehensive range reading tool
@mcp.tool(name="sheets_read_range_details")
async def sheets_read_range_details(spreadsheet_id: str, range_name: str) -> str:
    """Get comprehensive details about a range including formulas, values, formatting, and errors.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        range_name: A1 notation range (e.g., 'A1', 'A1:C3', 'Sheet1!B2:D4')

    Returns:
        JSON-formatted detailed information about each cell in the range including:
        - Cell address (A1 notation)
        - Display value (what user sees)
        - Effective value (calculated result)
        - User entered value (raw input)
        - Formula (if cell contains formula)
        - Error information (if formula has errors)
        - Complete formatting details
        - Hyperlinks and notes

    Examples:
        Single cell: range_name='A1'
        Range: range_name='A1:C5'
        Specific sheet: range_name='Sheet2!B2:D10'
        Entire column: range_name='A:A'
        Entire row: range_name='1:1'

    Note:
        This tool provides complete cell information including formulas, calculated values,
        formatting, and error details. Use this when you need to understand the full
        state of cells including their formulas and formatting.
    """
    await initialize_services()

    try:
        result = await sheets_service.get_range_details(spreadsheet_id, range_name)

        # Format the output for better readability
        import json

        # Create a more structured output
        output = {
            "range_info": {
                "range": result["range"],
                "spreadsheet_id": result["spreadsheet_id"],
                "sheet_name": result["sheet_name"],
                "total_cells": len(result["cells"]),
            },
            "cells": result["cells"],
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"❌ Error reading range details: {str(e)}"


# Translation tool
@mcp.tool(name="translate_text")
async def translate_text(text: str, target_language: str, source_language: str = "") -> str:
    """Translate text using Google Translate. Specify target language code (e.g., 'fr', 'es'). Source language is auto-detected if not specified."""
    await initialize_services()

    result = await translate_service.translate_text(text, target_language, source_language if source_language else None)
    return str(result)


# Speech-to-Text tool
@mcp.tool(name="speech_to_text")
async def speech_to_text(
    audio_file_path: str,
    language_code: str = "auto",
    enable_punctuation: bool = True,
    enable_word_timing: bool = False,
    use_long_running: bool = False,
) -> str:
    """Transcribe audio file to text using Google Speech-to-Text API.

    Args:
        audio_file_path: Path to audio file (MP3, WAV, OPUS, FLAC)
        language_code: Language code or shortcut (e.g., 'en', 'fr', 'french', 'en-US', 'fr-FR', 'es-ES'). Use 'auto' for automatic detection.
        enable_punctuation: Add automatic punctuation to transcription
        enable_word_timing: Include word timing information in response
        use_long_running: Force long-running transcription for large files

    Examples:
        Basic transcription: audio_file_path="recording.mp3"
        French audio: audio_file_path="french.wav", language_code="fr"
        Spanish audio: audio_file_path="spanish.mp3", language_code="spanish"
        Full code: audio_file_path="recording.opus", language_code="fr-FR"
        With timing: audio_file_path="meeting.opus", enable_word_timing=True
        Long audio: audio_file_path="lecture.mp3", use_long_running=True

    Returns:
        JSON-formatted transcription results with confidence scores and metadata
    """
    await initialize_services()

    try:
        # Check if file exists
        import os

        if not os.path.exists(audio_file_path):
            return f"❌ Error: Audio file not found: {audio_file_path}"

        # Detect audio properties
        properties = speech_service.detect_audio_properties(audio_file_path)

        # Choose transcription method
        if use_long_running or properties["recommended_method"] == "long":
            result = await speech_service.transcribe_audio_long(
                audio_file_path, language_code, enable_punctuation, enable_word_timing, None, properties
            )
        else:
            result = await speech_service.transcribe_audio_file(
                audio_file_path, language_code, enable_punctuation, enable_word_timing, None, properties
            )

        # Format response
        import json

        # Create structured output
        output = {
            "audio_info": {
                "file_path": result["audio_file"],
                "encoding": result["encoding"],
                "language": result["language_code"],
                "total_results": result["total_results"],
                "file_size_mb": round(properties["file_size_bytes"] / (1024 * 1024), 2),
            },
            "transcriptions": [],
        }

        for i, transcript in enumerate(result["transcripts"]):
            transcript_data = {
                "transcript_id": i + 1,
                "text": transcript["transcript"],
                "confidence": round(transcript["confidence"], 3),
            }

            if enable_word_timing and "words" in transcript:
                transcript_data["word_count"] = len(transcript["words"])
                transcript_data["duration_seconds"] = transcript["words"][-1]["end_time"] if transcript["words"] else 0
                # Include first few words as sample
                transcript_data["sample_words"] = transcript["words"][:5]

            output["transcriptions"].append(transcript_data)

        return f"✅ Speech transcription completed successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error during speech transcription: {str(e)}"


# Forms tools
@mcp.tool(name="forms_get_form")
async def forms_get_form(form_id: str) -> str:
    """Get complete Google Form structure including questions and sections.

    Args:
        form_id: Google Form ID

    Returns:
        JSON-formatted form structure with metadata
    """
    await initialize_services()

    try:
        form = forms_service.get_form(form_id)

        output = {
            "form_id": form.get("form_id"),
            "title": form.get("title", "Untitled"),
            "description": form.get("description", ""),
            "document_title": form.get("document_title", ""),
            "total_items": len(form.get("items", [])),
            "responder_uri": form.get("responderUri"),
            "linked_sheet_id": form.get("linkedSheetId"),
            "revision_id": form.get("revisionId"),
            "settings": form.get("settings", {}),
        }

        return f"✅ Form structure retrieved successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error retrieving form: {str(e)}"


@mcp.tool(name="forms_get_questions")
async def forms_get_questions(form_id: str, section_filter: Optional[int] = None) -> str:
    """Get all questions from a Google Form organized by sections.

    Args:
        form_id: Google Form ID
        section_filter: Optional section number (1-based) to filter questions.
                       If provided, only questions from that section are returned.
                       If None, all questions are returned.

    Returns:
        JSON-formatted list of questions with section information
    """
    await initialize_services()

    try:
        # Use service-level filtering
        questions = forms_service.get_questions(form_id, section_filter)
        actual_questions = [q for q in questions if not q.get("is_section_break")]
        sections = [q for q in questions if q.get("is_section_break")]

        output = {
            "form_id": form_id,
            "section_filter": section_filter,
            "total_questions": len(actual_questions),
            "total_sections": len(sections),
            "questions": [],
        }

        for question in actual_questions:
            question_data = {
                "question_number": question["question_number"],
                "title": question["title"],
                "description": question.get("description", ""),
                "type": question["question_type"],
                "required": question["required"],
                "section": {"title": question["section"]["title"], "index": question["section"]["index"]},
            }

            if question.get("choices"):
                question_data["options"] = [choice["value"] for choice in question["choices"]]

            if question.get("choice_navigation"):
                question_data["navigation_options"] = question["choice_navigation"]

            output["questions"].append(question_data)

        filter_msg = f" from section {section_filter}" if section_filter else ""
        return f"✅ Questions{filter_msg} retrieved successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error retrieving questions: {str(e)}"


@mcp.tool(name="forms_get_sections")
async def forms_get_sections(form_id: str) -> str:
    """Get all sections from a Google Form with navigation options.

    IMPORTANT: Section numbers are 1-based for user interaction.
    For example, "Training" is Section 7 (user-facing) but at internal index 6.

    Args:
        form_id: Google Form ID

    Returns:
        JSON-formatted list of sections with navigation details.
        Each section includes both section_number (1-based) and internal_index (0-based).
    """
    await initialize_services()

    try:
        sections = forms_service.get_sections(form_id)

        output = {"form_id": form_id, "total_sections": len(sections), "sections": []}

        for i, section in enumerate(sections):
            section_data = {
                "section_number": i + 1,  # 1-based numbering for users
                "internal_index": section["index"],  # Keep internal 0-based index
                "title": section["title"],
                "description": section.get("description", ""),
                "question_count": section["question_count"],
            }

            if section.get("go_to_action"):
                section_data["navigation"] = {
                    "action": section["go_to_action"],
                    "target_section_id": section.get("go_to_section_id"),
                }

            if section.get("item_id"):
                section_data["item_id"] = section["item_id"]

            output["sections"].append(section_data)

        return f"✅ Sections retrieved successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error retrieving sections: {str(e)}"


@mcp.tool(name="forms_add_section")
async def forms_add_section(
    form_id: str,
    title: str,
    description: str = "",
    position: str = "end",
    section_number: Optional[int] = None,
    question_number: Optional[int] = None,
) -> str:
    """Add a new section to a Google Form.

    IMPORTANT: All section and question numbers use 1-based numbering.

    Args:
        form_id: Google Form ID
        title: Section title
        description: Section description (optional)
        position: Position relative to reference ("before", "after", "end")
        section_number: Section number for positioning (1-based, required if not "end")
        question_number: Question number within section for positioning (1-based, required if not "end")

    Returns:
        Success message with section creation details
    """
    await initialize_services()

    try:
        response = forms_service.add_section(form_id, title, description, position, section_number, question_number)

        return f"✅ Section '{title}' added successfully"

    except Exception as e:
        return f"❌ Error adding section: {str(e)}"


@mcp.tool(name="forms_add_question")
async def forms_add_question(
    form_id: str,
    title: str,
    question_type: str = "text",
    description: str = "",
    required: bool = False,
    section_index: int = 0,
    position: str = "end",
    reference_question: Optional[int] = None,
    options: Optional[List[str]] = None,
) -> str:
    """Add a new question to a Google Form.

    IMPORTANT: All numbering uses 1-based indexing for user interaction.
    - section_index: Use 1-based section numbers (Training=7, Default=1)
    - reference_question: Use 1-based question numbers (first question=1)
    Service layer handles 1-based validation and conversion automatically.

    Args:
        form_id: Google Form ID
        title: Question title
        question_type: Question type ("text", "choice", "scale", "date", "time", "file_upload")
        description: Question description (optional)
        required: Whether the question is required
        section_index: Target section number (1-based)
        position: Position relative to reference ("before", "after", "end")
        reference_question: Question number (1-based) for positioning (required for "before" and "after")
        options: Choice options (for choice questions)

    Returns:
        Success message with question creation details
    """
    await initialize_services()

    try:
        question_data = {
            "title": title,
            "description": description,
            "question_type": question_type,
            "required": required,
        }

        if options and question_type == "choice":
            question_data["options"] = options

        # Service layer handles 1-based numbering validation and conversion
        response = forms_service.add_question(form_id, question_data, section_index, position, reference_question)

        output = {
            "form_id": form_id,
            "operation": "add_question",
            "question_data": question_data,
            "section_index": section_index,
            "position": position,
            "reference_question": reference_question,
            "response": response,
        }

        return f"✅ Question '{title}' added successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error adding question: {str(e)}"


@mcp.tool(name="forms_update_section")
async def forms_update_section(
    form_id: str,
    section_index: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    go_to_action: Optional[str] = None,
    go_to_section_id: Optional[str] = None,
) -> str:
    """Update an existing section in a Google Form.

    IMPORTANT: Section numbers are 1-based (Training = 7, not 6).
    Tool automatically converts to internal 0-based indexing.

    Args:
        form_id: Google Form ID
        section_index: Section number to update (1-based, e.g., Training = 7)
        title: New section title (optional)
        description: New section description (optional)
        go_to_action: Navigation action after this section (optional)
        go_to_section_id: Target section ID for navigation (optional)

    Returns:
        Success message with update details
    """
    await initialize_services()

    try:
        kwargs = {}
        if title is not None:
            kwargs["title"] = title
        if description is not None:
            kwargs["description"] = description
        if go_to_action is not None:
            kwargs["go_to_action"] = go_to_action
        if go_to_section_id is not None:
            kwargs["go_to_section_id"] = go_to_section_id

        if not kwargs:
            return "❌ No update parameters provided"

        # Service layer handles 1-based numbering validation and conversion
        response = forms_service.update_section(form_id, section_index, **kwargs)

        output = {
            "form_id": form_id,
            "operation": "update_section",
            "section_index": section_index,
            "updated_data": kwargs,
            "response": response,
        }

        return f"✅ Section {section_index} updated successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error updating section: {str(e)}"


@mcp.tool(name="forms_remove_section")
async def forms_remove_section(form_id: str, section_index: int) -> str:
    """Remove a section and all its questions from a Google Form.

    Args:
        form_id: Google Form ID
        section_index: Section index to remove (0-based)

    Returns:
        Success message with removal details
    """
    await initialize_services()

    try:
        # Service layer handles 1-based numbering validation and conversion
        response = forms_service.remove_section(form_id, section_index)

        output = {
            "form_id": form_id,
            "operation": "remove_section",
            "section_number": section_index,
            "response": response,
        }

        return f"✅ Section {section_index} and its questions removed successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error removing section: {str(e)}"


@mcp.tool(name="forms_translate_question")
async def forms_translate_question(
    form_id: str,
    section_number: int,
    question_number_in_section: int,
    target_language: str,
    translate_answers: bool = True,
    source_language: str = "",
) -> str:
    """Translate a question and optionally its answers to another language.

    IMPORTANT: Section numbers and question numbers are 1-based (Section 7 = Training, Question 1 = first question in section).

    Args:
        form_id: Google Form ID
        section_number: Section number (1-based, e.g., Training = 7)
        question_number_in_section: Question number within the section (1-based, e.g., first question = 1)
        target_language: Target language code (e.g., 'fr', 'es', 'de')
        translate_answers: Whether to translate answer options (default: True)
        source_language: Source language code (auto-detected if empty)

    Returns:
        Translation results and success message
    """
    await initialize_services()

    try:
        # Convert section + question to global question number using service-level filtering
        section_questions_all = forms_service.get_questions(form_id, section_filter=section_number)
        section_questions = [q for q in section_questions_all if not q.get("is_section_break")]

        if (
            not section_questions
            or question_number_in_section < 1
            or question_number_in_section > len(section_questions)
        ):
            return f"❌ Question {question_number_in_section} not found in section {section_number}"

        # Get the global question number
        target_question = section_questions[question_number_in_section - 1]
        global_question_number = target_question.get("question_number")

        if not global_question_number:
            return f"❌ Could not find global question number for section {section_number}, question {question_number_in_section}"

        result = await forms_service.translate_question(
            form_id, global_question_number, target_language, translate_answers, source_language
        )

        output = {
            "form_id": form_id,
            "operation": "translate_question",
            "section_number": section_number,
            "question_number_in_section": question_number_in_section,
            "global_question_number": global_question_number,
            "target_language": target_language,
            "source_language": source_language or "auto",
            "translations": result["translations"],
        }

        return f"✅ Question {question_number_in_section} in section {section_number} translated to {target_language} successfully"

    except Exception as e:
        return f"❌ Error translating question: {str(e)}"


@mcp.tool(name="forms_remove_question")
async def forms_remove_question(form_id: str, section_number: int, question_number_in_section: int) -> str:
    """Remove a question by section and question number within that section.

    Args:
        form_id: Google Form ID
        section_number: Section number (1-based)
        question_number_in_section: Question number within the section (1-based)

    Returns:
        Success message with removal details
    """
    await initialize_services()

    try:
        response = forms_service.remove_question_by_section(form_id, section_number, question_number_in_section)

        output = {
            "form_id": form_id,
            "operation": "remove_question",
            "section_number": section_number,
            "question_number_in_section": question_number_in_section,
            "response": response,
        }

        return f"✅ Question {question_number_in_section} from section {section_number} removed successfully\n\n{json.dumps(output, ensure_ascii=False, indent=2)}"

    except Exception as e:
        return f"❌ Error removing question: {str(e)}"


@mcp.tool(name="forms_update_question")
async def forms_update_question(
    form_id: str,
    section_number: int,
    question_number_in_section: int,
    title: str = None,
    description: str = None,
    question_type: str = None,
    required: bool = None,
    options: List[str] = None,
) -> str:
    """Update a question by section and question number within that section.

    Args:
        form_id: Google Form ID
        section_number: Section number (1-based)
        question_number_in_section: Question number within the section (1-based)
        title: New question title (optional)
        description: New question description (optional)
        question_type: New question type (optional)
        required: Whether the question is required (optional)
        options: New choice options for choice questions (optional)

    Returns:
        Success message with update details
    """
    await initialize_services()

    try:
        # Build question data from provided parameters
        question_data = {}
        if title is not None:
            question_data["title"] = title
        if description is not None:
            question_data["description"] = description
        if question_type is not None:
            question_data["question_type"] = question_type
        if required is not None:
            question_data["required"] = required
        if options is not None:
            question_data["options"] = options

        if not question_data:
            return "❌ Error: At least one field must be provided for update"

        response = forms_service.update_question_by_section(
            form_id, section_number, question_number_in_section, question_data
        )

        output = {
            "form_id": form_id,
            "operation": "update_question",
            "section_number": section_number,
            "question_number_in_section": question_number_in_section,
            "updated_fields": question_data,
            "response": response,
        }

        return f"✅ Question {question_number_in_section} in section {section_number} updated successfully"

    except Exception as e:
        return f"❌ Error updating question: {str(e)}"


@mcp.tool(name="forms_move_question")
async def forms_move_question(
    form_id: str,
    source_section_number: int,
    source_question_number: int,
    target_section_number: int,
    target_question_number: int,
    position: str = "before",
) -> str:
    """Move a question from one position to another.

    IMPORTANT: All section and question numbers are 1-based.

    Args:
        form_id: Google Form ID
        source_section_number: Source section number (1-based)
        source_question_number: Source question number within section (1-based)
        target_section_number: Target section number (1-based)
        target_question_number: Target question number within section (1-based)
        position: Position relative to target ("before", "after")

    Returns:
        Success message
    """
    await initialize_services()

    try:
        forms_service.move_question(
            form_id,
            source_section_number,
            source_question_number,
            target_section_number,
            target_question_number,
            position,
        )

        return f"✅ Question {source_question_number} moved from section {source_section_number} to section {target_section_number} successfully"

    except Exception as e:
        return f"❌ Error moving question: {str(e)}"


@mcp.tool(name="forms_move_section")
async def forms_move_section(
    form_id: str,
    source_section_number: int,
    target_section_number: int,
    position: str = "before",
) -> str:
    """Move a section to a new position relative to another section.

    IMPORTANT: All section numbers are 1-based.

    Args:
        form_id: Google Form ID
        source_section_number: Source section number (1-based)
        target_section_number: Target section number (1-based)
        position: Position relative to target section ("before", "after")

    Returns:
        Success message
    """
    await initialize_services()

    try:
        await forms_service.move_section(
            form_id,
            source_section_number,
            target_section_number,
            position,
        )

        return f"✅ Section {source_section_number} moved {position} section {target_section_number} successfully"

    except Exception as e:
        return f"❌ Error moving section: {str(e)}"


@mcp.tool(name="slides_content_remove")
async def slides_content_remove(presentation_id: str, slide_id: str, element_id: str) -> str:
    """Remove content element from a slide by its ID.

    Args:
        presentation_id: Google Slides presentation ID
        slide_id: Slide ID containing the element
        element_id: Element ID to remove

    Returns:
        Success message
    """
    await initialize_services()

    try:
        result = await slides_service.remove_content_element(presentation_id, slide_id, element_id)
        return f"✅ Content element {element_id} removed from slide {slide_id} successfully"

    except Exception as e:
        return f"❌ Error removing content element: {str(e)}"


@mcp.tool(name="slides_content_move")
async def slides_content_move(presentation_id: str, slide_id: str, element_id: str, x: float, y: float) -> str:
    """Move content element to new position on slide.

    Args:
        presentation_id: Google Slides presentation ID
        slide_id: Slide ID containing the element
        element_id: Element ID to move
        x: New X position in presentation units
        y: New Y position in presentation units

    Returns:
        Success message
    """
    await initialize_services()

    try:
        result = await slides_service.move_content_element(presentation_id, slide_id, element_id, x, y)
        return f"✅ Content element {element_id} moved to position ({x}, {y}) successfully"

    except Exception as e:
        return f"❌ Error moving content element: {str(e)}"


@mcp.tool(name="slides_themes_import")
async def slides_themes_import(presentation_id: str, template_id: str, set_theme: bool = False) -> str:
    """Import theme from another presentation.

    Args:
        presentation_id: Target presentation ID
        template_id: Source presentation ID with theme to import
        set_theme: Whether to automatically apply the imported theme

    Returns:
        Success message
    """
    await initialize_services()

    try:
        result = await slides_service.import_theme(presentation_id, template_id, set_theme)
        message = f"✅ Theme imported from presentation {template_id} successfully"
        if set_theme:
            message += " and applied to presentation"
        return message

    except Exception as e:
        return f"❌ Error importing theme: {str(e)}"


@mcp.tool(name="slides_themes_set")
async def slides_themes_set(presentation_id: str, theme_name: str) -> str:
    """Set theme for presentation.

    Args:
        presentation_id: Presentation ID
        theme_name: Theme name (SIMPLE_LIGHT, SIMPLE_DARK, STREAMLINE, FOCUS, etc.)

    Returns:
        Success message
    """
    await initialize_services()

    try:
        result = await slides_service.set_theme(presentation_id, theme_name)
        return f"✅ Theme '{theme_name}' applied to presentation {presentation_id} successfully"

    except Exception as e:
        return f"❌ Error setting theme: {str(e)}"


@mcp.tool(name="slides_layout_list")
async def slides_layout_list(presentation_id: str) -> str:
    """List available layouts for a presentation.

    Args:
        presentation_id: Presentation ID

    Returns:
        JSON formatted list of available layouts
    """
    await initialize_services()

    try:
        layouts = slides_service.list_layouts(presentation_id)
        import json

        return json.dumps({"layouts": layouts}, indent=2)

    except Exception as e:
        return f"❌ Error listing layouts: {str(e)}"


@mcp.tool(name="slides_move")
async def slides_move(presentation_id: str, slide_id: str, new_position: int) -> str:
    """Move slide to new position in presentation.

    Args:
        presentation_id: Presentation ID
        slide_id: Slide ID to move
        new_position: New position (0-based index)

    Returns:
        Success message
    """
    await initialize_services()

    try:
        result = await slides_service.move_slide(presentation_id, slide_id, new_position)
        return f"✅ Slide moved to position {new_position} successfully"

    except Exception as e:
        return f"❌ Error moving slide: {str(e)}"


# Version Management Tools


@mcp.tool(name="slides_list_versions")
async def slides_list_versions(presentation_id: str) -> str:
    """List all versions/revisions of a Google Slides presentation.

    Args:
        presentation_id: Google Slides presentation ID

    Returns:
        JSON formatted list of versions with metadata
    """
    await initialize_services()

    try:
        versions = await slides_service.list_presentation_versions(presentation_id)
        import json

        # Format for better readability
        formatted_versions = []
        for version in versions:
            formatted_versions.append(
                {
                    "revision_id": version["id"],
                    "modified_time": version.get("modifiedTime"),
                    "size_bytes": version.get("size"),
                    "last_modifying_user": version.get("lastModifyingUser", {}).get("displayName"),
                    "keep_forever": version.get("keepForever", False),
                    "file_type": version.get("file_type", "presentation"),
                }
            )

        return json.dumps({"versions": formatted_versions}, indent=2)

    except Exception as e:
        return f"❌ Error listing presentation versions: {str(e)}"


@mcp.tool(name="slides_get_version")
async def slides_get_version(presentation_id: str, revision_id: str) -> str:
    """Get metadata for a specific version of a presentation.

    Args:
        presentation_id: Google Slides presentation ID
        revision_id: Revision ID to get metadata for

    Returns:
        JSON formatted version metadata
    """
    await initialize_services()

    try:
        version = await slides_service.get_presentation_version(presentation_id, revision_id)
        import json

        formatted_version = {
            "revision_id": version["id"],
            "modified_time": version.get("modifiedTime"),
            "size_bytes": version.get("size"),
            "last_modifying_user": version.get("lastModifyingUser", {}).get("displayName"),
            "keep_forever": version.get("keepForever", False),
            "file_type": version.get("file_type", "presentation"),
            "mime_type": version.get("mimeType"),
        }

        return json.dumps(formatted_version, indent=2)

    except Exception as e:
        return f"❌ Error getting presentation version: {str(e)}"


@mcp.tool(name="slides_compare_versions")
async def slides_compare_versions(
    presentation_id: str, revision_id_1: str, revision_id_2: str, output_dir: str = "/tmp"
) -> str:
    """Compare two versions of a presentation.

    Args:
        presentation_id: Google Slides presentation ID
        revision_id_1: First revision ID to compare
        revision_id_2: Second revision ID to compare
        output_dir: Directory to save comparison results (default: /tmp)

    Returns:
        JSON formatted comparison results
    """
    await initialize_services()

    try:
        result = await slides_service.compare_presentation_versions(
            presentation_id, revision_id_1, revision_id_2, output_dir
        )
        import json

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return f"❌ Error comparing presentation versions: {str(e)}"


@mcp.tool(name="docs_list_versions")
async def docs_list_versions(document_id: str) -> str:
    """List all versions/revisions of a Google Docs document.

    Args:
        document_id: Google Docs document ID

    Returns:
        JSON formatted list of versions with metadata
    """
    await initialize_services()

    try:
        versions = await docs_service.list_document_versions(document_id)
        import json

        # Format for better readability
        formatted_versions = []
        for version in versions:
            formatted_versions.append(
                {
                    "revision_id": version["id"],
                    "modified_time": version.get("modifiedTime"),
                    "size_bytes": version.get("size"),
                    "last_modifying_user": version.get("lastModifyingUser", {}).get("displayName"),
                    "keep_forever": version.get("keepForever", False),
                    "file_type": version.get("file_type", "document"),
                }
            )

        return json.dumps({"versions": formatted_versions}, indent=2)

    except Exception as e:
        return f"❌ Error listing document versions: {str(e)}"


@mcp.tool(name="docs_get_version")
async def docs_get_version(document_id: str, revision_id: str) -> str:
    """Get metadata for a specific version of a document.

    Args:
        document_id: Google Docs document ID
        revision_id: Revision ID to get metadata for

    Returns:
        JSON formatted version metadata
    """
    await initialize_services()

    try:
        version = await docs_service.get_document_version(document_id, revision_id)
        import json

        formatted_version = {
            "revision_id": version["id"],
            "modified_time": version.get("modifiedTime"),
            "size_bytes": version.get("size"),
            "last_modifying_user": version.get("lastModifyingUser", {}).get("displayName"),
            "keep_forever": version.get("keepForever", False),
            "file_type": version.get("file_type", "document"),
            "mime_type": version.get("mimeType"),
        }

        return json.dumps(formatted_version, indent=2)

    except Exception as e:
        return f"❌ Error getting document version: {str(e)}"


@mcp.tool(name="docs_compare_versions")
async def docs_compare_versions(
    document_id: str, revision_id_1: str, revision_id_2: str, output_dir: str = "/tmp"
) -> str:
    """Compare two versions of a document.

    Args:
        document_id: Google Docs document ID
        revision_id_1: First revision ID to compare
        revision_id_2: Second revision ID to compare
        output_dir: Directory to save comparison results (default: /tmp)

    Returns:
        JSON formatted comparison results
    """
    await initialize_services()

    try:
        result = await docs_service.compare_document_versions(document_id, revision_id_1, revision_id_2, output_dir)
        import json

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return f"❌ Error comparing document versions: {str(e)}"


@mcp.tool(name="sheets_list_versions")
async def sheets_list_versions(spreadsheet_id: str) -> str:
    """List all versions/revisions of a Google Sheets spreadsheet.

    Args:
        spreadsheet_id: Google Sheets spreadsheet ID

    Returns:
        JSON formatted list of versions with metadata
    """
    await initialize_services()

    try:
        versions = await sheets_service.list_spreadsheet_versions(spreadsheet_id)
        import json

        # Format for better readability
        formatted_versions = []
        for version in versions:
            formatted_versions.append(
                {
                    "revision_id": version["id"],
                    "modified_time": version.get("modifiedTime"),
                    "size_bytes": version.get("size"),
                    "last_modifying_user": version.get("lastModifyingUser", {}).get("displayName"),
                    "keep_forever": version.get("keepForever", False),
                    "file_type": version.get("file_type", "spreadsheet"),
                }
            )

        return json.dumps({"versions": formatted_versions}, indent=2)

    except Exception as e:
        return f"❌ Error listing spreadsheet versions: {str(e)}"


@mcp.tool(name="sheets_get_version")
async def sheets_get_version(spreadsheet_id: str, revision_id: str) -> str:
    """Get metadata for a specific version of a spreadsheet.

    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        revision_id: Revision ID to get metadata for

    Returns:
        JSON formatted version metadata
    """
    await initialize_services()

    try:
        version = await sheets_service.get_spreadsheet_version(spreadsheet_id, revision_id)
        import json

        formatted_version = {
            "revision_id": version["id"],
            "modified_time": version.get("modifiedTime"),
            "size_bytes": version.get("size"),
            "last_modifying_user": version.get("lastModifyingUser", {}).get("displayName"),
            "keep_forever": version.get("keepForever", False),
            "file_type": version.get("file_type", "spreadsheet"),
            "mime_type": version.get("mimeType"),
        }

        return json.dumps(formatted_version, indent=2)

    except Exception as e:
        return f"❌ Error getting spreadsheet version: {str(e)}"


@mcp.tool(name="sheets_compare_versions")
async def sheets_compare_versions(
    spreadsheet_id: str, revision_id_1: str, revision_id_2: str, output_dir: str = "/tmp"
) -> str:
    """Compare two versions of a spreadsheet.

    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        revision_id_1: First revision ID to compare
        revision_id_2: Second revision ID to compare
        output_dir: Directory to save comparison results (default: /tmp)

    Returns:
        JSON formatted comparison results
    """
    await initialize_services()

    try:
        result = await sheets_service.compare_spreadsheet_versions(
            spreadsheet_id, revision_id_1, revision_id_2, output_dir
        )
        import json

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return f"❌ Error comparing spreadsheet versions: {str(e)}"


@mcp.tool(name="keep_version_forever")
async def keep_version_forever(file_id: str, revision_id: str, file_type: str, keep_forever: bool = True) -> str:
    """Keep a version forever or allow auto-deletion for any Google Workspace file.

    Args:
        file_id: File ID (presentation, document, or spreadsheet)
        revision_id: Revision ID to update
        file_type: File type ('slides', 'docs', or 'sheets')
        keep_forever: Whether to keep forever (True) or allow auto-deletion (False)

    Returns:
        Success message
    """
    await initialize_services()

    try:
        if file_type.lower() in ["slides", "presentation"]:
            result = await slides_service.keep_presentation_version_forever(file_id, revision_id, keep_forever)
        elif file_type.lower() in ["docs", "document"]:
            result = await docs_service.keep_document_version_forever(file_id, revision_id, keep_forever)
        elif file_type.lower() in ["sheets", "spreadsheet"]:
            result = await sheets_service.keep_spreadsheet_version_forever(file_id, revision_id, keep_forever)
        else:
            return f"❌ Unsupported file type: {file_type}. Use 'slides', 'docs', or 'sheets'"

        action = "enabled" if keep_forever else "disabled"
        return f"✅ Keep forever {action} for version {revision_id} of {file_type} {file_id}"

    except Exception as e:
        return f"❌ Error updating keep forever setting: {str(e)}"
