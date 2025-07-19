"""Google Speech-to-Text API wrapper using aiogoogle for full async operations."""

import logging
import base64
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import asyncio

from .google_api_client import GoogleApiClient


class SpeechApiClient:
    """Async Google Speech-to-Text API client using aiogoogle."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Speech API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self._service = None

    async def _get_service(self):
        """Get or create Speech service."""
        if self._service is None:
            self._service = await self.api_client.discover_service("speech", "v1")
        return self._service

    async def recognize(
        self,
        audio_content: bytes,
        language_code: str = "en-US",
        encoding: str = "WEBM_OPUS",
        sample_rate_hertz: Optional[int] = None,
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
        max_alternatives: int = 1,
        profanity_filter: bool = False,
        enable_speaker_diarization: bool = False,
        diarization_speaker_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Recognize speech in audio content.

        Args:
            audio_content: Audio content as bytes
            language_code: Language code (e.g., "en-US", "fr-FR")
            encoding: Audio encoding format
            sample_rate_hertz: Sample rate in Hz
            enable_automatic_punctuation: Enable automatic punctuation
            enable_word_time_offsets: Enable word timing information
            max_alternatives: Maximum number of recognition alternatives
            profanity_filter: Enable profanity filter
            enable_speaker_diarization: Enable speaker diarization
            diarization_speaker_count: Number of speakers for diarization

        Returns:
            Recognition response
        """
        service = await self._get_service()

        # Encode audio content as base64
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

        # Build configuration
        config = {
            "encoding": encoding,
            "languageCode": language_code,
            "enableAutomaticPunctuation": enable_automatic_punctuation,
            "enableWordTimeOffsets": enable_word_time_offsets,
            "maxAlternatives": max_alternatives,
            "profanityFilter": profanity_filter,
        }

        if sample_rate_hertz:
            config["sampleRateHertz"] = sample_rate_hertz

        if enable_speaker_diarization:
            config["enableSpeakerDiarization"] = True
            if diarization_speaker_count:
                config["diarizationSpeakerCount"] = diarization_speaker_count

        # Build request body
        request_body = {"config": config, "audio": {"content": audio_base64}}

        return await self.api_client.execute_request(service, "speech.recognize", body=request_body)

    async def recognize_from_file(
        self,
        file_path: str,
        language_code: str = "en-US",
        encoding: Optional[str] = None,
        sample_rate_hertz: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Recognize speech from audio file.

        Args:
            file_path: Path to audio file
            language_code: Language code (e.g., "en-US", "fr-FR")
            encoding: Audio encoding format (auto-detected if None)
            sample_rate_hertz: Sample rate in Hz (auto-detected if None)
            **kwargs: Additional recognition parameters

        Returns:
            Recognition response
        """
        # Read audio file
        with open(file_path, "rb") as audio_file:
            audio_content = audio_file.read()

        # Auto-detect encoding and sample rate if not provided
        if not encoding or not sample_rate_hertz:
            detected_info = await self._detect_audio_format(file_path)
            if not encoding:
                encoding = detected_info.get("encoding", "LINEAR16")
            if not sample_rate_hertz:
                sample_rate_hertz = detected_info.get("sample_rate", 16000)

        return await self.recognize(
            audio_content=audio_content,
            language_code=language_code,
            encoding=encoding,
            sample_rate_hertz=sample_rate_hertz,
            **kwargs,
        )

    async def long_running_recognize(
        self,
        audio_content: bytes,
        language_code: str = "en-US",
        encoding: str = "WEBM_OPUS",
        sample_rate_hertz: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Start long-running speech recognition for large files.

        Args:
            audio_content: Audio content as bytes
            language_code: Language code
            encoding: Audio encoding format
            sample_rate_hertz: Sample rate in Hz
            **kwargs: Additional recognition parameters

        Returns:
            Operation name for polling
        """
        service = await self._get_service()

        # Encode audio content as base64
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

        # Build configuration
        config = {
            "encoding": encoding,
            "languageCode": language_code,
            "enableAutomaticPunctuation": kwargs.get("enable_automatic_punctuation", True),
            "enableWordTimeOffsets": kwargs.get("enable_word_time_offsets", False),
            "maxAlternatives": kwargs.get("max_alternatives", 1),
        }

        if sample_rate_hertz:
            config["sampleRateHertz"] = sample_rate_hertz

        # Build request body
        request_body = {"config": config, "audio": {"content": audio_base64}}

        response = await self.api_client.execute_request(service, "speech.longrunningrecognize", body=request_body)

        return response.get("name", "")

    async def get_operation(self, operation_name: str) -> Dict[str, Any]:
        """Get status of long-running operation.

        Args:
            operation_name: Operation name from long_running_recognize

        Returns:
            Operation status and result
        """
        service = await self._get_service()

        return await self.api_client.execute_request(service, "operations.get", name=operation_name)

    async def wait_for_operation(
        self, operation_name: str, poll_interval: int = 5, timeout: int = 600
    ) -> Dict[str, Any]:
        """Wait for long-running operation to complete.

        Args:
            operation_name: Operation name
            poll_interval: Polling interval in seconds
            timeout: Maximum wait time in seconds

        Returns:
            Final operation result
        """
        elapsed_time = 0

        while elapsed_time < timeout:
            operation = await self.get_operation(operation_name)

            if operation.get("done", False):
                if "error" in operation:
                    raise Exception(f"Operation failed: {operation['error']}")
                return operation.get("response", {})

            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval

        raise TimeoutError(f"Operation {operation_name} did not complete within {timeout} seconds")

    async def recognize_streaming(
        self,
        audio_chunks: List[bytes],
        language_code: str = "en-US",
        encoding: str = "WEBM_OPUS",
        sample_rate_hertz: Optional[int] = None,
        interim_results: bool = True,
        single_utterance: bool = False,
    ) -> List[Dict[str, Any]]:
        """Perform streaming speech recognition.

        Args:
            audio_chunks: List of audio chunks as bytes
            language_code: Language code
            encoding: Audio encoding format
            sample_rate_hertz: Sample rate in Hz
            interim_results: Return interim results
            single_utterance: Stop after single utterance

        Returns:
            List of recognition results
        """
        # Note: Streaming requires gRPC which aiogoogle doesn't support directly
        # For now, we'll process chunks sequentially using regular recognition
        results = []

        for i, chunk in enumerate(audio_chunks):
            try:
                result = await self.recognize(
                    audio_content=chunk,
                    language_code=language_code,
                    encoding=encoding,
                    sample_rate_hertz=sample_rate_hertz,
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=True,
                )

                # Add chunk index for reference
                result["chunk_index"] = i
                results.append(result)

            except Exception as e:
                self.logger.warning(f"Failed to process chunk {i}: {str(e)}")
                continue

        return results

    async def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List of supported language codes
        """
        # Common supported languages for Speech-to-Text
        return [
            "af-ZA",
            "am-ET",
            "ar-AE",
            "ar-BH",
            "ar-DZ",
            "ar-EG",
            "ar-IQ",
            "ar-IL",
            "ar-JO",
            "ar-KW",
            "ar-LB",
            "ar-LY",
            "ar-MA",
            "ar-OM",
            "ar-PS",
            "ar-QA",
            "ar-SA",
            "ar-SY",
            "ar-TN",
            "ar-YE",
            "az-AZ",
            "bg-BG",
            "bn-BD",
            "bn-IN",
            "bs-BA",
            "ca-ES",
            "cmn-Hans-CN",
            "cmn-Hans-HK",
            "cmn-Hant-TW",
            "cs-CZ",
            "da-DK",
            "de-AT",
            "de-CH",
            "de-DE",
            "el-GR",
            "en-AU",
            "en-CA",
            "en-GB",
            "en-IE",
            "en-IN",
            "en-NZ",
            "en-PH",
            "en-SG",
            "en-US",
            "en-ZA",
            "es-AR",
            "es-BO",
            "es-CL",
            "es-CO",
            "es-CR",
            "es-DO",
            "es-EC",
            "es-ES",
            "es-GT",
            "es-HN",
            "es-MX",
            "es-NI",
            "es-PA",
            "es-PE",
            "es-PR",
            "es-PY",
            "es-SV",
            "es-UY",
            "es-VE",
            "et-EE",
            "eu-ES",
            "fa-IR",
            "fi-FI",
            "fil-PH",
            "fr-BE",
            "fr-CA",
            "fr-CH",
            "fr-FR",
            "gl-ES",
            "gu-IN",
            "he-IL",
            "hi-IN",
            "hr-HR",
            "hu-HU",
            "hy-AM",
            "id-ID",
            "is-IS",
            "it-CH",
            "it-IT",
            "ja-JP",
            "jv-ID",
            "ka-GE",
            "kk-KZ",
            "km-KH",
            "kn-IN",
            "ko-KR",
            "lo-LA",
            "lt-LT",
            "lv-LV",
            "mk-MK",
            "ml-IN",
            "mn-MN",
            "mr-IN",
            "ms-MY",
            "mt-MT",
            "my-MM",
            "nb-NO",
            "ne-NP",
            "nl-BE",
            "nl-NL",
            "pl-PL",
            "pt-BR",
            "pt-PT",
            "ro-RO",
            "ru-RU",
            "si-LK",
            "sk-SK",
            "sl-SI",
            "sq-AL",
            "sr-RS",
            "su-ID",
            "sv-SE",
            "sw-KE",
            "sw-TZ",
            "ta-IN",
            "ta-LK",
            "ta-MY",
            "ta-SG",
            "te-IN",
            "th-TH",
            "tr-TR",
            "uk-UA",
            "ur-IN",
            "ur-PK",
            "uz-UZ",
            "vi-VN",
            "yue-Hant-HK",
            "zh-CN",
            "zh-HK",
            "zh-TW",
            "zu-ZA",
        ]

    async def _detect_audio_format(self, file_path: str) -> Dict[str, Any]:
        """Detect audio format and properties.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with encoding and sample rate information
        """
        try:
            from mutagen import File

            audio_file = File(file_path)
            if audio_file is None:
                return {"encoding": "LINEAR16", "sample_rate": 16000}

            # Get file info
            info = audio_file.info
            sample_rate = getattr(info, "sample_rate", 16000)

            # Determine encoding based on file extension
            file_ext = Path(file_path).suffix.lower()
            encoding_map = {
                ".wav": "LINEAR16",
                ".flac": "FLAC",
                ".opus": "WEBM_OPUS",
                ".ogg": "OGG_OPUS",
                ".webm": "WEBM_OPUS",
                ".mp3": "MP3",
                ".m4a": "MP3",  # Treating M4A as MP3 for Speech API
                ".aac": "MP3",  # Treating AAC as MP3 for Speech API
            }

            encoding = encoding_map.get(file_ext, "LINEAR16")

            return {
                "encoding": encoding,
                "sample_rate": sample_rate,
                "duration": getattr(info, "length", 0),
                "bitrate": getattr(info, "bitrate", 0),
            }

        except ImportError:
            self.logger.warning("mutagen not available, using default audio format detection")
            return {"encoding": "LINEAR16", "sample_rate": 16000}
        except Exception as e:
            self.logger.warning(f"Failed to detect audio format: {str(e)}")
            return {"encoding": "LINEAR16", "sample_rate": 16000}

    def get_optimal_encoding_for_file(self, file_path: str) -> str:
        """Get optimal encoding for a given file type.

        Args:
            file_path: Path to audio file

        Returns:
            Optimal encoding string
        """
        file_ext = Path(file_path).suffix.lower()

        encoding_map = {
            ".wav": "LINEAR16",
            ".flac": "FLAC",
            ".opus": "WEBM_OPUS",
            ".ogg": "OGG_OPUS",
            ".webm": "WEBM_OPUS",
            ".mp3": "MP3",
            ".m4a": "MP3",
            ".aac": "MP3",
        }

        return encoding_map.get(file_ext, "LINEAR16")
