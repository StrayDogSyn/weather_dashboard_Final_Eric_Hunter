#!/usr/bin/env python3
"""
Speech Engine - Text-to-Speech Implementation

This module provides text-to-speech functionality for the voice assistant
using pyttsx3 for cross-platform compatibility.
"""

import threading
import time
from typing import Optional, List, Callable
from queue import Queue, Empty

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from .models import VoiceSettings, VoiceResponse
from ...utils.logger import LoggerMixin


class SpeechEngine(LoggerMixin):
    """Text-to-speech engine with queue-based processing."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        super().__init__()
        self.settings = settings or VoiceSettings()
        self.engine: Optional[pyttsx3.Engine] = None
        self.speech_queue = Queue()
        self.is_speaking = False
        self.is_running = False
        self.speech_thread: Optional[threading.Thread] = None
        self.available_voices: List[dict] = []
        
        # Callbacks
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_speech_error: Optional[Callable] = None
        
        self._initialize_engine()
    
    def _initialize_engine(self) -> bool:
        """Initialize the TTS engine."""
        if not pyttsx3:
            self.logger.warning("pyttsx3 not available, speech disabled")
            return False
        
        try:
            self.engine = pyttsx3.init()
            if not self.engine:
                self.logger.error("Failed to initialize TTS engine")
                return False
            
            # Configure engine properties
            self._configure_engine()
            
            # Get available voices
            self._load_available_voices()
            
            # Start speech processing thread
            self._start_speech_thread()
            
            self.logger.info("Speech engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing speech engine: {e}")
            return False
    
    def _configure_engine(self):
        """Configure engine properties based on settings."""
        if not self.engine:
            return
        
        try:
            # Set speech rate
            self.engine.setProperty('rate', self.settings.speech_rate)
            
            # Set volume
            self.engine.setProperty('volume', self.settings.speech_volume)
            
            # Set voice if specified
            if self.settings.voice_id:
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if voice.id == self.settings.voice_id:
                        self.engine.setProperty('voice', voice.id)
                        break
            
            self.logger.debug("Engine configured with current settings")
            
        except Exception as e:
            self.logger.error(f"Error configuring engine: {e}")
    
    def _load_available_voices(self):
        """Load list of available system voices."""
        if not self.engine:
            return
        
        try:
            voices = self.engine.getProperty('voices')
            self.available_voices = []
            
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown')
                }
                self.available_voices.append(voice_info)
            
            self.logger.info(f"Loaded {len(self.available_voices)} available voices")
            
        except Exception as e:
            self.logger.error(f"Error loading voices: {e}")
    
    def _start_speech_thread(self):
        """Start the speech processing thread."""
        if self.speech_thread and self.speech_thread.is_alive():
            return
        
        self.is_running = True
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        self.logger.debug("Speech processing thread started")
    
    def _speech_worker(self):
        """Worker thread for processing speech queue."""
        while self.is_running:
            try:
                # Get next speech item from queue (with timeout)
                speech_item = self.speech_queue.get(timeout=1.0)
                
                if speech_item is None:  # Shutdown signal
                    break
                
                self._speak_text(speech_item)
                self.speech_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in speech worker: {e}")
                if self.on_speech_error:
                    self.on_speech_error(str(e))
    
    def _speak_text(self, text: str):
        """Actually speak the text using the engine."""
        if not self.settings.enabled:
            return

        try:
            self.is_speaking = True
            
            if self.on_speech_start:
                self.on_speech_start()
            
            # Add delay if configured
            if self.settings.response_delay > 0:
                time.sleep(self.settings.response_delay)
            
            # Reinitialize engine for each speech to avoid state issues
            try:
                if self.engine:
                    self.engine.stop()
                self.engine = pyttsx3.init()
                self._configure_engine()
            except Exception as init_error:
                self.logger.warning(f"Engine reinit failed, using existing: {init_error}")
                if not self.engine:
                    return
            
            # Speak the text
            self.engine.say(text)
            self.engine.runAndWait()
            
            self.logger.debug(f"Spoke text: {text[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
            if self.on_speech_error:
                self.on_speech_error(str(e))
        finally:
            self.is_speaking = False
            if self.on_speech_end:
                self.on_speech_end()
    
    def speak(self, text: str, priority: bool = False) -> bool:
        """Queue text for speech synthesis.
        
        Args:
            text: Text to speak
            priority: If True, add to front of queue
            
        Returns:
            True if successfully queued, False otherwise
        """
        if not self.engine or not self.settings.enabled:
            self.logger.debug("Speech engine not available or disabled")
            return False
        
        if not text or not text.strip():
            return False
        
        try:
            # Clean up text for speech
            clean_text = self._clean_text_for_speech(text)
            
            if priority:
                # For priority messages, clear queue and speak immediately
                self._clear_queue()
                self.speech_queue.put(clean_text)
            else:
                self.speech_queue.put(clean_text)
            
            self.logger.debug(f"Queued text for speech: {clean_text[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Error queuing speech: {e}")
            return False
    
    def speak_response(self, response: VoiceResponse) -> bool:
        """Speak a voice response if it should be spoken."""
        if response.should_speak and response.text:
            return self.speak(response.text)
        return False
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis."""
        # Remove or replace problematic characters
        text = text.replace('°', ' degrees')
        text = text.replace('%', ' percent')
        text = text.replace('&', ' and ')
        text = text.replace('@', ' at ')
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _clear_queue(self):
        """Clear the speech queue."""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except Empty:
                break
    
    def stop_speaking(self):
        """Stop current speech and clear queue."""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        
        self._clear_queue()
        self.is_speaking = False
        
        if self.on_speech_end:
            self.on_speech_end()
    
    def update_settings(self, settings: VoiceSettings):
        """Update speech engine settings."""
        self.settings = settings
        self._configure_engine()
        self.logger.info("Speech settings updated")
    
    def get_available_voices(self) -> List[dict]:
        """Get list of available system voices."""
        return self.available_voices.copy()
    
    def set_voice(self, voice_id: str) -> bool:
        """Set the voice by ID."""
        if not self.engine:
            return False
        
        try:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if voice.id == voice_id:
                    self.engine.setProperty('voice', voice.id)
                    self.settings.voice_id = voice_id
                    self.logger.info(f"Voice set to: {voice.name}")
                    return True
            
            self.logger.warning(f"Voice ID not found: {voice_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting voice: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if speech engine is available and working."""
        return self.engine is not None and self.settings.enabled
    
    def get_status(self) -> dict:
        """Get current status of the speech engine."""
        return {
            'available': self.is_available(),
            'speaking': self.is_speaking,
            'queue_size': self.speech_queue.qsize(),
            'enabled': self.settings.enabled,
            'voice_count': len(self.available_voices),
            'current_voice': self.settings.voice_id
        }
    
    def shutdown(self):
        """Shutdown the speech engine and cleanup resources."""
        self.logger.info("Shutting down speech engine")
        
        # Stop speech processing
        self.is_running = False
        self.stop_speaking()
        
        # Signal shutdown to worker thread
        self.speech_queue.put(None)
        
        # Wait for thread to finish
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2.0)
        
        # Cleanup engine
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
            self.engine = None
        
        self.logger.info("Speech engine shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.shutdown()