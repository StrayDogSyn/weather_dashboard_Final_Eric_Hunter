# Weather Dashboard - AI-Powered Weather Intelligence Platform

> **JTC Capstone Project** - A comprehensive weather dashboard utilizing all technologies and fundamentals learned in Tech Pathways / AI Edge 2025 cohort.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Overview

The Weather Dashboard is a sophisticated, AI-powered desktop application that transforms weather data into actionable insights. Built with modern Python technologies, it combines real-time weather monitoring, intelligent activity suggestions, collaborative features, and beautiful data visualizations in a glassmorphic user interface.

## ✨ Key Features

### 🌡️ **Real-Time Weather Monitoring**
- Live weather data from multiple API sources
- Interactive temperature graphs and trends
- Historical weather data analysis
- Multi-city weather comparison

### 📊 **Advanced Data Visualization**
- Interactive temperature trend graphs
- Weather pattern analysis
- Customizable chart types and time ranges
- Export capabilities (PNG, PDF, CSV)

### 📝 **Smart Weather Journal**
- AI-powered mood tracking based on weather
- Rich text editor with markdown support
- Weather correlation insights
- Searchable entries with tags and filters
- Auto-save functionality

### 🎯 **AI Activity Suggestions**
- Google Gemini AI-powered recommendations
- Weather-appropriate activity suggestions
- Spotify music integration for mood-based playlists
- Difficulty and duration filtering
- Personal preference learning

### 👥 **Team Collaboration**
- GitHub integration for team weather sharing
- Collaborative city comparisons
- Team activity tracking
- Real-time synchronization
- Export and import capabilities

### 🎨 **Modern UI/UX**
- Glassmorphic design with CustomTkinter
- Dark/Light theme support
- Responsive layout
- Accessibility features
- Professional animations and transitions

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Windows 10/11 (primary support)
- Internet connection for weather data and AI features

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/weather_dashboard_Final_Eric_Hunter.git
   cd weather_dashboard_Final_Eric_Hunter
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv weather_env
   weather_env\Scripts\activate  # Windows
   # source weather_env/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   # Weather API (choose one)
   OPENWEATHER_API_KEY=your_openweather_api_key
   WEATHERAPI_KEY=your_weatherapi_key
   
   # AI Integration
   GEMINI_API_KEY=your_google_gemini_api_key
   
   # Spotify Integration (optional)
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   
   # GitHub Integration (optional)
   GITHUB_TOKEN=your_github_personal_access_token
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

## 🔧 Configuration

### Quick Setup

**Option 1: Interactive Setup (Recommended)**
```bash
python setup_config.py
```

**Option 2: Demo Mode (No API Keys Required)**
```bash
python setup_config.py --demo
```

**Option 3: Manual Setup**
1. Copy `.env.example` to `.env`
2. Edit `.env` with your API keys

### API Keys Setup

