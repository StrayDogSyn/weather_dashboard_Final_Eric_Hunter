"""Voice Assistant Utilities

Utility functions for the Cortana voice assistant feature.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """Normalize text for processing.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text string
    """
    if not text:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = text.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove special characters except basic punctuation
    normalized = re.sub(r'[^\w\s.,!?-]', '', normalized)
    
    return normalized

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Normalize and split text
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Filter out stop words and short words
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    return keywords

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Extract keywords from both texts
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    return len(intersection) / len(union) if union else 0.0

def format_response(text: str, max_length: int = 200) -> str:
    """Format response text for voice output.
    
    Args:
        text: Response text to format
        max_length: Maximum length of response
        
    Returns:
        Formatted response text
    """
    if not text:
        return "I'm sorry, I don't have a response for that."
    
    # Truncate if too long
    if len(text) > max_length:
        # Try to truncate at sentence boundary
        sentences = text.split('. ')
        result = sentences[0]
        
        for sentence in sentences[1:]:
            if len(result + '. ' + sentence) <= max_length:
                result += '. ' + sentence
            else:
                break
        
        if not result.endswith('.'):
            result += '.'
        
        return result
    
    return text

def validate_audio_input(audio_data: Any) -> bool:
    """Validate audio input data.
    
    Args:
        audio_data: Audio data to validate
        
    Returns:
        True if valid, False otherwise
    """
    if audio_data is None:
        return False
    
    # Basic validation - check if audio_data has expected attributes
    try:
        # This is a basic check - in a real implementation,
        # you'd want more sophisticated audio validation
        return hasattr(audio_data, '__len__') and len(audio_data) > 0
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        return False

def log_voice_interaction(command: str, response: str, success: bool = True) -> None:
    """Log voice interaction for debugging and analytics.
    
    Args:
        command: User command
        response: System response
        success: Whether the interaction was successful
    """
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        'timestamp': timestamp,
        'command': command,
        'response': response,
        'success': success
    }
    
    if success:
        logger.info(f"Voice interaction: {json.dumps(log_entry)}")
    else:
        logger.warning(f"Failed voice interaction: {json.dumps(log_entry)}")

def sanitize_voice_input(text: str) -> str:
    """Sanitize voice input for security.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\'\\\/]', '', text)
    
    # Limit length
    sanitized = sanitized[:500]
    
    return sanitized.strip()

def get_confidence_level(recognition_result: Any) -> float:
    """Get confidence level from speech recognition result.
    
    Args:
        recognition_result: Speech recognition result
        
    Returns:
        Confidence level between 0 and 1
    """
    try:
        # This would depend on the specific speech recognition library
        # For now, return a default confidence
        if hasattr(recognition_result, 'confidence'):
            return float(recognition_result.confidence)
        else:
            return 0.8  # Default confidence
    except Exception as e:
        logger.error(f"Error getting confidence level: {e}")
        return 0.0

def create_error_response(error_type: str, details: str = "") -> Dict[str, Any]:
    """Create standardized error response.
    
    Args:
        error_type: Type of error
        details: Additional error details
        
    Returns:
        Error response dictionary
    """
    return {
        'success': False,
        'error_type': error_type,
        'details': details,
        'timestamp': datetime.now().isoformat(),
        'response': f"I encountered an error: {error_type}. {details}"
    }

def parse_time_expression(text: str) -> Optional[datetime]:
    """Parse time expressions from text.
    
    Args:
        text: Text containing time expression
        
    Returns:
        Parsed datetime object or None
    """
    # Simple time parsing - in a real implementation,
    # you'd want a more sophisticated time parser
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',
        r'(\d{1,2})\s*(am|pm)',
        r'(morning|afternoon|evening|night)'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text.lower())
        if match:
            # This is a simplified implementation
            # In practice, you'd want proper time parsing
            logger.info(f"Found time expression: {match.group()}")
            return datetime.now()  # Placeholder
    
    return None

