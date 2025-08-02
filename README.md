# 🌤️ Weather Dashboard

![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
[![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A modern, professional weather dashboard application built with Python and CustomTkinter. Features real-time weather data, interactive visualizations, weather journaling, and AI integration with a sleek Data Terminal interface.

> **📋 Status**: ✅ Production Ready | 🎯 Clean Architecture | 🔧 Dependency Injection | 🛠️ Recently Refactored

## **Screenshots**

![Weather Dashboard Screenshot](assets/images/Main.png)

## ✨ Features

### 🌤️ Weather Data

- **Real-time conditions** for any city worldwide
- **5-day forecasts** with detailed hourly data
- **Favorite locations** with quick access
- **Temperature units** (Celsius/Fahrenheit toggle)
- **Location detection** for local weather
- **🆕 Enhanced Features**: Air quality data, astronomical information, weather alerts
- **🆕 Advanced Search**: Autocomplete, recent searches, favorites management
- **🆕 Multi-location Support**: Compare weather across multiple cities

### 📊 Visualization & Analytics

- **Interactive charts** with keyboard shortcuts (Ctrl+1-4)
- **Weather trends** and historical data
- **City comparison** side-by-side view
- **Data export** capabilities

### 🎨 User Experience

- **Data Terminal UI** with professional dark theme (#121212 background, #00FFAB neon green accents)
- **Responsive design** adapts to window size
- **Voice assistant** integration (Cortana)
- **Weather journal** with mood tracking
- **Activity suggestions** based on conditions
- **AI-generated poetry** inspired by weather

### 🔧 Technical Features

- **Clean Architecture** with dependency injection and repository patterns
- **Type Safety** with comprehensive type hints and validation
- **Async Support** for non-blocking operations
- **SQLite database** with repository pattern for data persistence
- **Intelligent caching** with configurable TTL
- **Custom exceptions** for structured error handling
- **Comprehensive logging** with rotating file handlers
- **Code quality** tools (Black, isort, flake8, autoflake)
- **Development tools** and automated cleanup scripts
- **Cross-platform** compatibility
- **🆕 Enhanced Services**: Rate limiting, advanced caching, error recovery
- **🆕 Progressive Loading**: Basic data first, enhanced details after
- **🆕 Offline Support**: Cached data display when network unavailable
- **🆕 Robust Configuration**: Fixed ConfigService with proper property access
- **🆕 Exception Handling**: Specific exception handling replacing generic catches

> 📖 **Project Structure**: This is a streamlined weather dashboard with clean architecture and modular design

## 🔧 Recent Improvements

### Configuration Service Fixes (Latest)

- **✅ ConfigService AttributeError Resolution**: Fixed missing property methods for weather, UI, and app configurations
- **✅ Enhanced Configuration Structure**: Added missing attributes (api_key, base_url, default_city) to configuration classes
- **✅ Automatic Configuration Sync**: Weather API key and base URL now sync automatically from API configuration
- **✅ Type Safety**: Added proper type hints to all configuration property methods
- **✅ Exception Handling**: Replaced generic exception handlers with specific exception types throughout codebase

### Code Quality Improvements

- **Specific Exception Handling**: Enhanced error handling in search components, validators, and services
- **Type Annotations**: Improved type safety across public API functions
- **Configuration Robustness**: Eliminated AttributeError crashes during application startup
- **Service Integration**: Seamless integration between configuration and weather services

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ with tkinter
- [OpenWeatherMap API key](https://openweathermap.org/api) (free)

### Installation

```bash
# 1. Clone and navigate
git clone <repository-url>
cd weather_dashboard_Final_Eric_Hunter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
# Create a .env file in the root directory
# Add: OPENWEATHER_API_KEY=your_key_here

# 4. Install enhanced dependencies (optional)
pip install geopy geocoder ratelimit cachetools

# 5. Run application
python main.py
```

> 📚 **API Key**: Get your free API key from [OpenWeatherMap](https://openweathermap.org/api) and add it to your .env file

## 🎨 Interface Overview

### Navigation Tabs

- **Weather** - Current conditions and basic info
- **Forecast** - 5-day detailed forecasts
- **Comparison** - Multi-city weather comparison
- **Journal** - Personal weather tracking with moods
- **Activities** - Weather-based suggestions
- **Poetry** - AI-generated weather poems
- **Favorites** - Quick access to saved locations

### Design Highlights

- **Data Terminal theme** with neon green (#00FFAB) on dark backgrounds (#121212)
- **Professional typography** using JetBrains Mono font family
- **Responsive layout** adapts to window size
- **Custom hover effects** with #2A2A2A hover states
- **Color-coded data** with status colors (success: #00FF88, warning: #FFB800, error: #FF4444)
- **Card-based layout** with #1E1E1E card backgrounds and #333333 borders

> 🎨 **UI Framework**: Built with CustomTkinter for modern, responsive design

## 📱 Usage

### Basic Operations

1. Enter city name → Click "Get Weather"
2. Navigate tabs for different features
3. Toggle temperature units (°C/°F)
4. Save cities to favorites for quick access

### Keyboard Shortcuts

- **Ctrl+1** - Temperature trends chart
- **Ctrl+2** - Weather metrics comparison
- **Ctrl+3** - Forecast visualization
- **Ctrl+4** - Humidity/pressure data

> 📊 **Charts**: Interactive visualizations powered by Matplotlib with real-time data updates

### Advanced Features

- **🌍 City Comparison** - Side-by-side weather analysis
- **📔 Weather Journal** - Personal weather tracking with mood correlation
- **🎯 Activity Suggestions** - Weather-appropriate recommendations
- **🎨 Weather Poetry** - AI-generated poems with visual presentation
- **🔊 Voice Assistant** - Cortana integration for hands-free operation

> 🚀 **Modern Interface**: Glassmorphic design with responsive layout and intuitive navigation

## 🛠️ Technical Stack

### Architecture

- **Clean Architecture** with MVC pattern
- **Service layer** for API and data management
- **SQLite database** with SQLAlchemy ORM
- **Custom UI components** with modern styling
- **Matplotlib** for data visualization

### Key Dependencies

```txt
customtkinter     # Modern UI framework
requests         # HTTP client
matplotlib       # Charts and graphs
python-dotenv    # Environment management
Pillow          # Image processing
```

> 🏗️ **Clean Architecture**: Modular design with separation of concerns - models, services, and UI components

### Project Structure

```text
weather_dashboard_Final_Eric_Hunter/
├── src/                    # Source code
│   ├── config/            # Configuration management
│   │   └── app_config.py  # Application configuration
│   ├── models/            # Data models
│   │   └── weather_models.py # Weather data structures
│   ├── services/          # Business logic & APIs
│   │   ├── activity_service.py
│   │   ├── config_service.py
│   │   ├── enhanced_weather_service.py
│   │   ├── geocoding_service.py
│   │   ├── loading_manager.py
│   │   └── logging_service.py
│   ├── ui/               # GUI components
│   │   ├── components/   # Reusable UI components
│   │   │   └── search_components.py # Enhanced search functionality
│   │   ├── professional_weather_dashboard.py # Main dashboard
│   │   ├── safe_widgets.py # Safe CustomTkinter widgets
│   │   └── theme.py     # UI theming
│   └── utils/            # Utility functions
│       └── loading_manager.py
├── data/                 # Application data
│   └── window_config.json
├── cache/                # Weather data cache
├── assets/               # Images and sounds
├── docs/                 # Documentation
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

> 📁 **Clean Structure**: Streamlined architecture focusing on essential components with clear separation of concerns

## 🏗️ Architecture

The Weather Dashboard follows clean architecture principles with modular design and separation of concerns:

### Core Components

- **`src/config/`** - Application configuration management with environment variable support
- **`src/models/`** - Data models and domain entities (WeatherData, location models, etc.)
- **`src/services/`** - Business logic layer (weather, configuration, geocoding, activity services)
- **`src/ui/`** - User interface components and main dashboard
- **`src/utils/`** - Utility functions and loading management

### Key Patterns

- **Service Layer Architecture**: Clean separation between UI, business logic, and data
- **Configuration Management**: Centralized settings with environment variable support
- **Component-Based UI**: Modular CustomTkinter components for reusability
- **Caching Strategy**: Intelligent data caching for performance optimization

### Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture documentation
- **[API_GUIDE.md](API_GUIDE.md)** - API integration and internal interfaces
- **[WORKS_CITED.md](docs/WORKS_CITED.md)** - Comprehensive citations for all external resources
- **Development tools** - Automated cleanup, code quality, and testing scripts

> 🔧 **Modern Practices**: Type hints, async support, comprehensive error handling, and automated code quality tools

## 🌟 Project Highlights

### Technical Excellence

- **Clean Architecture** with modular design
- **Modern UI/UX** with glassmorphic styling
- **Data visualization** with interactive charts
- **Voice integration** for accessibility
- **Comprehensive testing** with CI/CD
- **Extensive documentation** and quality standards

### Innovation Features

- **AI-generated poetry** based on weather
- **Mood tracking** with weather correlation
- **Multi-city comparison** analytics
- **Voice-controlled interface** (Cortana)
- **Real-time data visualization** with hotkeys

> 🚀 **Extensible Design**: Modular architecture allows for easy feature additions and enhancements

---

**Author**: E Hunter Petross
**Project**: Weather Dashboard Capstone
**Technology**: Python, TKinter, OpenWeatherMap API

## 📚 Key Information

### Quick Reference

- **API Integration**: Uses OpenWeatherMap API for real-time weather data
- **UI Framework**: CustomTkinter for modern, responsive interface
- **Data Visualization**: Matplotlib for interactive charts and graphs
- **Architecture**: Clean separation with models, services, and UI layers
- **Configuration**: Environment-based API key management
- **Cross-Platform**: Compatible with Windows, macOS, and Linux

## 🧪 Development

### Running the Application

```bash
# Start the weather dashboard
python main.py

# Ensure all dependencies are installed
pip install -r requirements.txt

# Check Python version (3.8+ required)
python --version
```

**Development**: Modular codebase with clear separation of concerns for easy maintenance and extension

## 📖 Technical Details

### Application Architecture

- **Configuration Service** (`src/config/`) - Centralized application configuration management
- **Weather Models** (`src/models/`) - Data structures for weather information
- **Enhanced Weather Service** (`src/services/`) - API integration and data processing
- **Professional Dashboard** (`src/ui/`) - Main application interface with Data Terminal design theme
- **Search Components** (`src/ui/components/`) - Enhanced search functionality with autocomplete
- **Safe Widgets** (`src/ui/`) - Robust CustomTkinter widget implementations

### Key Features

- **Real-time Weather Data** - Current conditions and 5-day forecasts
- **Interactive Charts** - Temperature trends, metrics comparison, and forecast visualization
- **Responsive Design** - Adapts to different window sizes and screen resolutions
- **Modern UI** - Glassmorphic theme with smooth animations and transitions
- **Configuration Management** - Robust settings and API key handling

## 🔒 Security

- **API key protection** with environment variables
- **Input validation** and sanitization
- **Secure error handling** without information disclosure
- **Comprehensive logging** for security monitoring

> 🔐 **Security**: API keys stored in environment variables, input validation, and secure error handling

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run quality checks: `python scripts/pre_commit_check.py`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push and open Pull Request

**Standards**: PEP 8, 80%+ test coverage, type hints, conventional commits

> 👥 **Contributing**: Fork the repository, create feature branches, and submit pull requests with comprehensive testing

## 📄 License

MIT License - This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **[OpenWeatherMap](https://openweathermap.org/)** - Weather data API
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Modern GUI framework
- **[Microsoft Cortana](https://www.microsoft.com/en-us/cortana)** - Voice assistant integration
- **Python Community** - Excellent libraries and documentation

> 📚 **Complete Attribution**: See [WORKS_CITED.md](docs/WORKS_CITED.md) for comprehensive citations of all external resources, APIs, libraries, and frameworks used in this project.

---

## 🚀 CI/CD & Quality

### Automated Pipeline

- **Cross-platform testing** (Linux, Windows, macOS)
- **Python versions** 3.8-3.11 support
- **Code quality checks** (Black, flake8, mypy)
- **Security scanning** with CodeQL
- **85%+ test coverage** maintained

### Local Quality Checks

```bash
# Install dev dependencies
pip install -r tests/requirements-test.txt

# Run all checks
python scripts/pre_commit_check.py
```

> 🔧 **Development**: Python 3.8+, pip install requirements, configure API key, and run main.py

---

### Built with Python • CustomTkinter • OpenWeatherMap API

---

> 📚 **Getting Started**: Clone repository, install dependencies, configure API key, and launch with `python main.py`
