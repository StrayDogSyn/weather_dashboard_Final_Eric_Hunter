# Weather Dashboard API Guide

## Overview

This guide covers the internal APIs and external integrations used by the Weather
Dashboard application. The application integrates with multiple weather services
and provides a unified interface for weather data access.

## External API Integrations

### OpenWeatherMap API

#### Configuration

```python
# Environment variables
OPENWEATHER_API_KEY=your_api_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5
```

#### WeatherAPI Endpoints

##### WeatherAPI Current Weather

```http
GET /weather?q={city}&appid={API_key}&units=metric
```

##### 5-Day Forecast

```http
GET /forecast?q={city}&appid={API_key}&units=metric
```

##### Weather by Coordinates

```http
GET /weather?lat={lat}&lon={lon}&appid={API_key}&units=metric
```

#### Response Format

```json
{
  "coord": {"lon": -0.13, "lat": 51.51},
  "weather": [{
    "id": 300,
    "main": "Drizzle",
    "description": "light intensity drizzle",
    "icon": "09d"
  }],
  "main": {
    "temp": 280.32,
    "pressure": 1012,
    "humidity": 81,
    "temp_min": 279.15,
    "temp_max": 281.15
  },
  "name": "London"
}
```

### WeatherAPI.com

#### WeatherAPI Configuration

```python
# Environment variables
WEATHERAPI_KEY=your_api_key_here
WEATHERAPI_BASE_URL=https://api.weatherapi.com/v1
```

#### Endpoints Used

##### Current Weather

```http
GET /current.json?key={API_key}&q={city}&aqi=yes
```

##### Forecast

```http
GET /forecast.json?key={API_key}&q={city}&days=7&aqi=yes&alerts=yes
```

##### Historical Weather

```http
GET /history.json?key={API_key}&q={city}&dt={date}
```

### Google Maps API

#### Google Maps Configuration

```python
# Environment variables
GOOGLE_MAPS_API_KEY=your_api_key_here
```

#### Services Used

##### Geocoding

```http
GET https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_key}
```

##### Places API

```http
GET https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_key}
```

## Internal API Structure

### Weather Service Interface

```python
class IWeatherService(ABC):
    @abstractmethod
    async def get_current_weather(self, location: str) -> WeatherData:
        """Get current weather for a location."""
        pass
    
    @abstractmethod
    async def get_forecast(self, location: str, days: int = 5) -> List[ForecastData]:
        """Get weather forecast for a location."""
        pass
    
    @abstractmethod
    async def get_historical_weather(self, location: str, date: datetime) -> WeatherData:
        """Get historical weather data."""
        pass
```

### Configuration Service Interface

```python
class IConfigurationService(ABC):
    @abstractmethod
    def get_api_key(self, service: str) -> str:
        """Get API key for a service."""
        pass
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting."""
        pass
    
    @abstractmethod
    def update_setting(self, key: str, value: Any) -> None:
        """Update application setting."""
        pass
```

### Repository Interface

```python
class IWeatherRepository(ABC):
    @abstractmethod
    async def save_weather_data(self, data: WeatherData) -> None:
        """Save weather data to storage."""
        pass
    
    @abstractmethod
    async def get_cached_weather(self, location: str, max_age: timedelta) -> Optional[WeatherData]:
        """Get cached weather data if available and fresh."""
        pass
    
    @abstractmethod
    async def get_weather_history(self, location: str, start_date: datetime,
                                   end_date: datetime) -> List[WeatherData]:
        """Get historical weather data from storage."""
        pass
```

## Data Models

### WeatherData

```python
@dataclass
class WeatherData:
    location: str
    temperature: float
    humidity: int
    pressure: float
    description: str
    icon: str
    wind_speed: float
    wind_direction: int
    visibility: float
    uv_index: float
    timestamp: datetime
    feels_like: float
    dew_point: float
    cloud_cover: int
```

### ForecastData

```python
@dataclass
class ForecastData:
    date: datetime
    temperature_high: float
    temperature_low: float
    description: str
    icon: str
    precipitation_chance: int
    precipitation_amount: float
    wind_speed: float
    wind_direction: int
    humidity: int
```

### JournalEntry

```python
@dataclass
class JournalEntry:
    id: Optional[int]
    date: datetime
    location: str
    weather_data: WeatherData
    mood: str
    activities: List[str]
    notes: str
    photos: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
```

## Error Handling

### Custom Exceptions

```python
class WeatherAPIError(Exception):
    """Base exception for weather API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class RateLimitError(WeatherAPIError):
    """Raised when API rate limit is exceeded."""
    pass

class InvalidLocationError(WeatherAPIError):
    """Raised when location is not found."""
    pass

class APIKeyError(WeatherAPIError):
    """Raised when API key is invalid or missing."""
    pass
```

### Error Response Format

