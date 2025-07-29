# Modern Weather Dashboard

A professional weather dashboard application built with Python and CustomTkinter, featuring a sleek "Data Terminal" aesthetic and real-time weather data integration.

![Weather Dashboard](https://img.shields.io/badge/Python-3.8%2B-blue)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2.0%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### Core Functionality
- **Real-time Weather Data**: Current weather conditions with comprehensive metrics
- **5-Day Forecast**: Detailed hourly and daily weather predictions
- **Interactive Charts**: Temperature, humidity, and wind speed visualizations
- **City Search**: Instant weather updates for any global location
- **Geolocation Support**: Weather data by coordinates

### Technical Features
- **Modern UI**: CustomTkinter with "Data Terminal" dark theme
- **Professional Design**: JetBrains Mono typography and neon green accents
- **Responsive Layout**: Adaptive interface for different screen sizes
- **Error Handling**: Comprehensive error management and user feedback
- **Caching System**: Intelligent API response caching for performance
- **Loading States**: Professional loading animations and progress indicators

### Data Visualization
- **Temperature Charts**: Interactive line charts with matplotlib
- **Weather Metrics Grid**: Organized display of humidity, pressure, wind, UV index
- **Status Indicators**: Real-time connection and API status monitoring
- **Chart Type Selection**: Multiple visualization options for forecast data

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenWeather API key (free at [openweathermap.org](https://openweathermap.org/api))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd weather_dashboard_Final_Eric_Hunter
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your OpenWeather API key
   OPENWEATHER_API_KEY=your_api_key_here
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

## 📁 Project Structure

```
weather_dashboard_Final_Eric_Hunter/
├── src/
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # Application entry point
│   ├── services/                   # Core application services
│   │   ├── __init__.py
│   │   ├── config_service.py       # Configuration management
│   │   ├── logging_service.py      # Centralized logging
│   │   └── weather_service.py      # OpenWeather API integration
│   ├── ui/                         # User interface components
│   │   ├── __init__.py
│   │   ├── theme.py                # UI theme and styling
│   │   ├── weather_dashboard.py    # Main dashboard window
│   │   └── components/             # Reusable UI components
│   │       ├── __init__.py
│   │       ├── chart_display.py    # Chart visualization
│   │       ├── loading_overlay.py  # Loading animations
│   │       ├── search_bar.py       # City search interface
│   │       ├── status_bar.py       # Status indicators
│   │       └── weather_display.py  # Weather metrics display
│   ├── models/                     # Data models and structures
│   │   ├── __init__.py
│   │   ├── app_models.py           # Application state models
│   │   └── weather_models.py       # Weather data models
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       ├── formatters.py           # Data formatting utilities
│       ├── helpers.py              # General helper functions
│       └── validators.py           # Input validation utilities
├── tests/                          # Unit tests
│   ├── __init__.py
│   └── test_weather_service.py     # Weather service tests
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore patterns
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## 🎨 Design System

### Color Palette (Data Terminal Theme)
- **Background**: `#121212` - Deep dark for reduced eye strain
- **Primary Accent**: `#00FFAB` - Neon green for highlights and active states
- **Secondary**: `#2C2C2C` - Dark gray for containers and borders
- **Text Primary**: `#EAEAEA` - Light gray for main content
- **Text Secondary**: `#B0B0B0` - Medium gray for secondary information

### Typography
- **Primary Font**: JetBrains Mono - Professional monospace for technical aesthetic
- **Sizes**: 12px (body), 14px (headers), 16px (titles), 20px (main display)

### UI Components
- **Buttons**: Rounded corners, hover effects, neon green accents
- **Cards**: Dark containers with subtle borders and shadows
- **Charts**: Matplotlib integration with custom dark theme
- **Loading**: Animated spinners and progress bars

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```env
# OpenWeather API Configuration
OPENWEATHER_API_KEY=your_32_character_api_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5

# Application Settings
DEFAULT_CITY=New York
TEMPERATURE_UNIT=celsius
WIND_SPEED_UNIT=metric
PRESSURE_UNIT=hPa

# UI Configuration
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
THEME_MODE=dark
FONT_FAMILY=JetBrains Mono

# Performance Settings
API_TIMEOUT=10
CACHE_TTL=300
REFRESH_INTERVAL=600
MAX_RETRIES=3

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/weather_dashboard.log
MAX_LOG_SIZE=10485760
LOG_BACKUP_COUNT=5
```

### API Configuration
1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your free API key
3. Add it to your `.env` file
4. The application supports both current weather and 5-day forecast APIs

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src

# Run specific test file
python -m pytest tests/test_weather_service.py -v
```

### Test Coverage
- Weather service API integration
- Data model validation
- Configuration management
- Error handling scenarios
- Cache functionality

## 📊 Performance Features

### Caching Strategy
- **API Response Caching**: 5-minute TTL for weather data
- **Image Caching**: Weather icons cached locally
- **Search History**: Recent searches for quick access

### Optimization
- **Debounced Search**: Prevents excessive API calls during typing
- **Lazy Loading**: Components loaded on demand
- **Memory Management**: Automatic cleanup of expired cache entries
- **Request Pooling**: Reused HTTP connections for efficiency

## 🔍 API Integration

### OpenWeather API Endpoints
- **Current Weather**: `/weather` - Real-time conditions
- **5-Day Forecast**: `/forecast` - Hourly predictions
- **Geocoding**: `/geo/1.0/direct` - City name to coordinates

### Data Processing
- **Unit Conversion**: Automatic temperature, wind, and pressure conversions
- **Data Validation**: Input sanitization and API response validation
- **Error Recovery**: Graceful handling of API failures and network issues

## 🛠️ Development

### Code Style
- **PEP 8**: Python style guide compliance
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Explicit exception management

### Architecture Patterns
- **Service Layer**: Separation of business logic
- **Model-View Pattern**: Clean UI and data separation
- **Configuration Management**: Centralized settings
- **Dependency Injection**: Testable component design

### Adding New Features
1. **Services**: Add new functionality in `src/services/`
2. **UI Components**: Create reusable widgets in `src/ui/components/`
3. **Models**: Define data structures in `src/models/`
4. **Tests**: Add corresponding tests in `tests/`

## 🚨 Troubleshooting

### Common Issues

**API Key Issues**
```
Error: Invalid API key
Solution: Verify your API key in .env file is correct and active
```

**Network Connectivity**
```
Error: Connection timeout
Solution: Check internet connection and firewall settings
```

**Missing Dependencies**
```
Error: ModuleNotFoundError
Solution: Run 'pip install -r requirements.txt'
```

**Font Issues**
```
Error: Font not found
Solution: Install JetBrains Mono or update FONT_FAMILY in .env
```

### Debug Mode
Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

### Log Files
Application logs are stored in `logs/weather_dashboard.log` with automatic rotation.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

## 🔮 Future Enhancements

- [ ] Weather alerts and notifications
- [ ] Historical weather data charts
- [ ] Multiple location management
- [ ] Weather map integration
- [ ] Mobile-responsive design
- [ ] Dark/light theme toggle
- [ ] Export weather data functionality
- [ ] Weather widget for desktop

---

**Built with ❤️ using Python and CustomTkinter**