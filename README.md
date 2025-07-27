# CodeFront Weather Capstone

> **JTC Capstone Project** - A comprehensive AI-powered weather intelligence platform utilizing all technologies and fundamentals learned in Tech Pathways / AI Edge 2025 cohort.
>
> A modern, glassmorphic weather app powered by AI agents and built with TRAE 2.0 IDE.

---

## 🧰 Tech Stack

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Framework](https://img.shields.io/badge/Framework-Tkinter-000000.svg)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![Image](https://img.shields.io/badge/Image-Pillow-ff69b4.svg)

## 🤖 AI & IDE Integration

![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)
![LangChain](https://img.shields.io/badge/LLM-LangChain-purple.svg)
![TRAE IDE](https://img.shields.io/badge/Built%20with-TRAE%202.0-brightgreen.svg)

## ✅ Quality & Testing

![Pytest](https://img.shields.io/badge/Tested%20with-pytest-9cf.svg)
![Lint](https://img.shields.io/badge/linting-flake8-yellowgreen.svg)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)

## 📄 Meta & Status

![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-in%20development-lightgrey.svg)
![Platform](https://img.shields.io/badge/platform-desktop-lightblue.svg)
![Contributions](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)

---

## 🖼️ UI Preview

> *(Insert a screenshot here)*  
> `![UI Preview](./screenshots/glass_ui_preview.png)` *(update with your actual path)*

---

## ✨ Key Features

### 🌡️ **Real-Time Weather Intelligence**

- Live weather data from multiple API sources (OpenWeatherMap, WeatherAPI)
- Interactive temperature graphs and historical analysis
- Multi-city weather comparison and tracking

### 🤖 **AI-Powered Insights**

- Google Gemini AI activity suggestions based on weather conditions
- Smart weather journal with mood tracking and correlations
- Spotify music integration for weather-appropriate playlists

### 👥 **Collaborative Features**

- GitHub integration for team weather sharing
- Real-time data synchronization and export capabilities
- Team activity tracking and collaborative comparisons

### 🎨 **Modern UI/UX**

- Glassmorphic design with CustomTkinter framework
- Dark/Light theme support with responsive layouts
- Professional animations and accessibility features

### 🔧 **Technical Excellence**

- Agent-powered development via TRAE IDE
- Unit tested with `pytest` and linted using `flake8`
- Modular, scalable architecture with clean code principles

---

## 🧠 Powered by TRAE AI Agents

| Agent Type | Function | Implementation |
|------------|----------|----------------|
| **Cortana Builder** | Conversational AI implementation expert | Bot Framework SDK, Azure Cognitive Services integration |
| **Code Assistant** | Real-time code analysis and refactoring | Python architecture optimization, clean code patterns |
| **UI/UX Agent** | Modern interface design and accessibility | CustomTkinter glassmorphic themes, responsive layouts |
| **API Integration** | External service orchestration | Weather APIs, Gemini AI, Spotify, GitHub connectivity |

Built with TRAE IDE's advanced AI-powered development environment featuring real-time code assistance, intelligent refactoring, and seamless API integrations.

---

## 🌟 Overview

CodeFront Weather Capstone is a sophisticated, AI-powered desktop application that transforms weather data into actionable insights. Built with modern Python technologies using clean architecture principles, it combines real-time weather monitoring, intelligent activity suggestions, collaborative features, and beautiful data visualizations in a glassmorphic user interface.

**Single Entry Point:** `main.py`

```bash
python main.py
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11 (primary support)
- Internet connection for weather data and AI features

### Setup

1. **Clone and setup:**

   ```bash
   git clone https://github.com/yourusername/CodeFront-Weather-Capstone.git
   cd CodeFront-Weather-Capstone
   python -m venv weather_env
   weather_env\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**

   ```bash
   # Copy template and edit with your API keys
   copy .env.example .env
   # Edit .env with your API keys
   ```

3. **Run:**

   ```bash
   python main.py
   ```

## 🔧 Configuration

### Quick Setup

#### Option 1: Interactive Setup (Recommended)

```bash
python setup_config.py
```

#### Option 2: Demo Mode (No API Keys Required)

```bash
python setup_config.py --demo
```

#### Option 3: Manual Setup

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

  ```env
  SPOTIFY_CLIENT_ID=your_client_id_here
  SPOTIFY_CLIENT_SECRET=your_client_secret_here
  ```

#### GitHub (Optional)

- Generate a Personal Access Token at [GitHub Settings](https://github.com/settings/tokens)
- Required for team collaboration features
- Add to `.env`: `GITHUB_TOKEN=your_token_here`

### Application Settings

The application creates a configuration file at `~/.codefront_weather/config.yaml` with customizable settings:

```yaml
app_name: "CodeFront Weather Capstone"
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

**Clean Architecture Principles** with clear separation of concerns:

- **`main.py`** - Single application entry point and UI orchestration
- **`config/settings.py`** - Configuration management with environment variables
- **`services/`** - External API integrations (Weather, Gemini AI, GitHub, Spotify)
- **`data/database.py`** - SQLite database operations
- **`ui/`** - User interface components
- **`.env.example`** - Template for required environment variables

### Technology Stack

- **GUI Framework**: CustomTkinter (modern, themed Tkinter)
- **AI Integration**: Google Gemini API
- **Database**: SQLite
- **APIs**: OpenWeatherMap, Spotify Web API, GitHub API
- **Configuration**: python-dotenv

## 🧪 Development

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHER_API_KEY` | Yes | OpenWeatherMap API key |
| `GEMINI_API_KEY` | No | Google Gemini AI API key |
| `SPOTIFY_CLIENT_ID` | No | Spotify application client ID |
| `SPOTIFY_CLIENT_SECRET` | No | Spotify application client secret |
| `GITHUB_TOKEN` | No | GitHub personal access token |
| `DATABASE_PATH` | No | Custom database file path |
| `DEBUG_MODE` | No | Enable debug logging (true/false) |

### Adding Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement in appropriate service/module
3. Test functionality
4. Submit pull request

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🔍 Troubleshooting

### Common Issues

**Application won't start:**

- Check Python version (3.8+ required)
- Verify dependencies: `pip install -r requirements.txt`
- Ensure `.env` file exists with API keys

**Weather data not loading:**

- Verify internet connection and API key validity
- Check API rate limits

**UI issues:**

- Update CustomTkinter: `pip install --upgrade customtkinter`
- Check display scaling settings

### Debug Mode

Enable detailed logging:

```env
DEBUG_MODE=true
```

## 📊 Performance

### System Requirements

**Minimum:**

- Python 3.8+
- 4GB RAM
- 100MB disk space
- Internet connection

**Recommended:**

- Python 3.10+
- 8GB RAM
- Stable broadband connection

### Optimization

- Increase weather update intervals to reduce API calls
- Enable data caching for better performance
- Disable animations if experiencing UI lag

## 🔒 Security

### API Key Management

- Store API keys in `.env` file (never commit to git)
- Use environment variables for production
- Rotate API keys regularly

### Data Privacy

- Weather data cached locally for performance
- No personal data transmitted to third parties
- Location data only used for weather queries

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenWeatherMap](https://openweathermap.org/) - Weather data
- [Google Gemini](https://ai.google.dev/) - AI capabilities
- [Spotify Web API](https://developer.spotify.com/) - Music recommendations
- [GitHub API](https://docs.github.com/en/rest) - Code collaboration
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework

---

## 🌟 Built with Code, Caffeine, and a Dash of Collaborative Magic ☕

*"If it challenges me, it excites me!"* - This project embodies that spirit, blending modern web technologies with AI innovation to create something truly special for weather enthusiasts and developers alike.

🚀 **Ready to explore?** Dive into the code, customize it to your heart's content, and let's make weather data beautiful together!

⭐ **Found this helpful?** Give it a star and join the journey of turning meteorological data into meaningful experiences!

---

*Crafted with passion by a developer who believes that great software should be as dynamic and unpredictable as the weather itself* 🌦️✨
