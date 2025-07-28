#!/usr/bin/env python3
"""
Command Parser - Natural Language Processing for Voice Commands

This module handles parsing and understanding of natural language voice commands
using pattern matching and keyword extraction.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .models import VoiceCommand, CommandType, COMMAND_PATTERNS
from ...utils.logger import LoggerMixin


class CommandParser(LoggerMixin):
    """Natural language processor for voice commands."""
    
    def __init__(self):
        super().__init__()
        self.location_keywords = [
            'in', 'at', 'for', 'from', 'near', 'around', 'by'
        ]
        self.time_keywords = {
            'now': 'current',
            'today': 'today',
            'tomorrow': 'tomorrow',
            'tonight': 'tonight',
            'this week': 'week',
            'next week': 'next_week',
            'weekend': 'weekend',
            'morning': 'morning',
            'afternoon': 'afternoon',
            'evening': 'evening'
        }
        
        # Compile regex patterns for better performance
        self.compiled_patterns = {}
        for command_type, patterns in COMMAND_PATTERNS.items():
            self.compiled_patterns[command_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def parse_command(self, text: str) -> VoiceCommand:
        """Parse natural language text into a structured command.
        
        Args:
            text: Raw voice input text
            
        Returns:
            VoiceCommand object with parsed information
        """
        if not text or not text.strip():
            return VoiceCommand(
                raw_text=text,
                command_type=CommandType.UNKNOWN,
                confidence=0.0,
                parameters={},
                timestamp=datetime.now()
            )
        
        # Clean and normalize text
        clean_text = self._clean_text(text)
        
        # Determine command type and confidence
        command_type, confidence = self._classify_command(clean_text)
        
        # Extract parameters based on command type
        parameters = self._extract_parameters(clean_text, command_type)
        
        command = VoiceCommand(
            raw_text=text,
            command_type=command_type,
            confidence=confidence,
            parameters=parameters,
            timestamp=datetime.now()
        )
        
        self.logger.debug(f"Parsed command: {command_type.value} (confidence: {confidence:.2f})")
        return command
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove punctuation except apostrophes
        text = re.sub(r"[^\w\s']", ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common contractions
        contractions = {
            "what's": "what is",
            "how's": "how is",
            "where's": "where is",
            "it's": "it is",
            "that's": "that is",
            "i'm": "i am",
            "you're": "you are",
            "we're": "we are",
            "they're": "they are",
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "doesn't": "does not",
            "isn't": "is not",
            "aren't": "are not"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text.strip()
    
    def _classify_command(self, text: str) -> Tuple[CommandType, float]:
        """Classify the command type and calculate confidence.
        
        Returns:
            Tuple of (CommandType, confidence_score)
        """
        best_match = CommandType.UNKNOWN
        best_confidence = 0.0
        
        for command_type, patterns in self.compiled_patterns.items():
            confidence = self._calculate_pattern_confidence(text, patterns)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = command_type
        
        # Apply additional heuristics
        if best_confidence < 0.3:
            # Check for simple greetings
            if any(word in text for word in ['hello', 'hi', 'hey']):
                return CommandType.GREETING, 0.8
            
            # Check for goodbyes
            if any(word in text for word in ['bye', 'goodbye', 'exit', 'quit']):
                return CommandType.GOODBYE, 0.8
            
            # Check for help requests
            if any(word in text for word in ['help', 'commands', 'what can']):
                return CommandType.HELP, 0.7
        
        return best_match, best_confidence
    
    def _calculate_pattern_confidence(self, text: str, patterns: List[re.Pattern]) -> float:
        """Calculate confidence score for a set of patterns."""
        max_confidence = 0.0
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                # Base confidence from match
                confidence = 0.6
                
                # Boost confidence based on match quality
                match_length = len(match.group())
                text_length = len(text)
                coverage = match_length / text_length
                confidence += coverage * 0.3
                
                # Boost for exact matches
                if match.group().strip() == text.strip():
                    confidence += 0.1
                
                max_confidence = max(max_confidence, min(confidence, 1.0))
        
        return max_confidence
    
    def _extract_parameters(self, text: str, command_type: CommandType) -> Dict[str, Any]:
        """Extract parameters based on command type."""
        parameters = {}
        
        # Extract location for weather commands
        if command_type in [CommandType.WEATHER_CURRENT, CommandType.WEATHER_FORECAST, CommandType.LOCATION_SET]:
            location = self._extract_location(text)
            if location:
                parameters['location'] = location
        
        # Extract time period
        time_period = self._extract_time_period(text)
        if time_period:
            parameters['time_period'] = time_period
        
        # Extract specific parameters by command type
        if command_type == CommandType.JOURNAL_CREATE:
            # Extract mood or topic keywords
            mood_keywords = ['happy', 'sad', 'excited', 'calm', 'stressed', 'relaxed']
            for mood in mood_keywords:
                if mood in text:
                    parameters['mood'] = mood
                    break
        
        elif command_type == CommandType.ACTIVITY_SUGGEST:
            # Extract activity preferences
            activity_keywords = {
                'indoor': 'indoor',
                'outdoor': 'outdoor',
                'exercise': 'exercise',
                'relaxing': 'relaxing',
                'social': 'social',
                'creative': 'creative'
            }
            
            for keyword, category in activity_keywords.items():
                if keyword in text:
                    parameters['category'] = category
                    break
        
        return parameters
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text."""
        # Look for location patterns
        location_patterns = [
            r'(?:in|at|for|from|near)\s+([a-zA-Z\s]+?)(?:\s|$)',
            r'weather\s+(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\s|$)',
            r'([a-zA-Z\s]+?)\s+weather',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                
                # Filter out common non-location words
                stop_words = {
                    'the', 'is', 'like', 'today', 'tomorrow', 'now', 'current',
                    'what', 'how', 'when', 'where', 'weather', 'temperature',
                    'forecast', 'conditions', 'outside', 'there'
                }
                
                location_words = [word for word in location.split() 
                                if word.lower() not in stop_words]
                
                if location_words:
                    clean_location = ' '.join(location_words)
                    if len(clean_location) > 1:  # Avoid single characters
                        return clean_location.title()
        
        return None
    
    def _extract_time_period(self, text: str) -> Optional[str]:
        """Extract time period from text."""
        for keyword, period in self.time_keywords.items():
            if keyword in text:
                return period
        
        # Look for specific day patterns
        day_pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
        day_match = re.search(day_pattern, text, re.IGNORECASE)
        if day_match:
            return day_match.group(1).lower()
        
        # Look for date patterns (simple)
        date_patterns = [
            r'\b(\d{1,2})\s*(?:st|nd|rd|th)?\b',  # Day of month
            r'\b(next|this)\s+(week|month)\b',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).lower()
        
        return None
    
    def get_command_suggestions(self, partial_text: str) -> List[str]:
        """Get command suggestions based on partial input."""
        suggestions = []
        
        if not partial_text:
            return [
                "What's the weather like?",
                "Weather forecast for tomorrow",
                "Create a journal entry",
                "Suggest an activity",
                "Help"
            ]
        
        partial_lower = partial_text.lower()
        
        # Weather suggestions
        if any(word in partial_lower for word in ['weather', 'temperature', 'forecast']):
            suggestions.extend([
                "What's the weather like today?",
                "Weather forecast for tomorrow",
                "Current temperature",
                "Weather in [city name]"
            ])
        
        # Journal suggestions
        if any(word in partial_lower for word in ['journal', 'write', 'entry']):
            suggestions.extend([
                "Create a new journal entry",
                "Write about today's weather",
                "Add journal entry"
            ])
        
        # Activity suggestions
        if any(word in partial_lower for word in ['activity', 'suggest', 'do']):
            suggestions.extend([
                "Suggest an activity",
                "What should I do today?",
                "Recommend outdoor activities",
                "Indoor activity suggestions"
            ])
        
        # Help suggestions
        if any(word in partial_lower for word in ['help', 'command', 'can']):
            suggestions.extend([
                "What can you do?",
                "Show available commands",
                "Help with weather"
            ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def validate_command(self, command: VoiceCommand) -> bool:
        """Validate if a command is properly formed and actionable."""
        if not command.is_valid:
            return False
        
        # Additional validation based on command type
        if command.command_type == CommandType.LOCATION_SET:
            return 'location' in command.parameters
        
        elif command.command_type in [CommandType.WEATHER_CURRENT, CommandType.WEATHER_FORECAST]:
            # Weather commands are valid even without location (use default)
            return True
        
        elif command.command_type == CommandType.JOURNAL_CREATE:
            # Journal commands need some content indication
            return len(command.raw_text.split()) > 2
        
        return True
    
    def get_command_help(self, command_type: CommandType) -> str:
        """Get help text for a specific command type."""
        help_texts = {
            CommandType.WEATHER_CURRENT: "Ask about current weather conditions. Example: 'What's the weather like?' or 'Current weather in New York'",
            CommandType.WEATHER_FORECAST: "Get weather forecasts. Example: 'Weather forecast for tomorrow' or 'Will it rain this week?'",
            CommandType.LOCATION_SET: "Change your location. Example: 'Set location to Paris' or 'Weather in Tokyo'",
            CommandType.JOURNAL_CREATE: "Create journal entries. Example: 'Create a journal entry' or 'Write about today'",
            CommandType.ACTIVITY_SUGGEST: "Get activity suggestions. Example: 'Suggest an activity' or 'What should I do today?'",
            CommandType.HELP: "Get help and see available commands. Example: 'Help' or 'What can you do?'",
            CommandType.GREETING: "Say hello to start a conversation. Example: 'Hello' or 'Hi Cortana'",
            CommandType.GOODBYE: "End the conversation. Example: 'Goodbye' or 'See you later'"
        }
        
        return help_texts.get(command_type, "No help available for this command type.")