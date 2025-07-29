# Cortana Voice Integration

## Core Components

- **VoiceCommandProcessor**: NLU engine with intent classification
- **CortanaVoiceService**: Main voice service interface
- **Bot Framework Patterns**: Conversation context management
- **Azure Speech Integration**: TTS/STT capabilities (placeholder)

## Key Features

- Intent classification with confidence scoring
- Entity extraction (location, time, weather parameters)
- Multi-turn conversation context
- Multiple voice profiles and speech settings
- Performance caching and error handling

## Implementation

### Voice Command Processor
```python
from src.services.voice_command_processor import VoiceCommandProcessor

processor = VoiceCommandProcessor(
    weather_service=weather_service,
    cache_service=cache_service,
    storage_service=storage_service
)

response = await processor.process_command(
    "What's the weather like tomorrow in Seattle?",
    context={"user_location": "Portland"}
)
```

### Cortana Voice Service
```python
from src.services.cortana_voice_service import create_cortana_voice_service

cortana = create_cortana_voice_service(
    weather_service=weather_service,
    cache_service=cache_service,
    storage_service=storage_service
)

response = await cortana.process_voice_command(
    "Get me the forecast for London"
)
```

## Supported Commands

### Weather Queries
- "What's the weather in [city]?"
- "How's the weather today?"
- "What's the temperature in [city]?"

### Forecast Requests
- "Get forecast for [city]"
- "What's the weather like tomorrow?"
- "Show me the 5-day forecast"

### Location Management
- "Set my default location to [city]"
- "Change my location to [city]"

### Help
- "Help" / "What can you do?"

## Configuration

### Voice Profiles
- `en-US_Standard` (default)
- `en-GB_Standard` 
- `en-AU_Standard`
- `en-CA_Standard`

### Speech Settings
- **Rate**: 0.5 - 2.0 (default: 1.0)
- **Volume**: 0.0 - 1.0 (default: 0.8)
- **Pitch**: -1.0 - 1.0 (default: 0.0)

## Intent Classification

```python
class CommandType(Enum):
    CURRENT_WEATHER = "current_weather"
    FORECAST = "forecast"
    SET_LOCATION = "set_location"
    HELP = "help"
    UNKNOWN = "unknown"
```

## Entity Extraction
- **Location**: City names, regions, countries
- **Time**: "today", "tomorrow", "this weekend"
- **Weather**: "temperature", "humidity", "wind"

## Testing

```bash
python test_cortana_integration.py
```

## Performance
- Voice command processing: < 2 seconds
- Weather data retrieval: < 1 second
- Speech synthesis: < 3 seconds

## Future Enhancements
- Azure Speech Services integration
- LUIS integration for advanced NLU
- Multi-language support
- Proactive weather notifications

---

**For additional documentation, see the `docs/` directory.**
