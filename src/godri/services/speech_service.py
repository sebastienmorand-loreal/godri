"""Google Speech-to-Text service wrapper."""

import logging
import os
from typing import Dict, Any, List, Optional
from google.cloud import speech
from .auth_service import AuthService
from ..utils.language_mapper import LanguageMapper


class SpeechService:
    """Google Speech-to-Text operations."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.project_id = "oa-data-btdpexploration-np"  # Use exploration project

    async def initialize(self):
        """Initialize the Speech service using local credentials with quota project."""
        # Use local credentials with explicit quota project configuration
        try:
            import google.auth

            # Get default credentials
            credentials, project = google.auth.default()

            # Create credentials with quota project
            if hasattr(credentials, "with_quota_project"):
                credentials_with_quota = credentials.with_quota_project(self.project_id)
            else:
                credentials_with_quota = credentials

            # Set the project explicitly for Speech API billing
            os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id

            # Initialize client with credentials that include quota project
            self.client = speech.SpeechClient(credentials=credentials_with_quota)
            self.logger.info("Speech service initialized with local credentials and quota project: %s", self.project_id)
        except Exception as e:
            self.logger.error("Failed to initialize Speech service with local credentials: %s", str(e))
            self.logger.info("Attempting fallback to service account credentials...")
            # Fallback to service account credentials if available
            await self.auth_service.authenticate()
            self.client = speech.SpeechClient(credentials=self.auth_service.credentials)
            self.logger.info("Speech service initialized with service account credentials")

    def transcribe_audio_file(
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
        # Normalize language code using LanguageMapper
        try:
            normalized_language_code = LanguageMapper.normalize_language_code(language_code)
            self.logger.info("Language code '%s' normalized to '%s'", language_code, normalized_language_code)
        except ValueError as e:
            self.logger.error("Invalid language code: %s", str(e))
            suggestions = LanguageMapper.suggest_similar_languages(language_code)
            raise ValueError(f"Invalid language code '{language_code}'. Suggestions: {', '.join(suggestions)}")

        if normalized_language_code == "auto":
            self.logger.info("Transcribing audio file: %s with automatic language detection", audio_file_path)
        else:
            self.logger.info("Transcribing audio file: %s with language: %s", audio_file_path, normalized_language_code)

        # Read audio file
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()

        # Determine audio encoding from file extension
        file_extension = audio_file_path.lower().split(".")[-1]
        encoding_map = {
            "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
            "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "opus": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
            "m4a": speech.RecognitionConfig.AudioEncoding.MP3,
        }

        audio_encoding = encoding_map.get(file_extension, speech.RecognitionConfig.AudioEncoding.LINEAR16)

        # Use detected sample rate if not provided
        if not sample_rate_hertz and audio_properties:
            if file_extension == "opus" and "adjusted_sample_rate" in audio_properties:
                sample_rate_hertz = audio_properties["adjusted_sample_rate"]
            elif "sample_rate" in audio_properties:
                sample_rate_hertz = audio_properties["sample_rate"]

        # Prepare audio and config
        audio = speech.RecognitionAudio(content=content)

        # Configure recognition settings
        config_params = {
            "encoding": audio_encoding,
            "enable_automatic_punctuation": enable_automatic_punctuation,
            "enable_word_time_offsets": enable_word_time_offsets,
        }

        # Add sample rate if available
        if sample_rate_hertz:
            config_params["sample_rate_hertz"] = sample_rate_hertz

        # Handle language detection
        if normalized_language_code == "auto":
            # For auto-detection, use the most common language as primary and add alternatives
            config_params["language_code"] = "en-US"  # Primary language for auto-detection
            config_params["alternative_language_codes"] = [
                "fr-FR",
                "es-ES",
                "de-DE",
                "it-IT",
                "pt-BR",
                "zh-CN",
                "ja-JP",
                "ar-SA",
            ]
            self.logger.info("Using automatic language detection with primary language en-US and alternatives")
        else:
            config_params["language_code"] = normalized_language_code

        config = speech.RecognitionConfig(**config_params)

        # Perform the transcription
        response = self.client.recognize(config=config, audio=audio)

        # Process results
        transcripts = []
        detected_language = None
        for result in response.results:
            alternative = result.alternatives[0]

            transcript_data = {
                "transcript": alternative.transcript,
                "confidence": alternative.confidence,
            }

            # Capture detected language for auto-detection
            if hasattr(result, "language_code") and result.language_code:
                detected_language = result.language_code

            # Add word timing if requested
            if enable_word_time_offsets and alternative.words:
                words = []
                for word_info in alternative.words:
                    word_data = {
                        "word": word_info.word,
                        "start_time": word_info.start_time.total_seconds(),
                        "end_time": word_info.end_time.total_seconds(),
                    }
                    words.append(word_data)
                transcript_data["words"] = words

            transcripts.append(transcript_data)

        self.logger.info("Transcription completed. Found %d results", len(transcripts))

        # Use detected language if available, otherwise use normalized_language_code
        final_language = (
            detected_language if detected_language and normalized_language_code == "auto" else normalized_language_code
        )

        return {
            "transcripts": transcripts,
            "language_code": final_language,
            "detected_language": detected_language if normalized_language_code == "auto" else None,
            "original_language_input": language_code,
            "audio_file": audio_file_path,
            "encoding": audio_encoding.name,
            "total_results": len(transcripts),
        }

    def transcribe_audio_long(
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
        # Normalize language code using LanguageMapper
        try:
            normalized_language_code = LanguageMapper.normalize_language_code(language_code)
            self.logger.info("Language code '%s' normalized to '%s'", language_code, normalized_language_code)
        except ValueError as e:
            self.logger.error("Invalid language code: %s", str(e))
            suggestions = LanguageMapper.suggest_similar_languages(language_code)
            raise ValueError(f"Invalid language code '{language_code}'. Suggestions: {', '.join(suggestions)}")

        self.logger.info(
            "Starting long-running transcription for: %s with language: %s", audio_file_path, normalized_language_code
        )

        # Read audio file
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()

        # Determine audio encoding
        file_extension = audio_file_path.lower().split(".")[-1]
        encoding_map = {
            "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
            "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "opus": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
        }

        audio_encoding = encoding_map.get(file_extension, speech.RecognitionConfig.AudioEncoding.LINEAR16)

        # Use detected sample rate if not provided
        if not sample_rate_hertz and audio_properties:
            if file_extension == "opus" and "adjusted_sample_rate" in audio_properties:
                sample_rate_hertz = audio_properties["adjusted_sample_rate"]
            elif "sample_rate" in audio_properties:
                sample_rate_hertz = audio_properties["sample_rate"]

        # Prepare audio and config
        audio = speech.RecognitionAudio(content=content)

        config = speech.RecognitionConfig(
            encoding=audio_encoding,
            sample_rate_hertz=sample_rate_hertz,
            language_code=normalized_language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            enable_word_time_offsets=enable_word_time_offsets,
        )

        # Start long-running operation
        operation = self.client.long_running_recognize(config=config, audio=audio)

        self.logger.info("Waiting for operation to complete...")
        response = operation.result(timeout=300)  # 5 minute timeout

        # Process results (same as regular transcription)
        transcripts = []
        for result in response.results:
            alternative = result.alternatives[0]

            transcript_data = {
                "transcript": alternative.transcript,
                "confidence": alternative.confidence,
            }

            # Add word timing if requested
            if enable_word_time_offsets and alternative.words:
                words = []
                for word_info in alternative.words:
                    word_data = {
                        "word": word_info.word,
                        "start_time": word_info.start_time.total_seconds(),
                        "end_time": word_info.end_time.total_seconds(),
                    }
                    words.append(word_data)
                transcript_data["words"] = words

            transcripts.append(transcript_data)

        self.logger.info("Long-running transcription completed. Found %d results", len(transcripts))

        return {
            "transcripts": transcripts,
            "language_code": normalized_language_code,
            "original_language_input": language_code,
            "audio_file": audio_file_path,
            "encoding": audio_encoding.name,
            "total_results": len(transcripts),
            "operation_type": "long_running",
        }

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported language codes for speech recognition.

        Returns:
            List of dictionaries with language codes and names
        """
        # Common language codes supported by Google Speech-to-Text
        languages = [
            {"code": "en-US", "name": "English (United States)"},
            {"code": "en-GB", "name": "English (United Kingdom)"},
            {"code": "fr-FR", "name": "French (France)"},
            {"code": "es-ES", "name": "Spanish (Spain)"},
            {"code": "de-DE", "name": "German (Germany)"},
            {"code": "it-IT", "name": "Italian (Italy)"},
            {"code": "ja-JP", "name": "Japanese (Japan)"},
            {"code": "ko-KR", "name": "Korean (South Korea)"},
            {"code": "zh-CN", "name": "Chinese (Simplified)"},
            {"code": "pt-BR", "name": "Portuguese (Brazil)"},
            {"code": "ru-RU", "name": "Russian (Russia)"},
            {"code": "ar-SA", "name": "Arabic (Saudi Arabia)"},
            {"code": "hi-IN", "name": "Hindi (India)"},
            {"code": "nl-NL", "name": "Dutch (Netherlands)"},
            {"code": "sv-SE", "name": "Swedish (Sweden)"},
            {"code": "da-DK", "name": "Danish (Denmark)"},
            {"code": "no-NO", "name": "Norwegian (Norway)"},
            {"code": "fi-FI", "name": "Finnish (Finland)"},
            {"code": "pl-PL", "name": "Polish (Poland)"},
            {"code": "tr-TR", "name": "Turkish (Turkey)"},
        ]

        return languages

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
