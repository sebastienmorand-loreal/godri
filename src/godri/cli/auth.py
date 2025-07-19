"""Authentication CLI commands."""

import asyncio
import logging
import os
import sys
from typing import Optional
import typer
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

# Import will be updated after refactoring services
# from ..services.auth_service import AuthService

auth_app = typer.Typer(help="Authentication commands")


@auth_app.command()
def authenticate(
    force: bool = typer.Option(False, "--force", "-f", help="Force re-authentication"),
    print_token: bool = typer.Option(False, "--print", help="Print OAuth2 token to stdout"),
):
    """Authenticate with Google services."""
    asyncio.run(_handle_auth(force, print_token))


async def _handle_auth(force: bool, print_token: bool) -> None:
    """Handle authentication command.

    Args:
        force: Force re-authentication
        print_token: Print token to stdout
    """
    try:
        # TODO: Update import after refactoring
        from ..services.auth_service import AuthService

        if force:
            # Delete existing token to force re-authentication
            token_file = os.path.expanduser("~/.godri-token.json")
            if os.path.exists(token_file):
                os.remove(token_file)
                console.print("Existing token deleted. Starting fresh authentication...")

        auth_service = AuthService()
        credentials = await auth_service.authenticate()

        if print_token:
            # Print the OAuth2 token to stdout
            if credentials and credentials.token:
                console.print(credentials.token)
            else:
                console.print("No valid token available", style="red")
                sys.exit(1)
        else:
            console.print("Authentication successful!", style="green")
    except Exception as e:
        logger.error("Authentication failed: %s", str(e))
        console.print(f"Authentication failed: {str(e)}", style="red")
        sys.exit(1)
