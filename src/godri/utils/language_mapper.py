"""Language mapping utility for easy language code conversion."""

from typing import Dict, Optional, List


class LanguageMapper:
    """Maps common language shortcuts to full language codes for Google APIs."""

    # Mapping from simple language codes to full regional codes
    LANGUAGE_MAP: Dict[str, str] = {
        # English variants
        "en": "en-US",
        "english": "en-US",
        # French variants
        "fr": "fr-FR",
        "french": "fr-FR",
        "francais": "fr-FR",
        # Spanish variants
        "es": "es-ES",
        "spanish": "es-ES",
        "espanol": "es-ES",
        # German variants
        "de": "de-DE",
        "german": "de-DE",
        "deutsch": "de-DE",
        # Italian variants
        "it": "it-IT",
        "italian": "it-IT",
        "italiano": "it-IT",
        # Portuguese variants
        "pt": "pt-BR",  # Default to Brazilian Portuguese (more common)
        "portuguese": "pt-BR",
        "portugues": "pt-BR",
        # Chinese variants
        "zh": "zh-CN",  # Default to Simplified Chinese
        "chinese": "zh-CN",
        "mandarin": "zh-CN",
        # Japanese variants
        "ja": "ja-JP",
        "japanese": "ja-JP",
        # Korean variants
        "ko": "ko-KR",
        "korean": "ko-KR",
        # Russian variants
        "ru": "ru-RU",
        "russian": "ru-RU",
        # Arabic variants
        "ar": "ar-SA",  # Default to Saudi Arabia
        "arabic": "ar-SA",
        # Hindi variants
        "hi": "hi-IN",
        "hindi": "hi-IN",
        # Dutch variants
        "nl": "nl-NL",
        "dutch": "nl-NL",
        "nederlands": "nl-NL",
        # Swedish variants
        "sv": "sv-SE",
        "swedish": "sv-SE",
        "svenska": "sv-SE",
        # Danish variants
        "da": "da-DK",
        "danish": "da-DK",
        "dansk": "da-DK",
        # Norwegian variants
        "no": "no-NO",
        "norwegian": "no-NO",
        "norsk": "no-NO",
        # Finnish variants
        "fi": "fi-FI",
        "finnish": "fi-FI",
        "suomi": "fi-FI",
        # Polish variants
        "pl": "pl-PL",
        "polish": "pl-PL",
        "polski": "pl-PL",
        # Turkish variants
        "tr": "tr-TR",
        "turkish": "tr-TR",
        "turkce": "tr-TR",
    }

    # Additional regional variants for commonly used languages
    REGIONAL_VARIANTS: Dict[str, str] = {
        # English variants
        "en-gb": "en-GB",
        "en-uk": "en-GB",
        "en-au": "en-AU",
        "en-ca": "en-CA",
        "en-in": "en-IN",
        # Spanish variants
        "es-mx": "es-MX",  # Mexican Spanish
        "es-ar": "es-AR",  # Argentinian Spanish
        "es-us": "es-US",  # US Spanish
        # Portuguese variants
        "pt-pt": "pt-PT",  # European Portuguese
        "pt-br": "pt-BR",  # Brazilian Portuguese
        # Chinese variants
        "zh-tw": "zh-TW",  # Traditional Chinese (Taiwan)
        "zh-hk": "zh-HK",  # Cantonese (Hong Kong)
        # French variants
        "fr-ca": "fr-CA",  # Canadian French
        "fr-be": "fr-BE",  # Belgian French
        "fr-ch": "fr-CH",  # Swiss French
        # German variants
        "de-at": "de-AT",  # Austrian German
        "de-ch": "de-CH",  # Swiss German
        # Arabic variants
        "ar-ae": "ar-AE",  # UAE Arabic
        "ar-eg": "ar-EG",  # Egyptian Arabic
        "ar-ma": "ar-MA",  # Moroccan Arabic
    }

    @classmethod
    def normalize_language_code(cls, language_input: str) -> str:
        """Convert a language input to a standardized Google API language code.

        Args:
            language_input: Language code or name (e.g., 'fr', 'french', 'fr-FR', 'auto')

        Returns:
            Standardized language code (e.g., 'fr-FR') or 'auto' for auto-detection

        Raises:
            ValueError: If language is not supported
        """
        if not language_input or not language_input.strip():
            raise ValueError("Language input cannot be empty")

        # Normalize input: lowercase and strip whitespace
        normalized_input = language_input.lower().strip()

        # Handle auto-detection
        if normalized_input in ["auto", "automatic", "detect", "auto-detect"]:
            return "auto"

        # Check if it's already a valid full language code (e.g., 'fr-FR')
        if len(normalized_input) == 5 and "-" in normalized_input:
            # Convert to uppercase for country code
            parts = normalized_input.split("-")
            if len(parts) == 2:
                return f"{parts[0]}-{parts[1].upper()}"

        # Check regional variants first (more specific)
        if normalized_input in cls.REGIONAL_VARIANTS:
            return cls.REGIONAL_VARIANTS[normalized_input]

        # Check main language mapping
        if normalized_input in cls.LANGUAGE_MAP:
            return cls.LANGUAGE_MAP[normalized_input]

        # If it's not found in our mappings, reject it (but this should never happen for 'auto' now)
        available_shortcuts = cls.get_supported_shortcuts()
        raise ValueError(f"Unsupported language: '{language_input}'. Use one of: {available_shortcuts}")

    @classmethod
    def get_supported_shortcuts(cls) -> List[str]:
        """Get list of all supported language shortcuts.

        Returns:
            Sorted list of supported language shortcuts
        """
        all_shortcuts = list(cls.LANGUAGE_MAP.keys()) + list(cls.REGIONAL_VARIANTS.keys()) + ["auto"]
        return sorted(set(all_shortcuts))

    @classmethod
    def get_language_info(cls, language_input: str) -> Dict[str, str]:
        """Get detailed information about a language code.

        Args:
            language_input: Language code or name

        Returns:
            Dictionary with language information
        """
        try:
            normalized_code = cls.normalize_language_code(language_input)

            # Extract language and region
            if "-" in normalized_code:
                lang, region = normalized_code.split("-", 1)
            else:
                lang, region = normalized_code, ""

            # Get language name mapping
            language_names = {
                "en": "English",
                "fr": "French",
                "es": "Spanish",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese",
                "zh": "Chinese",
                "ja": "Japanese",
                "ko": "Korean",
                "ru": "Russian",
                "ar": "Arabic",
                "hi": "Hindi",
                "nl": "Dutch",
                "sv": "Swedish",
                "da": "Danish",
                "no": "Norwegian",
                "fi": "Finnish",
                "pl": "Polish",
                "tr": "Turkish",
            }

            # Get region name mapping
            region_names = {
                "US": "United States",
                "GB": "United Kingdom",
                "AU": "Australia",
                "CA": "Canada",
                "IN": "India",
                "FR": "France",
                "ES": "Spain",
                "MX": "Mexico",
                "AR": "Argentina",
                "DE": "Germany",
                "AT": "Austria",
                "CH": "Switzerland",
                "IT": "Italy",
                "BR": "Brazil",
                "PT": "Portugal",
                "CN": "China (Simplified)",
                "TW": "Taiwan (Traditional)",
                "HK": "Hong Kong",
                "JP": "Japan",
                "KR": "South Korea",
                "RU": "Russia",
                "SA": "Saudi Arabia",
                "AE": "UAE",
                "EG": "Egypt",
                "MA": "Morocco",
                "NL": "Netherlands",
                "BE": "Belgium",
                "SE": "Sweden",
                "DK": "Denmark",
                "NO": "Norway",
                "FI": "Finland",
                "PL": "Poland",
                "TR": "Turkey",
            }

            language_name = language_names.get(lang, lang.upper())
            region_name = region_names.get(region, region) if region else ""

            display_name = f"{language_name}"
            if region_name:
                display_name += f" ({region_name})"

            return {
                "code": normalized_code,
                "language": lang,
                "region": region,
                "display_name": display_name,
                "input": language_input,
            }

        except ValueError as e:
            return {
                "error": str(e),
                "input": language_input,
            }

    @classmethod
    def suggest_similar_languages(cls, invalid_input: str) -> List[str]:
        """Suggest similar language codes for invalid input.

        Args:
            invalid_input: The invalid language input

        Returns:
            List of suggested language codes
        """
        suggestions = []
        invalid_lower = invalid_input.lower()

        # Look for partial matches
        for shortcut in cls.get_supported_shortcuts():
            if invalid_lower in shortcut or shortcut.startswith(invalid_lower):
                suggestions.append(shortcut)

        # If no partial matches, suggest the most common languages including auto
        if not suggestions:
            suggestions = ["auto", "en", "fr", "es", "de", "it", "pt", "zh", "ja", "ru", "ar"]

        return suggestions[:5]  # Limit to 5 suggestions
