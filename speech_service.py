import os
import json
import base64
import logging
from google.cloud import speech
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Speech-to-Text client"""
        try:
            # Try to get credentials from environment variable
            credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
            
            if credentials_json:
                # Parse JSON credentials
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                self.client = speech.SpeechClient(credentials=credentials)
                logger.info("Google Cloud Speech client initialized with service account")
            else:
                # Fall back to default credentials (for local development)
                try:
                    self.client = speech.SpeechClient()
                    logger.info("Google Cloud Speech client initialized with default credentials")
                except Exception as e:
                    logger.warning(f"Could not initialize Google Cloud Speech client: {str(e)}")
                    self.client = None
                    
        except Exception as e:
            logger.error(f"Failed to initialize speech client: {str(e)}")
            self.client = None
    
    def transcribe_audio(self, audio_data, language_code='en-US'):
        """
        Transcribe audio data using Google Cloud Speech-to-Text
        
        Args:
            audio_data: Base64 encoded audio data
            language_code: Language code for transcription
            
        Returns:
            dict: Transcription result with transcript, confidence, and is_final
        """
        if not self.client:
            logger.error("Speech client not initialized")
            return None
        
        try:
            # Decode base64 audio data
            audio_content = base64.b64decode(audio_data)
            
            # Configure recognition
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model='latest_long',
            )
            
            # Perform recognition
            response = self.client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                
                return {
                    'transcript': alternative.transcript,
                    'confidence': alternative.confidence,
                    'is_final': True
                }
            else:
                logger.warning("No transcription results")
                return None
                
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return None
    
    def transcribe_streaming(self, audio_stream, language_code='en-US'):
        """
        Perform streaming speech recognition
        
        Args:
            audio_stream: Stream of audio data
            language_code: Language code for transcription
            
        Yields:
            dict: Streaming transcription results
        """
        if not self.client:
            logger.error("Speech client not initialized")
            return
        
        try:
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True,
            )
            
            responses = self.client.streaming_recognize(streaming_config, audio_stream)
            
            for response in responses:
                for result in response.results:
                    alternative = result.alternatives[0]
                    yield {
                        'transcript': alternative.transcript,
                        'confidence': alternative.confidence if hasattr(alternative, 'confidence') else 0.0,
                        'is_final': result.is_final
                    }
                    
        except Exception as e:
            logger.error(f"Streaming transcription error: {str(e)}")
    
    def get_supported_languages(self):
        """Get list of supported languages for speech recognition"""
        return {
            'en-US': 'English (US)',
            'hi-IN': 'Hindi (India)',
            'bn-IN': 'Bengali (India)',
            'te-IN': 'Telugu (India)',
            'ta-IN': 'Tamil (India)',
            'gu-IN': 'Gujarati (India)',
            'kn-IN': 'Kannada (India)',
            'ml-IN': 'Malayalam (India)',
            'mr-IN': 'Marathi (India)',
            'pa-IN': 'Punjabi (India)'
        }
