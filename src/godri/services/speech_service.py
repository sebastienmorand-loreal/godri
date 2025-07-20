"""Google Speech-to-Text service wrapper."""

import logging
from typing import Dict, Any, List, Optional
from ..commons.api.google_api_client import GoogleApiClient
from ..commons.api.speech_api import SpeechApiClient
from .auth_service_new import AuthService


class SpeechService:
    """Google Speech-to-Text operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.speech_api = None

    async def initialize(self):
        """Initialize the Speech service using gcloud access token."""
        # Get gcloud access token instead of OAuth2 credentials
        access_token = await self.auth_service.get_gcloud_access_token()
        if not access_token:
            raise ValueError("Failed to get gcloud access token for Google Speech")

        # Create a simple token credentials object
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=access_token)

        api_client = GoogleApiClient(credentials)
        await api_client.initialize()
        self.speech_api = SpeechApiClient(api_client)
        self.logger.info("Speech service initialized with gcloud token")

    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        language_code: str = "auto",
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
        sample_rate_hertz: Optional[int] = None,
        audio_properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transcribe an audio file to text.

        Args:
            audio_file_path: Path to the audio file (MP3, WAV, OPUS)
            language_code: Language code or shortcut (e.g., 'en', 'fr', 'en-US', 'fr-FR', 'french', 'auto')
            enable_automatic_punctuation: Add punctuation to transcription
            enable_word_time_offsets: Include word timing information
            sample_rate_hertz: Sample rate of the audio file (auto-detected if None)

        Returns:
            Dictionary containing transcription results and metadata
        """
        self.logger.info("Transcribing audio file: %s with language: %s", audio_file_path, language_code)

        result = await self.speech_api.transcribe_audio(
            audio_file_path=audio_file_path,
            language_code=language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            enable_word_time_offsets=enable_word_time_offsets,
            sample_rate_hertz=sample_rate_hertz,
            audio_properties=audio_properties,
        )

        self.logger.info("Transcription completed")
        return result

    async def transcribe_audio_long(
        self,
        audio_file_path: str,
        language_code: str = "auto",
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
        sample_rate_hertz: Optional[int] = None,
        audio_properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transcribe long audio files (>1 minute) using long-running operation.

        Args:
            audio_file_path: Path to the audio file
            language_code: Language code or shortcut (e.g., 'en', 'fr', 'en-US', 'fr-FR', 'french')
            enable_automatic_punctuation: Add punctuation to transcription
            enable_word_time_offsets: Include word timing information
            sample_rate_hertz: Sample rate of the audio file (auto-detected if None)

        Returns:
            Dictionary containing transcription results and metadata
        """
        self.logger.info(
            "Starting long-running transcription for: %s with language: %s", audio_file_path, language_code
        )

        result = await self.speech_api.transcribe_audio_long(
            audio_file_path=audio_file_path,
            language_code=language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            enable_word_time_offsets=enable_word_time_offsets,
            sample_rate_hertz=sample_rate_hertz,
            audio_properties=audio_properties,
        )

        self.logger.info("Long-running transcription completed")
        return result

    async def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported language codes for speech recognition.

        Returns:
            List of dictionaries with language codes and names
        """
        return await self.speech_api.get_supported_languages()

    def detect_audio_properties(self, audio_file_path: str) -> Dict[str, Any]:
        """Detect audio file properties for optimal transcription settings.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dictionary with detected audio properties
        """
        import wave
        import os
        from mutagen import File as MutagenFile

        file_extension = audio_file_path.lower().split(".")[-1]
        file_size = os.path.getsize(audio_file_path)

        properties = {
            "file_path": audio_file_path,
            "file_extension": file_extension,
            "file_size_bytes": file_size,
            "recommended_method": "short" if file_size < 10 * 1024 * 1024 else "long",  # 10MB threshold
        }

        # Try to get detailed properties using mutagen for all formats
        try:
            audio_file = MutagenFile(audio_file_path)
            if audio_file is not None:
                # Get common properties
                if hasattr(audio_file, "info"):
                    info = audio_file.info
                    if hasattr(info, "length"):
                        properties["duration_seconds"] = info.length
                    if hasattr(info, "bitrate"):
                        properties["bitrate"] = info.bitrate
                    if hasattr(info, "channels"):
                        properties["channels"] = info.channels

                    # Sample rate detection
                    sample_rate = None
                    if hasattr(info, "sample_rate"):
                        sample_rate = info.sample_rate
                    elif hasattr(info, "samplerate"):
                        sample_rate = info.samplerate

                    if sample_rate:
                        properties["sample_rate"] = sample_rate

                        # For OPUS files, ensure sample rate is supported by Google Speech API
                        if file_extension == "opus":
                            supported_rates = [8000, 12000, 16000, 24000, 48000]
                            if sample_rate not in supported_rates:
                                # Find closest supported rate
                                closest_rate = min(supported_rates, key=lambda x: abs(x - sample_rate))
                                properties["original_sample_rate"] = sample_rate
                                properties["adjusted_sample_rate"] = closest_rate
                                self.logger.info(
                                    "OPUS file sample rate %d not supported, will use %d", sample_rate, closest_rate
                                )
                            else:
                                properties["adjusted_sample_rate"] = sample_rate

                # Special handling for OPUS files when sample rate is not detected
                if file_extension == "opus" and "sample_rate" not in properties:
                    # OPUS files are typically 48kHz, but for speech recognition, 16kHz is often more suitable
                    properties["sample_rate"] = 48000  # Default OPUS sample rate
                    properties["adjusted_sample_rate"] = 16000  # Optimal for speech recognition
                    self.logger.info("OPUS file: using default 48kHz rate, adjusted to 16kHz for speech recognition")

                self.logger.info("Audio properties detected: %s", properties)
        except Exception as e:
            self.logger.warning("Could not read audio properties with mutagen: %s", str(e))

            # Fallback to wave for WAV files
            if file_extension == "wav":
                try:
                    with wave.open(audio_file_path, "rb") as wav_file:
                        properties.update(
                            {
                                "sample_rate": wav_file.getframerate(),
                                "channels": wav_file.getnchannels(),
                                "duration_seconds": wav_file.getnframes() / wav_file.getframerate(),
                                "sample_width": wav_file.getsampwidth(),
                            }
                        )
                except Exception as wav_error:
                    self.logger.warning("Could not read WAV properties: %s", str(wav_error))

        return properties
