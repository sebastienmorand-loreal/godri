"""Main MCP server combining all Google Workspace tools."""

import asyncio
import logging
import os
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Global services - will be initialized on first use
from ..services.auth_service import AuthService
from ..commons.api.google_api_client import GoogleApiClient
from ..commons.api.drive_api import DriveApiClient
from ..commons.api.docs_api import DocsApiClient
from ..commons.api.sheets_api import SheetsApiClient
from ..commons.api.slides_api import SlidesApiClient
from ..commons.api.forms_api import FormsApiClient
from ..commons.api.translate_api import TranslateApiClient
from ..commons.api.speech_api import SpeechApiClient

# Import MCP tool modules
from .drive_tools import DriveTools
from .docs_tools import DocsTools
from .sheets_tools import SheetsTools
from .slides_tools import SlidesTools
from .forms_tools import FormsTools
from .translate_tools import TranslateTools
from .speech_tools import SpeechTools

logger = logging.getLogger(__name__)

# Initialize FastMCP server
main_server = FastMCP("Godri")

# Global service instances
auth_service: Optional[AuthService] = None
api_client: Optional[GoogleApiClient] = None
drive_api: Optional[DriveApiClient] = None
docs_api: Optional[DocsApiClient] = None
sheets_api: Optional[SheetsApiClient] = None
slides_api: Optional[SlidesApiClient] = None
forms_api: Optional[FormsApiClient] = None
translate_api: Optional[TranslateApiClient] = None
speech_api: Optional[SpeechApiClient] = None

# Tool instances
drive_tools: Optional[DriveTools] = None
docs_tools: Optional[DocsTools] = None
sheets_tools: Optional[SheetsTools] = None
slides_tools: Optional[SlidesTools] = None
forms_tools: Optional[FormsTools] = None
translate_tools: Optional[TranslateTools] = None
speech_tools: Optional[SpeechTools] = None


async def initialize_services():
    """Initialize all Google services and API clients."""
    global auth_service, api_client, drive_api, docs_api, sheets_api, slides_api
    global forms_api, translate_api, speech_api, drive_tools, docs_tools, sheets_tools
    global slides_tools, forms_tools, translate_tools, speech_tools

    if auth_service is not None:
        return  # Already initialized

    logger.info("Initializing MCP services...")

    # Try to get token from environment or default location
    token_path = os.path.expanduser("~/.godri-token.json")
    oauth_token = None
    if os.path.exists(token_path):
        import json

        with open(token_path, "r") as f:
            token_data = json.load(f)
            oauth_token = token_data.get("access_token")

    # Initialize services
    auth_service = AuthService(oauth_token=oauth_token)
    api_client = await auth_service.get_api_client()

    # Initialize API clients
    drive_api = DriveApiClient(api_client)
    docs_api = DocsApiClient(api_client)
    sheets_api = SheetsApiClient(api_client)
    slides_api = SlidesApiClient(api_client)
    forms_api = FormsApiClient(api_client)
    translate_api = TranslateApiClient(api_client)
    speech_api = SpeechApiClient(api_client)

    # Initialize tool instances
    drive_tools = DriveTools(drive_api)
    docs_tools = DocsTools(docs_api, translate_api)
    sheets_tools = SheetsTools(sheets_api, translate_api)
    slides_tools = SlidesTools(slides_api, translate_api)
    forms_tools = FormsTools(forms_api, translate_api)
    translate_tools = TranslateTools(translate_api)
    speech_tools = SpeechTools(speech_api)

    # Register all tools with the MCP server
    await register_all_tools()

    logger.info("MCP services initialized successfully")


async def register_all_tools():
    """Register all tools with the MCP server."""
    # Register tools from each module
    drive_tools.register_tools(main_server)
    docs_tools.register_tools(main_server)
    sheets_tools.register_tools(main_server)
    slides_tools.register_tools(main_server)
    forms_tools.register_tools(main_server)
    translate_tools.register_tools(main_server)
    speech_tools.register_tools(main_server)


# Ensure services are initialized before handling any requests
@main_server.call_handler()
async def handle_call():
    """Initialize services before handling any MCP calls."""
    await initialize_services()


if __name__ == "__main__":
    # Run the MCP server
    asyncio.run(main_server.run())
