"""Google Translate service wrapper."""

import logging
from typing import Dict, Any, List, Optional
from ..commons.api.google_api_client import GoogleApiClient
from ..commons.api.translate_api import TranslateApiClient
from .auth_service_new import AuthService


class TranslateService:
    """Google Translate operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.translate_api = None

    async def initialize(self):
        """Initialize the Translate service using gcloud access token."""
        # Get gcloud access token instead of OAuth2 credentials
        access_token = await self.auth_service.get_gcloud_access_token()
        if not access_token:
            raise ValueError("Failed to get gcloud access token for Google Translate")

        # Create a simple token credentials object
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=access_token)

        api_client = GoogleApiClient(credentials)
        await api_client.initialize()
        self.translate_api = TranslateApiClient(api_client)
        self.logger.info("Translate service initialized with gcloud token")

    async def translate_text(
        self, text: str, target_language: str, source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to target language."""
        self.logger.info("Translating text to %s", target_language)

        result = await self.translate_api.translate_text(text, target_language, source_language)

        self.logger.info("Translation completed")
        return result

    async def translate_texts(
        self, texts: List[str], target_language: str, source_language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Translate multiple texts."""
        self.logger.info("Translating %d texts to %s", len(texts), target_language)

        results = await self.translate_api.translate_texts(texts, target_language, source_language)

        self.logger.info("Batch translation completed")
        return results

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of text."""
        self.logger.info("Detecting language for text")

        result = await self.translate_api.detect_language(text)
        return result

    async def detect_languages(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Detect languages for multiple texts."""
        self.logger.info("Detecting languages for %d texts", len(texts))

        results = await self.translate_api.detect_languages(texts)
        return results

    async def get_supported_languages(self, target_language: str = "en") -> List[Dict[str, str]]:
        """Get list of supported languages."""
        self.logger.info("Getting supported languages")

        results = await self.translate_api.get_supported_languages(target_language)
        return results

    async def translate_with_model(
        self, text: str, target_language: str, model: str = "base", source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text using specific model."""
        self.logger.info("Translating text with model %s to %s", model, target_language)

        result = await self.translate_api.translate_with_model(text, target_language, model, source_language)
        return result

    async def get_language_name(self, language_code: str, target_language: str = "en") -> str:
        """Get the name of a language code in target language."""
        languages = await self.get_supported_languages(target_language)

        for lang in languages:
            if lang["language"] == language_code:
                return lang["name"]

        return language_code
