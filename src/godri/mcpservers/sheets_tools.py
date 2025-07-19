"""Google Sheets MCP tools."""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from .base_tools import BaseTools
from ..commons.api.sheets_api import SheetsApiClient
from ..commons.api.translate_api import TranslateApiClient


class SheetsTools(BaseTools):
    """Google Sheets MCP tools."""

    def __init__(self, sheets_api: SheetsApiClient, translate_api: TranslateApiClient):
        """Initialize Sheets tools."""
        super().__init__()
        self.sheets_api = sheets_api
        self.translate_api = translate_api

    def register_tools(self, server: FastMCP) -> None:
        """Register Sheets tools with MCP server."""

        @server.tool()
        async def sheets_createdocument(title: str, folder_id: str = "") -> Dict[str, Any]:
            """Create a new Google Spreadsheet with specified title. Optionally specify parent folder ID."""
            try:
                # TODO: Implement using sheets_api
                return {"success": True, "message": "Sheets tool placeholder"}
            except Exception as e:
                return self.handle_error(e, "sheets_createdocument")

        # TODO: Add other sheets tools
