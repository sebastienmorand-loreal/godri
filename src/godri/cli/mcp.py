"""MCP server CLI commands."""

import asyncio
import logging
import sys
import typer
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

mcp_app = typer.Typer(help="MCP server commands")


@mcp_app.command()
def stdio():
    """Start MCP server with stdio transport."""
    asyncio.run(_handle_stdio())


async def _handle_stdio() -> None:
    """Handle stdio MCP server command."""
    try:
        # TODO: Update import after refactoring MCP servers
        from ..mcpservers.main_server import main_server

        # Run the MCP server
        await main_server.run()

    except Exception as e:
        logger.error("MCP server failed: %s", str(e))
        console.print(f"MCP server failed: {str(e)}", style="red")
        sys.exit(1)
