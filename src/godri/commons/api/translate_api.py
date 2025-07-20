"""Google Translate API client with async aiohttp."""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from .google_api_client import GoogleApiClient


class TranslateApiClient:
    """Async Google Translate API client."""

    def __init__(self, api_client: GoogleApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://translation.googleapis.com/language/translate/v2"
        self._quota_project = None

    async def _get_quota_project(self) -> Optional[str]:
        """Get quota project from gcloud config."""
        if self._quota_project:
            return self._quota_project

        try:
            result = await asyncio.create_subprocess_shell(
                "gcloud config get core/project",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                self._quota_project = stdout.decode().strip()
                self.logger.debug("Got quota project: %s", self._quota_project)
                return self._quota_project
            else:
                self.logger.warning("Failed to get quota project: %s", stderr.decode())
                return None
        except Exception as e:
            self.logger.warning("Failed to run gcloud command: %s", str(e))
            return None

    async def translate_text(
        self,
        text: Union[str, List[str]],
        target_language: str,
        source_language: Optional[str] = None,
        format_type: str = "text",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Translate text to target language."""

        # Ensure text is a list for consistent processing
        text_list = [text] if isinstance(text, str) else text
        self.logger.info(f"Translating {len(text_list)} text(s) to {target_language}")

        translate_data = {"q": text_list, "target": target_language, "format": format_type}

        if source_language:
            translate_data["source"] = source_language
        if model:
            translate_data["model"] = model

        # Get quota project and add to URL and headers
        quota_project = await self._get_quota_project()
        url = f"{self.base_url}"

        additional_headers = {}
        if quota_project:
            url = f"{self.base_url}?quotaUser={quota_project}"
            additional_headers["X-Goog-User-Project"] = quota_project

        result = await self.api_client.make_request(
            "POST", url, data=translate_data, additional_headers=additional_headers
        )

        translations = result.get("data", {}).get("translations", [])
        self.logger.info(f"Successfully translated {len(translations)} text(s)")

        # Return single translation if input was a single string
        if isinstance(text, str) and len(translations) == 1:
            translation = translations[0]
            return {
                "translatedText": translation.get("translatedText", ""),
                "detectedSourceLanguage": translation.get("detectedSourceLanguage"),
                "model": translation.get("model"),
            }

        return result

    async def detect_language(self, text: Union[str, List[str]]) -> Dict[str, Any]:
        """Detect the language of input text."""

        # Ensure text is a list for consistent processing
        text_list = [text] if isinstance(text, str) else text
        self.logger.info(f"Detecting language for {len(text_list)} text(s)")

        detect_data = {"q": text_list}
        url = f"{self.base_url}/detect"

        result = await self.api_client.make_request("POST", url, data=detect_data)

        detections = result.get("data", {}).get("detections", [])
        self.logger.info(f"Successfully detected languages for {len(detections)} text(s)")

        # Return single detection if input was a single string
        if isinstance(text, str) and len(detections) == 1 and len(detections[0]) > 0:
            detection = detections[0][0]  # Get first (most confident) detection
            return {
                "language": detection.get("language"),
                "confidence": detection.get("confidence", 0.0),
                "isReliable": detection.get("isReliable", False),
            }

        return result

    async def get_supported_languages(self, target_language: Optional[str] = None) -> Dict[str, Any]:
        """Get list of supported languages."""
        self.logger.info("Getting supported languages")

        params = {}
        if target_language:
            params["target"] = target_language

        url = f"{self.base_url}/languages"
        result = await self.api_client.make_request("GET", url, params=params)

        languages = result.get("data", {}).get("languages", [])
        self.logger.info(f"Retrieved {len(languages)} supported languages")

        return result

    async def translate_document(
        self,
        document_content: str,
        target_language: str,
        source_language: Optional[str] = None,
        format_type: str = "html",
        preserve_formatting: bool = True,
    ) -> Dict[str, Any]:
        """Translate document content while attempting to preserve formatting."""
        self.logger.info(f"Translating document to {target_language}")

        if preserve_formatting and format_type == "html":
            # Split content into translatable segments while preserving HTML structure
            segments = self._extract_translatable_segments(document_content)

            if not segments:
                self.logger.warning("No translatable content found in document")
                return {"translatedText": document_content, "detectedSourceLanguage": None, "segmentsTranslated": 0}

            # Translate all segments at once
            segment_texts = [seg["text"] for seg in segments]
            translation_result = await self.translate_text(
                segment_texts, target_language, source_language, "text"  # Use text format for individual segments
            )

            translations = translation_result.get("data", {}).get("translations", [])

            if len(translations) != len(segments):
                self.logger.error("Translation count mismatch")
                return {"error": "Translation failed - segment count mismatch"}

            # Replace original segments with translations
            translated_content = document_content
            offset = 0

            for i, segment in enumerate(segments):
                if i < len(translations):
                    original_text = segment["text"]
                    translated_text = translations[i].get("translatedText", original_text)

                    # Adjust position based on previous replacements
                    start_pos = segment["start"] + offset
                    end_pos = segment["end"] + offset

                    # Replace the text
                    translated_content = translated_content[:start_pos] + translated_text + translated_content[end_pos:]

                    # Update offset for next replacements
                    offset += len(translated_text) - len(original_text)

            detected_language = translations[0].get("detectedSourceLanguage") if translations else None

            return {
                "translatedText": translated_content,
                "detectedSourceLanguage": detected_language,
                "segmentsTranslated": len(translations),
            }
        else:
            # Simple translation without formatting preservation
            return await self.translate_text(document_content, target_language, source_language, format_type)

    def _extract_translatable_segments(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract translatable text segments from HTML content."""
        import re

        segments = []

        # Pattern to match text outside of HTML tags
        # This is a simplified approach - a full HTML parser would be more robust
        pattern = r">([^<]+)<"

        for match in re.finditer(pattern, html_content):
            text = match.group(1).strip()
            if text and not text.isspace():
                # Skip if text is just numbers, punctuation, or very short
                if len(text) > 2 and not text.replace(" ", "").replace(".", "").replace(",", "").isdigit():
                    segments.append({"text": text, "start": match.start(1), "end": match.end(1)})

        return segments

    async def translate_batch(
        self, texts: List[str], target_language: str, source_language: Optional[str] = None, batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Translate large batches of text efficiently."""
        self.logger.info(f"Translating {len(texts)} texts in batches of {batch_size}")

        all_results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            self.logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch)} texts")

            try:
                result = await self.translate_text(batch, target_language, source_language)

                translations = result.get("data", {}).get("translations", [])
                all_results.extend(translations)

            except Exception as e:
                self.logger.error(f"Failed to translate batch {i//batch_size + 1}: {e}")
                # Add placeholder results for failed batch
                for _ in batch:
                    all_results.append({"translatedText": "", "error": str(e)})

        self.logger.info(f"Completed batch translation: {len(all_results)} results")
        return all_results

    async def translate_with_glossary(
        self,
        text: Union[str, List[str]],
        target_language: str,
        glossary_config: Dict[str, Any],
        source_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Translate text using a custom glossary."""
        self.logger.info(f"Translating with glossary to {target_language}")

        # This would require Google Cloud Translation API v3 for full glossary support
        # For now, we'll do basic translation and log the glossary requirement
        self.logger.warning("Glossary translation requires Cloud Translation API v3")

        return await self.translate_text(text, target_language, source_language)

    def normalize_language_code(self, language_code: str) -> str:
        """Normalize language code to standard format."""
        # Handle common language code variations
        language_mapping = {
            "en": "en",
            "english": "en",
            "fr": "fr",
            "french": "fr",
            "es": "es",
            "spanish": "es",
            "de": "de",
            "german": "de",
            "it": "it",
            "italian": "it",
            "pt": "pt",
            "portuguese": "pt",
            "ru": "ru",
            "russian": "ru",
            "ja": "ja",
            "japanese": "ja",
            "ko": "ko",
            "korean": "ko",
            "zh": "zh",
            "chinese": "zh",
            "ar": "ar",
            "arabic": "ar",
            "hi": "hi",
            "hindi": "hi",
        }

        normalized = language_code.lower().strip()
        return language_mapping.get(normalized, normalized)

    async def translate_with_confidence_check(
        self, text: str, target_language: str, source_language: Optional[str] = None, min_confidence: float = 0.8
    ) -> Dict[str, Any]:
        """Translate text with language detection confidence check."""
        self.logger.info(f"Translating with confidence check (min: {min_confidence})")

        # First detect the language if not provided
        if not source_language:
            detection_result = await self.detect_language(text)

            confidence = detection_result.get("confidence", 0.0)
            detected_language = detection_result.get("language")

            if confidence < min_confidence:
                self.logger.warning(f"Low confidence language detection: {confidence}")
                return {
                    "error": f"Language detection confidence too low: {confidence}",
                    "detectedLanguage": detected_language,
                    "confidence": confidence,
                }

            source_language = detected_language

        # Proceed with translation
        result = await self.translate_text(text, target_language, source_language)

        # Add confidence information to result
        if isinstance(result, dict):
            result["detectionConfidence"] = min_confidence

        return result

    async def get_translation_usage(self) -> Dict[str, Any]:
        """Get translation API usage statistics (if available)."""
        self.logger.info("Getting translation usage statistics")

        # This would typically require Cloud Translation API v3 or quotas API
        # For now, return a placeholder
        return {
            "message": "Usage statistics require Cloud Translation API v3",
            "charactersTranslated": "N/A",
            "quotaRemaining": "N/A",
        }
