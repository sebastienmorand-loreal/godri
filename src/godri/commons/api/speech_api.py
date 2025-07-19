"""Google Speech-to-Text API client with async aiohttp."""

import json
import logging
import base64
import asyncio
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .google_api_client import GoogleApiClient


class SpeechApiClient:
    """Async Google Speech-to-Text API client."""

    def __init__(self, api_client: GoogleApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://speech.googleapis.com/v1"

    async def recognize_sync(self, audio_content: bytes, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform synchronous speech recognition."""
        self.logger.info("Performing synchronous speech recognition")

        # Encode audio content as base64
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

        request_data = {"config": config, "audio": {"content": audio_base64}}

        url = f"{self.base_url}/speech:recognize"
        result = await self.api_client.make_request("POST", url, data=request_data)

        results = result.get("results", [])
        self.logger.info(f"Recognition completed with {len(results)} results")

        return result

    async def recognize_async(self, audio_uri: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start asynchronous speech recognition operation."""
        self.logger.info(f"Starting async speech recognition for: {audio_uri}")

        request_data = {"config": config, "audio": {"uri": audio_uri}}

        url = f"{self.base_url}/speech:longrunningrecognize"
        result = await self.api_client.make_request("POST", url, data=request_data)

        operation_name = result.get("name")
        self.logger.info(f"Async operation started: {operation_name}")

        return result

    async def get_operation_status(self, operation_name: str) -> Dict[str, Any]:
        """Get the status of a long-running operation."""
        self.logger.info(f"Checking operation status: {operation_name}")

        url = f"https://speech.googleapis.com/v1/operations/{operation_name}"
        result = await self.api_client.make_request("GET", url)

        done = result.get("done", False)
        self.logger.info(f"Operation done: {done}")

        return result

    async def wait_for_operation(
        self, operation_name: str, timeout: int = 300, check_interval: int = 5
    ) -> Dict[str, Any]:
        """Wait for a long-running operation to complete."""
        self.logger.info(f"Waiting for operation to complete: {operation_name}")

        start_time = asyncio.get_event_loop().time()

        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                raise TimeoutError(f"Operation timeout after {timeout} seconds")

            status = await self.get_operation_status(operation_name)

            if status.get("done", False):
                if "error" in status:
                    error = status["error"]
                    raise RuntimeError(f"Operation failed: {error.get('message', 'Unknown error')}")

                self.logger.info("Operation completed successfully")
                return status.get("response", {})

            self.logger.debug(f"Operation still running, waiting {check_interval}s...")
            await asyncio.sleep(check_interval)

    async def transcribe_audio_file(
        self,
        file_path: str,
        language_code: str = "en-US",
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
        sample_rate_hertz: Optional[int] = None,
        audio_channel_count: Optional[int] = None,
        encoding: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe an audio file using synchronous recognition."""
        self.logger.info(f"Transcribing audio file: {file_path}")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Detect audio properties if not provided
        audio_properties = self._detect_audio_properties(file_path)

        # Use detected properties as defaults
        if not sample_rate_hertz:
            sample_rate_hertz = audio_properties.get("sample_rate")
        if not audio_channel_count:
            audio_channel_count = audio_properties.get("channels", 1)
        if not encoding:
            encoding = audio_properties.get("encoding", "LINEAR16")

        # Read audio content
        with open(file_path, "rb") as audio_file:
            audio_content = audio_file.read()

        # Check file size for sync vs async decision
        file_size_mb = len(audio_content) / (1024 * 1024)
        if file_size_mb > 10:  # 10MB limit for sync recognition
            self.logger.warning(f"File size ({file_size_mb:.1f}MB) exceeds recommended limit for sync recognition")

        # Build recognition config
        config = {
            "encoding": encoding,
            "sampleRateHertz": sample_rate_hertz,
            "audioChannelCount": audio_channel_count,
            "languageCode": language_code,
            "enableAutomaticPunctuation": enable_automatic_punctuation,
            "enableWordTimeOffsets": enable_word_time_offsets,
        }

        # Perform recognition
        result = await self.recognize_sync(audio_content, config)

        # Process and format results
        return self._format_recognition_results(result, str(file_path), language_code, encoding, audio_properties)

    async def transcribe_audio_long(
        self,
        audio_uri: str,
        language_code: str = "en-US",
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
        sample_rate_hertz: Optional[int] = None,
        audio_channel_count: Optional[int] = None,
        encoding: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio using long-running recognition (for large files)."""
        self.logger.info(f"Starting long-running transcription for: {audio_uri}")

        # Build recognition config
        config = {
            "languageCode": language_code,
            "enableAutomaticPunctuation": enable_automatic_punctuation,
            "enableWordTimeOffsets": enable_word_time_offsets,
        }

        if encoding:
            config["encoding"] = encoding
        if sample_rate_hertz:
            config["sampleRateHertz"] = sample_rate_hertz
        if audio_channel_count:
            config["audioChannelCount"] = audio_channel_count

        # Start async operation
        operation = await self.recognize_async(audio_uri, config)
        operation_name = operation.get("name")

        if not operation_name:
            raise RuntimeError("Failed to start async recognition operation")

        # Wait for completion
        result = await self.wait_for_operation(operation_name)

        # Format results
        return self._format_recognition_results(result, audio_uri, language_code, encoding or "AUTO", {})

    def _detect_audio_properties(self, file_path: Path) -> Dict[str, Any]:
        """Detect audio file properties using mutagen."""
        try:
            from mutagen import File as MutagenFile
            from mutagen.id3 import ID3NoHeaderError
        except ImportError:
            self.logger.warning("Mutagen not available for audio property detection")
            return self._guess_audio_properties_by_extension(file_path)

        try:
            audio_file = MutagenFile(str(file_path))
            if audio_file is None:
                return self._guess_audio_properties_by_extension(file_path)

            properties = {}

            # Get basic info
            if hasattr(audio_file, "info"):
                info = audio_file.info
                properties["duration"] = getattr(info, "length", 0)
                properties["bitrate"] = getattr(info, "bitrate", 0)
                properties["sample_rate"] = getattr(info, "sample_rate", 16000)
                properties["channels"] = getattr(info, "channels", 1)

            # Determine encoding based on file extension and properties
            extension = file_path.suffix.lower()
            if extension == ".wav":
                properties["encoding"] = "LINEAR16"
            elif extension == ".flac":
                properties["encoding"] = "FLAC"
            elif extension in [".mp3", ".m4a", ".aac"]:
                properties["encoding"] = "MP3"
            elif extension == ".ogg":
                properties["encoding"] = "OGG_OPUS"
            else:
                properties["encoding"] = "LINEAR16"  # Default

            return properties

        except (ID3NoHeaderError, Exception) as e:
            self.logger.warning(f"Could not detect audio properties: {e}")
            return self._guess_audio_properties_by_extension(file_path)

    def _guess_audio_properties_by_extension(self, file_path: Path) -> Dict[str, Any]:
        """Guess audio properties based on file extension."""
        extension = file_path.suffix.lower()

        encoding_map = {
            ".wav": "LINEAR16",
            ".flac": "FLAC",
            ".mp3": "MP3",
            ".m4a": "MP3",
            ".aac": "MP3",
            ".ogg": "OGG_OPUS",
            ".opus": "OGG_OPUS",
        }

        return {
            "encoding": encoding_map.get(extension, "LINEAR16"),
            "sample_rate": 16000,  # Common default
            "channels": 1,
            "duration": 0,
            "bitrate": 0,
        }

    def _format_recognition_results(
        self,
        raw_result: Dict[str, Any],
        audio_source: str,
        language_code: str,
        encoding: str,
        audio_properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format recognition results into a consistent structure."""
        results = raw_result.get("results", [])

        transcripts = []
        for result in results:
            alternatives = result.get("alternatives", [])
            if alternatives:
                best_alternative = alternatives[0]  # First alternative is usually best

                transcript_data = {
                    "transcript": best_alternative.get("transcript", ""),
                    "confidence": best_alternative.get("confidence", 0.0),
                }

                # Add word timing if available
                words = best_alternative.get("words", [])
                if words:
                    word_timings = []
                    for word in words:
                        word_timings.append(
                            {
                                "word": word.get("word", ""),
                                "start_time": self._parse_duration(word.get("startTime", "0s")),
                                "end_time": self._parse_duration(word.get("endTime", "0s")),
                            }
                        )
                    transcript_data["words"] = word_timings

                transcripts.append(transcript_data)

        return {
            "audio_file": audio_source,
            "language_code": language_code,
            "encoding": encoding,
            "total_results": len(results),
            "transcripts": transcripts,
            "audio_properties": audio_properties,
        }

    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string (e.g., '1.234s') to float seconds."""
        if duration_str.endswith("s"):
            try:
                return float(duration_str[:-1])
            except ValueError:
                return 0.0
        return 0.0

    async def upload_audio_to_gcs(self, file_path: str, bucket_name: str, object_name: Optional[str] = None) -> str:
        """Upload audio file to Google Cloud Storage for long-running recognition."""
        self.logger.info(f"Uploading audio file to GCS: {file_path}")

        # This would require Google Cloud Storage API integration
        # For now, we'll return a placeholder URI and log the requirement
        self.logger.warning("GCS upload requires Google Cloud Storage API integration")

        if not object_name:
            object_name = Path(file_path).name

        gcs_uri = f"gs://{bucket_name}/{object_name}"
        self.logger.info(f"Would upload to: {gcs_uri}")

        # Placeholder - in real implementation, this would upload the file
        return gcs_uri

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages for speech recognition."""
        return [
            {"code": "en-US", "name": "English (United States)"},
            {"code": "en-GB", "name": "English (United Kingdom)"},
            {"code": "fr-FR", "name": "French (France)"},
            {"code": "es-ES", "name": "Spanish (Spain)"},
            {"code": "de-DE", "name": "German (Germany)"},
            {"code": "it-IT", "name": "Italian (Italy)"},
            {"code": "pt-BR", "name": "Portuguese (Brazil)"},
            {"code": "ru-RU", "name": "Russian (Russia)"},
            {"code": "ja-JP", "name": "Japanese (Japan)"},
            {"code": "ko-KR", "name": "Korean (South Korea)"},
            {"code": "zh-CN", "name": "Chinese (Simplified)"},
            {"code": "zh-TW", "name": "Chinese (Traditional)"},
            {"code": "ar-XA", "name": "Arabic"},
            {"code": "hi-IN", "name": "Hindi (India)"},
            {"code": "nl-NL", "name": "Dutch (Netherlands)"},
            {"code": "sv-SE", "name": "Swedish (Sweden)"},
            {"code": "no-NO", "name": "Norwegian (Norway)"},
            {"code": "da-DK", "name": "Danish (Denmark)"},
            {"code": "fi-FI", "name": "Finnish (Finland)"},
            {"code": "tr-TR", "name": "Turkish (Turkey)"},
            {"code": "pl-PL", "name": "Polish (Poland)"},
            {"code": "cs-CZ", "name": "Czech (Czech Republic)"},
            {"code": "hu-HU", "name": "Hungarian (Hungary)"},
            {"code": "ro-RO", "name": "Romanian (Romania)"},
            {"code": "sk-SK", "name": "Slovak (Slovakia)"},
            {"code": "bg-BG", "name": "Bulgarian (Bulgaria)"},
            {"code": "hr-HR", "name": "Croatian (Croatia)"},
            {"code": "sl-SI", "name": "Slovenian (Slovenia)"},
            {"code": "et-EE", "name": "Estonian (Estonia)"},
            {"code": "lv-LV", "name": "Latvian (Latvia)"},
            {"code": "lt-LT", "name": "Lithuanian (Lithuania)"},
        ]

    def normalize_language_code(self, language_input: str) -> str:
        """Normalize language input to standard BCP-47 format."""
        language_input = language_input.lower().strip()

        # Language shortcuts
        shortcuts = {
            "en": "en-US",
            "english": "en-US",
            "fr": "fr-FR",
            "french": "fr-FR",
            "es": "es-ES",
            "spanish": "es-ES",
            "de": "de-DE",
            "german": "de-DE",
            "it": "it-IT",
            "italian": "it-IT",
            "pt": "pt-BR",
            "portuguese": "pt-BR",
            "ru": "ru-RU",
            "russian": "ru-RU",
            "ja": "ja-JP",
            "japanese": "ja-JP",
            "ko": "ko-KR",
            "korean": "ko-KR",
            "zh": "zh-CN",
            "chinese": "zh-CN",
            "ar": "ar-XA",
            "arabic": "ar-XA",
            "hi": "hi-IN",
            "hindi": "hi-IN",
        }

        # Check shortcuts first
        if language_input in shortcuts:
            return shortcuts[language_input]

        # If already in BCP-47 format, validate and return
        supported_codes = [lang["code"] for lang in self.get_supported_languages()]
        if language_input.upper() in [code.upper() for code in supported_codes]:
            # Find the exact case match
            for code in supported_codes:
                if code.upper() == language_input.upper():
                    return code

        # Default to en-US if not recognized
        self.logger.warning(f"Language '{language_input}' not recognized, defaulting to en-US")
        return "en-US"

    def get_recommended_config(self, audio_properties: Dict[str, Any], use_case: str = "general") -> Dict[str, Any]:
        """Get recommended recognition config based on audio properties and use case."""
        config = {
            "encoding": audio_properties.get("encoding", "LINEAR16"),
            "sampleRateHertz": audio_properties.get("sample_rate", 16000),
            "audioChannelCount": audio_properties.get("channels", 1),
            "enableAutomaticPunctuation": True,
        }

        # Adjust based on use case
        if use_case == "dictation":
            config["enableWordTimeOffsets"] = True
            config["enableAutomaticPunctuation"] = True
        elif use_case == "conversation":
            config["enableSpeakerDiarization"] = True
            config["diarizationSpeakerCount"] = 2
        elif use_case == "phone_call":
            config["model"] = "phone_call"
            config["useEnhanced"] = True
        elif use_case == "video":
            config["model"] = "video"
            config["enableWordTimeOffsets"] = True

        return config
