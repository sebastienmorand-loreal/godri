"""Godri CLI main application using typer."""

import asyncio
import logging
import sys
from pathlib import Path
import typer
from rich.console import Console

# Add the src directory to the path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# Import logging configuration
import godri.config.logging_config

# Import CLI modules
from godri.cli.auth import auth_app
from godri.cli.drive import drive_app
from godri.cli.docs import docs_app
from godri.cli.mcp import mcp_app
from godri.cli.translate import translate_app

console = Console()
logger = logging.getLogger(__name__)

# Create main typer app
app = typer.Typer(
    name="godri", help="Google Drive and Workspace CLI tool with MCP server integration", add_completion=False
)

# Add subcommands
app.add_typer(auth_app, name="auth")
app.add_typer(drive_app, name="drive")
app.add_typer(docs_app, name="docs")
app.add_typer(mcp_app, name="mcp")
app.add_typer(translate_app, name="translate")

# TODO: Add other subcommands after creating their CLI modules
# app.add_typer(sheets_app, name="sheets")
# app.add_typer(slides_app, name="slides")
# app.add_typer(forms_app, name="forms")
# app.add_typer(speech_app, name="speech")


@app.command()
def version():
    """Show version information."""
    console.print("Godri v0.2.0", style="bold green")
    console.print("Google Drive and Workspace CLI tool")


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
):
    """Godri - Google Drive and Workspace CLI tool."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)


def main():
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user", style="yellow")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        console.print(f"Unexpected error: {str(e)}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
