"""Data Transfer Objects Package

This package contains DTOs for different aspects of the weather application:
- weather_dto: API response mapping and weather data structures
- ui_dto: User interface data structures and display formatting
- export_dto: Data export formats and structures
"""

# Weather DTOs
from .weather_dto import (
    WeatherProvider,
    CoordinatesDTO,
    LocationDTO,
    WeatherConditionDTO,
    TemperatureDTO,
    WindDTO,
    AtmosphericDTO,
    PrecipitationDTO,
    SunTimesDTO,
    CurrentWeatherDTO,
    HourlyForecastDTO,
    DailyForecastDTO,
    ForecastDTO,
    WeatherAlertDTO,
    WeatherResponseDTO,
    WeatherRequestDTO
)

# UI DTOs
from .ui_dto import (
    DisplayMode,
    AlertLevel,
    IconDTO,
    ColorSchemeDTO,
    FormattedValueDTO,
    CurrentWeatherDisplayDTO,
    ForecastItemDisplayDTO,
    ForecastDisplayDTO,
    WeatherAlertDisplayDTO,
    LocationDisplayDTO,
    ChartDataDTO,
    NotificationDTO,
    DashboardLayoutDTO,
    WeatherDashboardDTO
)

# Export DTOs
from .export_dto import (
    ExportFormat,
    ExportScope,
    ExportMetadataDTO,
    WeatherExportRecordDTO,
    ForecastExportRecordDTO,
    AlertExportRecordDTO,
    WeatherExportDTO,
    ExportRequestDTO,
    ExportResponseDTO
)

__all__ = [
    # Weather DTOs
    "WeatherProvider",
    "CoordinatesDTO",
    "LocationDTO",
    "WeatherConditionDTO",
    "TemperatureDTO",
    "WindDTO",
    "AtmosphericDTO",
    "PrecipitationDTO",
    "SunTimesDTO",
    "CurrentWeatherDTO",
    "HourlyForecastDTO",
    "DailyForecastDTO",
    "ForecastDTO",
    "WeatherAlertDTO",
    "WeatherResponseDTO",
    "WeatherRequestDTO",
    
    # UI DTOs
    "DisplayMode",
    "AlertLevel",
    "IconDTO",
    "ColorSchemeDTO",
    "FormattedValueDTO",
    "CurrentWeatherDisplayDTO",
    "ForecastItemDisplayDTO",
    "ForecastDisplayDTO",
    "WeatherAlertDisplayDTO",
    "LocationDisplayDTO",
    "ChartDataDTO",
    "NotificationDTO",
    "DashboardLayoutDTO",
    "WeatherDashboardDTO",
    
    # Export DTOs
    "ExportFormat",
    "ExportScope",
    "ExportMetadataDTO",
    "WeatherExportRecordDTO",
    "ForecastExportRecordDTO",
    "AlertExportRecordDTO",
    "WeatherExportDTO",
    "ExportRequestDTO",
    "ExportResponseDTO"
]