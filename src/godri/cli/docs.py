"""Google Docs CLI commands."""

import asyncio
import logging
from typing import Optional
import typer
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

docs_app = typer.Typer(help="Google Docs commands")


@docs_app.command("create")
def create_document(
    title: str = typer.Argument(..., help="Document title"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Initial content"),
    folder_id: Optional[str] = typer.Option(None, "--folder-id", "-f", help="Parent folder ID"),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Content is in markdown format"),
):
    """Create a new Google Document."""
    asyncio.run(_handle_create(title, content, folder_id, markdown))


@docs_app.command("read")
def read_document(
    document_id: str = typer.Argument(..., help="Google Docs document ID"),
    plain_text: bool = typer.Option(False, "--plain-text", "-p", help="Output plain text only"),
):
    """Read content from a Google Document."""
    asyncio.run(_handle_read(document_id, plain_text))


@docs_app.command("update")
def update_document(
    document_id: str = typer.Argument(..., help="Google Docs document ID"),
    content: str = typer.Argument(..., help="Content to add/replace"),
    replace: bool = typer.Option(False, "--replace", "-r", help="Replace entire document"),
    index: int = typer.Option(1, "--index", "-i", help="Insertion position"),
    markdown: bool = typer.Option(False, "--markdown", "-m", help="Content is in markdown format"),
):
    """Update Google Document content."""
    asyncio.run(_handle_update(document_id, content, replace, index, markdown))


@docs_app.command("translate")
def translate_document(
    document_id: str = typer.Argument(..., help="Google Docs document ID"),
    target_language: str = typer.Argument(..., help="Target language code"),
    source_language: Optional[str] = typer.Option(None, "--source", "-s", help="Source language code"),
    start_index: int = typer.Option(1, "--start", help="Start index for translation"),
    end_index: int = typer.Option(0, "--end", help="End index for translation (0 = end of document)"),
):
    """Translate Google Document content."""
    asyncio.run(_handle_translate(document_id, target_language, source_language, start_index, end_index))


async def _handle_create(title: str, content: Optional[str], folder_id: Optional[str], markdown: bool) -> None:
    """Handle create document command."""
    try:
        # TODO: Update import after refactoring
        from ..services.docs_service import DocsService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        docs_service = DocsService(auth_service)
        await docs_service.initialize()

        result = await docs_service.create_document(title, content or "", folder_id, markdown)

        if result:
            console.print(f"Document created successfully. ID: {result.get('documentId')}", style="green")
            console.print(f"Title: {result.get('title')}")
        else:
            console.print("Document creation failed", style="red")

    except Exception as e:
        logger.error("Document creation failed: %s", str(e))
        console.print(f"Document creation failed: {str(e)}", style="red")


async def _handle_read(document_id: str, plain_text: bool) -> None:
    """Handle read document command."""
    try:
        # TODO: Update import after refactoring
        from ..services.docs_service import DocsService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        docs_service = DocsService(auth_service)
        await docs_service.initialize()

        content = await docs_service.read_document(document_id, plain_text)
        console.print(content)

    except Exception as e:
        logger.error("Read failed: %s", str(e))
        console.print(f"Read failed: {str(e)}", style="red")


async def _handle_update(document_id: str, content: str, replace: bool, index: int, markdown: bool) -> None:
    """Handle update document command."""
    try:
        # TODO: Update import after refactoring
        from ..services.docs_service import DocsService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        docs_service = DocsService(auth_service)
        await docs_service.initialize()

        success = await docs_service.update_document(document_id, content, replace, index, markdown)

        if success:
            console.print("Document updated successfully", style="green")
        else:
            console.print("Update failed", style="red")

    except Exception as e:
        logger.error("Update failed: %s", str(e))
        console.print(f"Update failed: {str(e)}", style="red")


async def _handle_translate(
    document_id: str, target_language: str, source_language: Optional[str], start_index: int, end_index: int
) -> None:
    """Handle translate document command."""
    try:
        # TODO: Update import after refactoring
        from ..services.docs_service import DocsService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        docs_service = DocsService(auth_service)
        await docs_service.initialize()

        success = await docs_service.translate_document(
            document_id, target_language, source_language, start_index, end_index
        )

        if success:
            console.print("Document translated successfully", style="green")
        else:
            console.print("Translation failed", style="red")

    except Exception as e:
        logger.error("Translation failed: %s", str(e))
        console.print(f"Translation failed: {str(e)}", style="red")
