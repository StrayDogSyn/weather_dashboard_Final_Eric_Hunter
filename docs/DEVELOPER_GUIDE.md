# 👨‍💻 Developer Guide

## Overview

This guide provides comprehensive instructions for developers working on the Weather Dashboard project. The application uses modern Python development practices with dependency injection, clean architecture, and comprehensive testing.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Dependency Injection Usage](#dependency-injection-usage)
4. [Adding New Services](#adding-new-services)
5. [Testing Patterns](#testing-patterns)
6. [Code Standards](#code-standards)
7. [Debugging Guide](#debugging-guide)
8. [Common Development Tasks](#common-development-tasks)
9. [Troubleshooting](#troubleshooting)

## Development Environment Setup

### Prerequisites

- **Python 3.8+** (recommended: Python 3.11)
- **Git** for version control
- **IDE**: VS Code, PyCharm, or similar with Python support
- **API Keys**: OpenWeatherMap, Google Gemini (optional)

### Initial Setup

1. **Clone the Repository**:
```bash
git clone <repository-url>
cd weather_dashboard_Final_Eric_Hunter
```

2. **Create Virtual Environment**:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure Environment Variables**:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# Required:
OPENWEATHER_API_KEY=your_api_key_here

# Optional:
GEMINI_API_KEY=your_gemini_key_here
DEBUG=true
LOG_LEVEL=DEBUG
```

5. **Verify Installation**:
```bash
# Run tests to verify setup
pytest

# Start the application
python main.py
```

### IDE Configuration

#### VS Code Settings

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": [
        "--profile",
        "black"
    ]
}
```

#### PyCharm Configuration

1. Set Python interpreter to `./venv/bin/python`
2. Enable pytest as test runner
3. Configure code style to use Black formatter
4. Enable type checking with mypy

## Project Structure

```
weather_dashboard_Final_Eric_Hunter/
├── src/                          # Source code
│   ├── core/                     # Core application logic
│   │   ├── __init__.py
│   │   ├── app_controller.py     # Application orchestration
│   │   ├── dependency_container.py  # IoC container
│   │   ├── error_handling.py     # Error handling framework
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── interfaces.py         # Service interfaces
│   │   └── service_registry.py   # Service registration
│   ├── services/                 # Service implementations
│   │   ├── __init__.py
│   │   ├── config_service_impl.py
│   │   ├── database_impl.py
│   │   ├── weather_service_impl.py
│   │   └── ...
│   ├── ui/                       # User interface
│   │   ├── __init__.py
│   │   ├── dashboard_main.py     # Main UI controller
│   │   └── components/           # UI components
│   └── utils/                    # Utility functions
├── tests/                        # Test suite
│   ├── test_dependency_injection.py
│   ├── test_error_handling.py
│   └── fixtures/                 # Test data
├── docs/                         # Documentation
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── main.py                       # Application entry point
└── README.md                     # Project overview
```

### Key Directories

- **`src/core/`**: Core application logic, dependency injection, interfaces
- **`src/services/`**: Business logic implementations
- **`src/ui/`**: User interface components and controllers
- **`tests/`**: Comprehensive test suite
- **`docs/`**: Project documentation

## Dependency Injection Usage

### Understanding the Container

The `DependencyContainer` is the heart of the application's architecture:

```python
from src.core.dependency_container import DependencyContainer
from src.core.interfaces import IWeatherService, ServiceLifetime

# Get the global container instance
container = DependencyContainer()

# Register services
container.register_singleton(IWeatherService, WeatherServiceImpl)

# Resolve services
weather_service = container.resolve(IWeatherService)
```

### Service Registration Patterns

#### 1. Singleton Registration
```python
# For stateless services that should be shared
container.register_singleton(IConfigurationService, ConfigurationServiceImpl)
container.register_singleton(ILoggingService, LoggingServiceImpl)
```

#### 2. Transient Registration
```python
# For services that need fresh instances
container.register_transient(IRequestHandler, RequestHandler)
container.register_transient(IDataProcessor, DataProcessor)
```

#### 3. Factory Registration
```python
# For complex service creation
container.register_factory(
    IDatabase,
    lambda: DatabaseImpl(
        connection_string=container.resolve(IConfigurationService).get("database_url"),
        logger=container.resolve(ILoggingService)
    ),
    ServiceLifetime.SINGLETON
)
```

### Service Resolution

```python
# Basic resolution
service = container.resolve(IServiceInterface)

# Check if service is registered
if container.is_registered(IServiceInterface):
    service = container.resolve(IServiceInterface)

# Handle resolution errors
try:
    service = container.resolve(IServiceInterface)
except ServiceResolutionError as e:
    logger.error(f"Failed to resolve service: {e}")
```

### Constructor Injection

```python
class WeatherServiceImpl(IWeatherService):
    def __init__(self, 
                 config_service: IConfigurationService,
                 cache_service: ICacheService,
                 logger_service: ILoggingService):
        """Constructor injection - dependencies provided by container."""
        self._config = config_service
        self._cache = cache_service
        self._logger = logger_service
        
        # Initialize service
        self._api_key = self._config.get("openweather_api_key")
        self._base_url = self._config.get("openweather_base_url")
```

## Adding New Services

### Step 1: Define the Interface

```python
# src/core/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional

class INewService(ABC):
    """Interface for new service functionality."""
    
    @abstractmethod
    def process_data(self, input_data: str) -> str:
        """Process input data and return result."""
        pass
    
    @abstractmethod
    def get_status(self) -> bool:
        """Get service status."""
        pass
```

### Step 2: Implement the Service

```python
# src/services/new_service_impl.py
from src.core.interfaces import INewService, ILoggingService, IConfigurationService
from src.core.exceptions import ServiceError

class NewServiceImpl(INewService):
    """Implementation of new service."""
    
    def __init__(self, 
                 config_service: IConfigurationService,
                 logger_service: ILoggingService):
        self._config = config_service
        self._logger = logger_service
        self._is_initialized = False
        
        self._initialize()
    
    def _initialize(self):
        """Initialize service with configuration."""
        try:
            # Load configuration
            self._setting = self._config.get("new_service_setting", "default")
            self._is_initialized = True
            self._logger.info("NewService initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize NewService: {e}")
            raise ServiceError(f"NewService initialization failed: {e}")
    
    def process_data(self, input_data: str) -> str:
        """Process input data and return result."""
        if not self._is_initialized:
            raise ServiceError("Service not initialized")
        
        try:
            # Process data
            result = f"Processed: {input_data} with setting: {self._setting}"
            self._logger.debug(f"Processed data: {input_data}")
            return result
        except Exception as e:
            self._logger.error(f"Data processing failed: {e}")
            raise ServiceError(f"Data processing failed: {e}")
    
    def get_status(self) -> bool:
        """Get service status."""
        return self._is_initialized
```

### Step 3: Register the Service

```python
# src/core/service_registry.py
def configure_services(self, container: DependencyContainer):
    """Configure all services in the container."""
    
    # Existing services...
    
    # Register new service
    container.register_factory(
        INewService,
        lambda: NewServiceImpl(
            config_service=container.resolve(IConfigurationService),
            logger_service=container.resolve(ILoggingService)
        ),
        ServiceLifetime.SINGLETON
    )
```

### Step 4: Create Tests

```python
# tests/test_new_service.py
import pytest
from unittest.mock import Mock
from src.services.new_service_impl import NewServiceImpl
from src.core.exceptions import ServiceError

class TestNewService:
    def setUp(self):
        self.mock_config = Mock()
        self.mock_logger = Mock()
        self.mock_config.get.return_value = "test_setting"
        
        self.service = NewServiceImpl(
            config_service=self.mock_config,
            logger_service=self.mock_logger
        )
    
    def test_process_data_success(self):
        # Arrange
        input_data = "test input"
        
        # Act
        result = self.service.process_data(input_data)
        
        # Assert
        assert "Processed: test input" in result
        assert "test_setting" in result
    
    def test_get_status_returns_true_when_initialized(self):
        # Act
        status = self.service.get_status()
        
        # Assert
        assert status is True
```

### Step 5: Update Service Exports

```python
# src/services/__init__.py
from .new_service_impl import NewServiceImpl

__all__ = [
    'NewServiceImpl',
    # ... other services
]
```

## Testing Patterns

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch
from src.services.weather_service_impl import WeatherServiceImpl
from src.core.exceptions import ExternalServiceError

class TestWeatherService:
    def setUp(self):
        self.mock_config = Mock()
        self.mock_cache = Mock()
        self.mock_logger = Mock()
        
        # Configure mocks
        self.mock_config.get.side_effect = lambda key, default=None: {
            "openweather_api_key": "test_key",
            "openweather_base_url": "https://api.test.com"
        }.get(key, default)
        
        self.service = WeatherServiceImpl(
            config_service=self.mock_config,
            cache_service=self.mock_cache,
            logger_service=self.mock_logger
        )
    
    @patch('requests.get')
    def test_get_current_weather_success(self, mock_get):
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "main": {"temp": 20.5, "humidity": 65},
            "weather": [{"description": "clear sky"}],
            "name": "London"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Act
        result = self.service.get_current_weather("London")
        
        # Assert
        assert result.location == "London"
        assert result.temperature == 20.5
        assert result.description == "clear sky"
```

### Integration Testing

```python
class TestServiceIntegration:
    def setUp(self):
        self.container = DependencyContainer()
        self.registry = ServiceRegistry()
        self.registry.configure_development_services(use_mock_external=True)
        self.registry.register_services(self.container)
    
    def test_weather_service_with_real_dependencies(self):
        # Act
        weather_service = self.container.resolve(IWeatherService)
        result = weather_service.get_current_weather("London")
        
        # Assert
        assert result is not None
        assert result.location == "London"
```

### Mock Service Testing

```python
class TestWithMockServices:
    def setUp(self):
        self.container = DependencyContainer()
        
        # Register mock services
        self.mock_weather = MockWeatherService(Mock())
        self.container.register_instance(IWeatherService, self.mock_weather)
    
    def test_error_handling_with_mock(self):
        # Arrange
        self.mock_weather.set_should_fail(True)
        
        # Act & Assert
        with pytest.raises(ExternalServiceError):
            self.mock_weather.get_current_weather("London")
```

## Code Standards

### Python Style Guide

- **PEP 8**: Follow Python style guidelines
- **Black**: Use Black formatter for consistent formatting
- **Type Hints**: Use type hints for all public methods
- **Docstrings**: Document all classes and public methods

### Naming Conventions

```python
# Classes: PascalCase
class WeatherServiceImpl(IWeatherService):
    pass

# Methods and variables: snake_case
def get_current_weather(self, location: str) -> WeatherDataDTO:
    api_key = self._config.get("api_key")
    return weather_data

# Constants: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3

# Private methods: _snake_case
def _validate_location(self, location: str) -> bool:
    return len(location.strip()) > 0
```

### Documentation Standards

```python
class WeatherServiceImpl(IWeatherService):
    """Implementation of weather service using OpenWeatherMap API.
    
    This service provides current weather data and forecasts with
    caching and error handling capabilities.
    
    Attributes:
        _config: Configuration service for API settings
        _cache: Cache service for storing weather data
        _logger: Logging service for operation tracking
    """
    
    def get_current_weather(self, location: str) -> WeatherDataDTO:
        """Get current weather data for specified location.
        
        Args:
            location: City name or coordinates (e.g., "London" or "51.5074,-0.1278")
            
        Returns:
            WeatherDataDTO containing current weather information
            
        Raises:
            ValidationError: If location is invalid
            ExternalServiceError: If weather API is unavailable
            NetworkError: If network request fails
        """
        pass
```

### Error Handling Standards

```python
def get_weather_data(self, location: str) -> WeatherDataDTO:
    """Get weather data with comprehensive error handling."""
    
    # Input validation
    if not location or not location.strip():
        raise ValidationError("Location cannot be empty")
    
    try:
        # Main operation
        response = self._make_api_request(location)
        return self._parse_response(response)
        
    except requests.RequestException as e:
        self._logger.error(f"Network error fetching weather for {location}: {e}")
        raise NetworkError(f"Failed to fetch weather data: {e}")
        
    except ValueError as e:
        self._logger.error(f"Invalid response format for {location}: {e}")
        raise ExternalServiceError(f"Invalid weather data format: {e}")
        
    except Exception as e:
        self._logger.error(f"Unexpected error fetching weather for {location}: {e}")
        raise ServiceError(f"Weather service error: {e}")
```

## Debugging Guide

### Logging Configuration

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Service-specific logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Debugging Dependency Injection

```python
# Check service registration
if not container.is_registered(IWeatherService):
    print("WeatherService not registered!")

# Debug service resolution
try:
    service = container.resolve(IWeatherService)
    print(f"Resolved service: {type(service)}")
except Exception as e:
    print(f"Resolution failed: {e}")

# List registered services
registered_services = container.get_registered_services()
for interface, implementation in registered_services.items():
    print(f"{interface.__name__} -> {implementation.__name__}")
```

### Common Debugging Scenarios

#### Service Not Found
```python
# Problem: ServiceResolutionError
# Solution: Check service registration
container.register_singleton(IWeatherService, WeatherServiceImpl)
```

#### Circular Dependencies
```python
# Problem: Circular dependency detected
# Solution: Refactor to break circular reference
# Use factory pattern or event-driven communication
```

#### Configuration Issues
```python
# Problem: Missing configuration values
# Solution: Check .env file and configuration service
config_service = container.resolve(IConfigurationService)
api_key = config_service.get("openweather_api_key")
if not api_key:
    print("API key not configured!")
```

## Common Development Tasks

### Adding a New UI Component

1. Create component file in `src/ui/components/`
2. Implement component with dependency injection
3. Register component in main UI controller
4. Add tests for component functionality

### Integrating External API

1. Define service interface
2. Implement service with error handling
3. Add configuration for API credentials
4. Create mock service for testing
5. Register service in container
6. Add integration tests

### Adding Configuration Options

1. Add option to `.env.example`
2. Update configuration service to handle new option
3. Document option in configuration guide
4. Add validation for option values

### Performance Optimization

1. Identify bottlenecks with profiling
2. Add caching where appropriate
3. Optimize database queries
4. Use async operations for I/O
5. Monitor performance metrics

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Problem: ModuleNotFoundError
# Solution: Check PYTHONPATH and virtual environment
export PYTHONPATH="${PYTHONPATH}:${PWD}"
source venv/bin/activate
```

#### Test Failures
```bash
# Problem: Tests failing after changes
# Solution: Run specific test with verbose output
pytest tests/test_specific.py -v -s

# Check test isolation
pytest tests/test_specific.py::TestClass::test_method -v
```

#### Configuration Issues
```bash
# Problem: Missing environment variables
# Solution: Check .env file exists and is loaded
cp .env.example .env
# Edit .env with correct values
```

#### Service Resolution Errors
```python
# Problem: Service not resolving
# Solution: Check registration and dependencies
container.register_singleton(IService, ServiceImpl)

# Verify all dependencies are registered
service_deps = [IConfigService, ILogService]
for dep in service_deps:
    if not container.is_registered(dep):
        print(f"Missing dependency: {dep}")
```

### Getting Help

1. **Check Documentation**: Review relevant documentation files
2. **Run Tests**: Ensure all tests pass
3. **Check Logs**: Review application logs for errors
4. **Debug Step-by-Step**: Use debugger to trace execution
5. **Ask Team**: Reach out to team members for assistance

---

*This guide provides the foundation for effective development on the Weather Dashboard project. Follow these patterns and practices to maintain code quality and project consistency.*