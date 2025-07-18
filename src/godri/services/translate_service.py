"""Google Translate service wrapper."""

import logging
import os
from typing import Dict, Any, List, Optional
from google.cloud import translate_v2 as translate
from .auth_service import AuthService


class TranslateService:
    """Google Translate operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.project_id = "oa-data-btdpexploration-np"  # Use exploration project

    async def initialize(self):
        """Initialize the Translate service using local credentials with quota project."""
        # Use local credentials with explicit quota project configuration
        try:
            import google.auth
            from google.auth import impersonated_credentials
            from google.oauth2 import service_account

            # Get default credentials
            credentials, project = google.auth.default()

            # Create credentials with quota project
            if hasattr(credentials, "with_quota_project"):
                credentials_with_quota = credentials.with_quota_project(self.project_id)
            else:
                credentials_with_quota = credentials

            # Set the project explicitly for translation billing
            os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id

            # Initialize client with credentials that include quota project
            self.client = translate.Client(credentials=credentials_with_quota)
            self.logger.info(
                "Translate service initialized with local credentials and quota project: %s", self.project_id
            )
        except Exception as e:
            self.logger.error("Failed to initialize Translate service with local credentials: %s", str(e))
            self.logger.info("Attempting fallback to service account credentials...")
            # Fallback to service account credentials if available
            await self.auth_service.authenticate()
            self.client = translate.Client(credentials=self.auth_service.credentials)
            self.logger.info("Translate service initialized with service account credentials")

    def translate_text(self, text: str, target_language: str, source_language: Optional[str] = None) -> Dict[str, Any]:
        """Translate text to target language."""
        self.logger.info("Translating text to %s", target_language)

        kwargs = {"target_language": target_language}

        if source_language:
            kwargs["source_language"] = source_language

        result = self.client.translate(text, **kwargs)

        self.logger.info("Translation completed")
        return {
            "translatedText": result["translatedText"],
            "detectedSourceLanguage": result.get("detectedSourceLanguage"),
            "input": result.get("input"),
            "confidence": result.get("confidence"),
        }

    def translate_texts(
        self, texts: List[str], target_language: str, source_language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Translate multiple texts."""
        self.logger.info("Translating %d texts to %s", len(texts), target_language)

        kwargs = {"target_language": target_language}

        if source_language:
            kwargs["source_language"] = source_language

        results = self.client.translate(texts, **kwargs)

        translations = []
        for result in results:
            translations.append(
                {
                    "translatedText": result["translatedText"],
                    "detectedSourceLanguage": result.get("detectedSourceLanguage"),
                    "input": result.get("input"),
                    "confidence": result.get("confidence"),
                }
            )

        self.logger.info("Batch translation completed")
        return translations

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of text."""
        self.logger.info("Detecting language for text")

        result = self.client.detect_language(text)

        return {"language": result["language"], "confidence": result["confidence"], "input": result["input"]}

    def detect_languages(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Detect languages for multiple texts."""
        self.logger.info("Detecting languages for %d texts", len(texts))

        results = self.client.detect_language(texts)

        detections = []
        for result in results:
            detections.append(
                {"language": result["language"], "confidence": result["confidence"], "input": result["input"]}
            )

        return detections

    def get_supported_languages(self, target_language: str = "en") -> List[Dict[str, str]]:
        """Get list of supported languages."""
        self.logger.info("Getting supported languages")

        results = self.client.get_languages(target_language=target_language)

        languages = []
        for language in results:
            languages.append({"language": language["language"], "name": language["name"]})

        return languages

    def translate_with_model(
        self, text: str, target_language: str, model: str = "base", source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text using specific model."""
        self.logger.info("Translating text with model %s to %s", model, target_language)

        kwargs = {"target_language": target_language, "model": model}

        if source_language:
            kwargs["source_language"] = source_language

        result = self.client.translate(text, **kwargs)

        return {
            "translatedText": result["translatedText"],
            "detectedSourceLanguage": result.get("detectedSourceLanguage"),
            "input": result.get("input"),
            "model": model,
        }

    def get_language_name(self, language_code: str, target_language: str = "en") -> str:
        """Get the name of a language code in target language."""
        languages = self.get_supported_languages(target_language)

        for lang in languages:
            if lang["language"] == language_code:
                return lang["name"]

        return language_code