#### Weather API (Required for Live Data)
- **OpenWeatherMap**: Get your free API key at [openweathermap.org](https://openweathermap.org/api)
  - Free tier: 1,000 calls/day
  - Add to `.env`: `OPENWEATHER_API_KEY=your_key_here`
- **WeatherAPI**: Alternative at [weatherapi.com](https://www.weatherapi.com/)
  - Free tier: 1 million calls/month
  - Add to `.env`: `WEATHER_API_KEY=your_key_here`

#### Google Gemini AI (Optional)
- Get your API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Required for AI activity suggestions
- Add to `.env`: `GEMINI_API_KEY=your_key_here`

#### Spotify (Optional)
- Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Required for music recommendations
- Add to `.env`: 
  ```
  SPOTIFY_CLIENT_ID=your_client_id_here
  SPOTIFY_CLIENT_SECRET=your_client_secret_here
  ```

#### GitHub (Optional)
- Generate a Personal Access Token at [GitHub Settings](https://github.com/settings/tokens)
- Required for team collaboration features
- Add to `.env`: `GITHUB_TOKEN=your_token_here`

### Application Settings

The application creates a configuration file at `~/.weather_dashboard/config.yaml` with customizable settings:

```yaml
app_name: "Weather Dashboard"
version: "1.0.0"
theme: "dark"  # or "light"
update_interval: 10  # minutes
default_city: "New York"
auto_save_interval: 30  # seconds
```

## 📱 Usage Guide

### Getting Started

1. **Launch the application** - Run `python main.py`
2. **Set your location** - Enter your city in the search bar
3. **Explore features** - Navigate through different tabs and widgets
4. **Customize settings** - Access settings through the menu

### Feature Walkthroughs

#### Temperature Graphs
- View real-time and historical temperature data
- Switch between different time ranges (24h, 7d, 30d)
- Export graphs as images or data files
- Compare multiple cities

#### Weather Journal
- Create entries with weather context
- Use markdown formatting for rich text
- Add tags and mood indicators
- Search and filter entries
- View weather correlations

#### Activity Suggestions
- Get AI-powered activity recommendations
- Filter by category, difficulty, and duration
- Save favorites and mark completed activities
- Get Spotify playlists for activities
- Rate activities to improve suggestions

#### Team Collaboration
- Connect your GitHub account
- Share weather data with team members
- Create collaborative city comparisons
- Track team activities and insights

## 🏗️ Architecture

### Project Structure

```
weather_dashboard_Final_Eric_Hunter/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── README.md              # This file
├── LICENSE                # MIT License
├── .gitignore            # Git ignore rules
│
├── src/
│   ├── core/             # Core application logic
│   │   ├── app_controller.py
│   │   ├── config_manager.py
│   │   └── database_manager.py
│   │
│   ├── features/         # Feature implementations
│   │   ├── temperature_graph.py
│   │   ├── weather_journal.py
│   │   ├── activity_suggester.py
│   │   └── team_collaboration.py
│   │
│   ├── services/         # External service integrations
│   │   ├── weather_service.py
│   │   └── github_service.py
│   │
│   ├── ui/              # User interface components
│   │   ├── dashboard_ui.py
│   │   ├── theme_manager.py
│   │   └── components/
│   │
│   └── utils/           # Utility functions
│       └── logger.py
│
├── assets/              # Static assets
│   ├── images/
│   └── sounds/
│
├── docs/               # Documentation
└── tests/              # Unit tests
```

### Technology Stack

- **GUI Framework**: CustomTkinter (modern, themed Tkinter)
- **Data Processing**: Pandas, NumPy, Matplotlib
- **AI Integration**: Google Gemini API
- **Database**: SQLite with SQLAlchemy ORM
- **APIs**: Weather APIs, Spotify Web API, GitHub API
- **Configuration**: YAML, python-dotenv
- **Async Support**: aiohttp, asyncio

## 🧪 Development

### Setting Up Development Environment

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   # Uncomment dev dependencies in requirements.txt
   ```

2. **Run tests:**
   ```bash
   pytest tests/
   ```

3. **Code formatting:**
   ```bash
   black src/
   flake8 src/
   ```

4. **Type checking:**
   ```bash
   mypy src/
   ```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for all public methods
- Maintain test coverage above 80%

## 🔍 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Ensure virtual environment is activated
weather_env\Scripts\activate
pip install -r requirements.txt
```

#### Weather data not loading
- Check your internet connection
- Verify API keys in `.env` file
- Check API rate limits

#### AI suggestions not working
- Ensure Gemini API key is valid
- Check Google AI Studio quota
- Verify internet connectivity

#### UI not displaying correctly
- Update CustomTkinter: `pip install --upgrade customtkinter`
- Check system compatibility
- Try different theme settings

### Logging

Logs are stored in `~/.weather_dashboard/logs/`:
- `app.log` - General application logs
- `error.log` - Error-specific logs
- `debug.log` - Detailed debug information

## 📊 Performance

### System Requirements

- **Minimum**: 4GB RAM, 1GB storage, Python 3.8+
- **Recommended**: 8GB RAM, 2GB storage, Python 3.10+
- **Network**: Broadband internet for real-time features

### Optimization Tips

- Enable caching for better performance
- Adjust update intervals based on usage
- Use local database for offline functionality
- Optimize image assets for faster loading

## 🔒 Security

### Data Privacy

- All API keys are stored locally in `.env` file
- Weather data is cached locally for offline access
- No personal data is transmitted without consent
- GitHub integration uses secure OAuth flow

### Best Practices

- Never commit API keys to version control
- Use environment variables for sensitive data
- Regularly update dependencies for security patches
- Enable two-factor authentication for connected services

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **JTC Tech Pathways / AI Edge 2025 Cohort** for the educational foundation
- **OpenWeatherMap** and **WeatherAPI** for weather data
- **Google** for Gemini AI capabilities
- **Spotify** for music integration
- **GitHub** for collaboration features
- **CustomTkinter** community for the modern GUI framework

## 📞 Support

For support, questions, or feature requests:

- 📧 Email: [your-email@example.com]
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/weather_dashboard_Final_Eric_Hunter/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/weather_dashboard_Final_Eric_Hunter/discussions)

---

**Built with ❤️ by Eric Hunter as part of the JTC Tech Pathways / AI Edge 2025 Capstone Project**
