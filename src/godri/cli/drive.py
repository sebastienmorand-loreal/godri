"""Google Drive CLI commands."""

import asyncio
import logging
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)

drive_app = typer.Typer(help="Google Drive commands")


@drive_app.command()
def search(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="File name to search for"),
    mime_type: Optional[str] = typer.Option(None, "--mime-type", "-m", help="MIME type filter"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of results"),
):
    """Search for files in Google Drive."""
    asyncio.run(_handle_search(query, name, mime_type, limit))


@drive_app.command()
def download(
    file_id: str = typer.Argument(..., help="Google Drive file ID"),
    output_path: str = typer.Argument(..., help="Output file path"),
    smart: bool = typer.Option(False, "--smart", "-s", help="Smart download with format conversion"),
):
    """Download a file from Google Drive."""
    asyncio.run(_handle_download(file_id, output_path, smart))


@drive_app.command()
def upload(
    file_path: str = typer.Argument(..., help="Local file path to upload"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Custom name for uploaded file"),
    folder_id: Optional[str] = typer.Option(None, "--folder-id", "-f", help="Parent folder ID"),
):
    """Upload a file to Google Drive."""
    asyncio.run(_handle_upload(file_path, name, folder_id))


@drive_app.command("create-folder")
def create_folder(
    name: str = typer.Argument(..., help="Folder name"),
    parent_id: Optional[str] = typer.Option(None, "--parent-id", "-p", help="Parent folder ID"),
):
    """Create a new folder in Google Drive."""
    asyncio.run(_handle_create_folder(name, parent_id))


@drive_app.command("delete")
def delete_file(file_id: str = typer.Argument(..., help="Google Drive file ID to delete")):
    """Delete a file from Google Drive."""
    asyncio.run(_handle_delete(file_id))


async def _handle_search(query: Optional[str], name: Optional[str], mime_type: Optional[str], limit: int) -> None:
    """Handle search command."""
    try:
        # TODO: Update import after refactoring
        from ..services.drive_service import DriveService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        drive_service = DriveService(auth_service)
        await drive_service.initialize()

        if name:
            results = await drive_service.search_by_name(name, mime_type)
        else:
            results = await drive_service.search_files(query, limit)

        if not results:
            console.print("No files found.")
            return

        table = Table(title=f"Found {len(results)} files")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="magenta")
        table.add_column("Type", style="green")
        table.add_column("Size", style="yellow")
        table.add_column("Modified", style="blue")

        for file_info in results:
            table.add_row(
                file_info.get("name", ""),
                file_info.get("id", ""),
                file_info.get("mimeType", ""),
                file_info.get("size", "N/A"),
                file_info.get("modifiedTime", ""),
            )

        console.print(table)

    except Exception as e:
        logger.error("Search failed: %s", str(e))
        console.print(f"Search failed: {str(e)}", style="red")


async def _handle_download(file_id: str, output_path: str, smart: bool) -> None:
    """Handle download command."""
    try:
        # TODO: Update import after refactoring
        from ..services.drive_service import DriveService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        drive_service = DriveService(auth_service)
        await drive_service.initialize()

        success = await drive_service.download_file(file_id, output_path, smart)

        if success:
            console.print(f"File downloaded successfully to: {output_path}", style="green")
        else:
            console.print("Download failed", style="red")

    except Exception as e:
        logger.error("Download failed: %s", str(e))
        console.print(f"Download failed: {str(e)}", style="red")


async def _handle_upload(file_path: str, name: Optional[str], folder_id: Optional[str]) -> None:
    """Handle upload command."""
    try:
        # TODO: Update import after refactoring
        from ..services.drive_service import DriveService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        drive_service = DriveService(auth_service)
        await drive_service.initialize()

        result = await drive_service.upload_file(file_path, name, folder_id)

        if result:
            console.print(f"File uploaded successfully. ID: {result.get('id')}", style="green")
            console.print(f"Web URL: {result.get('webViewLink')}")
        else:
            console.print("Upload failed", style="red")

    except Exception as e:
        logger.error("Upload failed: %s", str(e))
        console.print(f"Upload failed: {str(e)}", style="red")


async def _handle_create_folder(name: str, parent_id: Optional[str]) -> None:
    """Handle create folder command."""
    try:
        # TODO: Update import after refactoring
        from ..services.drive_service import DriveService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        drive_service = DriveService(auth_service)
        await drive_service.initialize()

        result = await drive_service.create_folder(name, parent_id)

        if result:
            console.print(f"Folder created successfully. ID: {result.get('id')}", style="green")
            console.print(f"Web URL: {result.get('webViewLink')}")
        else:
            console.print("Folder creation failed", style="red")

    except Exception as e:
        logger.error("Folder creation failed: %s", str(e))
        console.print(f"Folder creation failed: {str(e)}", style="red")


async def _handle_delete(file_id: str) -> None:
    """Handle delete command."""
    try:
        # TODO: Update import after refactoring
        from ..services.drive_service import DriveService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        drive_service = DriveService(auth_service)
        await drive_service.initialize()

        success = await drive_service.delete_file(file_id)

        if success:
            console.print("File deleted successfully", style="green")
        else:
            console.print("Delete failed", style="red")

    except Exception as e:
        logger.error("Delete failed: %s", str(e))
        console.print(f"Delete failed: {str(e)}", style="red")
