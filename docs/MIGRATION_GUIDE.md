# Model Organization Migration Guide

This guide explains the changes made to reorganize the weather dashboard models into a more structured architecture.

## Overview

The original `weather_models.py` file has been split into multiple organized modules to improve maintainability and follow domain-driven design principles.

## New Structure

### Before (Old Structure)
```
src/models/
├── __init__.py
└── weather_models.py  # All models in one file
```

### After (New Structure)
```
src/models/
├── __init__.py
├── weather/
│   ├── __init__.py
│   ├── current_weather.py    # WeatherData, WeatherCondition
│   ├── forecast_models.py    # ForecastData, ForecastEntry, DailyForecast
│   └── alert_models.py       # WeatherAlert, AlertSeverity, AlertType
├── location/
│   ├── __init__.py
│   └── location_models.py    # Location, LocationResult, LocationSearchQuery
└── user/
    ├── __init__.py
    └── preference_models.py  # UserPreferences, UnitPreferences, etc.
```

## New Data Access Layer

### Repositories
```
src/data/
├── __init__.py
├── repositories/
│   ├── __init__.py
│   ├── base_repository.py      # Abstract base repository
│   ├── weather_repository.py   # Weather data access
│   ├── preference_repository.py # User preferences
│   └── activity_repository.py  # Activity recommendations
├── unit_of_work.py            # Unit of Work pattern
└── database_context.py        # Database connection management
```

### DTOs (Data Transfer Objects)
```
src/dto/
├── __init__.py
├── weather_dto.py    # API request/response DTOs
├── ui_dto.py         # UI display DTOs
└── export_dto.py     # Data export DTOs
```

## Import Changes

### Weather Models
```python
# Old imports
from src.models.weather_models import WeatherData, WeatherCondition, ForecastData

# New imports
from src.models.weather import WeatherData, WeatherCondition, ForecastData
# Or more specific:
from src.models.weather.current_weather import WeatherData, WeatherCondition
from src.models.weather.forecast_models import ForecastData
```

### Location Models
```python
# Old imports
from src.models.weather_models import Location, LocationResult

# New imports
from src.models.location import Location, LocationResult
# Or more specific:
from src.models.location.location_models import Location, LocationResult
```

### User Preferences
```python
# New imports (previously not available)
from src.models.user import UserPreferences, TemperatureUnit, WindSpeedUnit
from src.models.user.preference_models import UnitPreferences, NotificationPreferences
```

## Key Benefits

1. **Separation of Concerns**: Each module has a single responsibility
2. **Better Organization**: Related models are grouped together
3. **Improved Maintainability**: Easier to find and modify specific functionality
4. **Enhanced Testability**: Smaller, focused modules are easier to test
5. **Repository Pattern**: Proper data access abstraction
6. **Unit of Work**: Transaction management and consistency
7. **DTOs**: Clear separation between domain models and data transfer

## New Features Added

### Enhanced Weather Models
- `WeatherAlert` with severity levels and types
- `AlertSeverity` enum with color coding
- Enhanced `Location` with distance calculations
- `LocationSearchQuery` for structured searches

### User Preferences
- Comprehensive unit preferences (temperature, wind, pressure, distance)
- Notification preferences with customizable settings
- Display preferences for themes and layouts
- Preference history and change tracking

### Data Access Layer
- Abstract `BaseRepository` with common CRUD operations
- Specialized repositories for different data types
- `UnitOfWork` for transaction management
- `DatabaseContext` for connection management
- In-memory implementations for testing

### DTOs for Different Contexts
- `WeatherDTO` for API communication
- `UIDisplayDTO` for user interface rendering
- `ExportDTO` for data export functionality

## Migration Steps

1. **Update Imports**: Change all imports from `weather_models` to the new structure
2. **Review Dependencies**: Check for any missing imports or circular dependencies
3. **Test Functionality**: Ensure all existing functionality still works
4. **Leverage New Features**: Consider using the new repository pattern and DTOs
5. **Update Documentation**: Update any documentation that references the old structure

## Backward Compatibility

The main `src/models/__init__.py` file still exports all the original classes, so existing code using:
```python
from src.models import WeatherData, Location, etc.
```
will continue to work without changes.

## Files Updated

The following files were automatically updated to use the new import structure:
- `src/ui/components/search_components.py`
- `src/services/enhanced_weather_service.py`
- `src/services/activity_service.py`
- `src/ui/professional_weather_dashboard.py`
- `src/services/geocoding_service.py`

## Next Steps

1. Consider implementing the repository pattern in services
2. Use DTOs for API communication
3. Implement user preferences in the UI
4. Add comprehensive unit tests for new modules
5. Consider adding validation and business rules to domain models