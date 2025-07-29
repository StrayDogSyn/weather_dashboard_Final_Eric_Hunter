# Architecture Overview

## Layers

- **Models** - Data structures and entities
- **Services** - Business logic and API integrations  
- **UI** - User interface components
- **Utils** - Shared utilities

## Project Structure

```
src/
├── models/          # Data models
├── services/        # API integrations
├── ui/              # Interface components
└── utils/           # Utilities

cache/               # Application cache
config/              # Configuration
docs/                # Documentation
main.py              # Entry point
```

## Core Components

- **Weather Service** - OpenWeatherMap API with caching
- **Configuration** - Type-safe settings
- **Modern UI** - CustomTkinter interface
- **Data Models** - Structured entities

## Features

- Real-time weather data
- Interactive charts and visualization
- Caching for performance
- Error handling and user feedback

## Usage

```bash
python main.py
```

**Configuration**: Set API keys in `config/config.yaml`

## Extension Opportunities

- Testing framework and unit tests
- Additional weather APIs and data sources
- Enhanced caching with Redis
- SQLite database for historical data
- Interactive maps and advanced visualization
- Export features (PDF, CSV)
- Weather alerts and notifications
- Voice integration with Cortana

---

**For additional documentation, see the `docs/` directory.**
