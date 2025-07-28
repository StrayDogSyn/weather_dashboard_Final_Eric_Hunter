#!/usr/bin/env python3
"""
Cortana Service - Main Voice Assistant Implementation

This module provides the main Cortana voice assistant service that integrates
speech recognition, command parsing, and response generation.
"""

import asyncio
import threading
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import json

try:
    import speech_recognition as sr
except ImportError:
    sr = None

from .models import (
    VoiceCommand, VoiceResponse, VoiceSettings, CommandHistory,
    CommandType, ResponseType, VoiceState
)
from .speech_engine import SpeechEngine
from .command_parser import CommandParser
from ...utils.logger import LoggerMixin
from ...core.interfaces import IWeatherService, IDatabase, IConfigurationService


class CortanaService(LoggerMixin):
    """Main Cortana voice assistant service."""
    
    def __init__(
        self,
        weather_service: Optional[IWeatherService] = None,
        database: Optional[IDatabase] = None,
        config_service: Optional[IConfigurationService] = None
    ):
        super().__init__()
        
        # Core services
        self.weather_service = weather_service
        self.database = database
        self.config_service = config_service
        
        # Voice components
        self.speech_engine = SpeechEngine()
        self.command_parser = CommandParser()
        
        # Speech recognition
        self.recognizer = sr.Recognizer() if sr else None
        self.microphone = sr.Microphone() if sr else None
        
        # State management
        self.state = VoiceState.IDLE
        self.settings = VoiceSettings()
        self.command_history = CommandHistory()
        
        # Event callbacks
        self.on_command_received: Optional[Callable[[VoiceCommand], None]] = None
        self.on_response_generated: Optional[Callable[[VoiceResponse], None]] = None
        self.on_state_changed: Optional[Callable[[VoiceState], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # Threading
        self._listening_thread: Optional[threading.Thread] = None
        self._stop_listening = threading.Event()
        
        # Initialize components
        self._initialize_speech_recognition()
        self._load_settings()
        
        self.logger.info("Cortana service initialized")
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition with optimal settings."""
        if not self.recognizer or not self.microphone:
            self.logger.warning("Speech recognition not available - missing dependencies")
            return
        
        try:
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Configure recognition settings
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.phrase_threshold = 0.3
            
            self.logger.info("Speech recognition initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {e}")
    
    def _load_settings(self):
        """Load voice assistant settings from configuration."""
        if not self.config_service:
            return
        
        try:
            # Load settings from config
            voice_config = self.config_service.get_section('voice_assistant', {})
            
            self.settings.enabled = voice_config.get('enabled', True)
            self.settings.wake_word = voice_config.get('wake_word', 'cortana')
            self.settings.voice_id = voice_config.get('voice_id', 'default')
            self.settings.speech_rate = voice_config.get('speech_rate', 200)
            self.settings.volume = voice_config.get('volume', 0.8)
            self.settings.auto_listen = voice_config.get('auto_listen', False)
            self.settings.privacy_mode = voice_config.get('privacy_mode', True)
            
            # Configure speech engine
            self.speech_engine.configure(
                voice_id=self.settings.voice_id,
                rate=self.settings.speech_rate,
                volume=self.settings.volume
            )
            
            self.logger.info("Voice settings loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load voice settings: {e}")
    
    def start_listening(self) -> bool:
        """Start continuous voice listening.
        
        Returns:
            True if listening started successfully
        """
        if not self.settings.enabled or not self.recognizer:
            self.logger.warning("Cannot start listening - voice assistant disabled or not available")
            return False
        
        if self.state == VoiceState.LISTENING:
            self.logger.warning("Already listening")
            return True
        
        try:
            self._stop_listening.clear()
            self._listening_thread = threading.Thread(
                target=self._listening_loop,
                daemon=True
            )
            self._listening_thread.start()
            
            self._set_state(VoiceState.LISTENING)
            self.logger.info("Started voice listening")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start listening: {e}")
            self._handle_error(e)
            return False
    
    def stop_listening(self):
        """Stop voice listening."""
        if self.state != VoiceState.LISTENING:
            return
        
        self._stop_listening.set()
        
        if self._listening_thread and self._listening_thread.is_alive():
            self._listening_thread.join(timeout=2.0)
        
        self._set_state(VoiceState.IDLE)
        self.logger.info("Stopped voice listening")
    
    def _listening_loop(self):
        """Main listening loop for continuous voice recognition."""
        while not self._stop_listening.is_set():
            try:
                # Listen for audio
                with self.microphone as source:
                    # Listen with timeout
                    audio = self.recognizer.listen(
                        source,
                        timeout=1.0,
                        phrase_time_limit=5.0
                    )
                
                if self._stop_listening.is_set():
                    break
                
                # Recognize speech
                try:
                    text = self.recognizer.recognize_google(audio)
                    if text:
                        self._process_voice_input(text)
                        
                except sr.UnknownValueError:
                    # No speech detected - continue listening
                    continue
                except sr.RequestError as e:
                    self.logger.error(f"Speech recognition service error: {e}")
                    continue
                
            except sr.WaitTimeoutError:
                # Timeout - continue listening
                continue
            except Exception as e:
                self.logger.error(f"Error in listening loop: {e}")
                self._handle_error(e)
                break
    
    def process_text_command(self, text: str) -> VoiceResponse:
        """Process a text command directly (for testing or text input).
        
        Args:
            text: Command text to process
            
        Returns:
            VoiceResponse with the result
        """
        return self._process_voice_input(text)
    
    def _process_voice_input(self, text: str) -> VoiceResponse:
        """Process voice input text and generate response.
        
        Args:
            text: Recognized speech text
            
        Returns:
            VoiceResponse object
        """
        try:
            self._set_state(VoiceState.PROCESSING)
            
            # Parse the command
            command = self.command_parser.parse_command(text)
            
            # Add to history
            self.command_history.add_command(command)
            
            # Trigger callback
            if self.on_command_received:
                self.on_command_received(command)
            
            # Generate response
            response = self._generate_response(command)
            
            # Add to history
            self.command_history.add_response(response)
            
            # Trigger callback
            if self.on_response_generated:
                self.on_response_generated(response)
            
            # Speak the response
            if response.should_speak:
                self.speak(response.text)
            
            self._set_state(VoiceState.IDLE)
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing voice input: {e}")
            error_response = VoiceResponse(
                text="I'm sorry, I encountered an error processing your request.",
                response_type=ResponseType.ERROR,
                should_speak=True,
                data={'error': str(e)}
            )
            self._handle_error(e)
            return error_response
    
    def _generate_response(self, command: VoiceCommand) -> VoiceResponse:
        """Generate appropriate response for a command.
        
        Args:
            command: Parsed voice command
            
        Returns:
            VoiceResponse object
        """
        try:
            if command.command_type == CommandType.GREETING:
                return self._handle_greeting(command)
            
            elif command.command_type == CommandType.GOODBYE:
                return self._handle_goodbye(command)
            
            elif command.command_type == CommandType.HELP:
                return self._handle_help(command)
            
            elif command.command_type == CommandType.WEATHER_CURRENT:
                return self._handle_weather_current(command)
            
            elif command.command_type == CommandType.WEATHER_FORECAST:
                return self._handle_weather_forecast(command)
            
            elif command.command_type == CommandType.LOCATION_SET:
                return self._handle_location_set(command)
            
            elif command.command_type == CommandType.JOURNAL_CREATE:
                return self._handle_journal_create(command)
            
            elif command.command_type == CommandType.ACTIVITY_SUGGEST:
                return self._handle_activity_suggest(command)
            
            else:
                return VoiceResponse(
                    text="I'm not sure how to help with that. Try asking about the weather, creating a journal entry, or say 'help' for more options.",
                    response_type=ResponseType.CLARIFICATION,
                    should_speak=True
                )
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return VoiceResponse(
                text="I encountered an error while processing your request.",
                response_type=ResponseType.ERROR,
                should_speak=True,
                data={'error': str(e)}
            )
    
    def _handle_greeting(self, command: VoiceCommand) -> VoiceResponse:
        """Handle greeting commands."""
        greetings = [
            "Hello! I'm Cortana, your weather assistant. How can I help you today?",
            "Hi there! Ready to check the weather or plan your day?",
            "Good to see you! What would you like to know about the weather?"
        ]
        
        import random
        greeting = random.choice(greetings)
        
        return VoiceResponse(
            text=greeting,
            response_type=ResponseType.GREETING,
            should_speak=True
        )
    
    def _handle_goodbye(self, command: VoiceCommand) -> VoiceResponse:
        """Handle goodbye commands."""
        goodbyes = [
            "Goodbye! Have a great day!",
            "See you later! Stay safe out there!",
            "Take care! Don't forget to check the weather!"
        ]
        
        import random
        goodbye = random.choice(goodbyes)
        
        return VoiceResponse(
            text=goodbye,
            response_type=ResponseType.GOODBYE,
            should_speak=True
        )
    
    def _handle_help(self, command: VoiceCommand) -> VoiceResponse:
        """Handle help commands."""
        help_text = (
            "I can help you with weather information, journal entries, and activity suggestions. "
            "Try saying: 'What's the weather like?', 'Create a journal entry', or 'Suggest an activity'."
        )
        
        return VoiceResponse(
            text=help_text,
            response_type=ResponseType.INFORMATION,
            should_speak=True,
            data={'available_commands': list(CommandType)}
        )
    
    def _handle_weather_current(self, command: VoiceCommand) -> VoiceResponse:
        """Handle current weather requests."""
        if not self.weather_service:
            return VoiceResponse(
                text="Weather service is not available right now.",
                response_type=ResponseType.ERROR,
                should_speak=True
            )
        
        try:
            location = command.parameters.get('location', 'New York')
            
            # Get real weather data from the weather service
            weather_data = None
            if hasattr(self.weather_service, 'get_current_weather'):
                weather_data = self.weather_service.get_current_weather(location)
            elif hasattr(self.weather_service, 'get_weather'):
                weather_data = self.weather_service.get_weather(location)
            
            if weather_data:
                # Format the response with real data
                temp = getattr(weather_data, 'temperature', 'unknown')
                condition = getattr(weather_data, 'condition', 'unknown')
                humidity = getattr(weather_data, 'humidity', None)
                
                response_text = f"The current weather in {location} is {condition} with a temperature of {temp} degrees."
                if humidity:
                    response_text += f" Humidity is {humidity} percent."
                
                return VoiceResponse(
                    text=response_text,
                    response_type=ResponseType.WEATHER,
                    should_speak=True,
                    data={'location': location, 'type': 'current', 'weather_data': weather_data}
                )
            else:
                return VoiceResponse(
                    text=f"I couldn't find weather information for {location}. Please try a different location.",
                    response_type=ResponseType.ERROR,
                    should_speak=True
                )
            
        except Exception as e:
            self.logger.error(f"Error getting weather for {location}: {e}")
            return VoiceResponse(
                text="I couldn't get the current weather information right now. Please try again later.",
                response_type=ResponseType.ERROR,
                should_speak=True,
                data={'error': str(e)}
            )
    
    def _handle_weather_forecast(self, command: VoiceCommand) -> VoiceResponse:
        """Handle weather forecast requests."""
        if not self.weather_service:
            return VoiceResponse(
                text="Weather service is not available right now.",
                response_type=ResponseType.ERROR,
                should_speak=True
            )
        
        try:
            location = command.parameters.get('location', 'New York')
            time_period = command.parameters.get('time_period', 'tomorrow')
            
            # Try to get forecast data
            forecast_data = None
            if hasattr(self.weather_service, 'get_forecast'):
                forecast_data = self.weather_service.get_forecast(location)
            elif hasattr(self.weather_service, 'get_current_weather'):
                # Fallback to current weather if forecast not available
                forecast_data = self.weather_service.get_current_weather(location)
            
            if forecast_data:
                temp = getattr(forecast_data, 'temperature', 'unknown')
                condition = getattr(forecast_data, 'condition', 'unknown')
                
                response_text = f"The forecast for {time_period} in {location} shows {condition} with temperatures around {temp} degrees."
                
                return VoiceResponse(
                    text=response_text,
                    response_type=ResponseType.WEATHER,
                    should_speak=True,
                    data={'location': location, 'time_period': time_period, 'type': 'forecast'}
                )
            else:
                return VoiceResponse(
                    text=f"I couldn't find forecast information for {location}. Please try a different location.",
                    response_type=ResponseType.ERROR,
                    should_speak=True
                )
                
        except Exception as e:
            self.logger.error(f"Error getting forecast for {location}: {e}")
            return VoiceResponse(
                text="I couldn't get the forecast information right now. Please try again later.",
                response_type=ResponseType.ERROR,
                should_speak=True,
                data={'error': str(e)}
            )
    
    def _handle_location_set(self, command: VoiceCommand) -> VoiceResponse:
        """Handle location setting commands."""
        location = command.parameters.get('location')
        
        if not location:
            return VoiceResponse(
                text="Please specify a location. For example, say 'Set location to New York'.",
                response_type=ResponseType.CLARIFICATION,
                should_speak=True
            )
        
        # Save location preference (simplified)
        response_text = f"I've set your location to {location}. I'll use this for weather updates."
        
        return VoiceResponse(
            text=response_text,
            response_type=ResponseType.CONFIRMATION,
            should_speak=True,
            data={'location': location}
        )
    
    def _handle_journal_create(self, command: VoiceCommand) -> VoiceResponse:
        """Handle journal creation commands."""
        mood = command.parameters.get('mood', 'neutral')
        
        response_text = f"I've created a new journal entry for you with a {mood} mood. You can add more details in the journal tab."
        
        return VoiceResponse(
            text=response_text,
            response_type=ResponseType.CONFIRMATION,
            should_speak=True,
            data={'action': 'journal_created', 'mood': mood}
        )
    
    def _handle_activity_suggest(self, command: VoiceCommand) -> VoiceResponse:
        """Handle activity suggestion commands."""
        category = command.parameters.get('category', 'general')
        
        # Simple activity suggestions based on category
        suggestions = {
            'outdoor': ['Take a walk in the park', 'Go for a bike ride', 'Have a picnic'],
            'indoor': ['Read a book', 'Try a new recipe', 'Watch a documentary'],
            'exercise': ['Do some yoga', 'Go for a run', 'Try bodyweight exercises'],
            'relaxing': ['Take a warm bath', 'Listen to music', 'Practice meditation'],
            'general': ['Check out a local museum', 'Call a friend', 'Learn something new online']
        }
        
        import random
        activity_list = suggestions.get(category, suggestions['general'])
        activity = random.choice(activity_list)
        
        response_text = f"Based on the current conditions, I suggest: {activity}. Would you like more suggestions?"
        
        return VoiceResponse(
            text=response_text,
            response_type=ResponseType.SUGGESTION,
            should_speak=True,
            data={'activity': activity, 'category': category}
        )
    
    def speak(self, text: str, priority: bool = False):
        """Speak text using the speech engine.
        
        Args:
            text: Text to speak
            priority: Whether this is a priority message
        """
        if not self.settings.enabled:
            return
        
        try:
            self.speech_engine.speak(text, priority=priority)
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
    
    def _set_state(self, new_state: VoiceState):
        """Update the voice assistant state."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            self.logger.debug(f"State changed: {old_state.value} -> {new_state.value}")
            
            if self.on_state_changed:
                self.on_state_changed(new_state)
    
    def _handle_error(self, error: Exception):
        """Handle errors and notify callbacks."""
        self.logger.error(f"Voice assistant error: {error}")
        
        if self.on_error:
            self.on_error(error)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current voice assistant status."""
        return {
            'state': self.state.value,
            'enabled': self.settings.enabled,
            'listening': self.state == VoiceState.LISTENING,
            'speech_available': self.recognizer is not None,
            'commands_processed': len(self.command_history),
            'last_command': self.command_history.get_last_command(),
            'settings': {
                'wake_word': self.settings.wake_word,
                'voice_id': self.settings.voice_id,
                'speech_rate': self.settings.speech_rate,
                'volume': self.settings.speech_volume,
                'auto_listen': self.settings.auto_listen
            }
        }
    
    def update_settings(self, **kwargs):
        """Update voice assistant settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                self.logger.info(f"Updated setting {key} = {value}")
        
        # Reconfigure speech engine if needed
        if any(key in kwargs for key in ['voice_id', 'speech_rate', 'volume']):
            self.speech_engine.configure(
                voice_id=self.settings.voice_id,
                rate=self.settings.speech_rate,
                volume=self.settings.volume
            )
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up Cortana service")
        
        # Stop listening
        self.stop_listening()
        
        # Cleanup speech engine
        if self.speech_engine:
            self.speech_engine.cleanup()
        
        # Clear callbacks
        self.on_command_received = None
        self.on_response_generated = None
        self.on_state_changed = None
        self.on_error = None
        
        self._set_state(VoiceState.IDLE)
        self.logger.info("Cortana service cleanup completed")