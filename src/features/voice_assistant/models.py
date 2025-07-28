#!/usr/bin/env python3
"""
Voice Assistant Models

This module defines the data models and enums used throughout the voice assistant feature.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class CommandType(Enum):
    """Types of voice commands supported by the assistant."""
    WEATHER_CURRENT = "weather_current"
    WEATHER_FORECAST = "weather_forecast"
    WEATHER_HISTORY = "weather_history"
    LOCATION_SET = "location_set"
    JOURNAL_CREATE = "journal_create"
    JOURNAL_READ = "journal_read"
    ACTIVITY_SUGGEST = "activity_suggest"
    HELP = "help"
    UNKNOWN = "unknown"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    STATUS = "status"
    SETTINGS = "settings"


class ResponseType(Enum):
    """Types of voice assistant responses."""
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    CONFIRMATION = "confirmation"
    QUESTION = "question"
    GREETING = "greeting"
    HELP = "help"
    WEATHER = "weather"
    SUGGESTION = "suggestion"


class VoiceState(Enum):
    """Current state of the voice assistant."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class VoiceCommand:
    """Represents a voice command from the user."""
    raw_text: str
    command_type: CommandType
    confidence: float
    parameters: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def location(self) -> Optional[str]:
        """Extract location parameter if present."""
        return self.parameters.get('location')
    
    @property
    def time_period(self) -> Optional[str]:
        """Extract time period parameter if present."""
        return self.parameters.get('time_period')
    
    @property
    def is_valid(self) -> bool:
        """Check if the command is valid and processable."""
        return (
            self.confidence > 0.3 and
            self.command_type != CommandType.UNKNOWN and
            len(self.raw_text.strip()) > 0
        )


