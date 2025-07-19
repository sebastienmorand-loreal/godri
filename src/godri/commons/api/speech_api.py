"""Google Speech-to-Text API wrapper using async HTTP client."""

import logging
import base64
from typing import Optional, Dict, Any, List
from .google_api_client import GoogleApiClient


class SpeechApiClient:
    """Async Google Speech-to-Text API client."""

    def __init__(self, api_client: GoogleApiClient):
        """Initialize Speech API client.

        Args:
            api_client: Google API client instance
        """
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.base_url = "/speech/v1"

    async def recognize(
        self,
        audio_content: bytes,
        language_code: str = "en-US",
        encoding: str = "WEBM_OPUS",
        sample_rate_hertz: Optional[int] = None,
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
    ) -> Dict[str, Any]:
        """Recognize speech in audio content.

        Args:
            audio_content: Audio content as bytes
            language_code: Language code (e.g., "en-US", "fr-FR")
            encoding: Audio encoding format
            sample_rate_hertz: Sample rate in Hz
            enable_automatic_punctuation: Enable automatic punctuation
            enable_word_time_offsets: Enable word timing information

        Returns:
            Recognition response
        """
        # Encode audio content as base64
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

        # Build request body
        config = {
            "encoding": encoding,
            "languageCode": language_code,
            "enableAutomaticPunctuation": enable_automatic_punctuation,
            "enableWordTimeOffsets": enable_word_time_offsets,
        }

        if sample_rate_hertz:
            config["sampleRateHertz"] = sample_rate_hertz

        body = {"config": config, "audio": {"content": audio_base64}}

        return await self.api_client.post(f"{self.base_url}/speech:recognize", json_data=body)

    async def long_running_recognize(
        self,
        audio_content: bytes,
        language_code: str = "en-US",
        encoding: str = "WEBM_OPUS",
        sample_rate_hertz: Optional[int] = None,
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
    ) -> Dict[str, Any]:
        """Start long-running speech recognition.

        Args:
            audio_content: Audio content as bytes
            language_code: Language code (e.g., "en-US", "fr-FR")
            encoding: Audio encoding format
            sample_rate_hertz: Sample rate in Hz
            enable_automatic_punctuation: Enable automatic punctuation
            enable_word_time_offsets: Enable word timing information

        Returns:
            Long-running operation response
        """
        # Encode audio content as base64
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

        # Build request body
        config = {
            "encoding": encoding,
            "languageCode": language_code,
            "enableAutomaticPunctuation": enable_automatic_punctuation,
            "enableWordTimeOffsets": enable_word_time_offsets,
        }

        if sample_rate_hertz:
            config["sampleRateHertz"] = sample_rate_hertz

        body = {"config": config, "audio": {"content": audio_base64}}

        return await self.api_client.post(f"{self.base_url}/speech:longrunningrecognize", json_data=body)

    async def get_operation(self, operation_name: str) -> Dict[str, Any]:
        """Get status of long-running operation.

        Args:
            operation_name: Operation name from long_running_recognize

        Returns:
            Operation status response
        """
        # Operation name includes the full path
        return await self.api_client.get(f"/v1/{operation_name}")
