"""Translation CLI commands."""

import asyncio
import logging
from typing import Optional
import typer
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

translate_app = typer.Typer(help="Translation commands")


@translate_app.command("text")
def translate_text(
    text: str = typer.Argument(..., help="Text to translate"),
    target_language: str = typer.Argument(..., help="Target language code"),
    source_language: Optional[str] = typer.Option(None, "--source", "-s", help="Source language code"),
):
    """Translate text to target language."""
    asyncio.run(_handle_translate_text(text, target_language, source_language))


async def _handle_translate_text(text: str, target_language: str, source_language: Optional[str]) -> None:
    """Handle text translation command."""
    try:
        # TODO: Update import after refactoring
        from ..services.translate_service import TranslateService
        from ..services.auth_service import AuthService

        auth_service = AuthService()
        translate_service = TranslateService(auth_service)
        await translate_service.initialize()

        result = await translate_service.translate_text(text, target_language, source_language)

        if result:
            console.print(f"Translated text: {result}", style="green")
        else:
            console.print("Translation failed", style="red")

    except Exception as e:
        logger.error("Translation failed: %s", str(e))
        console.print(f"Translation failed: {str(e)}", style="red")
