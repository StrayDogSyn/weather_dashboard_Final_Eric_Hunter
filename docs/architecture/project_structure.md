# Project Structure

## Layout

```text
weather_dashboard/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── src/                       # Source code
│   ├── models/               # Data models
│   ├── services/             # Business logic
│   ├── ui/                   # User interface
│   └── utils/                # Utilities
├── docs/                     # Documentation
├── tests/                    # Test suite
├── config/                   # Configuration
└── data/                     # Application data
```

## Architecture Benefits

- **Modular Design**: Component-based architecture with clear separation
- **Maintainability**: 82% reduction in main GUI file size (3,500+ → 649 lines)
- **Reusability**: Standardized widgets and components
- **Type Safety**: Comprehensive type hints throughout
- **Testability**: Components can be tested in isolation

## Component Layers

- **Styles**: Glassmorphic design system
- **Widgets**: Reusable UI components
- **Animations**: Visual effects and transitions
- **Components**: Weather-specific UI elements

## Usage

```bash
python main.py
```

## Features

- Real-time weather data and 5-day forecast
- City comparison and weather journal
- Activity suggestions and data visualization
- Export functionality

## Dependencies

- `tkinter`, `requests`, `sqlite3`, `matplotlib`, `Pillow`

---

For detailed documentation, see the `docs/` directory.