```python
@dataclass
class APIErrorResponse:
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

## Caching Strategy

### Cache Configuration

```python
CACHE_SETTINGS = {
    'current_weather': timedelta(minutes=10),
    'forecast': timedelta(hours=1),
    'historical': timedelta(days=1),
    'geocoding': timedelta(days=7),
    'max_cache_size': 1000,
    'cleanup_interval': timedelta(hours=1)
}
```

### Cache Implementation

```python
class WeatherCache:
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            return entry.value
        return None
    
    async def set(self, key: str, value: Any, ttl: timedelta) -> None:
        """Set cached value with TTL."""
        if len(self._cache) >= self._max_size:
            await self._evict_oldest()
        
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=datetime.now() + ttl
        )
```

## Rate Limiting

### Rate Limit Configuration

```python
RATE_LIMITS = {
    'openweathermap': {
        'requests_per_minute': 60,
        'requests_per_day': 1000
    },
    'weatherapi': {
        'requests_per_minute': 100,
        'requests_per_day': 1000000
    },
    'google_maps': {
        'requests_per_second': 50,
        'requests_per_day': 100000
    }
}
```

### Rate Limiter Implementation

```python
class RateLimiter:
    def __init__(self, max_requests: int, time_window: timedelta):
        self._max_requests = max_requests
        self._time_window = time_window
        self._requests: List[datetime] = []
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request."""
        now = datetime.now()
        cutoff = now - self._time_window
        
        # Remove old requests
        self._requests = [req for req in self._requests if req > cutoff]
        
        if len(self._requests) < self._max_requests:
            self._requests.append(now)
            return True
        
        return False
```

## Authentication

### API Key Management

```python
class APIKeyManager:
    def __init__(self, config_service: IConfigurationService):
        self._config = config_service
        self._keys: Dict[str, str] = {}
    
    def get_key(self, service: str) -> str:
        """Get API key for service."""
        if service not in self._keys:
            key = self._config.get_api_key(service)
            if not key:
                raise APIKeyError(f"No API key found for {service}")
            self._keys[service] = key
        
        return self._keys[service]
    
    def rotate_key(self, service: str, new_key: str) -> None:
        """Rotate API key for service."""
        self._keys[service] = new_key
        self._config.update_setting(f"{service}_api_key", new_key)
```

## Testing

### Mock Services

```python
class MockWeatherService(IWeatherService):
    async def get_current_weather(self, location: str) -> WeatherData:
        return WeatherData(
            location=location,
            temperature=20.0,
            humidity=65,
            pressure=1013.25,
            description="Clear sky",
            icon="01d",
            wind_speed=5.0,
            wind_direction=180,
            visibility=10.0,
            uv_index=3.0,
            timestamp=datetime.now(),
            feels_like=22.0,
            dew_point=12.0,
            cloud_cover=0
        )
```

### Test Utilities

```python
class APITestHelper:
    @staticmethod
    def create_mock_response(data: Dict[str, Any], status_code: int = 200) -> Mock:
        """Create mock HTTP response."""
        response = Mock()
        response.status_code = status_code
        response.json.return_value = data
        return response
    
    @staticmethod
    def assert_weather_data_valid(weather_data: WeatherData) -> None:
        """Assert weather data is valid."""
        assert weather_data.location
        assert -100 <= weather_data.temperature <= 100
        assert 0 <= weather_data.humidity <= 100
        assert weather_data.pressure > 0
```

## Performance Optimization

### Async Operations

```python
class AsyncWeatherService:
    async def get_multiple_locations(self, locations: List[str]) -> List[WeatherData]:
        """Get weather for multiple locations concurrently."""
        tasks = [self.get_current_weather(loc) for loc in locations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        weather_data = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error getting weather: {result}")
            else:
                weather_data.append(result)
        
        return weather_data
```

### Connection Pooling

```python
class HTTPClient:
    def __init__(self, max_connections: int = 100):
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        self._session = aiohttp.ClientSession(connector=connector)
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request with connection pooling."""
        return await self._session.get(url, **kwargs)
```

## Monitoring and Logging

### API Metrics

```python
@dataclass
class APIMetrics:
    service: str
    endpoint: str
    response_time: float
    status_code: int
    timestamp: datetime
    cache_hit: bool = False
```

### Logging Configuration

```python
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/weather_dashboard.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        }
    },
    'loggers': {
        'weather_dashboard': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

## Security Considerations

### Input Validation

```python
def validate_location(location: str) -> str:
    """Validate and sanitize location input."""
    if not location or len(location.strip()) == 0:
        raise ValidationError("Location cannot be empty")
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[^\w\s,-]', '', location.strip())
    
    if len(sanitized) > 100:
        raise ValidationError("Location name too long")
    
    return sanitized
```

### API Key Security

```python
class SecureAPIKeyStorage:
    def __init__(self, encryption_key: bytes):
        self._cipher = Fernet(encryption_key)
    
    def store_key(self, service: str, api_key: str) -> None:
        """Store encrypted API key."""
        encrypted_key = self._cipher.encrypt(api_key.encode())
        # Store encrypted_key securely
    
    def retrieve_key(self, service: str) -> str:
        """Retrieve and decrypt API key."""
        encrypted_key = self._get_stored_key(service)
        return self._cipher.decrypt(encrypted_key).decode()
```

This API guide provides comprehensive documentation for integrating with and
extending the Weather Dashboard's API functionality.
