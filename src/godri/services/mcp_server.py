"""MCP Server implementation for Godri."""

import asyncio
import logging
from typing import List, Optional
import os
from mcp.server.fastmcp import FastMCP
from .auth_service import AuthService
from .drive_service import DriveService
from .docs_service import DocsService
from .sheets_service import SheetsService
from .slides_service import SlidesService
from .translate_service import TranslateService

# Initialize FastMCP server
mcp = FastMCP("Godri")

# Global services - will be initialized on first use
auth_service: Optional[AuthService] = None
drive_service: Optional[DriveService] = None
docs_service: Optional[DocsService] = None
sheets_service: Optional[SheetsService] = None
slides_service: Optional[SlidesService] = None
translate_service: Optional[TranslateService] = None

logger = logging.getLogger(__name__)


async def initialize_services():
    """Initialize all Google services."""
    global auth_service, drive_service, docs_service, sheets_service, slides_service, translate_service

    if auth_service is not None:
        return  # Already initialized

    # Try to get token from environment or default location
    token_path = os.path.expanduser("~/.godri-token.json")
    oauth_token = None
    if os.path.exists(token_path):
        with open(token_path, "r") as f:
            import json

            token_data = json.load(f)
            oauth_token = token_data.get("access_token")

    auth_service = AuthService(oauth_token=oauth_token)
    drive_service = DriveService(auth_service)
    docs_service = DocsService(auth_service)
    sheets_service = SheetsService(auth_service)
    slides_service = SlidesService(auth_service)
    translate_service = TranslateService(auth_service)

    await drive_service.initialize()
    await docs_service.initialize()
    await sheets_service.initialize()
    await slides_service.initialize()
    await translate_service.initialize()

    logger.info("All services initialized for MCP server")


# Drive tools
@mcp.tool(name="drive_search")
async def drive_search(query: str = "", name: str = "", mime_type: str = "", limit: int = 20) -> str:
    """Search for files in Google Drive. Use query for general search or name for exact filename matching. Optionally filter by MIME type."""
    await initialize_services()

    if name:
        result = drive_service.search_by_name(name, mime_type)
    else:
        result = drive_service.search_files(query, limit)

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

    result = drive_service.create_folder(name, parent_id if parent_id else None)
    return str(result)


@mcp.tool(name="drive_folder_delete")
async def drive_folder_delete(file_id: str) -> str:
    """Delete a file or folder from Google Drive by its ID."""
    await initialize_services()

    success = drive_service.delete_file(file_id)
    return "File/folder deleted successfully!" if success else "Failed to delete file/folder."


# Docs tools
@mcp.tool(name="docs_createdocument")
async def docs_createdocument(title: str, folder_id: str = "", content: str = "", markdown: bool = False) -> str:
    """Create a new Google Doc with specified title. Optionally add initial content and specify if content is markdown."""
    await initialize_services()

    result = docs_service.create_document(title, folder_id if folder_id else None)

    if content:
        if markdown:
            docs_service.insert_markdown_text(result["documentId"], content)
        else:
            docs_service.insert_text(result["documentId"], content)

    return str(result)


@mcp.tool(name="docs_read")
async def docs_read(document_id: str, plain_text: bool = False) -> str:
    """Read content from a Google Doc. Set plain_text=True to get only text without formatting."""
    await initialize_services()

    if plain_text:
        return docs_service.get_document_text(document_id)
    else:
        document = docs_service.get_document(document_id)
        content = docs_service.get_document_text(document_id)
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

    result = sheets_service.create_spreadsheet(title, folder_id if folder_id else None)
    return str(result)


@mcp.tool(name="sheets_read")
async def sheets_read(spreadsheet_id: str) -> str:
    """List all sheets in a Google Spreadsheet with their properties."""
    await initialize_services()

    result = sheets_service.list_sheets(spreadsheet_id)
    return str(result)


@mcp.tool(name="sheets_create")
async def sheets_create(spreadsheet_id: str, sheet_name: str) -> str:
    """Create a new sheet within an existing Google Spreadsheet."""
    await initialize_services()

    result = sheets_service.create_sheet(spreadsheet_id, sheet_name)
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
async def sheets_values_read(spreadsheet_id: str, sheet_name: str = "", range_name: str = "") -> str:
    """Read data from a Google Sheet. Specify sheet_name for entire sheet or range_name for specific range (e.g., 'A1:C10')."""
    await initialize_services()

    if range_name:
        values = sheets_service.get_values(spreadsheet_id, range_name)
    else:
        values = sheets_service.read_entire_sheet(spreadsheet_id, sheet_name)

    return str(values) if values else "No data found."


@mcp.tool(name="sheets_values_set")
async def sheets_values_set(spreadsheet_id: str, range_name: str, values: str, formula: bool = False) -> str:
    """Set values in Google Sheet cells. Values can be comma-separated or JSON array. Set formula=True for formula input."""
    await initialize_services()

    # Parse values - support JSON array or comma-separated
    if values.startswith("["):
        import json

        parsed_values = json.loads(values)
    else:
        parsed_values = [v.strip() for v in values.split(",")]

    if formula:
        result = sheets_service.set_formula(spreadsheet_id, range_name, values)
    else:
        result = sheets_service.set_values_in_range(spreadsheet_id, range_name, parsed_values)

    return f"Values set successfully in range '{range_name}'. Updated {result.get('updatedCells', 0)} cells"


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


# Slides tools
@mcp.tool(name="slides_createdocument")
async def slides_createdocument(title: str, folder_id: str = "", theme: str = "STREAMLINE") -> str:
    """Create a new Google Slides presentation with specified title and theme. Available themes: SIMPLE_LIGHT, SIMPLE_DARK, STREAMLINE, FOCUS, etc."""
    await initialize_services()

    result = slides_service.create_presentation(title, folder_id if folder_id else None, theme)
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
    result = slides_service.add_slide(presentation_id, layout, pos)
    return "Slide added successfully"


@mcp.tool(name="slides_remove")
async def slides_remove(presentation_id: str, slide_id: str) -> str:
    """Remove a slide from presentation by slide ID."""
    await initialize_services()

    result = slides_service.remove_slide(presentation_id, slide_id)
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
        result = slides_service.add_text_content(presentation_id, slide_id, content, x, y, width, height)
        return f"Text content added to slide {slide_id}"
    elif content_type == "image":
        result = slides_service.add_image_content(presentation_id, slide_id, content, x, y, width, height)
        return f"Image content added to slide {slide_id}"
    elif content_type == "table":
        if "x" in content.lower():
            rows, cols = map(int, content.lower().split("x"))
            result = slides_service.add_table_content(presentation_id, slide_id, rows, cols, x, y, width, height)
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

    result = slides_service.copy_slides(
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
        result = sheets_service.copy_sheet(
            source_spreadsheet_id,
            target_spreadsheet_id,
            names[0],
            target_sheet_name=target_name,
            preserve_formatting=preserve_formatting,
        )
        return f"Successfully copied sheet '{result['source_sheet']}' to '{result['target_sheet']}' (ID: {result['new_sheet_id']})"
    else:
        # Multiple sheets copy
        result = sheets_service.copy_multiple_sheets(
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


# Translation tool
@mcp.tool(name="translate_text")
async def translate_text(text: str, target_language: str, source_language: str = "") -> str:
    """Translate text using Google Translate. Specify target language code (e.g., 'fr', 'es'). Source language is auto-detected if not specified."""
    await initialize_services()

    result = translate_service.translate_text(text, target_language, source_language if source_language else None)
    return str(result)
