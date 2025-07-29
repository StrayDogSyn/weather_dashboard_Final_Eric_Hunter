"""Weather Service Interface

Defines the contract for weather service implementations,
enabling dependency injection and loose coupling.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from models.weather_models import WeatherData, ForecastData


class IWeatherService(ABC):
    """Abstract interface for weather services."""
    
    @abstractmethod
    async def get_current_weather(self, city: str) -> Optional[WeatherData]:
        """Get current weather data for a city.
        
        Args:
            city: City name to get weather for
            
        Returns:
            WeatherData object or None if not found
        """
        pass
    
    @abstractmethod
    async def get_forecast(self, city: str, days: int = 5) -> Optional[List[ForecastData]]:
        """Get weather forecast for a city.
        
        Args:
            city: City name to get forecast for
            days: Number of days to forecast
            
        Returns:
            List of ForecastData objects or None if not found
        """
        pass
    
    @abstractmethod
    async def search_cities(self, query: str) -> List[Dict[str, Any]]:
        """Search for cities matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of city dictionaries with name, country, etc.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the weather service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass


class IDataProcessor(ABC):
    """Abstract interface for data processors."""
    
    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Any:
        """Process raw data into a structured format.
        
        Args:
            raw_data: Raw data dictionary from API
            
        Returns:
            Processed data object
        """
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate processed data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass


class IDataParser(ABC):
    """Abstract interface for API response parsers."""
    
    @abstractmethod
    def parse(self, response: Dict[str, Any]) -> Any:
        """Parse API response into structured data.
        
        Args:
            response: Raw API response dictionary
            
        Returns:
            Parsed data object
        """
        pass
    
    @abstractmethod
    def can_parse(self, response: Dict[str, Any]) -> bool:
        """Check if this parser can handle the response.
        
        Args:
            response: API response to check
            
        Returns:
            True if parser can handle response, False otherwise
        """
        pass