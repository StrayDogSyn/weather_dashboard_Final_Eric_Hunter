"""Common UI Components

Shared UI components used across the application.
"""

from .header import HeaderComponent
from .search_bar import SearchBar
from .status_bar_component import StatusBarComponent
from .loading_spinner import LoadingSpinner, ShimmerLoader, ProgressSpinner
from .error_display import ErrorDisplay, InlineErrorDisplay

# Alias for backward compatibility
Header = HeaderComponent

__all__ = [
    "Header",
    "HeaderComponent",
    "SearchBar", 
    "StatusBarComponent",
    "LoadingSpinner",
    "ShimmerLoader",
    "ProgressSpinner",
    "ErrorDisplay",
    "InlineErrorDisplay"
]
