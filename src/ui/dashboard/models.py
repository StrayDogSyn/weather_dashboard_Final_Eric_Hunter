"""Data models and configuration for dashboard UI.

This module contains all data structures, enums, and configuration classes
used by the main dashboard interface.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List


class DashboardSection(Enum):
    """Dashboard section identifiers for navigation and layout management.

    This enum supports modular dashboard design with clear
    section separation and navigation.
    """
    OVERVIEW = "overview"
    TEMPERATURE_GRAPH = "temperature_graph"
    WEATHER_JOURNAL = "weather_journal"
    ACTIVITY_SUGGESTER = "activity_suggester"
    TEAM_COLLABORATION = "team_collaboration"
    SETTINGS = "settings"


@dataclass
class DashboardConfig:
    """Configuration for dashboard appearance and behavior."""
    auto_refresh: bool = True
    refresh_interval: int = 300  # seconds
    show_sidebar: bool = True
    compact_mode: bool = False
    enable_animations: bool = True
    default_section: DashboardSection = DashboardSection.OVERVIEW
    
    # Layout settings
    sidebar_width: int = 250
    header_height: int = 80
    footer_height: int = 40
    content_padding: int = 20
    
    # Theme settings
    use_weather_themes: bool = True
    glassmorphism_enabled: bool = True
    background_blur: int = 20
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'auto_refresh': self.auto_refresh,
            'refresh_interval': self.refresh_interval,
            'show_sidebar': self.show_sidebar,
            'compact_mode': self.compact_mode,
            'enable_animations': self.enable_animations,
            'default_section': self.default_section.value,
            'sidebar_width': self.sidebar_width,
            'header_height': self.header_height,
            'footer_height': self.footer_height,
            'content_padding': self.content_padding,
            'use_weather_themes': self.use_weather_themes,
            'glassmorphism_enabled': self.glassmorphism_enabled,
            'background_blur': self.background_blur
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardConfig':
        """Create from dictionary."""
        return cls(
            auto_refresh=data.get('auto_refresh', True),
            refresh_interval=data.get('refresh_interval', 300),
            show_sidebar=data.get('show_sidebar', True),
            compact_mode=data.get('compact_mode', False),
            enable_animations=data.get('enable_animations', True),
            default_section=DashboardSection(data.get('default_section', DashboardSection.OVERVIEW.value)),
            sidebar_width=data.get('sidebar_width', 250),
            header_height=data.get('header_height', 80),
            footer_height=data.get('footer_height', 40),
            content_padding=data.get('content_padding', 20),
            use_weather_themes=data.get('use_weather_themes', True),
            glassmorphism_enabled=data.get('glassmorphism_enabled', True),
            background_blur=data.get('background_blur', 20)
        )


@dataclass
class NavigationItem:
    """Navigation item for dashboard sidebar."""
    section: DashboardSection
    title: str
    icon: str
    description: Optional[str] = None
    shortcut: Optional[str] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'section': self.section.value,
            'title': self.title,
            'icon': self.icon,
            'description': self.description,
            'shortcut': self.shortcut,
            'enabled': self.enabled
        }


@dataclass
class DashboardState:
    """Current state of the dashboard."""
    current_section: DashboardSection = DashboardSection.OVERVIEW
    sidebar_collapsed: bool = False
    loading: bool = False
    last_refresh: Optional[str] = None
    error_message: Optional[str] = None
    notifications: List[str] = None
    
    def __post_init__(self):
        if self.notifications is None:
            self.notifications = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'current_section': self.current_section.value,
            'sidebar_collapsed': self.sidebar_collapsed,
            'loading': self.loading,
            'last_refresh': self.last_refresh,
            'error_message': self.error_message,
            'notifications': self.notifications
        }