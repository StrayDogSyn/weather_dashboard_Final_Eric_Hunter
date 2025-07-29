# Deployment Guide

## Quick Setup

### Requirements
- Python 3.8+
- OpenWeatherMap API key
- Internet connection

### System Support
- Windows 10/11 (primary)
- macOS and Linux (compatible)

## Installation

```bash
# 1. Clone and navigate
git clone <repository-url>
cd weather-dashboard

# 2. Create virtual environment
python -m venv weather_env
weather_env\Scripts\activate  # Windows
# source weather_env/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
# Create config/config.yaml with your OpenWeatherMap API key
```

## Usage

```bash
# Run the application
python main.py
```

### Configuration
Create `config/config.yaml`:
```yaml
api:
  openweather:
    api_key: "your_api_key_here"
    base_url: "https://api.openweathermap.org/data/2.5"

ui:
  theme: "dark"
  window_size: [1200, 800]

cache:
  ttl: 600
  enabled: true
```
## Testing

```bash
# Verify installation
python --version  # Should be 3.8+
python -c "import customtkinter, requests, pydantic, pyyaml"

# Run tests
python -m pytest tests/ -v
```

## Distribution

### Create Executable
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "WeatherDashboard" main.py
# Output: dist/WeatherDashboard.exe
```
## Troubleshooting

### Common Issues
- **API Key Error**: Verify your OpenWeatherMap API key in config
- **Import Error**: Ensure virtual environment is activated
- **GUI Error**: Install tkinter (usually included with Python)

### Performance
- **Clear Cache**: Delete `cache/weather_cache.json` if needed
- **Monitor Memory**: Use Task Manager (Windows) or Activity Monitor (Mac)

## Maintenance

### Updates
```bash
# Check outdated packages
pip list --outdated

# Update dependencies
pip install --upgrade customtkinter
```

### Configuration
- **API Key**: Update in `.env` file, restart application
- **Settings**: Modify `config/settings.yaml` as needed
- **Cache**: Delete `cache/` folder to reset

## Security Notes

- Keep API keys in `.env` file (never commit to version control)
- Add `.env` to `.gitignore`
- Use environment variables in production

---

**For additional documentation, see the `docs/` directory.**