@dataclass
class VoiceResponse:
    """Represents a response from the voice assistant."""
    text: str
    response_type: ResponseType
    data: Optional[Dict[str, Any]] = None
    should_speak: bool = True
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error response."""
        return self.response_type == ResponseType.ERROR
    
    @property
    def has_data(self) -> bool:
        """Check if response contains additional data."""
        return self.data is not None and len(self.data) > 0


@dataclass
class VoiceSettings:
    """Voice assistant configuration settings."""
    enabled: bool = True
    speech_rate: float = 200  # Words per minute
    speech_volume: float = 0.8  # 0.0 to 1.0
    voice_id: Optional[str] = None  # System voice ID
    language: str = "en-US"
    wake_word_enabled: bool = False
    wake_word: str = "Hey Cortana"
    auto_listen: bool = False
    response_delay: float = 0.5  # Seconds before speaking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for storage."""
        return {
            'enabled': self.enabled,
            'speech_rate': self.speech_rate,
            'speech_volume': self.speech_volume,
            'voice_id': self.voice_id,
            'language': self.language,
            'wake_word_enabled': self.wake_word_enabled,
            'wake_word': self.wake_word,
            'auto_listen': self.auto_listen,
            'response_delay': self.response_delay
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceSettings':
        """Create settings from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            speech_rate=data.get('speech_rate', 200),
            speech_volume=data.get('speech_volume', 0.8),
            voice_id=data.get('voice_id'),
            language=data.get('language', 'en-US'),
            wake_word_enabled=data.get('wake_word_enabled', False),
            wake_word=data.get('wake_word', 'Hey Cortana'),
            auto_listen=data.get('auto_listen', False),
            response_delay=data.get('response_delay', 0.5)
        )


@dataclass
class CommandHistoryEntry:
    """Represents a single command-response pair in the voice assistant history."""
    command: VoiceCommand
    response: VoiceResponse
    execution_time: float  # Seconds
    success: bool
    
    @property
    def formatted_timestamp(self) -> str:
        """Get formatted timestamp for display."""
        return self.command.timestamp.strftime("%H:%M:%S")
    
    @property
    def summary(self) -> str:
        """Get a summary of the command and response."""
        return f"{self.command.command_type.value}: {self.command.raw_text[:50]}..."


class CommandHistory:
    """Manages the history of voice commands and responses."""
    
    def __init__(self, max_entries: int = 100):
        self.entries: List[CommandHistoryEntry] = []
        self.max_entries = max_entries
        self._pending_command: Optional[VoiceCommand] = None
    
    def add_command(self, command: VoiceCommand) -> None:
        """Add a command to the history (pending response)."""
        self._pending_command = command
    
    def add_response(self, response: VoiceResponse) -> None:
        """Add a response to the most recent command."""
        if self._pending_command:
            entry = CommandHistoryEntry(
                command=self._pending_command,
                response=response,
                execution_time=0.0,  # Could be calculated if needed
                success=response.response_type != ResponseType.ERROR
            )
            self.entries.append(entry)
            
            # Limit history size
            if len(self.entries) > self.max_entries:
                self.entries.pop(0)
            
            self._pending_command = None
    
    def get_last_command(self) -> Optional[VoiceCommand]:
        """Get the most recent command."""
        if self.entries:
            return self.entries[-1].command
        return None
    
    def get_last_response(self) -> Optional[VoiceResponse]:
        """Get the most recent response."""
        if self.entries:
            return self.entries[-1].response
        return None
    
    def clear(self) -> None:
        """Clear all history."""
        self.entries.clear()
        self._pending_command = None
    
    def __len__(self) -> int:
        """Return the number of completed command-response pairs."""
        return len(self.entries)
    
    def __getitem__(self, index: int) -> CommandHistoryEntry:
        """Get a history entry by index."""
        return self.entries[index]


# Command patterns for natural language processing
COMMAND_PATTERNS = {
    CommandType.WEATHER_CURRENT: [
        r"what.*weather.*like",
        r"current.*weather",
        r"weather.*now",
        r"how.*weather",
        r"temperature.*now",
        r"weather.*today"
    ],
    CommandType.WEATHER_FORECAST: [
        r"weather.*tomorrow",
        r"forecast",
        r"weather.*next.*days?",
        r"weather.*this.*week",
        r"will.*rain",
        r"weather.*later"
    ],
    CommandType.LOCATION_SET: [
        r"set.*location",
        r"change.*city",
        r"weather.*in.*",
        r"location.*to.*",
        r"switch.*to.*"
    ],
    CommandType.JOURNAL_CREATE: [
        r"create.*entry",
        r"new.*journal",
        r"write.*journal",
        r"add.*entry",
        r"journal.*entry"
    ],
    CommandType.ACTIVITY_SUGGEST: [
        r"suggest.*activity",
        r"what.*should.*do",
        r"activity.*recommendation",
        r"things.*to.*do",
        r"recommend.*activity"
    ],
    CommandType.HELP: [
        r"help",
        r"what.*can.*do",
        r"commands",
        r"how.*use",
        r"instructions"
    ],
    CommandType.GREETING: [
        r"hello",
        r"hi",
        r"hey",
        r"good.*morning",
        r"good.*afternoon",
        r"good.*evening"
    ],
    CommandType.GOODBYE: [
        r"goodbye",
        r"bye",
        r"see.*you",
        r"talk.*later",
        r"exit",
        r"quit"
    ]
}

# Response templates
RESPONSE_TEMPLATES = {
    ResponseType.GREETING: [
        "Hello! I'm Cortana, your weather assistant. How can I help you today?",
        "Hi there! Ready to check the weather or explore other features?",
        "Good to see you! What would you like to know about the weather?"
    ],
    ResponseType.HELP: [
        "I can help you with weather information, create journal entries, suggest activities, and more. Try saying 'What's the weather like?' or 'Suggest an activity'.",
        "Here are some things you can ask me: Check current weather, get forecasts, create journal entries, or get activity suggestions.",
        "I'm here to help with weather and more! You can ask about current conditions, forecasts, or say 'suggest an activity'."
    ],
    ResponseType.ERROR: [
        "I'm sorry, I didn't understand that. Could you try rephrasing?",
        "I'm having trouble with that request. Can you try again?",
        "Sorry, something went wrong. Please try a different command."
    ],
    ResponseType.CONFIRMATION: [
        "Got it!",
        "Done!",
        "Understood!",
        "Perfect!"
    ]
}