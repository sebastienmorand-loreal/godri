"""Google Translate API wrapper using async HTTP client."""

import logging
from typing import Optional, Dict, Any, List
from .google_api_client import GoogleApiClient


class TranslateApiClient:
    """Async Google Translate API client."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Translate API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.base_url = "/language/translate/v2"

    async def translate_text(
        self, text: str, target_language: str, source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to target language.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if None)

        Returns:
            Translation response
        """
        params = {"q": text, "target": target_language}

        if source_language:
            params["source"] = source_language

        return await self.api_client.post(self.base_url, json_data=params)

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text.

        Args:
            text: Text to analyze

        Returns:
            Detection response
        """
        params = {"q": text}
        return await self.api_client.post(f"{self.base_url}/detect", json_data=params)

    async def get_supported_languages(self, target: Optional[str] = None) -> Dict[str, Any]:
        """Get list of supported languages.

        Args:
            target: Target language for language names

        Returns:
            Supported languages response
        """
        params = {}
        if target:
            params["target"] = target

        return await self.api_client.get(f"{self.base_url}/languages", params=params)
