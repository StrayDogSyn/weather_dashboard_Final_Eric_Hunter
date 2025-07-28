#!/usr/bin/env python3
"""
Voice Assistant Package - Cortana Integration

This package provides voice assistant functionality with:
- Speech recognition for voice commands
- Text-to-speech for responses
- Natural language processing for weather queries
- Privacy-focused on-device processing
- Integration with weather services and other features

Package Structure:
- models.py: Data structures and enums (VoiceCommand, CommandType, VoiceResponse)
- speech_engine.py: Text-to-speech implementation
- command_parser.py: Natural language processing for commands
- cortana_service.py: Main voice assistant service
- voice_widget.py: UI widget for voice interaction
- voice_controller.py: Business logic and command handling
- utils.py: Utility functions for voice processing

Usage:
    from .voice_assistant import create_voice_assistant
    
    voice_assistant = create_voice_assistant(parent, weather_service, database_manager)
    voice_assistant.pack(fill="both", expand=True)
"""

# Import main components for easy access
from .models import VoiceCommand, CommandType, VoiceResponse
from .cortana_service import CortanaService
# from .voice_widget import VoiceAssistantWidget, create_voice_assistant  # Not implemented yet
# from .voice_controller import VoiceController  # Not implemented yet
from .speech_engine import SpeechEngine
from .command_parser import CommandParser
from .utils import (
    parse_weather_query,
    format_weather_response,
    extract_location_from_text,
    validate_voice_command,
    sanitize_speech_text
)

# Main export - the factory function for creating the voice assistant widget
__all__ = [
    # Main factory function
    'create_voice_assistant',
    
    # Core components
    'VoiceAssistantWidget',
    'CortanaService',
    'VoiceController',
    'SpeechEngine',
    'CommandParser',
    
    # Data models
    'VoiceCommand',
    'CommandType',
    'VoiceResponse',
    
    # Utility functions
    'parse_weather_query',
    'format_weather_response',
    'extract_location_from_text',
    'validate_voice_command',
    'sanitize_speech_text'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Weather Dashboard Team'
__description__ = 'Voice Assistant with Cortana-like functionality for weather queries'