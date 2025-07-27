"""Team collaboration feature for sharing weather data and city comparisons.

This module provides a comprehensive team collaboration interface that integrates with
GitHub for sharing city weather data, creating team comparisons, and tracking team activity.
"""

import json
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import uuid
import threading
import webbrowser

from ..ui.components.base_components import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry, GlassProgressBar
)
from ..services.github_service import (
    GitHubService, TeamMember, CityData, TeamComparison
)
from ..utils.logger import LoggerMixin


@dataclass
class CollaborationConfig:
    """Configuration for team collaboration features."""
    auto_sync: bool = True
    sync_interval: int = 300  # seconds
    max_cities_display: int = 50
    max_comparisons_display: int = 20
    enable_notifications: bool = True
    default_comparison_metrics: List[str] = None

    def __post_init__(self):
        if self.default_comparison_metrics is None:
            self.default_comparison_metrics = [
                "temperature", "humidity", "wind_speed", "pressure"
            ]


class TeamCollaborationWidget(ctk.CTkFrame, LoggerMixin):
    """Team collaboration widget for weather data sharing."""

    def __init__(self, parent, github_service: GitHubService, **kwargs):
        """Initialize team collaboration widget.

        Args:
            parent: Parent widget
            github_service: GitHub service instance
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)

        self.github_service = github_service
        self.config = CollaborationConfig()

        # Data storage
        self.team_members: List[TeamMember] = []
        self.shared_cities: List[CityData] = []
        self.team_comparisons: List[TeamComparison] = []
        self.current_weather_data: Optional[Dict[str, Any]] = None

        # UI state
        self.selected_cities: List[str] = []
        self.comparison_metrics: List[str] = self.config.default_comparison_metrics.copy()

        # Callbacks
        self.on_city_selected: Optional[Callable[[str], None]] = None
        self.on_comparison_created: Optional[Callable[[TeamComparison], None]] = None

        # Auto-sync timer
        self.sync_timer = None

        # Setup UI
        self._setup_ui()

        # Initial data load
        self._load_initial_data()

        # Start auto-sync if enabled
        if self.config.auto_sync:
            self._start_auto_sync()

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self._create_header()

        # Main content with tabs
        self._create_main_content()

        # Status bar
        self._create_status_bar()

    def _create_header(self):
        """Create header with connection status and controls."""
        header_frame = GlassFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = GlassLabel(
            header_frame,
            text="🤝 CodeFront Team Collaboration",
            font=("Segoe UI", 18, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        # Connection status
        self.status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.status_frame.grid(row=0, column=1, sticky="e", padx=10, pady=10)

        self.connection_label = GlassLabel(
            self.status_frame,
            text="🔴 Disconnected",
            font=("Segoe UI", 12)
        )
        self.connection_label.pack(side="left", padx=(0, 10))

        # Sync button
        self.sync_button = GlassButton(
            self.status_frame,
            text="🔄 Sync",
            width=80,
            command=self._manual_sync
        )
        self.sync_button.pack(side="left", padx=(0, 10))

        # Settings button
        settings_button = GlassButton(
            self.status_frame,
            text="⚙️ Settings",
            width=90,
            command=self._show_settings
        )
        settings_button.pack(side="left")

        # Update connection status
        self._update_connection_status()

    def _create_main_content(self):
        """Create main content area with tabs."""
        # Tab view
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Create tabs
        self.team_tab = self.tab_view.add("👥 Team")
        self.cities_tab = self.tab_view.add("🏙️ Cities")
        self.comparisons_tab = self.tab_view.add("📊 Comparisons")
        self.activity_tab = self.tab_view.add("📈 Activity")

        # Setup tab content
        self._setup_team_tab()
        self._setup_cities_tab()
        self._setup_comparisons_tab()
        self._setup_activity_tab()

    def _setup_team_tab(self):
        """Setup team members tab."""
        # Configure grid
        self.team_tab.grid_columnconfigure(0, weight=1)
        self.team_tab.grid_rowconfigure(1, weight=1)

        # Header
        team_header = ctk.CTkFrame(self.team_tab, fg_color="transparent")
        team_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        team_header.grid_columnconfigure(1, weight=1)

        team_title = GlassLabel(
            team_header,
            text="Team Members",
            font=("Segoe UI", 16, "bold")
        )
        team_title.grid(row=0, column=0, sticky="w")

        # Member count
        self.member_count_label = GlassLabel(
            team_header,
            text="0 members",
            font=("Segoe UI", 12)
        )
        self.member_count_label.grid(row=0, column=1, sticky="e")

        # Members list
        self.members_frame = ctk.CTkScrollableFrame(self.team_tab)
        self.members_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.members_frame.grid_columnconfigure(0, weight=1)

    def _setup_cities_tab(self):
        """Setup shared cities tab."""
        # Configure grid
        self.cities_tab.grid_columnconfigure(0, weight=1)
        self.cities_tab.grid_rowconfigure(2, weight=1)

        # Header with controls
        cities_header = ctk.CTkFrame(self.cities_tab, fg_color="transparent")
        cities_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        cities_header.grid_columnconfigure(1, weight=1)

        cities_title = GlassLabel(
            cities_header,
            text="Shared Cities",
            font=("Segoe UI", 16, "bold")
        )
        cities_title.grid(row=0, column=0, sticky="w")

        # City controls
        city_controls = ctk.CTkFrame(cities_header, fg_color="transparent")
        city_controls.grid(row=0, column=1, sticky="e")

        share_button = GlassButton(
            city_controls,
            text="📤 Share Current",
            width=120,
            command=self._share_current_city
        )
        share_button.pack(side="left", padx=(0, 10))

        import_button = GlassButton(
            city_controls,
            text="📥 Import",
            width=80,
            command=self._import_cities
        )
        import_button.pack(side="left")

        # Search bar
        search_frame = ctk.CTkFrame(self.cities_tab, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        search_frame.grid_columnconfigure(1, weight=1)

        search_label = GlassLabel(search_frame, text="🔍 Search:")
        search_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.city_search_var = ctk.StringVar()
        self.city_search_var.trace("w", self._on_city_search_changed)

        search_entry = GlassEntry(
            search_frame,
            textvariable=self.city_search_var,
            placeholder_text="Search cities..."
        )
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # Filter buttons
        filter_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        filter_frame.grid(row=0, column=2, sticky="e")

        self.show_favorites_var = ctk.BooleanVar()
        favorites_check = ctk.CTkCheckBox(
            filter_frame,
            text="⭐ Favorites",
            variable=self.show_favorites_var,
            command=self._update_cities_display
        )
        favorites_check.pack(side="left", padx=(0, 10))

        # Cities list
        self.cities_frame = ctk.CTkScrollableFrame(self.cities_tab)
        self.cities_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.cities_frame.grid_columnconfigure(0, weight=1)

    def _setup_comparisons_tab(self):
        """Setup team comparisons tab."""
        # Configure grid
        self.comparisons_tab.grid_columnconfigure(0, weight=1)
        self.comparisons_tab.grid_rowconfigure(2, weight=1)

        # Header
        comp_header = ctk.CTkFrame(self.comparisons_tab, fg_color="transparent")
        comp_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        comp_header.grid_columnconfigure(1, weight=1)

        comp_title = GlassLabel(
            comp_header,
            text="Team Comparisons",
            font=("Segoe UI", 16, "bold")
        )
        comp_title.grid(row=0, column=0, sticky="w")

        # Comparison controls
        comp_controls = ctk.CTkFrame(comp_header, fg_color="transparent")
        comp_controls.grid(row=0, column=1, sticky="e")

        create_button = GlassButton(
            comp_controls,
            text="➕ New Comparison",
            width=140,
            command=self._create_new_comparison
        )
        create_button.pack(side="left")

        # Quick comparison setup
        quick_frame = GlassFrame(self.comparisons_tab)
        quick_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        quick_frame.grid_columnconfigure(1, weight=1)

        quick_label = GlassLabel(
            quick_frame,
            text="Quick Compare:",
            font=("Segoe UI", 12, "bold")
        )
        quick_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        # Selected cities display
        self.selected_cities_frame = ctk.CTkFrame(quick_frame, fg_color="transparent")
        self.selected_cities_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

        compare_button = GlassButton(
            quick_frame,
            text="📊 Compare",
            width=100,
            command=self._quick_compare,
            state="disabled"
        )
        compare_button.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        self.quick_compare_button = compare_button

        # Comparisons list
        self.comparisons_frame = ctk.CTkScrollableFrame(self.comparisons_tab)
        self.comparisons_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.comparisons_frame.grid_columnconfigure(0, weight=1)

    def _setup_activity_tab(self):
        """Setup team activity tab."""
        # Configure grid
        self.activity_tab.grid_columnconfigure(0, weight=1)
        self.activity_tab.grid_rowconfigure(1, weight=1)

        # Header
        activity_header = ctk.CTkFrame(self.activity_tab, fg_color="transparent")
        activity_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        activity_header.grid_columnconfigure(1, weight=1)

        activity_title = GlassLabel(
            activity_header,
            text="Team Activity",
            font=("Segoe UI", 16, "bold")
        )
        activity_title.grid(row=0, column=0, sticky="w")

        # Time range selector
        time_frame = ctk.CTkFrame(activity_header, fg_color="transparent")
        time_frame.grid(row=0, column=1, sticky="e")

        time_label = GlassLabel(time_frame, text="Period:")
        time_label.pack(side="left", padx=(0, 5))

        self.time_range_var = ctk.StringVar(value="7 days")
        time_menu = ctk.CTkOptionMenu(
            time_frame,
            values=["1 day", "7 days", "30 days", "90 days"],
            variable=self.time_range_var,
            command=self._update_activity_display
        )
        time_menu.pack(side="left")

        # Activity content
        self.activity_content = ctk.CTkScrollableFrame(self.activity_tab)
        self.activity_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.activity_content.grid_columnconfigure(0, weight=1)

    def _create_status_bar(self):
        """Create status bar."""
        status_frame = GlassFrame(self)
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_columnconfigure(1, weight=1)

        # Status label
        self.status_label = GlassLabel(
            status_frame,
            text="Ready",
            font=("Segoe UI", 10)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        # Last sync time
        self.last_sync_label = GlassLabel(
            status_frame,
            text="Never synced",
            font=("Segoe UI", 10)
        )
        self.last_sync_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)

    def _load_initial_data(self):
        """Load initial data from GitHub."""
        if not self.github_service.is_connected():
            self._update_status("GitHub not connected")
            return

        def load_data():
            try:
                self._update_status("Loading team data...")

                # Load team members
                self.team_members = self.github_service.get_team_members()

                # Load shared cities
                self.shared_cities = self.github_service.get_shared_cities()

                # Load team comparisons
                self.team_comparisons = self.github_service.get_team_comparisons()

                # Update UI on main thread
                self.after(0, self._update_all_displays)
                self.after(0, lambda: self._update_status("Data loaded successfully"))

            except Exception as e:
                self.logger.error(f"Error loading initial data: {e}")
                self.after(0, lambda: self._update_status(f"Error loading data: {e}"))

        # Load data in background thread
        threading.Thread(target=load_data, daemon=True).start()

    def _update_all_displays(self):
        """Update all UI displays with current data."""
        self._update_team_display()
        self._update_cities_display()
        self._update_comparisons_display()
        self._update_activity_display()
        self._update_connection_status()

    def _update_connection_status(self):
        """Update connection status display."""
        if self.github_service.is_connected():
            self.connection_label.configure(
                text="🟢 Connected",
                text_color="#4CAF50"
            )
        else:
            self.connection_label.configure(
                text="🔴 Disconnected",
                text_color="#F44336"
            )

    def _update_team_display(self):
        """Update team members display."""
        # Clear existing content
        for widget in self.members_frame.winfo_children():
            widget.destroy()

        # Update member count
        count = len(self.team_members)
        self.member_count_label.configure(text=f"{count} member{'s' if count != 1 else ''}")

        # Display members
        for i, member in enumerate(self.team_members):
            member_card = self._create_member_card(self.members_frame, member)
            member_card.grid(row=i, column=0, sticky="ew", pady=2)

    def _create_member_card(self, parent, member: TeamMember) -> ctk.CTkFrame:
        """Create a member card widget."""
        card = GlassFrame(parent)
        card.grid_columnconfigure(1, weight=1)

        # Avatar (placeholder)
        avatar_label = GlassLabel(
            card,
            text="👤",
            font=("Segoe UI", 20)
        )
        avatar_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        # Member info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(10, 5))
        info_frame.grid_columnconfigure(0, weight=1)

        # Name and username
        name_label = GlassLabel(
            info_frame,
            text=member.name,
            font=("Segoe UI", 14, "bold")
        )
        name_label.grid(row=0, column=0, sticky="w")

        username_label = GlassLabel(
            info_frame,
            text=f"@{member.username}",
            font=("Segoe UI", 11),
            text_color="#888888"
        )
        username_label.grid(row=1, column=0, sticky="w")

        # Role badge
        role_colors = {
            "admin": "#FF5722",
            "maintainer": "#FF9800",
            "member": "#2196F3"
        }

        role_label = GlassLabel(
            info_frame,
            text=member.role.title(),
            font=("Segoe UI", 10),
            text_color=role_colors.get(member.role, "#757575")
        )
        role_label.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Stats
        stats_frame = ctk.CTkFrame(card, fg_color="transparent")
        stats_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))

        stats_text = f"🏙️ {member.cities_shared} cities • 📊 {member.contributions} contributions"
        stats_label = GlassLabel(
            stats_frame,
            text=stats_text,
            font=("Segoe UI", 10),
            text_color="#666666"
        )
        stats_label.pack(anchor="w")

        return card

    def _update_comparisons_display(self):
        """Update team comparisons display."""
        # Clear existing content
        for widget in self.comparisons_frame.winfo_children():
            widget.destroy()

        # Display comparisons
        for i, comparison in enumerate(self.team_comparisons[:self.config.max_comparisons_display]):
            comp_card = self._create_comparison_card(self.comparisons_frame, comparison)
            comp_card.grid(row=i, column=0, sticky="ew", pady=2)

    def _create_comparison_card(self, parent, comparison: TeamComparison) -> ctk.CTkFrame:
        """Create a comparison card widget."""
        card = GlassFrame(parent)
        card.grid_columnconfigure(1, weight=1)

        # Comparison icon
        icon_label = GlassLabel(
            card,
            text="📊",
            font=("Segoe UI", 16)
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        # Comparison info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(10, 5))
        info_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = GlassLabel(
            info_frame,
            text=comparison.title,
            font=("Segoe UI", 14, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Cities count and metrics
        cities_count = len(comparison.cities)
        metrics_count = len(comparison.metrics)
        details_text = f"{cities_count} cities • {metrics_count} metrics"

        details_label = GlassLabel(
            info_frame,
            text=details_text,
            font=("Segoe UI", 11),
            text_color="#666666"
        )
        details_label.grid(row=1, column=0, sticky="w")

        # Action buttons
        actions_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=1, rowspan=2, sticky="e")

        # View comparison
        view_button = GlassButton(
            actions_frame,
            text="👁️ View",
            width=70,
            height=28,
            command=lambda c=comparison: self._view_comparison(c)
        )
        view_button.pack(side="top", pady=(0, 5))

        # Export comparison
        export_button = GlassButton(
            actions_frame,
            text="💾 Export",
            width=70,
            height=28,
            command=lambda c=comparison: self._export_comparison(c)
        )
        export_button.pack(side="top")

        # Meta info
        meta_frame = ctk.CTkFrame(card, fg_color="transparent")
        meta_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))

        # Created by and date
        created_text = f"Created by {comparison.created_by} • {self._format_date(comparison.created_at)}"
        created_label = GlassLabel(
            meta_frame,
            text=created_text,
            font=("Segoe UI", 9),
            text_color="#888888"
        )
        created_label.pack(anchor="w")

        return card

    def _update_activity_display(self, *args):
        """Update team activity display."""
        # Clear existing content
        for widget in self.activity_content.winfo_children():
            widget.destroy()

        # Get time range
        time_range = self.time_range_var.get()
        days = int(time_range.split()[0])

        # Load activity data
        def load_activity():
            try:
                activity_data = self.github_service.get_team_activity(days=days)
                self.after(0, lambda: self._display_activity_data(activity_data))
            except Exception as e:
                self.logger.error(f"Error loading activity data: {e}")
                self.after(0, lambda: self._display_activity_error(str(e)))

        # Show loading
        loading_label = GlassLabel(
            self.activity_content,
            text="📊 Loading activity data...",
            font=("Segoe UI", 12)
        )
        loading_label.pack(pady=20)

        # Load in background
        threading.Thread(target=load_activity, daemon=True).start()

    def _display_activity_data(self, activity_data: List[Dict[str, Any]]):
        """Display activity data."""
        # Clear loading message
        for widget in self.activity_content.winfo_children():
            widget.destroy()

        if not activity_data:
            no_data_label = GlassLabel(
                self.activity_content,
                text="📭 No activity data available",
                font=("Segoe UI", 12),
                text_color="#888888"
            )
            no_data_label.pack(pady=20)
            return

        # Display activity items
        for i, activity in enumerate(activity_data):
            activity_card = self._create_activity_card(self.activity_content, activity)
            activity_card.pack(fill="x", padx=5, pady=2)

    def _create_activity_card(self, parent, activity: Dict[str, Any]) -> ctk.CTkFrame:
        """Create an activity card widget."""
        card = GlassFrame(parent)
        card.grid_columnconfigure(1, weight=1)

        # Activity type icon
        icons = {
            "city_shared": "🏙️",
            "comparison_created": "📊",
            "data_updated": "🔄",
            "member_joined": "👋",
            "default": "📝"
        }

        icon = icons.get(activity.get("type", "default"), icons["default"])
        icon_label = GlassLabel(
            card,
            text=icon,
            font=("Segoe UI", 14)
        )
        icon_label.grid(row=0, column=0, padx=10, pady=10)

        # Activity details
        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        details_frame.grid_columnconfigure(0, weight=1)

        # Description
        desc_label = GlassLabel(
            details_frame,
            text=activity.get("description", "Unknown activity"),
            font=("Segoe UI", 12)
        )
        desc_label.grid(row=0, column=0, sticky="w")

        # Timestamp and user
        timestamp = activity.get("timestamp", datetime.now())
        user = activity.get("user", "Unknown")
        meta_text = f"{user} • {self._format_date(timestamp)}"

        meta_label = GlassLabel(
            details_frame,
            text=meta_text,
            font=("Segoe UI", 10),
            text_color="#888888"
        )
        meta_label.grid(row=1, column=0, sticky="w")

        return card

    def _display_activity_error(self, error_message: str):
        """Display activity loading error."""
        # Clear loading message
        for widget in self.activity_content.winfo_children():
            widget.destroy()

        error_label = GlassLabel(
            self.activity_content,
            text=f"❌ Error loading activity: {error_message}",
            font=("Segoe UI", 12),
            text_color="#F44336"
        )
        error_label.pack(pady=20)

    def _manual_sync(self):
        """Manually sync data with GitHub."""
        if not self.github_service.is_connected():
            messagebox.showerror("Error", "GitHub not connected")
            return

        def sync_data():
            try:
                self._update_status("Syncing with GitHub...")

                # Sync all data
                self.team_members = self.github_service.get_team_members()
                self.shared_cities = self.github_service.get_shared_cities()
                self.team_comparisons = self.github_service.get_team_comparisons()

                # Update UI
                self.after(0, self._update_all_displays)
                self.after(0, lambda: self._update_status("Sync completed"))
                self.after(0, self._update_last_sync)

            except Exception as e:
                self.logger.error(f"Error during manual sync: {e}")
                self.after(0, lambda: self._update_status(f"Sync failed: {e}"))
                self.after(0, lambda: messagebox.showerror("Sync Error", str(e)))

        # Sync in background
        threading.Thread(target=sync_data, daemon=True).start()

    def _start_auto_sync(self):
        """Start automatic sync timer."""
        if self.sync_timer:
            self.after_cancel(self.sync_timer)

        def auto_sync():
            if self.config.auto_sync and self.github_service.is_connected():
                self._manual_sync()

            # Schedule next sync
            if self.config.auto_sync:
                self.sync_timer = self.after(
                    self.config.sync_interval * 1000,
                    auto_sync
                )

        # Start timer
        self.sync_timer = self.after(
            self.config.sync_interval * 1000,
            auto_sync
        )

    def _show_settings(self):
        """Show collaboration settings dialog."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Team Collaboration Settings")
        settings_window.geometry("400x500")
        settings_window.transient(self)
        settings_window.grab_set()

        # Center window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (500 // 2)
        settings_window.geometry(f"400x500+{x}+{y}")

        # Settings content
        content_frame = ctk.CTkScrollableFrame(settings_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Auto-sync setting
        auto_sync_var = ctk.BooleanVar(value=self.config.auto_sync)
        auto_sync_check = ctk.CTkCheckBox(
            content_frame,
            text="Enable automatic sync",
            variable=auto_sync_var
        )
        auto_sync_check.pack(anchor="w", pady=(0, 10))

        # Sync interval
        interval_label = ctk.CTkLabel(content_frame, text="Sync interval (seconds):")
        interval_label.pack(anchor="w", pady=(10, 5))

        interval_var = ctk.StringVar(value=str(self.config.sync_interval))
        interval_entry = ctk.CTkEntry(content_frame, textvariable=interval_var)
        interval_entry.pack(fill="x", pady=(0, 10))

        # Max displays
        max_cities_label = ctk.CTkLabel(content_frame, text="Max cities to display:")
        max_cities_label.pack(anchor="w", pady=(10, 5))

        max_cities_var = ctk.StringVar(value=str(self.config.max_cities_display))
        max_cities_entry = ctk.CTkEntry(content_frame, textvariable=max_cities_var)
        max_cities_entry.pack(fill="x", pady=(0, 10))

        # Notifications
        notifications_var = ctk.BooleanVar(value=self.config.enable_notifications)
        notifications_check = ctk.CTkCheckBox(
            content_frame,
            text="Enable notifications",
            variable=notifications_var
        )
        notifications_check.pack(anchor="w", pady=(10, 10))

        # Comparison metrics
        metrics_label = ctk.CTkLabel(content_frame, text="Default comparison metrics:")
        metrics_label.pack(anchor="w", pady=(10, 5))

        metrics_frame = ctk.CTkFrame(content_frame)
        metrics_frame.pack(fill="x", pady=(0, 10))

        available_metrics = [
            "temperature", "humidity", "wind_speed", "pressure",
            "visibility", "uv_index", "feels_like"
        ]

        metrics_vars = {}
        for metric in available_metrics:
            var = ctk.BooleanVar(value=metric in self.config.default_comparison_metrics)
            metrics_vars[metric] = var

            check = ctk.CTkCheckBox(
                metrics_frame,
                text=metric.replace("_", " ").title(),
                variable=var
            )
            check.pack(anchor="w", padx=10, pady=2)

        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        def save_settings():
            try:
                # Update config
                self.config.auto_sync = auto_sync_var.get()
                self.config.sync_interval = int(interval_var.get())
                self.config.max_cities_display = int(max_cities_var.get())
                self.config.enable_notifications = notifications_var.get()

                # Update metrics
                self.config.default_comparison_metrics = [
                    metric for metric, var in metrics_vars.items()
                    if var.get()
                ]

                # Restart auto-sync if needed
                if self.config.auto_sync:
                    self._start_auto_sync()
                elif self.sync_timer:
                    self.after_cancel(self.sync_timer)
                    self.sync_timer = None

                settings_window.destroy()
                messagebox.showinfo("Settings", "Settings saved successfully")

            except ValueError as e:
                messagebox.showerror("Error", "Invalid numeric value")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving settings: {e}")

        save_button = ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_settings
        )
        save_button.pack(side="right", padx=(10, 0))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=settings_window.destroy
        )
        cancel_button.pack(side="right")

    def _share_current_city(self):
        """Share current city weather data."""
        if not self.current_weather_data:
            messagebox.showwarning("Warning", "No current weather data to share")
            return

        if not self.github_service.is_connected():
            messagebox.showerror("Error", "GitHub not connected")
            return

        # Create share dialog
        share_window = ctk.CTkToplevel(self)
        share_window.title("Share City")
        share_window.geometry("400x300")
        share_window.transient(self)
        share_window.grab_set()

        # Center window
        share_window.update_idletasks()
        x = (share_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (share_window.winfo_screenheight() // 2) - (300 // 2)
        share_window.geometry(f"400x300+{x}+{y}")

        # Share form
        form_frame = ctk.CTkFrame(share_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # City info
        city_name = self.current_weather_data.get("city", "Unknown")
        country = self.current_weather_data.get("country", "Unknown")

        info_label = ctk.CTkLabel(
            form_frame,
            text=f"Sharing: {city_name}, {country}",
            font=("Segoe UI", 14, "bold")
        )
        info_label.pack(pady=(10, 20))

        # Tags
        tags_label = ctk.CTkLabel(form_frame, text="Tags (comma-separated):")
        tags_label.pack(anchor="w", padx=10, pady=(0, 5))

        tags_var = ctk.StringVar()
        tags_entry = ctk.CTkEntry(form_frame, textvariable=tags_var)
        tags_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Description
        desc_label = ctk.CTkLabel(form_frame, text="Description (optional):")
        desc_label.pack(anchor="w", padx=10, pady=(10, 5))

        desc_text = ctk.CTkTextbox(form_frame, height=80)
        desc_text.pack(fill="x", padx=10, pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10)

        def share_city():
            try:
                tags = [tag.strip() for tag in tags_var.get().split(",") if tag.strip()]
                description = desc_text.get("1.0", "end-1c").strip()

                # Create city data
                city_data = CityData(
                    id=str(uuid.uuid4()),
                    city_name=city_name,
                    country=country,
                    latitude=self.current_weather_data.get("latitude", 0.0),
                    longitude=self.current_weather_data.get("longitude", 0.0),
                    current_weather=self.current_weather_data,
                    shared_by=self.github_service.username or "Unknown",
                    shared_at=datetime.now(),
                    tags=tags,
                    description=description
                )

                # Share via GitHub
                self.github_service.share_city_data(city_data)

                # Update local data
                self.shared_cities.append(city_data)
                self._update_cities_display()

                share_window.destroy()
                messagebox.showinfo("Success", "City shared successfully!")

            except Exception as e:
                self.logger.error(f"Error sharing city: {e}")
                messagebox.showerror("Error", f"Failed to share city: {e}")

        share_button = ctk.CTkButton(
            button_frame,
            text="Share",
            command=share_city
        )
        share_button.pack(side="right", padx=(10, 0))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=share_window.destroy
        )
        cancel_button.pack(side="right")

    def _import_cities(self):
        """Import cities from file."""
        file_path = filedialog.askopenfilename(
            title="Import Cities",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate and import cities
            imported_count = 0
            for city_dict in data:
                try:
                    # Convert dict to CityData
                    city_data = CityData(
                        id=city_dict.get('id', str(uuid.uuid4())),
                        city_name=city_dict['city_name'],
                        country=city_dict['country'],
                        latitude=city_dict.get('latitude', 0.0),
                        longitude=city_dict.get('longitude', 0.0),
                        current_weather=city_dict.get('current_weather', {}),
                        shared_by=city_dict.get('shared_by', 'Imported'),
                        shared_at=datetime.fromisoformat(city_dict.get('shared_at', datetime.now().isoformat())),
                        tags=city_dict.get('tags', []),
                        description=city_dict.get('description', ''),
                        is_favorite=city_dict.get('is_favorite', False)
                    )

                    # Check if city already exists
                    if not any(c.city_name == city_data.city_name and c.country == city_data.country
                              for c in self.shared_cities):
                        self.shared_cities.append(city_data)
                        imported_count += 1

                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Skipping invalid city data: {e}")
                    continue

            # Update display
            self._update_cities_display()

            messagebox.showinfo(
                "Import Complete",
                f"Successfully imported {imported_count} cities"
            )

        except Exception as e:
            self.logger.error(f"Error importing cities: {e}")
            messagebox.showerror("Import Error", f"Failed to import cities: {e}")

    def _on_city_search_changed(self, *args):
        """Handle city search text change."""
        self._update_cities_display()

    def _toggle_city_selection(self, city: CityData):
        """Toggle city selection for comparison."""
        city_key = f"{city.city_name}, {city.country}"

        if city_key in self.selected_cities:
            self.selected_cities.remove(city_key)
        else:
            self.selected_cities.append(city_key)

        # Update selected cities display
        self._update_selected_cities_display()

        # Enable/disable compare button
        self.quick_compare_button.configure(
            state="normal" if len(self.selected_cities) >= 2 else "disabled"
        )

    def _update_selected_cities_display(self):
        """Update selected cities display."""
        # Clear existing
        for widget in self.selected_cities_frame.winfo_children():
            widget.destroy()

        if not self.selected_cities:
            no_selection_label = GlassLabel(
                self.selected_cities_frame,
                text="No cities selected",
                text_color="#888888"
            )
            no_selection_label.pack()
            return

        # Display selected cities
        for i, city_name in enumerate(self.selected_cities):
            city_frame = ctk.CTkFrame(self.selected_cities_frame, fg_color="transparent")
            city_frame.pack(side="left", padx=(0, 10))

            city_label = GlassLabel(
                city_frame,
                text=city_name,
                font=("Segoe UI", 10)
            )
            city_label.pack(side="left")

            remove_button = GlassButton(
                city_frame,
                text="✕",
                width=20,
                height=20,
                command=lambda c=city_name: self._remove_selected_city(c)
            )
            remove_button.pack(side="left", padx=(5, 0))

    def _remove_selected_city(self, city_name: str):
        """Remove city from selection."""
        if city_name in self.selected_cities:
            self.selected_cities.remove(city_name)
            self._update_selected_cities_display()

            # Update compare button state
            self.quick_compare_button.configure(
                state="normal" if len(self.selected_cities) >= 2 else "disabled"
            )

    def _quick_compare(self):
        """Create quick comparison from selected cities."""
        if len(self.selected_cities) < 2:
            messagebox.showwarning("Warning", "Select at least 2 cities to compare")
            return

        # Create comparison
        comparison = TeamComparison(
            id=str(uuid.uuid4()),
            title=f"Quick Comparison - {', '.join(self.selected_cities[:3])}{'...' if len(self.selected_cities) > 3 else ''}",
            cities=self.selected_cities.copy(),
            metrics=self.comparison_metrics.copy(),
            created_by=self.github_service.username or "Unknown",
            created_at=datetime.now(),
            data={}
        )

        # Generate comparison data
        self._generate_comparison_data(comparison)

        # Add to comparisons
        self.team_comparisons.append(comparison)
        self._update_comparisons_display()

        # Clear selection
        self.selected_cities.clear()
        self._update_selected_cities_display()
        self.quick_compare_button.configure(state="disabled")

        # Show comparison
        self._view_comparison(comparison)

    def _create_new_comparison(self):
        """Create new detailed comparison."""
        # Create comparison dialog
        comp_window = ctk.CTkToplevel(self)
        comp_window.title("New Comparison")
        comp_window.geometry("500x600")
        comp_window.transient(self)
        comp_window.grab_set()

        # Center window
        comp_window.update_idletasks()
        x = (comp_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (comp_window.winfo_screenheight() // 2) - (600 // 2)
        comp_window.geometry(f"500x600+{x}+{y}")

        # Comparison form
        form_frame = ctk.CTkScrollableFrame(comp_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(form_frame, text="Title:")
        title_label.pack(anchor="w", pady=(0, 5))

        title_var = ctk.StringVar()
        title_entry = ctk.CTkEntry(form_frame, textvariable=title_var)
        title_entry.pack(fill="x", pady=(0, 10))

        # Cities selection
        cities_label = ctk.CTkLabel(form_frame, text="Cities to Compare:")
        cities_label.pack(anchor="w", pady=(10, 5))

        cities_frame = ctk.CTkFrame(form_frame)
        cities_frame.pack(fill="x", pady=(0, 10))

        city_vars = {}
        for city in self.shared_cities:
            city_key = f"{city.city_name}, {city.country}"
            var = ctk.BooleanVar(value=city_key in self.selected_cities)
            city_vars[city_key] = var

            check = ctk.CTkCheckBox(
                cities_frame,
                text=city_key,
                variable=var
            )
            check.pack(anchor="w", padx=10, pady=2)

        # Metrics selection
        metrics_label = ctk.CTkLabel(form_frame, text="Metrics to Compare:")
        metrics_label.pack(anchor="w", pady=(10, 5))

        metrics_frame = ctk.CTkFrame(form_frame)
        metrics_frame.pack(fill="x", pady=(0, 20))

        available_metrics = [
            "temperature", "humidity", "wind_speed", "pressure",
            "visibility", "uv_index", "feels_like"
        ]

        metric_vars = {}
        for metric in available_metrics:
            var = ctk.BooleanVar(value=metric in self.comparison_metrics)
            metric_vars[metric] = var

            check = ctk.CTkCheckBox(
                metrics_frame,
                text=metric.replace("_", " ").title(),
                variable=var
            )
            check.pack(anchor="w", padx=10, pady=2)

        # Buttons
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        def create_comparison():
            try:
                title = title_var.get().strip()
                if not title:
                    messagebox.showerror("Error", "Please enter a title")
                    return

                # Get selected cities
                selected_cities = [
                    city for city, var in city_vars.items()
                    if var.get()
                ]

                if len(selected_cities) < 2:
                    messagebox.showerror("Error", "Select at least 2 cities")
                    return

                # Get selected metrics
                selected_metrics = [
                    metric for metric, var in metric_vars.items()
                    if var.get()
                ]

                if not selected_metrics:
                    messagebox.showerror("Error", "Select at least 1 metric")
                    return

                # Create comparison
                comparison = TeamComparison(
                    id=str(uuid.uuid4()),
                    title=title,
                    cities=selected_cities,
                    metrics=selected_metrics,
                    created_by=self.github_service.username or "Unknown",
                    created_at=datetime.now(),
                    data={}
                )

                # Generate comparison data
                self._generate_comparison_data(comparison)

                # Add to comparisons
                self.team_comparisons.append(comparison)
                self._update_comparisons_display()

                comp_window.destroy()

                # Show comparison
                self._view_comparison(comparison)

            except Exception as e:
                self.logger.error(f"Error creating comparison: {e}")
                messagebox.showerror("Error", f"Failed to create comparison: {e}")

        create_button = ctk.CTkButton(
            button_frame,
            text="Create",
            command=create_comparison
        )
        create_button.pack(side="right", padx=(10, 0))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=comp_window.destroy
        )
        cancel_button.pack(side="right")

    def _generate_comparison_data(self, comparison: TeamComparison):
        """Generate comparison data for cities and metrics."""
        comparison_data = {}

        for city_name in comparison.cities:
            # Find city data
            city_data = next(
                (c for c in self.shared_cities
                 if f"{c.city_name}, {c.country}" == city_name),
                None
            )

            if city_data and city_data.current_weather:
                city_metrics = {}
                weather = city_data.current_weather

                for metric in comparison.metrics:
                    if metric == "temperature":
                        city_metrics[metric] = weather.get("temperature", 0)
                    elif metric == "humidity":
                        city_metrics[metric] = weather.get("humidity", 0)
                    elif metric == "wind_speed":
                        city_metrics[metric] = weather.get("wind_speed", 0)
                    elif metric == "pressure":
                        city_metrics[metric] = weather.get("pressure", 0)
                    elif metric == "visibility":
                        city_metrics[metric] = weather.get("visibility", 0)
                    elif metric == "uv_index":
                        city_metrics[metric] = weather.get("uv_index", 0)
                    elif metric == "feels_like":
                        city_metrics[metric] = weather.get("feels_like", 0)

                comparison_data[city_name] = city_metrics

        comparison.data = comparison_data

    def _view_comparison(self, comparison: TeamComparison):
        """View comparison in detail window."""
        # Create comparison viewer window
        viewer_window = ctk.CTkToplevel(self)
        viewer_window.title(f"Comparison: {comparison.title}")
        viewer_window.geometry("800x600")
        viewer_window.transient(self)

        # Center window
        viewer_window.update_idletasks()
        x = (viewer_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (viewer_window.winfo_screenheight() // 2) - (600 // 2)
        viewer_window.geometry(f"800x600+{x}+{y}")

        # Viewer content
        content_frame = ctk.CTkScrollableFrame(viewer_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text=comparison.title,
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Comparison table
        if comparison.data:
            self._create_comparison_table(content_frame, comparison)
        else:
            no_data_label = ctk.CTkLabel(
                content_frame,
                text="No comparison data available",
                text_color="#888888"
            )
            no_data_label.pack(pady=20)

    def _create_comparison_table(self, parent, comparison: TeamComparison):
        """Create comparison data table."""
        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill="both", expand=True)

        # Headers
        header_frame = ctk.CTkFrame(table_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # City header
        city_label = ctk.CTkLabel(
            header_frame,
            text="City",
            font=("Segoe UI", 12, "bold")
        )
        city_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Metric headers
        for i, metric in enumerate(comparison.metrics):
            metric_label = ctk.CTkLabel(
                header_frame,
                text=metric.replace("_", " ").title(),
                font=("Segoe UI", 12, "bold")
            )
            metric_label.grid(row=0, column=i+1, padx=10, pady=5)

        # Data rows
        for row, (city_name, city_data) in enumerate(comparison.data.items()):
            row_frame = ctk.CTkFrame(table_frame)
            row_frame.pack(fill="x", padx=10, pady=2)

            # City name
            city_label = ctk.CTkLabel(
                row_frame,
                text=city_name,
                font=("Segoe UI", 11)
            )
            city_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            # Metric values
            for i, metric in enumerate(comparison.metrics):
                value = city_data.get(metric, "N/A")
                if isinstance(value, (int, float)):
                    value = f"{value:.1f}"

                value_label = ctk.CTkLabel(
                    row_frame,
                    text=str(value),
                    font=("Segoe UI", 11)
                )
                value_label.grid(row=0, column=i+1, padx=10, pady=5)

    def _export_comparison(self, comparison: TeamComparison):
        """Export comparison to file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Comparison",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.csv'):
                self._export_comparison_csv(comparison, file_path)
            else:
                self._export_comparison_json(comparison, file_path)

            messagebox.showinfo("Success", "Comparison exported successfully!")

        except Exception as e:
            self.logger.error(f"Error exporting comparison: {e}")
            messagebox.showerror("Error", f"Failed to export comparison: {e}")

    def _export_comparison_json(self, comparison: TeamComparison, file_path: str):
        """Export comparison as JSON."""
        export_data = {
            "title": comparison.title,
            "cities": comparison.cities,
            "metrics": comparison.metrics,
            "created_by": comparison.created_by,
            "created_at": comparison.created_at.isoformat(),
            "data": comparison.data
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def _export_comparison_csv(self, comparison: TeamComparison, file_path: str):
        """Export comparison as CSV."""
        import csv

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            header = ["City"] + [metric.replace("_", " ").title() for metric in comparison.metrics]
            writer.writerow(header)

            # Data rows
            for city_name, city_data in comparison.data.items():
                row = [city_name]
                for metric in comparison.metrics:
                    value = city_data.get(metric, "N/A")
                    row.append(str(value))
                writer.writerow(row)

    def _view_city_details(self, city: CityData):
        """View city details in popup window."""
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"City Details: {city.city_name}")
        details_window.geometry("500x400")
        details_window.transient(self)

        # Center window
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (details_window.winfo_screenheight() // 2) - (400 // 2)
        details_window.geometry(f"500x400+{x}+{y}")

        # Details content
        content_frame = ctk.CTkScrollableFrame(details_window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # City header
        header_label = ctk.CTkLabel(
            content_frame,
            text=f"{city.city_name}, {city.country}",
            font=("Segoe UI", 18, "bold")
        )
        header_label.pack(pady=(0, 20))

        # Location
        location_label = ctk.CTkLabel(
            content_frame,
            text=f"📍 {city.latitude:.4f}, {city.longitude:.4f}",
            font=("Segoe UI", 12)
        )
        location_label.pack(pady=(0, 10))

        # Weather data
        if city.current_weather:
            weather_frame = ctk.CTkFrame(content_frame)
            weather_frame.pack(fill="x", pady=(0, 10))

            weather_title = ctk.CTkLabel(
                weather_frame,
                text="Current Weather",
                font=("Segoe UI", 14, "bold")
            )
            weather_title.pack(pady=(10, 5))

            for key, value in city.current_weather.items():
                if key != "timestamp":
                    weather_item = ctk.CTkLabel(
                        weather_frame,
                        text=f"{key.replace('_', ' ').title()}: {value}",
                        font=("Segoe UI", 11)
                    )
                    weather_item.pack(anchor="w", padx=10, pady=2)

        # Meta info
        meta_frame = ctk.CTkFrame(content_frame)
        meta_frame.pack(fill="x", pady=(10, 0))

        meta_title = ctk.CTkLabel(
            meta_frame,
            text="Sharing Info",
            font=("Segoe UI", 14, "bold")
        )
        meta_title.pack(pady=(10, 5))

        shared_label = ctk.CTkLabel(
            meta_frame,
            text=f"Shared by: {city.shared_by}",
            font=("Segoe UI", 11)
        )
        shared_label.pack(anchor="w", padx=10, pady=2)

        date_label = ctk.CTkLabel(
            meta_frame,
            text=f"Shared on: {self._format_date(city.shared_at)}",
            font=("Segoe UI", 11)
        )
        date_label.pack(anchor="w", padx=10, pady=2)

        if city.description:
            desc_label = ctk.CTkLabel(
                meta_frame,
                text=f"Description: {city.description}",
                font=("Segoe UI", 11)
            )
            desc_label.pack(anchor="w", padx=10, pady=2)

        if city.tags:
            tags_label = ctk.CTkLabel(
                meta_frame,
                text=f"Tags: {', '.join(city.tags)}",
                font=("Segoe UI", 11)
            )
            tags_label.pack(anchor="w", padx=10, pady=(2, 10))

    def _format_date(self, date: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - date

        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return date.strftime("%Y-%m-%d")

    def _update_status(self, message: str):
        """Update status message."""
        self.status_label.configure(text=message)

    def _update_last_sync(self):
        """Update last sync time display."""
        now = datetime.now()
        self.last_sync_label.configure(text=f"Last sync: {now.strftime('%H:%M:%S')}")

    # Public API methods
    def set_weather_data(self, weather_data: Dict[str, Any]):
        """Set current weather data for sharing."""
        self.current_weather_data = weather_data

    def refresh_data(self):
        """Refresh all collaboration data."""
        self._manual_sync()

    def get_shared_cities(self) -> List[CityData]:
        """Get list of shared cities."""
        return self.shared_cities.copy()

    def get_team_comparisons(self) -> List[TeamComparison]:
        """Get list of team comparisons."""
        return self.team_comparisons.copy()

    def export_all_data(self, file_path: str):
        """Export all collaboration data to file."""
        export_data = {
            "team_members": [asdict(member) for member in self.team_members],
            "shared_cities": [
                {
                    **asdict(city),
                    "shared_at": city.shared_at.isoformat()
                }
                for city in self.shared_cities
            ],
            "team_comparisons": [
                {
                    **asdict(comparison),
                    "created_at": comparison.created_at.isoformat()
                }
                for comparison in self.team_comparisons
            ],
            "exported_at": datetime.now().isoformat()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def destroy(self):
        """Clean up resources."""
        # Cancel auto-sync timer
        if self.sync_timer:
            self.after_cancel(self.sync_timer)

        super().destroy()


def create_team_collaboration(parent, github_service: GitHubService) -> TeamCollaborationWidget:
    """Factory function to create team collaboration widget."""
    return TeamCollaborationWidget(parent, github_service)


if __name__ == "__main__":
    # Test the widget
    import sys
    sys.path.append("../..")

    from services.github_service import GitHubService

    # Create test app
    app = ctk.CTk()
    app.title("Team Collaboration Test")
    app.geometry("1000x700")

    # Create mock GitHub service
    github_service = GitHubService("test_token", "test_repo")

    # Create widget
    widget = create_team_collaboration(app, github_service)
    widget.pack(fill="both", expand=True, padx=20, pady=20)

    # Test data
    test_weather = {
        "city": "New York",
        "country": "USA",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "temperature": 22.5,
        "humidity": 65,
        "wind_speed": 12.3,
        "pressure": 1013.25,
        "condition": "partly cloudy"
    }

    widget.set_weather_data(test_weather)

    app.mainloop()
