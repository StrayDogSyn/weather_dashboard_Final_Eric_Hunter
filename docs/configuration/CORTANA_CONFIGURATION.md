# Configuration Guide

## Quick Setup

1. Copy `.env.example` to `.env`
2. Add your OpenWeatherMap API key
3. Customize `config/settings.yaml` as needed

## Configuration Files

### `config/settings.yaml`
```yaml
app:
  name: "Weather Dashboard"
  version: "1.0.0"

api:
  base_url: "https://api.openweathermap.org/data/2.5"
  timeout: 30
  retry_attempts: 3

ui:
  theme: "dark"  # or "light"
  window_size:
    width: 1200
    height: 800
  default_city: "London"

cache:
  enabled: true
  ttl_minutes: 30
```

### `.env`
```env
OPENWEATHER_API_KEY=your_api_key_here
DEBUG=false
LOG_LEVEL=INFO
```

## Programmatic Usage

```python
from src.services.config_service import ConfigService

# Load configuration
config = ConfigService.load_config()

# Access settings
api_key = config.api.key
default_city = config.ui.default_city
cache_ttl = config.cache.ttl_minutes
```

## Key Features

- **Security**: API keys in environment variables
- **Validation**: Type-safe with Pydantic models
- **Caching**: 30-minute TTL for weather data
- **Themes**: Dark/light mode support

---

**For additional documentation, see the `docs/` directory.**
