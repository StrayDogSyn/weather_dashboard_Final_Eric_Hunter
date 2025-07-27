# Activity Suggester Module Structure

This document describes the refactored module structure for the Activity Suggester feature.

## Module Overview

The Activity Suggester has been broken down into focused, maintainable modules:

### Core Modules

- **`models.py`** - Data models and enums (ActivitySuggestion, UserPreferences, etc.)
- **`activity_widget.py`** - Main widget class with layout and UI structure
- **`activity_controller.py`** - Business logic and controller methods
- **`ui_components.py`** - UI component creation methods (cards, dialogs, etc.)
- **`utils.py`** - Utility functions and helper classes

### Service Modules

- **`database.py`** - Database operations and data persistence
- **`ai_service.py`** - AI-powered activity generation
- **`spotify_service.py`** - Spotify integration for music recommendations

## File Sizes

All modules are optimized for maintainability:

- **ui_components.py**: 704 lines - UI creation methods
- **activity_widget.py**: 471 lines - Main widget and layout
- **utils.py**: 415 lines - Utility functions and helpers
- **activity_controller.py**: 310 lines - Business logic

## Module Responsibilities

### ActivitySuggesterWidget (`activity_widget.py`)
- Main widget class inheriting from GlassFrame
- UI layout and structure setup
- Event handling delegation to controller
- Public API methods for external integration

### ActivityController (`activity_controller.py`)
- Suggestion generation logic
- User interaction handling
- State management
- API integration coordination

### ActivityUIComponents (`ui_components.py`)
- Suggestion card creation
- Dialog windows (details, rating, preferences, analytics)
- Export/import UI functionality
- Music recommendation display

### ActivityUtils (`utils.py`)
- Data validation and formatting
- Activity scoring and filtering
- Weather-based recommendations
- Export/import utilities

## Usage

```python
from .activity_suggester import create_activity_suggester

# Create the widget
widget = create_activity_suggester(parent, database_manager)

# Configure API keys
widget.configure_api_keys(
    gemini_api_key="your_key",
    spotify_client_id="your_id",
    spotify_client_secret="your_secret"
)

# Set weather data
widget.set_weather_data({
    'condition': 'sunny',
    'temperature': 22
})
```

## Benefits of This Structure

1. **Modularity**: Each module has a single responsibility
2. **Maintainability**: Smaller files are easier to understand and modify
3. **Testability**: Individual components can be tested in isolation
4. **Reusability**: UI components and utilities can be reused elsewhere
5. **Separation of Concerns**: UI, logic, and data are clearly separated