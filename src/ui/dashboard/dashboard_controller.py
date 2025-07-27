"""Dashboard controller for managing UI state and navigation.

This module handles dashboard business logic, navigation management,
and UI state coordination.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import threading

from .models import DashboardSection, DashboardConfig, DashboardState, NavigationItem


class DashboardController:
    """Controller for managing dashboard state and navigation."""

    def __init__(self, app_controller, config: Optional[DashboardConfig] = None):
        self.app_controller = app_controller
        self.config = config or DashboardConfig()
        self.logger = logging.getLogger(__name__)
        
        # Dashboard state
        self.state = DashboardState()
        
        # Navigation items
        self.navigation_items = self._create_navigation_items()
        
        # Auto-refresh timer
        self.refresh_timer: Optional[threading.Timer] = None
        
        # Callbacks
        self.on_section_changed: Optional[Callable[[DashboardSection], None]] = None
        self.on_state_updated: Optional[Callable[[DashboardState], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    def initialize(self):
        """Initialize the dashboard controller."""
        try:
            # Set initial section
            self.navigate_to_section(self.config.default_section)
            
            # Start auto-refresh if enabled
            if self.config.auto_refresh:
                self.start_auto_refresh()
                
            self.logger.info("Dashboard controller initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing dashboard controller: {e}")
            self._handle_error(f"Failed to initialize dashboard: {e}")

    def navigate_to_section(self, section: DashboardSection):
        """Navigate to a specific dashboard section."""
        try:
            if section != self.state.current_section:
                self.logger.info(f"Navigating to section: {section.value}")
                
                old_section = self.state.current_section
                self.state.current_section = section
                
                # Trigger section change callback
                if self.on_section_changed:
                    self.on_section_changed(section)
                
                # Update state
                self._update_state()
                
                self.logger.debug(f"Navigation completed: {old_section.value} -> {section.value}")
                
        except Exception as e:
            self.logger.error(f"Error navigating to section {section}: {e}")
            self._handle_error(f"Navigation failed: {e}")

    def toggle_sidebar(self):
        """Toggle sidebar collapsed state."""
        self.state.sidebar_collapsed = not self.state.sidebar_collapsed
        self._update_state()
        self.logger.debug(f"Sidebar toggled: collapsed={self.state.sidebar_collapsed}")

    def refresh_dashboard(self):
        """Refresh dashboard data."""
        try:
            self.state.loading = True
            self.state.error_message = None
            self._update_state()
            
            # Trigger app controller refresh
            if self.app_controller:
                self.app_controller.refresh_all_data()
            
            self.state.last_refresh = datetime.now().strftime("%H:%M:%S")
            self.state.loading = False
            self._update_state()
            
            self.logger.info("Dashboard refreshed successfully")
            
        except Exception as e:
            self.state.loading = False
            self.state.error_message = str(e)
            self._update_state()
            self.logger.error(f"Error refreshing dashboard: {e}")
            self._handle_error(f"Refresh failed: {e}")

    def add_notification(self, message: str):
        """Add a notification message."""
        self.state.notifications.append(message)
        self._update_state()
        self.logger.info(f"Notification added: {message}")

    def clear_notifications(self):
        """Clear all notifications."""
        self.state.notifications.clear()
        self._update_state()
        self.logger.debug("Notifications cleared")

    def update_config(self, new_config: DashboardConfig):
        """Update dashboard configuration."""
        old_auto_refresh = self.config.auto_refresh
        self.config = new_config
        
        # Restart auto-refresh if setting changed
        if not old_auto_refresh and new_config.auto_refresh:
            self.start_auto_refresh()
        elif old_auto_refresh and not new_config.auto_refresh:
            self.stop_auto_refresh()
            
        self.logger.info("Dashboard configuration updated")

    def start_auto_refresh(self):
        """Start automatic dashboard refresh."""
        if self.config.auto_refresh:
            self._schedule_refresh()
            self.logger.debug(f"Auto-refresh started: {self.config.refresh_interval}s interval")

    def stop_auto_refresh(self):
        """Stop automatic dashboard refresh."""
        if self.refresh_timer:
            self.refresh_timer.cancel()
            self.refresh_timer = None
            self.logger.debug("Auto-refresh stopped")

    def get_navigation_items(self) -> List[NavigationItem]:
        """Get list of navigation items."""
        return self.navigation_items

    def get_current_section_info(self) -> Dict[str, Any]:
        """Get information about the current section."""
        current_item = None
        for item in self.navigation_items:
            if item.section == self.state.current_section:
                current_item = item
                break
        
        return {
            'section': self.state.current_section,
            'title': current_item.title if current_item else "Unknown",
            'icon': current_item.icon if current_item else "❓",
            'description': current_item.description if current_item else None
        }

    def is_section_enabled(self, section: DashboardSection) -> bool:
        """Check if a section is enabled."""
        for item in self.navigation_items:
            if item.section == section:
                return item.enabled
        return False

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        return {
            'current_section': self.state.current_section.value,
            'total_sections': len(self.navigation_items),
            'enabled_sections': len([item for item in self.navigation_items if item.enabled]),
            'last_refresh': self.state.last_refresh,
            'notifications_count': len(self.state.notifications),
            'auto_refresh_enabled': self.config.auto_refresh,
            'refresh_interval': self.config.refresh_interval
        }

    def handle_keyboard_shortcut(self, shortcut: str) -> bool:
        """Handle keyboard shortcuts for navigation."""
        for item in self.navigation_items:
            if item.shortcut == shortcut and item.enabled:
                self.navigate_to_section(item.section)
                return True
        return False

    def search_sections(self, query: str) -> List[NavigationItem]:
        """Search sections by title or description."""
        query_lower = query.lower()
        results = []
        
        for item in self.navigation_items:
            if (query_lower in item.title.lower() or 
                (item.description and query_lower in item.description.lower())):
                results.append(item)
        
        return results

    def _create_navigation_items(self) -> List[NavigationItem]:
        """Create default navigation items."""
        return [
            NavigationItem(
                section=DashboardSection.OVERVIEW,
                title="Dashboard Overview",
                icon="🏠",
                description="Main dashboard with weather overview",
                shortcut="Ctrl+1"
            ),
            NavigationItem(
                section=DashboardSection.TEMPERATURE_GRAPH,
                title="Temperature Graph",
                icon="📈",
                description="Interactive temperature visualization",
                shortcut="Ctrl+2"
            ),
            NavigationItem(
                section=DashboardSection.WEATHER_JOURNAL,
                title="Weather Journal",
                icon="📝",
                description="Weather diary and notes",
                shortcut="Ctrl+3"
            ),
            NavigationItem(
                section=DashboardSection.ACTIVITY_SUGGESTER,
                title="Activity Suggester",
                icon="🎯",
                description="AI-powered activity recommendations",
                shortcut="Ctrl+4"
            ),
            NavigationItem(
                section=DashboardSection.TEAM_COLLABORATION,
                title="Team Collaboration",
                icon="👥",
                description="Share weather data with team",
                shortcut="Ctrl+5"
            ),
            NavigationItem(
                section=DashboardSection.SETTINGS,
                title="Settings",
                icon="⚙️",
                description="Application settings and preferences",
                shortcut="Ctrl+,"
            )
        ]

    def _schedule_refresh(self):
        """Schedule the next automatic refresh."""
        if self.config.auto_refresh:
            self.refresh_timer = threading.Timer(
                self.config.refresh_interval,
                self._auto_refresh_callback
            )
            self.refresh_timer.start()

    def _auto_refresh_callback(self):
        """Callback for automatic refresh timer."""
        self.refresh_dashboard()
        self._schedule_refresh()

    def _update_state(self):
        """Update dashboard state and notify listeners."""
        if self.on_state_updated:
            self.on_state_updated(self.state)

    def _handle_error(self, error_message: str):
        """Handle error and notify listeners."""
        self.state.error_message = error_message
        self._update_state()
        
        if self.on_error:
            self.on_error(error_message)

    def cleanup(self):
        """Cleanup resources."""
        self.stop_auto_refresh()
        self.logger.info("Dashboard controller cleaned up")