def parse_weather_query(text: str) -> Dict[str, Any]:
    """Parse weather-related queries from text.
    
    Args:
        text: Input text containing weather query
        
    Returns:
        Dictionary with parsed weather query components
    """
    query_info = {
        'location': None,
        'time_frame': 'current',
        'weather_type': 'general',
        'units': 'metric'
    }
    
    text_lower = text.lower()
    
    # Extract location
    location_patterns = [
        r'in ([a-zA-Z\s]+)',
        r'for ([a-zA-Z\s]+)',
        r'at ([a-zA-Z\s]+)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text_lower)
        if match:
            query_info['location'] = match.group(1).strip()
            break
    
    # Extract time frame
    if any(word in text_lower for word in ['tomorrow', 'next day']):
        query_info['time_frame'] = 'tomorrow'
    elif any(word in text_lower for word in ['today', 'now', 'current']):
        query_info['time_frame'] = 'current'
    elif 'week' in text_lower:
        query_info['time_frame'] = 'week'
    
    # Extract weather type
    if any(word in text_lower for word in ['temperature', 'temp', 'hot', 'cold']):
        query_info['weather_type'] = 'temperature'
    elif any(word in text_lower for word in ['rain', 'precipitation', 'shower']):
        query_info['weather_type'] = 'precipitation'
    elif any(word in text_lower for word in ['wind', 'windy']):
        query_info['weather_type'] = 'wind'
    elif any(word in text_lower for word in ['humidity', 'humid']):
        query_info['weather_type'] = 'humidity'
    
    return query_info

def format_weather_response(weather_data: Dict[str, Any]) -> str:
    """Format weather data into a natural language response.
    
    Args:
        weather_data: Weather data dictionary
        
    Returns:
        Formatted weather response string
    """
    if not weather_data:
        return "I'm sorry, I couldn't retrieve the weather information."
    
    try:
        location = weather_data.get('location', 'your location')
        temperature = weather_data.get('temperature', 'unknown')
        description = weather_data.get('description', 'unknown conditions')
        humidity = weather_data.get('humidity', 'unknown')
        
        response = f"The weather in {location} is currently {description} with a temperature of {temperature} degrees."
        
        if humidity != 'unknown':
            response += f" The humidity is {humidity} percent."
        
        return response
    except Exception as e:
        logger.error(f"Error formatting weather response: {e}")
        return "I encountered an error while formatting the weather information."

def validate_voice_command(command: str) -> bool:
    """Validate voice command input.
    
    Args:
        command: Voice command to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not command or not isinstance(command, str):
        return False
    
    # Check length
    if len(command.strip()) < 2 or len(command) > 500:
        return False
    
    # Check for potentially harmful content
    harmful_patterns = [
        r'<script',
        r'javascript:',
        r'eval\(',
        r'exec\(',
        r'import\s+os',
        r'subprocess'
    ]
    
    command_lower = command.lower()
    for pattern in harmful_patterns:
        if re.search(pattern, command_lower):
            return False
    
    return True

def extract_location_from_text(text: str) -> Optional[str]:
    """Extract location information from text.
    
    Args:
        text: Input text
        
    Returns:
        Extracted location or None
    """
    if not text:
        return None
    
    # Common location indicators
    location_patterns = [
        r'in ([A-Za-z\s,]+?)(?:\s|$|[.!?])',
        r'for ([A-Za-z\s,]+?)(?:\s|$|[.!?])',
        r'at ([A-Za-z\s,]+?)(?:\s|$|[.!?])',
        r'([A-Za-z\s,]+?)\s+weather'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Filter out common non-location words
            if location.lower() not in ['the', 'a', 'an', 'my', 'current', 'local']:
                return location
    
    return None

def sanitize_speech_text(text: str) -> str:
    """Sanitize speech text for processing.
    
    Args:
        text: Speech text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful content
    sanitized = re.sub(r'[<>"\'\\\/]', '', text)
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Limit length for security
    sanitized = sanitized[:1000]
    
    # Remove non-printable characters
    sanitized = ''.join(char for char in sanitized if char.isprintable() or char.isspace())
    
    return sanitized.strip()