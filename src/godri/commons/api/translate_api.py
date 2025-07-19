"""Google Translate API wrapper using aiogoogle for full async operations."""

import logging
from typing import Optional, Dict, Any, List, Union

from .google_api_client import GoogleApiClient


class TranslateApiClient:
    """Async Google Translate API client using aiogoogle."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Translate API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self._service = None

    async def _get_service(self):
        """Get or create Translate service."""
        if self._service is None:
            self._service = await self.api_client.discover_service("translate", "v2")
        return self._service

    async def translate_text(
        self,
        text: Union[str, List[str]],
        target_language: str,
        source_language: Optional[str] = None,
        format_type: str = "text",
    ) -> Dict[str, Any]:
        """Translate text to target language.

        Args:
            text: Text to translate (string or list of strings)
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
            format_type: Format of text ('text' or 'html')

        Returns:
            Translation response
        """
        service = await self._get_service()

        # Prepare input text
        if isinstance(text, str):
            text_list = [text]
        else:
            text_list = text

        params = {"q": text_list, "target": target_language, "format": format_type}

        if source_language:
            params["source"] = source_language

        return await self.api_client.execute_request(service, "translations.translate", **params)

    async def detect_language(self, text: Union[str, List[str]]) -> Dict[str, Any]:
        """Detect language of text.

        Args:
            text: Text to analyze (string or list of strings)

        Returns:
            Detection response
        """
        service = await self._get_service()

        # Prepare input text
        if isinstance(text, str):
            text_list = [text]
        else:
            text_list = text

        params = {"q": text_list}

        return await self.api_client.execute_request(service, "detections.detect", **params)

    async def get_supported_languages(self, target_language: Optional[str] = None) -> Dict[str, Any]:
        """Get list of supported languages.

        Args:
            target_language: Language code for language names (optional)

        Returns:
            Supported languages response
        """
        service = await self._get_service()

        params = {}
        if target_language:
            params["target"] = target_language

        return await self.api_client.execute_request(service, "languages.list", **params)

    async def translate_batch(
        self, texts: List[str], target_language: str, source_language: Optional[str] = None, format_type: str = "text"
    ) -> List[Dict[str, Any]]:
        """Translate multiple texts in batch.

        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
            format_type: Format of text ('text' or 'html')

        Returns:
            List of translation responses
        """
        # Split into smaller batches if needed (API limit is typically 128 strings)
        batch_size = 100
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self.translate_text(batch, target_language, source_language, format_type)

            # Extract translations from response
            translations = response.get("data", {}).get("translations", [])
            results.extend(translations)

        return results

    async def translate_with_confidence(
        self, text: str, target_language: str, source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text and return confidence score.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if None)

        Returns:
            Translation with confidence information
        """
        # First detect language if not provided
        detected_language = None
        if not source_language:
            detection_result = await self.detect_language(text)
            detections = detection_result.get("data", {}).get("detections", [[]])[0]
            if detections:
                detected_language = detections[0].get("language")
                confidence = detections[0].get("confidence", 0.0)
            else:
                confidence = 0.0
        else:
            detected_language = source_language
            confidence = 1.0

        # Translate text
        translation_result = await self.translate_text(text, target_language, detected_language)
        translations = translation_result.get("data", {}).get("translations", [])

        if translations:
            return {
                "translatedText": translations[0].get("translatedText", ""),
                "detectedSourceLanguage": detected_language,
                "confidence": confidence,
                "targetLanguage": target_language,
            }
        else:
            return {
                "translatedText": "",
                "detectedSourceLanguage": detected_language,
                "confidence": 0.0,
                "targetLanguage": target_language,
            }

    async def is_translation_needed(
        self, text: str, target_language: str, confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Check if translation is needed for the text.

        Args:
            text: Text to check
            target_language: Target language code
            confidence_threshold: Minimum confidence for language detection

        Returns:
            Dictionary with translation_needed flag and detected language info
        """
        detection_result = await self.detect_language(text)
        detections = detection_result.get("data", {}).get("detections", [[]])[0]

        if not detections:
            return {
                "translation_needed": True,
                "detected_language": None,
                "confidence": 0.0,
                "reason": "Could not detect language",
            }

        detected_language = detections[0].get("language")
        confidence = detections[0].get("confidence", 0.0)

        # Check if detection confidence is sufficient
        if confidence < confidence_threshold:
            return {
                "translation_needed": True,
                "detected_language": detected_language,
                "confidence": confidence,
                "reason": f"Low confidence detection ({confidence:.2f})",
            }

        # Check if target language matches detected language
        translation_needed = detected_language.lower() != target_language.lower()

        return {
            "translation_needed": translation_needed,
            "detected_language": detected_language,
            "confidence": confidence,
            "reason": "Different languages" if translation_needed else "Same language",
        }

    def get_language_name(self, language_code: str) -> str:
        """Get human-readable language name from code.

        Args:
            language_code: Two-letter language code

        Returns:
            Human-readable language name
        """
        language_names = {
            "af": "Afrikaans",
            "sq": "Albanian",
            "am": "Amharic",
            "ar": "Arabic",
            "hy": "Armenian",
            "az": "Azerbaijani",
            "eu": "Basque",
            "be": "Belarusian",
            "bn": "Bengali",
            "bs": "Bosnian",
            "bg": "Bulgarian",
            "ca": "Catalan",
            "ceb": "Cebuano",
            "ny": "Chichewa",
            "zh": "Chinese",
            "zh-cn": "Chinese (Simplified)",
            "zh-tw": "Chinese (Traditional)",
            "co": "Corsican",
            "hr": "Croatian",
            "cs": "Czech",
            "da": "Danish",
            "nl": "Dutch",
            "en": "English",
            "eo": "Esperanto",
            "et": "Estonian",
            "tl": "Filipino",
            "fi": "Finnish",
            "fr": "French",
            "fy": "Frisian",
            "gl": "Galician",
            "ka": "Georgian",
            "de": "German",
            "el": "Greek",
            "gu": "Gujarati",
            "ht": "Haitian Creole",
            "ha": "Hausa",
            "haw": "Hawaiian",
            "iw": "Hebrew",
            "he": "Hebrew",
            "hi": "Hindi",
            "hmn": "Hmong",
            "hu": "Hungarian",
            "is": "Icelandic",
            "ig": "Igbo",
            "id": "Indonesian",
            "ga": "Irish",
            "it": "Italian",
            "ja": "Japanese",
            "jw": "Javanese",
            "kn": "Kannada",
            "kk": "Kazakh",
            "km": "Khmer",
            "ko": "Korean",
            "ku": "Kurdish (Kurmanji)",
            "ky": "Kyrgyz",
            "lo": "Lao",
            "la": "Latin",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "lb": "Luxembourgish",
            "mk": "Macedonian",
            "mg": "Malagasy",
            "ms": "Malay",
            "ml": "Malayalam",
            "mt": "Maltese",
            "mi": "Maori",
            "mr": "Marathi",
            "mn": "Mongolian",
            "my": "Myanmar (Burmese)",
            "ne": "Nepali",
            "no": "Norwegian",
            "or": "Odia",
            "ps": "Pashto",
            "fa": "Persian",
            "pl": "Polish",
            "pt": "Portuguese",
            "pa": "Punjabi",
            "ro": "Romanian",
            "ru": "Russian",
            "sm": "Samoan",
            "gd": "Scots Gaelic",
            "sr": "Serbian",
            "st": "Sesotho",
            "sn": "Shona",
            "sd": "Sindhi",
            "si": "Sinhala",
            "sk": "Slovak",
            "sl": "Slovenian",
            "so": "Somali",
            "es": "Spanish",
            "su": "Sundanese",
            "sw": "Swahili",
            "sv": "Swedish",
            "tg": "Tajik",
            "ta": "Tamil",
            "tt": "Tatar",
            "te": "Telugu",
            "th": "Thai",
            "tr": "Turkish",
            "tk": "Turkmen",
            "uk": "Ukrainian",
            "ur": "Urdu",
            "ug": "Uyghur",
            "uz": "Uzbek",
            "vi": "Vietnamese",
            "cy": "Welsh",
            "xh": "Xhosa",
            "yi": "Yiddish",
            "yo": "Yoruba",
            "zu": "Zulu",
        }

        return language_names.get(language_code.lower(), language_code.upper())
