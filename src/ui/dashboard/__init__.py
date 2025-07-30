"""Weather Dashboard Package

Modular weather dashboard implementation using mixin architecture.
Provides a clean separation of concerns while maintaining backward compatibility.

Package Structure:
- base_dashboard.py: Shared utilities and constants
- window_mixin.py: Window management (~150 lines)
- layout_mixin.py: UI layout and components (~200 lines)
- event_mixin.py: Event handling (~100 lines)
- search_mixin.py: Search functionality (~200 lines)
- weather_mixin.py: Weather operations (~200 lines)
- status_mixin.py: Status and loading management (~100 lines)
- weather_dashboard.py: Main coordinator (~50 lines)

Total: ~1000 lines split into 8 focused modules (125 lines average)
Original: 998 lines in single file
"""

from .weather_dashboard import WeatherDashboard, create_weather_dashboard

# Export main classes for backward compatibility
__all__ = [
    'WeatherDashboard',
    'create_weather_dashboard'
]

# Version information
__version__ = '2.0.0'
__author__ = 'JTC Capstone Team'
__description__ = 'Modular Weather Dashboard Application'

# Package metadata
PACKAGE_INFO = {
    'name': 'weather_dashboard',
    'version': __version__,
    'description': __description__,
    'author': __author__,
    'architecture': 'mixin-based',
    'modules': {
        'base_dashboard': 'Shared utilities and constants',
        'window_mixin': 'Window management and configuration',
        'layout_mixin': 'UI layout and component creation',
        'event_mixin': 'Event handling and user interactions',
        'search_mixin': 'Search functionality and location detection',
        'weather_mixin': 'Weather data operations',
        'status_mixin': 'Status updates and loading states',
        'weather_dashboard': 'Main application coordinator'
    },
    'benefits': [
        'Single responsibility principle',
        'Improved maintainability',
        'Better testability',
        'Reduced file complexity',
        'Modular architecture',
        'Zero breaking changes'
    ]
}


def get_package_info():
    """Get package information and statistics."""
    return PACKAGE_INFO


def print_package_info():
    """Print package information to console."""
    info = get_package_info()
    print(f"\n{info['name']} v{info['version']}")
    print(f"Description: {info['description']}")
    print(f"Architecture: {info['architecture']}")
    print("\nModules:")
    for module, description in info['modules'].items():
        print(f"  - {module}: {description}")
    print("\nBenefits:")
    for benefit in info['benefits']:
        print(f"  ✓ {benefit}")
    print()


if __name__ == '__main__':
    print_package_info()