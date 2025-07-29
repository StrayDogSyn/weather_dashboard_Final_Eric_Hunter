# 🌤️ Weather Dashboard

![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
[![Code Quality](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A modern weather dashboard application with voice assistant integration, built using Python and CustomTkinter. Features real-time weather data, interactive visualizations, and an intuitive glassmorphic interface.

> **📋 Status**: ✅ Production Ready | 🎯 All Features Implemented | 🔧 CI/CD Enabled

## **Screenshots**

![Dashboard Screenshot](assets/images/Main.png)

## ✨ Features

### 🌤️ Weather Data
- **Real-time conditions** for any city worldwide
- **5-day forecasts** with detailed hourly data
- **Favorite locations** with quick access
- **Temperature units** (Celsius/Fahrenheit toggle)
- **Location detection** for local weather

### 📊 Visualization & Analytics
- **Interactive charts** with keyboard shortcuts (Ctrl+1-4)
- **Weather trends** and historical data
- **City comparison** side-by-side view
- **Data export** capabilities

### 🎨 User Experience
- **Glassmorphic UI** with modern dark theme
- **Responsive design** adapts to window size
- **Voice assistant** integration (Cortana)
- **Weather journal** with mood tracking
- **Activity suggestions** based on conditions
- **AI-generated poetry** inspired by weather

### 🔧 Technical Features
- **Clean Architecture** with modular design
- **SQLite database** for data persistence
- **Intelligent caching** for performance
- **Comprehensive testing** with CI/CD
- **Cross-platform** compatibility

> 📖 **Detailed Documentation**: See [Architecture Guide](docs/architecture/architecture.md) and [Implementation Guide](docs/development/IMPLEMENTATION_GUIDE.md)

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
cp .env.example .env
# Edit .env and add: OPENWEATHER_API_KEY=your_key_here

# 4. Run application
python main.py
```

> 📚 **Need Help?** See [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md) for detailed setup instructions and [Security Guide](docs/configuration/security.md) for API key best practices.

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
- **Glassmorphic theme** with transparency effects
- **Responsive layout** adapts to window size
- **Custom animations** and hover effects
- **Color-coded data** for quick recognition
- **Modern typography** for readability

> 🎨 **UI Details**: See [UI Components Guide](docs/development/ui_components.md) for design specifications

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

> 📊 **Advanced Features**: See [User Guide](docs/user/USER_GUIDE.md) for detailed feature explanations and [API Reference](docs/api/API_REFERENCE.md) for integration options

### Advanced Features

- **🌍 City Comparison** - Side-by-side weather analysis
- **📔 Weather Journal** - Personal weather tracking with mood correlation
- **🎯 Activity Suggestions** - Weather-appropriate recommendations
- **🎨 Weather Poetry** - AI-generated poems with visual presentation
- **🔊 Voice Assistant** - Cortana integration for hands-free operation

> 🚀 **Feature Deep Dive**: See [Features Documentation](docs/features/) for comprehensive guides on each advanced feature

## 🛠️ Technical Stack

### Architecture
- **Clean Architecture** with MVC pattern
- **Service layer** for API and data management
- **SQLite database** with SQLAlchemy ORM
- **Custom UI components** with modern styling
- **Matplotlib** for data visualization

### Key Dependencies
```
customtkinter     # Modern UI framework
requests         # HTTP client
matplotlib       # Charts and graphs
python-dotenv    # Environment management
Pillow          # Image processing
```

> 🏗️ **Architecture Details**: See [Architecture Guide](docs/architecture/architecture.md) and [Dependencies](docs/development/dependencies.md) for complete technical specifications

### Project Structure

```text
weather_dashboard_Final_Eric_Hunter/
├── src/                    # Source code
│   ├── models/            # Data models
│   ├── services/          # Business logic & APIs
│   ├── ui/               # GUI components
│   └── utils/            # Helper functions
├── docs/                  # Documentation
│   ├── architecture/     # System design
│   ├── configuration/    # Setup guides
│   ├── deployment/       # Deploy instructions
│   └── development/      # Dev guides
├── cache/                # Application cache
├── data/                 # User data & database
├── assets/               # Images & resources
├── tests/                # Test suite
├── main.py              # Entry point
└── requirements.txt     # Dependencies
```

> 📁 **Detailed Structure**: See [Project Structure](docs/development/project_structure.md) for complete file descriptions and organization details

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

> 🚀 **Roadmap**: See [Future Enhancements](docs/development/roadmap.md) for planned features and improvements

---

**Author**: E Hunter Petross
**Project**: Weather Dashboard Capstone
**Technology**: Python, TKinter, OpenWeatherMap API

## 📚 Documentation

### Quick Links
- **[Architecture Guide](docs/architecture/architecture.md)** - System design and patterns
- **[Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)** - Setup and deployment
- **[Implementation Guide](docs/development/IMPLEMENTATION_GUIDE.md)** - Development details
- **[User Guide](docs/user/USER_GUIDE.md)** - Feature explanations
- **[API Reference](docs/api/API_REFERENCE.md)** - Integration options
- **[Security Guide](docs/configuration/security.md)** - Best practices

### Development Resources
- **[Project Structure](docs/development/project_structure.md)** - File organization
- **[Dependencies](docs/development/dependencies.md)** - Library details
- **[Testing Guide](docs/development/testing.md)** - Test procedures
- **[Contributing](docs/development/contributing.md)** - Contribution guidelines

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/

# Run specific test
python -m pytest tests/test_weather_service.py
```

**Coverage**: Unit tests, integration tests, GUI tests, and API tests

> 🧪 **Testing Details**: See [Testing Guide](docs/development/testing.md) for comprehensive test procedures and CI/CD information

## 📚 Documentation

### Architecture & Design

- [Architecture Documentation](docs/architecture/architecture.md) - Detailed architecture overview and design principles
- [Project Structure](docs/architecture/project_structure.md) - Complete project organization and file structure

### Configuration & Setup

- [Security Guidelines](docs/configuration/security.md) - Security best practices and API key management
- [Cortana Configuration](docs/configuration/CORTANA_CONFIGURATION.md) - Cortana voice assistant setup and configuration
- [Cortana Integration](docs/configuration/CORTANA_INTEGRATION.md) - Cortana integration details

### Development & Implementation

- [Implementation Guide](docs/development/IMPLEMENTATION_GUIDE.md) - Detailed implementation documentation
- [GUI Layout Analysis](docs/development/GUI_LAYOUT_ANALYSIS_AND_IMPROVEMENTS.md) - UI design analysis and improvements
- [GitHub Team Integration](docs/development/GITHUB_TEAM_DATA_INTEGRATION.md) - Team collaboration features
- [SQL Database Documentation](docs/development/SQL_DATABASE.md) - Database design and implementation

### Deployment

- [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md) - Production deployment instructions

### Weekly Reflections

- [Week 11 Reflection](docs/reflections/Week11_Reflection.md) - Clean architecture and core service implementation
- [Week 12 Reflection](docs/reflections/Week12_Reflection.md) - Advanced features and data visualization
- [Week 13 Reflection](docs/reflections/Week13_Reflection.md) - Machine learning integration and analytics
- [Week 14 Reflection](docs/reflections/Week14_Reflection.md) - Development milestones and reflection
- [Week 15 Reflection](docs/reflections/Week15_Reflection.md) - Final project reflection

### Complete Documentation Index

- [Documentation Index](docs/README.md) - Complete documentation overview with works cited

## 🔒 Security

- **API key protection** with environment variables
- **Input validation** and sanitization
- **Secure error handling** without information disclosure
- **Comprehensive logging** for security monitoring

> 🔐 **Security Details**: See [Security Guide](docs/configuration/security.md) for complete security practices

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run quality checks: `python scripts/pre_commit_check.py`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push and open Pull Request

**Standards**: PEP 8, 80%+ test coverage, type hints, conventional commits

> 👥 **Contributing Guide**: See [Contributing](docs/development/contributing.md) for detailed guidelines and workflow

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[OpenWeatherMap](https://openweathermap.org/)** - Weather data API
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Modern GUI framework
- **[Microsoft Cortana](https://www.microsoft.com/en-us/cortana)** - Voice assistant integration
- **Python Community** - Excellent libraries and documentation

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

> 🔧 **Development Setup**: See [Development Guide](docs/development/setup.md) for complete development environment configuration

---

**Built with Python • CustomTkinter • OpenWeatherMap API**

---

> 📚 **Complete Documentation**: Visit [docs/](docs/) for comprehensive guides, API references, and development resources.
