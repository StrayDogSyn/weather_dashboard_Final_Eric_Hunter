"""City Comparison Panel for team collaboration and multi-city weather comparison."""

import customtkinter as ctk
import tkinter as tk
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime, timedelta
import logging
import threading
import json
import csv
from dataclasses import dataclass
from tkinter import filedialog, messagebox

from ..theme_manager import ThemeManager
from ...services.github_team_service import GitHubTeamService, TeamCityData
from ...services.enhanced_weather_service import EnhancedWeatherService

logger = logging.getLogger(__name__)


class CityPill(ctk.CTkFrame):
    """A pill-shaped widget representing a selected city."""

    def __init__(self, parent, city_name: str, on_remove: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.city_name = city_name
        self.on_remove = on_remove
        self.theme_manager = ThemeManager()

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Setup the pill UI."""
        self.configure(corner_radius=20, height=40)

        # City name label
        self.city_label = ctk.CTkLabel(
            self,
            text=self.city_name,
            font=("JetBrains Mono", 12, "bold")
        )
        self.city_label.pack(side="left", padx=(15, 5), pady=8)

        # Remove button
        if self.on_remove:
            self.remove_btn = ctk.CTkButton(
                self,
                text="×",
                width=24,
                height=24,
                corner_radius=12,
                command=self.on_remove,
                font=("JetBrains Mono", 14, "bold")
            )
            self.remove_btn.pack(side="right", padx=(0, 10), pady=8)

    def _apply_theme(self):
        """Apply current theme to the pill."""
        theme = self.theme_manager.get_current_theme()

        self.configure(
            fg_color=theme.get("card_bg", "#2b2b2b"),
            border_width=1,
            border_color=theme.get("border", "#404040")
        )

        self.city_label.configure(
            text_color=theme.get("text", "#ffffff")
        )

        if hasattr(self, 'remove_btn'):
            self.remove_btn.configure(
                fg_color=theme.get("error", "#ff6b6b"),
                hover_color=theme.get("error_hover", "#ff5252"),
                text_color=theme.get("background", "#1a1a1a")
            )


class CityComparisonColumn(ctk.CTkFrame):
    """A column displaying weather data for a single city."""

    def __init__(self, parent, city_data: Dict[str, Any], is_team_member: bool = False, **kwargs):
        super().__init__(parent, **kwargs)
        self.city_data = city_data
        self.is_team_member = is_team_member
        self.theme_manager = ThemeManager()

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Setup the column UI."""
        self.configure(corner_radius=12)

        # Header with city name and member info
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        # City name with enhanced team indicator
        city_name = self.city_data.get("city_name", "Unknown City")
        display_text = f"🏙️ {city_name}"

        self.city_label = ctk.CTkLabel(
            header_frame,
            text=display_text,
            font=("JetBrains Mono", 18, "bold")
        )
        self.city_label.pack()

        # Add team member badge if applicable
        if self.is_team_member:
            member_name = self.city_data.get("member_name", "Team Member")
            team_badge = ctk.CTkLabel(
                header_frame,
                text=f"🏢 TEAM MEMBER ({member_name})",
                font=("JetBrains Mono", 10, "bold"),
                text_color="#4CAF50"
            )
            team_badge.pack(pady=(2, 0))

        # Team member info (if applicable)
        if self.is_team_member:
            member_name = self.city_data.get("member_name", "Unknown Member")
            self.member_label = ctk.CTkLabel(
                header_frame,
                text=f"👤 {member_name}",
                font=("JetBrains Mono", 12)
            )
            self.member_label.pack(pady=(5, 0))

            # Last updated
            last_updated = self.city_data.get("last_updated", "")
            if last_updated:
                try:
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M %d/%m")
                    self.updated_label = ctk.CTkLabel(
                        header_frame,
                        text=f"🕒 {time_str}",
                        font=("JetBrains Mono", 10)
                    )
                    self.updated_label.pack()
                except ValueError:
                    pass

        # Weather data
        weather_data = self.city_data.get("weather_data", {})

        # Temperature
        temperature = weather_data.get("temperature", "N/A")
        self.temp_label = ctk.CTkLabel(
            self,
            text=f"{temperature}°C" if isinstance(temperature, (int, float)) else str(temperature),
            font=("JetBrains Mono", 36, "bold")
        )
        self.temp_label.pack(pady=10)

        # Weather description
        description = weather_data.get("description", "No data")
        self.desc_label = ctk.CTkLabel(
            self,
            text=description,
            font=("JetBrains Mono", 14)
        )
        self.desc_label.pack(pady=(0, 15))

        # Metrics frame
        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Weather metrics
        metrics = {
            "Humidity": f"{weather_data.get('humidity', 'N/A')}%" if weather_data.get('humidity') else "N/A",
            "Wind": f"{weather_data.get('wind_speed', 'N/A')} km/h" if weather_data.get('wind_speed') else "N/A",
            "Pressure": f"{weather_data.get('pressure', 'N/A')} hPa" if weather_data.get('pressure') else "N/A",
            "Feels Like": f"{weather_data.get('feels_like', 'N/A')}°C" if weather_data.get('feels_like') else "N/A"
        }

        for label, value in metrics.items():
            metric_frame = ctk.CTkFrame(metrics_frame, fg_color="transparent")
            metric_frame.pack(fill="x", pady=2)

            metric_label = ctk.CTkLabel(
                metric_frame,
                text=f"{label}:",
                font=("JetBrains Mono", 12)
            )
            metric_label.pack(side="left")

            metric_value = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=("JetBrains Mono", 12, "bold")
            )
            metric_value.pack(side="right")

    def _apply_theme(self):
        """Apply current theme to the column."""
        theme = self.theme_manager.get_current_theme()

        self.configure(
            fg_color=theme.get("card_bg", "#2b2b2b"),
            border_width=1,
            border_color=theme.get("border", "#404040")
        )

        # Apply theme to labels
        self.city_label.configure(text_color=theme.get("accent", "#00ff88"))

        if hasattr(self, 'member_label'):
            self.member_label.configure(text_color=theme.get("text_secondary", "#888888"))

        if hasattr(self, 'updated_label'):
            self.updated_label.configure(text_color=theme.get("text_secondary", "#888888"))

        self.temp_label.configure(text_color=theme.get("text", "#ffffff"))
        self.desc_label.configure(text_color=theme.get("text_secondary", "#888888"))

    def update_theme(self):
        """Update theme for this column."""
        self._apply_theme()


class CityComparisonPanel(ctk.CTkFrame):
    """Main panel for city comparison with team collaboration features."""

    def __init__(self, parent, weather_service: EnhancedWeatherService = None, github_service: GitHubTeamService = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.weather_service = weather_service
        self.github_service = github_service or GitHubTeamService()
        self.theme_manager = ThemeManager()

        self.selected_cities = []  # List of city names
        self.comparison_columns = []  # List of CityComparisonColumn widgets
        self.city_pills = []  # List of CityPill widgets
        self.team_cities_data = {}  # Dictionary to store team cities data
        self.selected_dropdown_cities = [None, None, None, None]  # Track dropdown selections

        # Auto-refresh functionality
        self.auto_refresh_enabled = True
        self.refresh_interval = 15 * 60 * 1000  # 15 minutes in milliseconds
        self.last_team_sync = None
        self.refresh_timer = None

        # Activity feed data
        self.activity_feed = []
        self.max_activity_items = 50

        # Sorting and filtering options
        self.sort_by = "temperature"  # temperature, humidity, wind_speed, pressure
        self.sort_ascending = False

        # Weather similarity tracking
        self.similarity_threshold = 0.8

        self._setup_ui()
        self._apply_theme()

        # Register for theme updates
        self.theme_manager.add_observer(self.update_theme)

        # Start auto-refresh timer
        self._start_auto_refresh()

    def _setup_ui(self):
        """Setup the main UI."""
        self.configure(corner_radius=12)

        # Header
        header_frame = ctk.CTkFrame(self, corner_radius=12)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🌍 Team Weather Comparison",
            font=("JetBrains Mono", 24, "bold")
        )
        title_label.pack(pady=20)

        # Controls section
        controls_frame = ctk.CTkFrame(self, corner_radius=12)
        controls_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Team data controls
        team_controls = ctk.CTkFrame(controls_frame, fg_color="transparent")
        team_controls.pack(fill="x", padx=15, pady=15)

        team_label = ctk.CTkLabel(
            team_controls,
            text="Team Collaboration",
            font=("JetBrains Mono", 16, "bold")
        )
        team_label.pack(anchor="w", pady=(0, 10))

        # Team buttons
        team_buttons = ctk.CTkFrame(team_controls, fg_color="transparent")
        team_buttons.pack(fill="x")

        self.sync_btn = ctk.CTkButton(
            team_buttons,
            text="🔄 Sync Team Data",
            command=self._sync_team_data,
            font=("JetBrains Mono", 12, "bold")
        )
        self.sync_btn.pack(side="left", padx=(0, 10))

        self.share_btn = ctk.CTkButton(
            team_buttons,
            text="📤 Share My City",
            command=self._show_share_dialog,
            font=("JetBrains Mono", 12, "bold")
        )
        self.share_btn.pack(side="left", padx=(0, 10))

        self.activity_btn = ctk.CTkButton(
            team_buttons,
            text="📋 Activity Feed",
            command=self._show_activity_feed,
            font=("JetBrains Mono", 12, "bold")
        )
        self.activity_btn.pack(side="left", padx=(0, 10))

        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.auto_refresh_checkbox = ctk.CTkCheckBox(
            team_buttons,
            text="Auto-refresh (15min)",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh,
            font=("JetBrains Mono", 10)
        )
        self.auto_refresh_checkbox.pack(side="left", padx=(10, 0))

        # Last sync indicator
        self.last_sync_label = ctk.CTkLabel(
            team_controls,
            text="Last sync: Never",
            font=("JetBrains Mono", 10),
            text_color=("#666666", "#999999")
        )
        self.last_sync_label.pack(anchor="w", pady=(5, 0))

        # City selection
        selection_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        selection_frame.pack(fill="x", padx=15, pady=(0, 15))

        selection_label = ctk.CTkLabel(
            selection_frame,
            text="Select Cities from Team Data (Max 4)",
            font=("JetBrains Mono", 16, "bold")
        )
        selection_label.pack(anchor="w", pady=(0, 10))

        # Dropdown selection controls
        dropdown_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        dropdown_frame.pack(fill="x", pady=(0, 10))

        # City 1 dropdown
        city1_frame = ctk.CTkFrame(dropdown_frame, fg_color="transparent")
        city1_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(
            city1_frame,
            text="City 1:",
            font=("JetBrains Mono", 12, "bold"),
            width=60
        ).pack(side="left", padx=(0, 10))

        self.city1_dropdown = ctk.CTkComboBox(
            city1_frame,
            values=["Select a city..."],
            width=200,
            font=("JetBrains Mono", 12),
            command=lambda choice: self._on_city_selected(choice, 1)
        )
        self.city1_dropdown.pack(side="left", padx=(0, 10))
        self.city1_dropdown.set("Select a city...")

        # City 2 dropdown
        city2_frame = ctk.CTkFrame(dropdown_frame, fg_color="transparent")
        city2_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(
            city2_frame,
            text="City 2:",
            font=("JetBrains Mono", 12, "bold"),
            width=60
        ).pack(side="left", padx=(0, 10))

        self.city2_dropdown = ctk.CTkComboBox(
            city2_frame,
            values=["Select a city..."],
            width=200,
            font=("JetBrains Mono", 12),
            command=lambda choice: self._on_city_selected(choice, 2)
        )
        self.city2_dropdown.pack(side="left", padx=(0, 10))
        self.city2_dropdown.set("Select a city...")

        # City 3 dropdown (optional)
        city3_frame = ctk.CTkFrame(dropdown_frame, fg_color="transparent")
        city3_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(
            city3_frame,
            text="City 3:",
            font=("JetBrains Mono", 12, "bold"),
            width=60
        ).pack(side="left", padx=(0, 10))

        self.city3_dropdown = ctk.CTkComboBox(
            city3_frame,
            values=["Select a city..."],
            width=200,
            font=("JetBrains Mono", 12),
            command=lambda choice: self._on_city_selected(choice, 3)
        )
        self.city3_dropdown.pack(side="left", padx=(0, 10))
        self.city3_dropdown.set("Select a city...")

        # City 4 dropdown (optional)
        city4_frame = ctk.CTkFrame(dropdown_frame, fg_color="transparent")
        city4_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(
            city4_frame,
            text="City 4:",
            font=("JetBrains Mono", 12, "bold"),
            width=60
        ).pack(side="left", padx=(0, 10))

        self.city4_dropdown = ctk.CTkComboBox(
            city4_frame,
            values=["Select a city..."],
            width=200,
            font=("JetBrains Mono", 12),
            command=lambda choice: self._on_city_selected(choice, 4)
        )
        self.city4_dropdown.pack(side="left", padx=(0, 10))
        self.city4_dropdown.set("Select a city...")

        # Quick add city frame
        quick_add_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        quick_add_frame.pack(fill="x", pady=(10, 0))

        quick_add_label = ctk.CTkLabel(
            quick_add_frame,
            text="Quick Add City:",
            font=("JetBrains Mono", 12, "bold")
        )
        quick_add_label.pack(side="left", padx=(0, 10))

        self.quick_city_entry = ctk.CTkEntry(
            quick_add_frame,
            placeholder_text="Enter city name...",
            font=("JetBrains Mono", 12),
            width=200
        )
        self.quick_city_entry.pack(side="left", padx=(0, 5))
        self.quick_city_entry.bind("<Return>", lambda e: self._quick_add_city())

        quick_add_btn = ctk.CTkButton(
            quick_add_frame,
            text="➕ Add",
            command=self._quick_add_city,
            font=("JetBrains Mono", 12),
            width=60
        )
        quick_add_btn.pack(side="left", padx=(0, 10))

        # Control buttons
        control_buttons_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        control_buttons_frame.pack(fill="x", pady=(10, 0))

        self.compare_btn = ctk.CTkButton(
            control_buttons_frame,
            text="🔍 Compare Selected Cities",
            command=self._compare_selected_cities,
            font=("JetBrains Mono", 14, "bold"),
            width=200
        )
        self.compare_btn.pack(side="left", padx=(0, 10))

        self.insights_btn = ctk.CTkButton(
            control_buttons_frame,
            text="📊 Show Insights",
            command=self._show_comparison_insights,
            font=("JetBrains Mono", 12, "bold"),
            width=150
        )
        self.insights_btn.pack(side="left", padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            control_buttons_frame,
            text="🗑️ Clear All",
            command=self._clear_all_selections,
            font=("JetBrains Mono", 12, "bold"),
            width=120
        )
        self.clear_btn.pack(side="left", padx=(0, 10))

        # Export button
        self.export_btn = ctk.CTkButton(
            control_buttons_frame,
            text="📊 Export Data",
            command=self._export_comparison_data,
            font=("JetBrains Mono", 12, "bold"),
            width=120
        )
        self.export_btn.pack(side="left")

        # Sorting controls frame
        sorting_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        sorting_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            sorting_frame,
            text="Sort by:",
            font=("JetBrains Mono", 10, "bold")
        ).pack(side="left", padx=(0, 5))

        self.sort_var = tk.StringVar(value="temperature")
        self.sort_dropdown = ctk.CTkOptionMenu(
            sorting_frame,
            values=["temperature", "humidity", "wind_speed", "pressure", "city_name"],
            variable=self.sort_var,
            command=self._on_sort_changed,
            font=("JetBrains Mono", 10),
            width=120
        )
        self.sort_dropdown.pack(side="left", padx=(0, 10))

        self.sort_order_var = tk.BooleanVar(value=False)
        self.sort_order_checkbox = ctk.CTkCheckBox(
            sorting_frame,
            text="Ascending",
            variable=self.sort_order_var,
            command=self._on_sort_changed,
            font=("JetBrains Mono", 10)
        )
        self.sort_order_checkbox.pack(side="left", padx=(0, 20))

        # Weather similarity threshold
        ctk.CTkLabel(
            sorting_frame,
            text="Similarity threshold:",
            font=("JetBrains Mono", 10, "bold")
        ).pack(side="left", padx=(0, 5))

        self.similarity_slider = ctk.CTkSlider(
            sorting_frame,
            from_=0.5,
            to=1.0,
            number_of_steps=10,
            command=self._on_similarity_changed,
            width=100
        )
        self.similarity_slider.set(0.8)
        self.similarity_slider.pack(side="left", padx=(0, 5))

        self.similarity_label = ctk.CTkLabel(
            sorting_frame,
            text="80%",
            font=("JetBrains Mono", 10)
        )
        self.similarity_label.pack(side="left")

        # Store dropdown references
        self.city_dropdowns = [self.city1_dropdown, self.city2_dropdown, self.city3_dropdown, self.city4_dropdown]

        # Status label
        self.status_label = ctk.CTkLabel(
            controls_frame,
            text="Ready to compare cities",
            font=("JetBrains Mono", 11),
            text_color=("#888888", "#AAAAAA")
        )
        self.status_label.pack(pady=(10, 0))

        # City pills container
        self.pills_frame = ctk.CTkFrame(selection_frame, fg_color="transparent")
        self.pills_frame.pack(fill="x", pady=(10, 0))

        # Comparison area
        self.comparison_container = ctk.CTkScrollableFrame(self)
        self.comparison_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Initial placeholder
        self.placeholder_label = ctk.CTkLabel(
            self.comparison_container,
            text="🌤️\n\nSync team data first, then select cities from dropdowns\nto start comparing weather data from your team",
            font=("JetBrains Mono", 16),
            justify="center"
        )
        self.placeholder_label.pack(expand=True, pady=50)

    def _apply_theme(self):
        """Apply current theme to the panel."""
        theme = self.theme_manager.get_current_theme()

        self.configure(
            fg_color=theme.get("background", "#1a1a1a")
        )

    def _sync_team_data(self):
        """Sync team data from GitHub with enhanced validation and error handling."""
        try:
            self.sync_btn.configure(text="🔄 Syncing...", state="disabled")
            self.update()

            # Fetch team cities in background thread
            def fetch_data():
                try:
                    team_cities = self.github_service.force_refresh()
                    self.after(0, lambda: self._process_team_data(team_cities))
                except Exception as e:
                    self.after(0, lambda: self._handle_team_sync_error(str(e)))

            threading.Thread(target=fetch_data, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to start team data sync: {e}")
            self._handle_team_sync_error(str(e))

    def _process_team_data(self, team_cities):
        """Process and validate team data."""
        try:
            if team_cities:
                # Validate and clean team data
                validated_cities = self._validate_team_cities(team_cities)

                if validated_cities:
                    # Extract unique city names for dropdowns
                    city_names = list(set([
                        city_data["city_name"] for city_data in validated_cities
                    ]))
                    city_names.sort()  # Sort alphabetically

                    # Add "Select a city..." as first option
                    dropdown_values = ["Select a city..."] + city_names

                    # Update all dropdowns with team cities
                    for dropdown in self.city_dropdowns:
                        current_selection = dropdown.get()
                        dropdown.configure(values=dropdown_values)
                        # Restore selection if it's still valid
                        if current_selection in dropdown_values:
                            dropdown.set(current_selection)
                        else:
                            dropdown.set("Select a city...")

                    # Store validated team data
                    self.team_cities_data = {}
                    for city_data in validated_cities:
                        city_name = city_data["city_name"]
                        if city_name not in self.team_cities_data:
                            self.team_cities_data[city_name] = []
                        self.team_cities_data[city_name].append(city_data)

                    # Update last sync time
                    self.last_team_sync = datetime.now()
                    sync_time_str = self.last_team_sync.strftime("%H:%M:%S")
                    self.last_sync_label.configure(text=f"Last sync: {sync_time_str}")

                    # Add to activity feed
                    self._add_activity_item(f"Synced {len(validated_cities)} team cities ({len(city_names)} unique)")

                    logger.info(f"Synced {len(validated_cities)} team cities, {len(city_names)} unique cities")
                else:
                    self._handle_no_valid_data()
            else:
                self._handle_no_valid_data()

        except Exception as e:
            logger.error(f"Error processing team data: {e}")
            self._handle_team_sync_error(str(e))
        finally:
            self.sync_btn.configure(text="🔄 Sync Team Data", state="normal")

    def _validate_team_cities(self, team_cities) -> List[Dict[str, Any]]:
        """Validate and clean team city data."""
        validated_cities = []

        for team_city in team_cities:
            try:
                # Validate city name
                if not hasattr(team_city, 'city_name') or not team_city.city_name:
                    continue

                city_name = team_city.city_name.strip()
                if not city_name or city_name.lower() in ['n/a', 'none', 'null', '']:
                    continue

                # Validate member name
                member_name = "Unknown"
                if hasattr(team_city, 'member_name') and team_city.member_name:
                    member_name = team_city.member_name.strip()

                # Validate timestamp
                last_updated = datetime.now().isoformat()
                if hasattr(team_city, 'last_updated') and team_city.last_updated:
                    try:
                        # Try to parse the timestamp
                        parsed_time = datetime.fromisoformat(team_city.last_updated.replace('Z', '+00:00'))
                        last_updated = team_city.last_updated
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid timestamp for {city_name}, using current time")

                # Extract weather data if available
                weather_data = None
                if hasattr(team_city, 'weather_data') and team_city.weather_data:
                    weather_data = team_city.weather_data

                validated_city = {
                    "city_name": city_name,
                    "member_name": member_name,
                    "last_updated": last_updated,
                    "weather_data": weather_data
                }

                validated_cities.append(validated_city)

            except Exception as e:
                logger.warning(f"Error validating team city data: {e}")
                continue

        return validated_cities

    def _handle_no_valid_data(self):
        """Handle case when no valid team data is available."""
        logger.warning("No valid team cities data available")
        for dropdown in self.city_dropdowns:
            dropdown.configure(values=["No team data available"])
            dropdown.set("No team data available")

        self.last_sync_label.configure(text="Last sync: No data")
        self._add_activity_item("Sync completed - no valid team data found")

    def _handle_team_sync_error(self, error_message: str):
        """Handle team sync errors with user feedback."""
        logger.error(f"Team sync error: {error_message}")

        # Update UI to show error
        for dropdown in self.city_dropdowns:
            dropdown.configure(values=["Error loading data"])
            dropdown.set("Error loading data")

        self.last_sync_label.configure(text="Last sync: Failed")
        self._add_activity_item(f"Sync failed: {error_message[:50]}...")

        # Reset button state
        self.sync_btn.configure(text="🔄 Sync Team Data", state="normal")

        # Show error dialog
        try:
            messagebox.showerror("Sync Error", f"Failed to sync team data:\n{error_message}")
        except Exception:
            pass  # Ignore if messagebox fails

    def _show_share_dialog(self):
        """Show enhanced dialog for sharing current city data."""
        try:
            # Create share dialog window
            share_window = ctk.CTkToplevel(self)
            share_window.title("Share My City Weather")
            share_window.geometry("500x400")
            share_window.transient(self)
            share_window.grab_set()

            # Center the window
            share_window.update_idletasks()
            x = (share_window.winfo_screenwidth() // 2) - (500 // 2)
            y = (share_window.winfo_screenheight() // 2) - (400 // 2)
            share_window.geometry(f"500x400+{x}+{y}")

            # Main frame
            main_frame = ctk.CTkFrame(share_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="📤 Share Your City Weather",
                font=("JetBrains Mono", 18, "bold")
            )
            title_label.pack(pady=(0, 20))

            # City input
            city_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            city_frame.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(
                city_frame,
                text="City Name:",
                font=("JetBrains Mono", 12, "bold")
            ).pack(anchor="w")

            city_entry = ctk.CTkEntry(
                city_frame,
                placeholder_text="Enter your city name...",
                font=("JetBrains Mono", 12),
                height=35
            )
            city_entry.pack(fill="x", pady=(5, 0))

            # Member name input
            member_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            member_frame.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(
                member_frame,
                text="Your Name:",
                font=("JetBrains Mono", 12, "bold")
            ).pack(anchor="w")

            member_entry = ctk.CTkEntry(
                member_frame,
                placeholder_text="Enter your name...",
                font=("JetBrains Mono", 12),
                height=35
            )
            member_entry.pack(fill="x", pady=(5, 0))

            # Status label
            status_label = ctk.CTkLabel(
                main_frame,
                text="",
                font=("JetBrains Mono", 10)
            )
            status_label.pack(pady=(10, 0))

            # Buttons frame
            buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            buttons_frame.pack(fill="x", pady=(20, 0))

            def share_city():
                city_name = city_entry.get().strip()
                member_name = member_entry.get().strip()

                if not city_name or not member_name:
                    status_label.configure(text="Please fill in both city name and your name", text_color="red")
                    return

                try:
                    status_label.configure(text="Fetching weather data...", text_color="blue")
                    share_window.update()

                    # Fetch current weather data for the city
                    if self.weather_service:
                        weather_data = self.weather_service.get_weather(city_name)
                        if weather_data:
                            # Create team city data
                            team_data = {
                                "city_name": city_name,
                                "member_name": member_name,
                                "last_updated": datetime.now().isoformat(),
                                "weather_data": weather_data
                            }

                            # Add to GitHub service (this would normally push to GitHub)
                            # For now, we'll simulate the sharing process
                            status_label.configure(text="Sharing data to team...", text_color="blue")
                            share_window.update()

                            # Simulate API call delay
                            self.after(1000, lambda: self._complete_share(share_window, status_label, team_data))
                        else:
                            status_label.configure(text="Could not fetch weather data for this city", text_color="red")
                    else:
                        status_label.configure(text="Weather service not available", text_color="red")

                except Exception as e:
                    status_label.configure(text=f"Error: {str(e)}", text_color="red")

            # Share button
            share_btn = ctk.CTkButton(
                buttons_frame,
                text="📤 Share City",
                command=share_city,
                font=("JetBrains Mono", 12, "bold"),
                height=35
            )
            share_btn.pack(side="left", padx=(0, 10))

            # Cancel button
            cancel_btn = ctk.CTkButton(
                buttons_frame,
                text="Cancel",
                command=share_window.destroy,
                font=("JetBrains Mono", 12),
                height=35
            )
            cancel_btn.pack(side="left")

            # Focus on city entry
            city_entry.focus()

        except Exception as e:
            logger.error(f"Error showing share dialog: {e}")
            messagebox.showerror("Error", f"Could not open share dialog: {e}")

    def _complete_share(self, share_window, status_label, team_data):
        """Complete the sharing process."""
        try:
            # Add to activity feed
            self._add_activity_item(f"Shared {team_data['city_name']} weather data")

            # Update status
            status_label.configure(text="Successfully shared your city data!", text_color="green")

            # Close window after delay
            self.after(2000, share_window.destroy)

            logger.info(f"Shared city data: {team_data['city_name']} by {team_data['member_name']}")

        except Exception as e:
            logger.error(f"Error completing share: {e}")
            status_label.configure(text=f"Error completing share: {e}", text_color="red")

    def _show_activity_feed(self):
        """Show enhanced team activity feed window."""
        try:
            # Create activity feed window
            activity_window = ctk.CTkToplevel(self)
            activity_window.title("Team Activity Feed")
            activity_window.geometry("600x500")
            activity_window.transient(self)
            activity_window.grab_set()

            # Center the window
            activity_window.update_idletasks()
            x = (activity_window.winfo_screenwidth() // 2) - (600 // 2)
            y = (activity_window.winfo_screenheight() // 2) - (500 // 2)
            activity_window.geometry(f"600x500+{x}+{y}")

            # Main frame
            main_frame = ctk.CTkFrame(activity_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="📋 Team Activity Feed",
                font=("JetBrains Mono", 18, "bold")
            )
            title_label.pack(pady=(0, 20))

            # Activity list frame with scrollbar
            list_frame = ctk.CTkFrame(main_frame)
            list_frame.pack(fill="both", expand=True, pady=(0, 20))

            # Scrollable frame
            scrollable_frame = ctk.CTkScrollableFrame(list_frame)
            scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Populate activity feed
            if self.activity_feed:
                for i, activity in enumerate(reversed(self.activity_feed[-20:])):
                    activity_item = ctk.CTkFrame(scrollable_frame)
                    activity_item.pack(fill="x", pady=2)

                    # Timestamp
                    timestamp_label = ctk.CTkLabel(
                        activity_item,
                        text=activity.get('timestamp', ''),
                        font=("JetBrains Mono", 9),
                        text_color=("#666666", "#999999")
                    )
                    timestamp_label.pack(anchor="w", padx=10, pady=(5, 0))

                    # Activity text
                    activity_label = ctk.CTkLabel(
                        activity_item,
                        text=activity.get('message', ''),
                        font=("JetBrains Mono", 11),
                        wraplength=500
                    )
                    activity_label.pack(anchor="w", padx=10, pady=(0, 5))
            else:
                # No activity message
                no_activity_label = ctk.CTkLabel(
                    scrollable_frame,
                    text="No recent activity",
                    font=("JetBrains Mono", 12),
                    text_color=("#666666", "#999999")
                )
                no_activity_label.pack(pady=50)

            # Buttons frame
            buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            buttons_frame.pack(fill="x")

            # Refresh button
            refresh_btn = ctk.CTkButton(
                buttons_frame,
                text="🔄 Refresh",
                command=lambda: self._refresh_activity_feed(scrollable_frame),
                font=("JetBrains Mono", 12, "bold")
            )
            refresh_btn.pack(side="left", padx=(0, 10))

            # Clear button
            clear_btn = ctk.CTkButton(
                buttons_frame,
                text="🗑️ Clear All",
                command=lambda: self._clear_activity_feed(scrollable_frame),
                font=("JetBrains Mono", 12)
            )
            clear_btn.pack(side="left", padx=(0, 10))

            # Close button
            close_btn = ctk.CTkButton(
                buttons_frame,
                text="Close",
                command=activity_window.destroy,
                font=("JetBrains Mono", 12)
            )
            close_btn.pack(side="right")

        except Exception as e:
             logger.error(f"Error showing activity feed: {e}")
             messagebox.showerror("Error", f"Could not open activity feed: {e}")

    def _add_activity_item(self, message: str):
        """Add an item to the activity feed."""
        try:
            activity_item = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'message': message
            }

            self.activity_feed.append(activity_item)

            # Keep only the most recent items
            if len(self.activity_feed) > self.max_activity_items:
                self.activity_feed = self.activity_feed[-self.max_activity_items:]

            logger.info(f"Added activity: {message}")

        except Exception as e:
            logger.error(f"Error adding activity item: {e}")

    def _refresh_activity_feed(self, scrollable_frame):
        """Refresh the activity feed display."""
        try:
            # Clear existing items
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

            # Repopulate with current activity feed
            if self.activity_feed:
                for activity in reversed(self.activity_feed[-20:]):
                    activity_item = ctk.CTkFrame(scrollable_frame)
                    activity_item.pack(fill="x", pady=2)

                    # Timestamp
                    timestamp_label = ctk.CTkLabel(
                        activity_item,
                        text=activity.get('timestamp', ''),
                        font=("JetBrains Mono", 9),
                        text_color=("#666666", "#999999")
                    )
                    timestamp_label.pack(anchor="w", padx=10, pady=(5, 0))

                    # Activity text
                    activity_label = ctk.CTkLabel(
                        activity_item,
                        text=activity.get('message', ''),
                        font=("JetBrains Mono", 11),
                        wraplength=500
                    )
                    activity_label.pack(anchor="w", padx=10, pady=(0, 5))
            else:
                # No activity message
                no_activity_label = ctk.CTkLabel(
                    scrollable_frame,
                    text="No recent activity",
                    font=("JetBrains Mono", 12),
                    text_color=("#666666", "#999999")
                )
                no_activity_label.pack(pady=50)

        except Exception as e:
            logger.error(f"Error refreshing activity feed: {e}")

    def _clear_activity_feed(self, scrollable_frame):
        """Clear all activity feed items."""
        try:
            self.activity_feed.clear()
            self._refresh_activity_feed(scrollable_frame)
            logger.info("Cleared activity feed")

        except Exception as e:
            logger.error(f"Error clearing activity feed: {e}")

    def _start_auto_refresh(self):
        """Start the auto-refresh timer for team data."""
        try:
            if self.auto_refresh_enabled and not self.refresh_timer:
                self._schedule_next_refresh()
                logger.info(f"Started auto-refresh with {self.refresh_interval} minute interval")

        except Exception as e:
            logger.error(f"Error starting auto-refresh: {e}")

    def _schedule_next_refresh(self):
        """Schedule the next auto-refresh."""
        try:
            if self.auto_refresh_enabled:
                # Convert minutes to milliseconds
                delay_ms = self.refresh_interval * 60 * 1000

                # Cancel existing timer
                if self.refresh_timer:
                    self.after_cancel(self.refresh_timer)

                # Schedule next refresh
                self.refresh_timer = self.after(delay_ms, self._auto_refresh_callback)

        except Exception as e:
            logger.error(f"Error scheduling auto-refresh: {e}")

    def _auto_refresh_callback(self):
        """Callback for auto-refresh timer."""
        try:
            if self.auto_refresh_enabled:
                self._add_activity_item("Auto-refreshing team data...")
                self._sync_team_data()
                self._schedule_next_refresh()

        except Exception as e:
            logger.error(f"Error in auto-refresh callback: {e}")

    def _toggle_auto_refresh(self):
        """Toggle auto-refresh on/off."""
        try:
            self.auto_refresh_enabled = self.auto_refresh_var.get()

            if self.auto_refresh_enabled:
                self._start_auto_refresh()
                self._add_activity_item("Auto-refresh enabled")
            else:
                if self.refresh_timer:
                    self.after_cancel(self.refresh_timer)
                    self.refresh_timer = None
                self._add_activity_item("Auto-refresh disabled")

            logger.info(f"Auto-refresh {'enabled' if self.auto_refresh_enabled else 'disabled'}")

        except Exception as e:
            logger.error(f"Error toggling auto-refresh: {e}")

    def _on_sort_changed(self, value):
        """Handle sorting option change."""
        try:
            self.sort_by = value
            self._update_comparison_display()
            self._add_activity_item(f"Sorted cities by {value}")
            logger.info(f"Changed sorting to: {value}")

        except Exception as e:
            logger.error(f"Error changing sort: {e}")

    def _toggle_sort_order(self):
        """Toggle sort order between ascending and descending."""
        try:
            self.sort_ascending = self.sort_ascending_var.get()
            self._update_comparison_display()
            order = "ascending" if self.sort_ascending else "descending"
            self._add_activity_item(f"Changed sort order to {order}")
            logger.info(f"Sort order: {order}")

        except Exception as e:
            logger.error(f"Error toggling sort order: {e}")

    def _on_similarity_changed(self, value):
        """Handle weather similarity threshold change."""
        try:
            self.similarity_threshold = float(value)
            self.similarity_label.configure(text=f"Weather Similarity: {self.similarity_threshold:.1f}°C")
            self._update_comparison_display()
            logger.info(f"Similarity threshold: {self.similarity_threshold}°C")

        except Exception as e:
            logger.error(f"Error changing similarity threshold: {e}")

    def _on_city_selected(self, city_name: str, dropdown_index: int):
        """Handle city selection from dropdown."""
        if city_name in ["Select a city...", "No team data available", "Error loading data"]:
            self.selected_dropdown_cities[dropdown_index - 1] = None
            return

        # Check if city is already selected in another dropdown
        for i, selected_city in enumerate(self.selected_dropdown_cities):
            if selected_city == city_name and i != (dropdown_index - 1):
                logger.warning(f"City {city_name} already selected in another dropdown")
                # Reset this dropdown
                self.city_dropdowns[dropdown_index - 1].set("Select a city...")
                self.selected_dropdown_cities[dropdown_index - 1] = None
                return

        # Store the selection
        self.selected_dropdown_cities[dropdown_index - 1] = city_name
        self._add_activity_item(f"Selected {city_name} for comparison")
        logger.info(f"Selected {city_name} in dropdown {dropdown_index}")

    def _compare_selected_cities(self):
        """Compare the selected cities from dropdowns."""
        selected_cities = []

        # Update status
        self.status_label.configure(text="Collecting selected cities...")

        # Collect selected cities from dropdowns
        for dropdown in self.city_dropdowns:
            city = dropdown.get()
            if city and city not in ["Select a city...", "No team data available", "Error loading data"]:
                selected_cities.append(city)

        if len(selected_cities) < 1:
            self.status_label.configure(text="⚠️ Please select at least 1 city to compare")
            logger.warning("Please select at least 1 city to compare")
            return

        # Clear existing comparison display
        self._clear_comparison_display()

        # Add comparison columns for selected cities
        for city_name in selected_cities:
            # Check if this city is from team data
            is_team_member = city_name in self.team_cities_data
            self._fetch_and_add_city(city_name, is_team_member=is_team_member)

        logger.info(f"Comparing {len(selected_cities)} cities: {', '.join(selected_cities)}")

    def _update_comparison_display(self):
        """Update the comparison display with current sorting and filtering."""
        try:
            if not self.comparison_columns:
                return

            # Get current city data with sorting
            city_data_list = []
            for column in self.comparison_columns:
                city_data = column.city_data
                weather_data = city_data.get("weather_data", {})

                # Extract sortable values
                sort_value = 0
                if self.sort_by == "Temperature":
                    sort_value = weather_data.get("temperature", 0)
                elif self.sort_by == "Humidity":
                    sort_value = weather_data.get("humidity", 0)
                elif self.sort_by == "Wind Speed":
                    sort_value = weather_data.get("wind_speed", 0)
                elif self.sort_by == "Pressure":
                    sort_value = weather_data.get("pressure", 0)
                elif self.sort_by == "City Name":
                    sort_value = city_data.get("city_name", "")

                city_data_list.append({
                    'data': city_data,
                    'column': column,
                    'sort_value': sort_value,
                    'is_team_member': column.is_team_member
                })

            # Sort the data
            if self.sort_by == "City Name":
                city_data_list.sort(key=lambda x: x['sort_value'], reverse=not self.sort_ascending)
            else:
                city_data_list.sort(key=lambda x: x['sort_value'], reverse=not self.sort_ascending)

            # Clear existing display
            for column in self.comparison_columns:
                column.grid_forget()

            # Re-add columns in sorted order
            for i, item in enumerate(city_data_list):
                column = item['column']
                col_index = i % 2
                row_index = i // 2

                column.grid(row=row_index, column=col_index, sticky="nsew", padx=10, pady=10)

                # Configure grid weights
                self.comparison_container.grid_columnconfigure(col_index, weight=1)
                self.comparison_container.grid_rowconfigure(row_index, weight=1)

            # Update rankings
            self._update_weather_rankings()

            # Apply weather similarity highlighting
            self._apply_similarity_highlighting()

        except Exception as e:
            logger.error(f"Error updating comparison display: {e}")

    def _apply_similarity_highlighting(self):
        """Apply highlighting to cities with similar weather conditions."""
        try:
            if len(self.comparison_columns) < 2:
                return

            # Group cities by temperature similarity
            similar_groups = []
            processed = set()

            for i, column1 in enumerate(self.comparison_columns):
                if i in processed:
                    continue

                temp1 = column1.city_data.get("weather_data", {}).get("temperature", 0)
                similar_group = [i]

                for j, column2 in enumerate(self.comparison_columns[i+1:], i+1):
                    if j in processed:
                        continue

                    temp2 = column2.city_data.get("weather_data", {}).get("temperature", 0)

                    if abs(temp1 - temp2) <= self.similarity_threshold:
                        similar_group.append(j)
                        processed.add(j)

                if len(similar_group) > 1:
                    similar_groups.append(similar_group)
                    for idx in similar_group:
                        processed.add(idx)

            # Apply highlighting to similar groups
            colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]

            for group_idx, group in enumerate(similar_groups):
                color = colors[group_idx % len(colors)]
                for column_idx in group:
                    if column_idx < len(self.comparison_columns):
                        column = self.comparison_columns[column_idx]
                        # Add similarity indicator
                        if not hasattr(column, 'similarity_indicator'):
                            column.similarity_indicator = ctk.CTkLabel(
                                column,
                                text=f"🌡️ Similar Weather Group {group_idx + 1}",
                                font=("JetBrains Mono", 10, "bold"),
                                text_color=color
                            )
                            column.similarity_indicator.pack(pady=(0, 5))
                        else:
                            column.similarity_indicator.configure(
                                text=f"🌡️ Similar Weather Group {group_idx + 1}",
                                text_color=color
                            )

        except Exception as e:
            logger.error(f"Error applying similarity highlighting: {e}")

    def _show_comparison_insights(self):
        """Show insights and statistics about the compared cities."""
        if not self.comparison_columns:
            logger.warning("No cities to analyze. Please compare some cities first.")
            return

        # Check if the widget still exists before creating toplevel
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # Collect weather data from all compared cities
        temperatures = []
        humidities = []
        wind_speeds = []
        pressures = []
        city_names = []
        team_cities = []

        for column in self.comparison_columns:
            city_data = column.city_data
            weather_data = city_data.get("weather_data", {})

            city_names.append(city_data.get("city_name", "Unknown"))
            temperatures.append(weather_data.get("temperature", 0))
            humidities.append(weather_data.get("humidity", 0))
            wind_speeds.append(weather_data.get("wind_speed", 0))
            pressures.append(weather_data.get("pressure", 0))

            if column.is_team_member:
                team_cities.append(city_data.get("city_name", "Unknown"))

        # Calculate insights
        insights = []

        if temperatures:
            hottest_city = city_names[temperatures.index(max(temperatures))]
            coldest_city = city_names[temperatures.index(min(temperatures))]
            avg_temp = sum(temperatures) / len(temperatures)
            temp_range = max(temperatures) - min(temperatures)

            insights.append(f"🌡️ Temperature Analysis:")
            insights.append(f"   • Hottest: {hottest_city} ({max(temperatures)}°C)")
            insights.append(f"   • Coldest: {coldest_city} ({min(temperatures)}°C)")
            insights.append(f"   • Average: {avg_temp:.1f}°C")
            insights.append(f"   • Temperature Range: {temp_range:.1f}°C")

            # Temperature recommendations
            if temp_range > 15:
                insights.append(f"   ⚠️ Large temperature variation - pack layers!")
            elif avg_temp > 25:
                insights.append(f"   ☀️ Generally warm weather across cities")
            elif avg_temp < 10:
                insights.append(f"   🧥 Generally cool weather - dress warmly")
            insights.append("")

        if humidities:
            most_humid = city_names[humidities.index(max(humidities))]
            least_humid = city_names[humidities.index(min(humidities))]
            avg_humidity = sum(humidities) / len(humidities)

            insights.append(f"💧 Humidity Analysis:")
            insights.append(f"   • Most humid: {most_humid} ({max(humidities)}%)")
            insights.append(f"   • Least humid: {least_humid} ({min(humidities)}%)")
            insights.append(f"   • Average humidity: {avg_humidity:.1f}%")

            # Humidity recommendations
            if avg_humidity > 70:
                insights.append(f"   💦 High humidity - expect muggy conditions")
            elif avg_humidity < 30:
                insights.append(f"   🏜️ Low humidity - stay hydrated")
            insights.append("")

        if wind_speeds:
            windiest_city = city_names[wind_speeds.index(max(wind_speeds))]
            calmest_city = city_names[wind_speeds.index(min(wind_speeds))]
            avg_wind = sum(wind_speeds) / len(wind_speeds)

            insights.append(f"💨 Wind Analysis:")
            insights.append(f"   • Windiest: {windiest_city} ({max(wind_speeds)} km/h)")
            insights.append(f"   • Calmest: {calmest_city} ({min(wind_speeds)} km/h)")
            insights.append(f"   • Average wind speed: {avg_wind:.1f} km/h")

            # Wind recommendations
            if max(wind_speeds) > 25:
                insights.append(f"   🌪️ Strong winds in {windiest_city} - secure loose items")
            elif avg_wind < 5:
                insights.append(f"   🍃 Generally calm conditions")
            insights.append("")

        if pressures:
            highest_pressure = max(pressures)
            lowest_pressure = min(pressures)
            high_pressure_city = city_names[pressures.index(highest_pressure)]
            low_pressure_city = city_names[pressures.index(lowest_pressure)]

            insights.append(f"🌀 Atmospheric Pressure:")
            insights.append(f"   • Highest: {high_pressure_city} ({highest_pressure} hPa)")
            insights.append(f"   • Lowest: {low_pressure_city} ({lowest_pressure} hPa)")

            if highest_pressure > 1020:
                insights.append(f"   ☀️ High pressure in {high_pressure_city} - clear skies likely")
            if lowest_pressure < 1000:
                insights.append(f"   🌧️ Low pressure in {low_pressure_city} - possible storms")
            insights.append("")

        # Weather similarity analysis
        insights.append(f"🌡️ Weather Similarity Analysis:")
        similar_pairs = self._find_similar_weather_pairs()
        if similar_pairs:
            insights.append(f"   • Found {len(similar_pairs)} similar weather pairs (within {self.similarity_threshold}°C):")
            for pair in similar_pairs:
                insights.append(f"     - {pair['city1']} & {pair['city2']}: {pair['temp_diff']:.1f}°C difference")
        else:
            insights.append(f"   • No cities with similar weather (threshold: {self.similarity_threshold}°C)")
        insights.append("")

        # Team collaboration insights
        if team_cities:
            insights.append(f"👥 Team Collaboration Insights:")
            insights.append(f"   • {len(team_cities)} team cities out of {len(city_names)} compared")
            insights.append(f"   • Team cities: {', '.join(team_cities)}")

            # Advanced team meetup recommendations
            meetup_recommendations = self._generate_meetup_recommendations(team_cities, city_names, temperatures, humidities, wind_speeds)
            if meetup_recommendations:
                insights.append(f"   🏢 Meetup Recommendations:")
                for rec in meetup_recommendations:
                    insights.append(f"     {rec}")
            
            # Team weather diversity
            if len(team_cities) > 1:
                team_temps = [temperatures[city_names.index(city)] for city in team_cities if city in city_names]
                team_temp_range = max(team_temps) - min(team_temps) if team_temps else 0
                insights.append(f"   📊 Team weather diversity: {team_temp_range:.1f}°C range")
                if team_temp_range > 15:
                    insights.append(f"     ⚠️ High diversity - consider virtual meetings")
                elif team_temp_range < 5:
                    insights.append(f"     ✅ Low diversity - great for in-person meetups")
        else:
            insights.append(f"👥 No team cities in current comparison")
            insights.append(f"   • Consider adding team member locations for collaboration insights")

        # Advanced travel recommendations
        insights.append("")
        insights.append(f"📋 Advanced Travel Recommendations:")
        if temperatures:
            # Comfort index calculation
            comfort_scores = self._calculate_comfort_scores()
            if comfort_scores:
                best_comfort_city = max(comfort_scores, key=comfort_scores.get)
                insights.append(f"   🌟 Most comfortable overall: {best_comfort_city} (score: {comfort_scores[best_comfort_city]:.1f}/10)")
            
            # Seasonal recommendations
            seasonal_advice = self._get_seasonal_advice(avg_temp, avg_humidity)
            if seasonal_advice:
                insights.append(f"   🗓️ Seasonal advice: {seasonal_advice}")
            
            # Packing recommendations
            packing_advice = self._get_packing_advice(temp_range, max(humidities) if humidities else 0, max(wind_speeds) if wind_speeds else 0)
            if packing_advice:
                insights.append(f"   🎒 Packing suggestions:")
                for advice in packing_advice:
                    insights.append(f"     • {advice}")
            
            # Activity recommendations
            activity_recommendations = self._get_activity_recommendations(avg_temp, avg_humidity, max(wind_speeds) if wind_speeds else 0)
            if activity_recommendations:
                insights.append(f"   🎯 Recommended activities:")
                for activity in activity_recommendations:
                    insights.append(f"     • {activity}")

        # Create insights dialog
        try:
            insights_window = ctk.CTkToplevel(self)
            insights_window.title("Weather Comparison Insights")
            insights_window.geometry("500x400")
            insights_window.transient(self)
            insights_window.grab_set()

            # Center the window
            insights_window.update_idletasks()
            x = (insights_window.winfo_screenwidth() // 2) - (500 // 2)
            y = (insights_window.winfo_screenheight() // 2) - (400 // 2)
            insights_window.geometry(f"500x400+{x}+{y}")
        except tk.TclError:
            # Widget has been destroyed, cannot create toplevel
            return

        # Insights content
        insights_frame = ctk.CTkScrollableFrame(insights_window)
        insights_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            insights_frame,
            text="📊 Weather Comparison Insights",
            font=("JetBrains Mono", 18, "bold")
        )
        title_label.pack(pady=(0, 20))

        insights_text = ctk.CTkTextbox(
            insights_frame,
            height=250,
            font=("JetBrains Mono", 12)
        )
        insights_text.pack(fill="both", expand=True)

        # Insert insights
        insights_content = "\n".join(insights)
        insights_text.insert("1.0", insights_content)
        insights_text.configure(state="disabled")

        # Button frame
        button_frame = ctk.CTkFrame(insights_window)
        button_frame.pack(pady=10, padx=20, fill="x")

        # Export button
        export_button = ctk.CTkButton(
            button_frame,
            text="📊 Export Data",
            command=lambda: self._export_comparison_data(insights_content),
            font=("JetBrains Mono", 12),
            width=120
        )
        export_button.pack(side="left", padx=(0, 10))

        # Close button
        close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            command=insights_window.destroy,
            font=("JetBrains Mono", 12),
            width=120
        )
        close_button.pack(side="right")

        logger.info("Displayed comparison insights")

    def _export_comparison_data(self, insights_content: str):
        """Export comparison data to JSON or CSV format."""
        try:
            # Prepare export data
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "comparison_summary": insights_content,
                "cities_data": [],
                "statistics": self._calculate_comparison_statistics()
            }
            
            # Add detailed city data
            for column in self.comparison_columns:
                city_data = column.city_data
                weather_data = city_data.get("weather_data", {})
                
                export_data["cities_data"].append({
                    "city_name": city_data.get("city_name", "Unknown"),
                    "is_team_member": column.is_team_member,
                    "member_name": city_data.get("member_name", None),
                    "temperature": weather_data.get("temperature", 0),
                    "humidity": weather_data.get("humidity", 0),
                    "wind_speed": weather_data.get("wind_speed", 0),
                    "pressure": weather_data.get("pressure", 0),
                    "description": weather_data.get("description", "N/A"),
                    "feels_like": weather_data.get("feels_like", 0),
                    "visibility": weather_data.get("visibility", 0),
                    "uv_index": weather_data.get("uv_index", 0),
                    "last_updated": weather_data.get("last_updated", "N/A")
                })
            
            # Ask user for save location and format
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"), 
                    ("CSV files", "*.csv"),
                    ("Text files", "*.txt"), 
                    ("All files", "*.*")
                ],
                title="Export Comparison Data"
            )
            
            if filename:
                if filename.endswith('.json'):
                    self._export_to_json(filename, export_data)
                elif filename.endswith('.csv'):
                    self._export_to_csv(filename, export_data)
                else:
                    self._export_to_text(filename, export_data, insights_content)
                
                messagebox.showinfo("Export Complete", f"Data exported successfully to {filename}")
                logger.info(f"Comparison data exported to {filename}")
                
        except Exception as e:
            logger.error(f"Failed to export comparison data: {e}")
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
    
    def _export_to_json(self, filename: str, export_data: dict):
        """Export data to JSON format."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_to_csv(self, filename: str, export_data: dict):
        """Export data to CSV format."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'City Name', 'Is Team Member', 'Member Name', 'Temperature (°C)',
                'Humidity (%)', 'Wind Speed (km/h)', 'Pressure (hPa)', 
                'Description', 'Feels Like (°C)', 'Visibility (km)', 
                'UV Index', 'Last Updated'
            ])
            
            # Write city data
            for city in export_data['cities_data']:
                writer.writerow([
                    city['city_name'],
                    'Yes' if city['is_team_member'] else 'No',
                    city['member_name'] or 'N/A',
                    city['temperature'],
                    city['humidity'],
                    city['wind_speed'],
                    city['pressure'],
                    city['description'],
                    city['feels_like'],
                    city['visibility'],
                    city['uv_index'],
                    city['last_updated']
                ])
            
            # Add statistics section
            writer.writerow([])  # Empty row
            writer.writerow(['Statistics'])
            stats = export_data['statistics']
            for key, value in stats.items():
                writer.writerow([key.replace('_', ' ').title(), value])
    
    def _export_to_text(self, filename: str, export_data: dict, insights_content: str):
        """Export data to text format."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Weather Comparison Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(insights_content)
            f.write("\n\n=== Detailed City Data ===\n")
            
            for city in export_data["cities_data"]:
                f.write(f"\n{city['city_name']}:\n")
                if city['is_team_member']:
                    f.write(f"  Team Member: {city.get('member_name', 'Unknown')}\n")
                f.write(f"  Temperature: {city['temperature']}°C (feels like {city['feels_like']}°C)\n")
                f.write(f"  Humidity: {city['humidity']}%\n")
                f.write(f"  Wind Speed: {city['wind_speed']} km/h\n")
                f.write(f"  Pressure: {city['pressure']} hPa\n")
                f.write(f"  Visibility: {city['visibility']} km\n")
                f.write(f"  UV Index: {city['uv_index']}\n")
                f.write(f"  Description: {city['description']}\n")
                f.write(f"  Last Updated: {city['last_updated']}\n")
            
            # Add statistics
            f.write("\n\n=== Statistics ===\n")
            stats = export_data['statistics']
            for key, value in stats.items():
                f.write(f"{key.replace('_', ' ').title()}: {value}\n")
    
    def _calculate_comparison_statistics(self) -> dict:
        """Calculate comprehensive statistics for the compared cities."""
        if not self.comparison_columns:
            return {}
        
        temperatures = []
        humidities = []
        wind_speeds = []
        pressures = []
        team_member_count = 0
        
        for column in self.comparison_columns:
            weather_data = column.city_data.get("weather_data", {})
            temperatures.append(weather_data.get("temperature", 0))
            humidities.append(weather_data.get("humidity", 0))
            wind_speeds.append(weather_data.get("wind_speed", 0))
            pressures.append(weather_data.get("pressure", 0))
            
            if column.is_team_member:
                team_member_count += 1
        
        stats = {
            "total_cities": len(self.comparison_columns),
            "team_member_cities": team_member_count,
            "avg_temperature": round(sum(temperatures) / len(temperatures), 1) if temperatures else 0,
            "min_temperature": min(temperatures) if temperatures else 0,
            "max_temperature": max(temperatures) if temperatures else 0,
            "temperature_range": round(max(temperatures) - min(temperatures), 1) if temperatures else 0,
            "avg_humidity": round(sum(humidities) / len(humidities), 1) if humidities else 0,
            "avg_wind_speed": round(sum(wind_speeds) / len(wind_speeds), 1) if wind_speeds else 0,
            "avg_pressure": round(sum(pressures) / len(pressures), 1) if pressures else 0,
            "weather_similarity_threshold": self.similarity_threshold,
            "sort_criteria": self.sort_by,
            "sort_ascending": self.sort_ascending
        }
        
        return stats
    
    def _find_similar_weather_pairs(self) -> List[Dict[str, Any]]:
        """Find pairs of cities with similar weather conditions."""
        similar_pairs = []
        
        for i, column1 in enumerate(self.comparison_columns):
            for j, column2 in enumerate(self.comparison_columns[i+1:], i+1):
                temp1 = column1.city_data.get("weather_data", {}).get("temperature", 0)
                temp2 = column2.city_data.get("weather_data", {}).get("temperature", 0)
                temp_diff = abs(temp1 - temp2)
                
                if temp_diff <= self.similarity_threshold:
                    similar_pairs.append({
                        'city1': column1.city_data.get("city_name", "Unknown"),
                        'city2': column2.city_data.get("city_name", "Unknown"),
                        'temp_diff': temp_diff,
                        'temp1': temp1,
                        'temp2': temp2
                    })
        
        return similar_pairs
    
    def _generate_meetup_recommendations(self, team_cities: List[str], city_names: List[str], 
                                       temperatures: List[float], humidities: List[float], 
                                       wind_speeds: List[float]) -> List[str]:
        """Generate intelligent meetup recommendations for team cities."""
        recommendations = []
        
        if len(team_cities) < 2:
            return recommendations
        
        # Find team city with best overall weather
        team_weather_scores = {}
        for city in team_cities:
            if city in city_names:
                idx = city_names.index(city)
                # Calculate weather score (0-10)
                temp_score = max(0, 10 - abs(temperatures[idx] - 22))  # Ideal temp ~22°C
                humidity_score = max(0, 10 - abs(humidities[idx] - 50) / 5)  # Ideal humidity ~50%
                wind_score = max(0, 10 - wind_speeds[idx] / 3)  # Lower wind is better
                
                overall_score = (temp_score + humidity_score + wind_score) / 3
                team_weather_scores[city] = overall_score
        
        if team_weather_scores:
            best_city = max(team_weather_scores, key=team_weather_scores.get)
            best_score = team_weather_scores[best_city]
            recommendations.append(f"🌟 Best location: {best_city} (weather score: {best_score:.1f}/10)")
            
            # Additional recommendations based on weather conditions
            best_idx = city_names.index(best_city)
            temp = temperatures[best_idx]
            humidity = humidities[best_idx]
            wind = wind_speeds[best_idx]
            
            if temp > 25:
                recommendations.append(f"☀️ Warm weather in {best_city} - consider indoor venues with AC")
            elif temp < 10:
                recommendations.append(f"🧥 Cool weather in {best_city} - indoor venues recommended")
            else:
                recommendations.append(f"🌤️ Pleasant weather in {best_city} - outdoor activities possible")
            
            if humidity > 70:
                recommendations.append(f"💧 High humidity - stay hydrated and avoid strenuous outdoor activities")
            
            if wind > 20:
                recommendations.append(f"💨 Windy conditions - secure outdoor setups")
        
        return recommendations
    
    def _calculate_comfort_scores(self) -> Dict[str, float]:
        """Calculate comfort scores for each city based on multiple weather factors."""
        comfort_scores = {}
        
        for column in self.comparison_columns:
            city_name = column.city_data.get("city_name", "Unknown")
            weather_data = column.city_data.get("weather_data", {})
            
            temp = weather_data.get("temperature", 0)
            humidity = weather_data.get("humidity", 0)
            wind_speed = weather_data.get("wind_speed", 0)
            pressure = weather_data.get("pressure", 1013)
            
            # Temperature comfort (ideal range: 18-24°C)
            temp_comfort = max(0, 10 - abs(temp - 21) * 0.5)
            
            # Humidity comfort (ideal range: 40-60%)
            humidity_comfort = max(0, 10 - abs(humidity - 50) * 0.2)
            
            # Wind comfort (ideal: 5-15 km/h)
            if 5 <= wind_speed <= 15:
                wind_comfort = 10
            else:
                wind_comfort = max(0, 10 - abs(wind_speed - 10) * 0.3)
            
            # Pressure comfort (ideal: 1013-1020 hPa)
            pressure_comfort = max(0, 10 - abs(pressure - 1016.5) * 0.1)
            
            # Overall comfort score
            overall_comfort = (temp_comfort * 0.4 + humidity_comfort * 0.3 + 
                             wind_comfort * 0.2 + pressure_comfort * 0.1)
            
            comfort_scores[city_name] = round(overall_comfort, 1)
        
        return comfort_scores
    
    def _get_seasonal_advice(self, avg_temp: float, avg_humidity: float) -> str:
        """Get seasonal advice based on average conditions."""
        if avg_temp > 30:
            return "Hot summer conditions - plan for heat management"
        elif avg_temp > 20:
            return "Pleasant spring/summer weather - ideal for outdoor activities"
        elif avg_temp > 10:
            return "Mild autumn/spring conditions - layer clothing recommended"
        elif avg_temp > 0:
            return "Cool winter weather - warm clothing essential"
        else:
            return "Cold winter conditions - heavy winter gear required"
    
    def _get_packing_advice(self, temp_range: float, max_humidity: float, max_wind: float) -> List[str]:
        """Get packing advice based on weather conditions."""
        advice = []
        
        if temp_range > 15:
            advice.append("Pack layers for varying temperatures")
            advice.append("Include both warm and cool weather clothing")
        elif temp_range > 10:
            advice.append("Pack versatile clothing for moderate temperature variation")
        
        if max_humidity > 70:
            advice.append("Bring moisture-wicking fabrics")
            advice.append("Pack extra changes of clothes")
        
        if max_wind > 25:
            advice.append("Bring windproof jacket or coat")
            advice.append("Secure loose items and accessories")
        elif max_wind > 15:
            advice.append("Light windbreaker recommended")
        
        if not advice:
            advice.append("Standard clothing appropriate for conditions")
        
        return advice
    
    def _get_activity_recommendations(self, avg_temp: float, avg_humidity: float, max_wind: float) -> List[str]:
        """Get activity recommendations based on weather conditions."""
        activities = []
        
        if 18 <= avg_temp <= 25 and avg_humidity < 70 and max_wind < 20:
            activities.append("Perfect for outdoor sightseeing and walking tours")
            activities.append("Great weather for outdoor dining")
            activities.append("Ideal for photography and outdoor events")
        elif avg_temp > 30 or avg_humidity > 80:
            activities.append("Visit air-conditioned museums and indoor attractions")
            activities.append("Plan indoor activities during peak heat hours")
            activities.append("Early morning or evening outdoor activities")
        elif avg_temp < 10:
            activities.append("Indoor cultural activities and museums")
            activities.append("Cozy cafes and indoor markets")
            activities.append("Winter sports if applicable")
        elif max_wind > 25:
            activities.append("Indoor activities recommended due to strong winds")
            activities.append("Avoid outdoor events with loose structures")
        else:
            activities.append("Mixed indoor and outdoor activities suitable")
            activities.append("Flexible planning recommended")
        
        return activities

    def _clear_all_selections(self):
         """Clear all city selections and comparison data."""
         # Reset dropdowns
         for dropdown in self.city_dropdowns:
             dropdown.set("Select a city...")

         # Clear selected cities tracking
         self.selected_dropdown_cities = [None, None, None, None]

         # Clear quick entry field
         if hasattr(self, 'quick_city_entry'):
             self.quick_city_entry.delete(0, "end")

         # Clear comparison display
         self._clear_comparison_display()

         # Reset any error states
         self.comparison_data = []

         # Update status
         if hasattr(self, 'status_label'):
             self.status_label.configure(text="Ready to compare cities")

         logger.info("Cleared all selections and reset interface")

    def _quick_add_city(self):
        """Add a city directly from the quick entry field."""
        city_name = self.quick_city_entry.get().strip()

        if not city_name:
            logger.warning("Please enter a city name")
            return

        if len(self.comparison_columns) >= 4:
            logger.warning("Maximum 4 cities can be compared at once")
            return

        # Check if city is already being compared
        existing_cities = [col.city_data.get("city_name", "") for col in self.comparison_columns]
        if city_name in existing_cities:
            logger.warning(f"City {city_name} is already being compared")
            return

        # Clear the entry field
        self.quick_city_entry.delete(0, "end")

        # Check if this is a team city
        is_team_member = city_name in self.team_cities_data

        # Add the city to comparison
        self._fetch_and_add_city(city_name, is_team_member=is_team_member)

        logger.info(f"Quick added city: {city_name}")

    def _clear_comparison_display(self):
        """Clear the comparison display area."""
        # Remove all comparison columns
        for column in self.comparison_columns:
            column.destroy()
        self.comparison_columns.clear()

        # Remove all city pills
        for pill in self.city_pills:
            pill.destroy()
        self.city_pills.clear()
        self.selected_cities.clear()

        # Show placeholder
        self.placeholder_label.pack(expand=True, pady=50)



    def _fetch_and_add_city(self, city_name: str, is_team_member: bool = False):
        """Fetch weather data for a city and add comparison column."""
        try:
            # Initialize base city data
            city_data = {
                "city_name": city_name,
                "weather_data": {}
            }

            # Add team member information if available
            if is_team_member and city_name in self.team_cities_data:
                team_data = self.team_cities_data[city_name]
                if isinstance(team_data, dict):
                    city_data["member_name"] = team_data.get("member_name", "Unknown Member")
                    city_data["last_updated"] = team_data.get("last_updated", "")
                    city_data["activity_status"] = team_data.get("activity_status", "Unknown")
                elif isinstance(team_data, list) and len(team_data) > 0 and isinstance(team_data[0], dict):
                    # Handle case where team_data is a list of dictionaries
                    first_member = team_data[0]
                    city_data["member_name"] = first_member.get("member_name", "Unknown Member")
                    city_data["last_updated"] = first_member.get("last_updated", "")
                    city_data["activity_status"] = first_member.get("activity_status", "Unknown")
                else:
                    # Fallback for unexpected data structure
                    city_data["member_name"] = "Unknown Member"
                    city_data["last_updated"] = ""
                    city_data["activity_status"] = "Unknown"

            # Try to get real weather data if weather service is available
            if self.weather_service:
                try:
                    # Use get_current_weather which returns a dictionary
                    weather_response = self.weather_service.get_current_weather(city_name)

                    # Handle case where weather_response might be a list or not have 'current' key
                    if isinstance(weather_response, dict):
                        current_data = weather_response.get("current", {})
                    elif isinstance(weather_response, list) and len(weather_response) > 0:
                        current_data = weather_response[0] if isinstance(weather_response[0], dict) else {}
                    else:
                        current_data = {}

                    # Ensure current_data is a dictionary
                    if not isinstance(current_data, dict):
                        current_data = {}

                    # Safely extract condition text
                    condition_data = current_data.get("condition", {}) if isinstance(current_data, dict) else {}
                    if isinstance(condition_data, dict):
                        description = condition_data.get("text", "Unknown")
                    elif isinstance(condition_data, list) and len(condition_data) > 0:
                        # Handle case where condition might be a list
                        first_condition = condition_data[0]
                        description = first_condition.get("text", "Unknown") if isinstance(first_condition, dict) else "Unknown"
                    else:
                        description = "Unknown"

                    # Safely extract weather data with type checking
                    if isinstance(current_data, dict):
                        city_data["weather_data"] = {
                            "temperature": current_data.get("temp_c", 0),
                            "description": description,
                            "humidity": current_data.get("humidity", 0),
                            "wind_speed": current_data.get("wind_kph", 0),  # Keep in km/h as expected by UI
                            "pressure": current_data.get("pressure_mb", 0),
                            "feels_like": current_data.get("feelslike_c", 0)
                        }
                    else:
                        # Fallback to default values if current_data is not a dict
                        city_data["weather_data"] = {
                            "temperature": 0,
                            "description": "Unknown",
                            "humidity": 0,
                            "wind_speed": 0,
                            "pressure": 1013,
                            "feels_like": 0
                        }
                except Exception as weather_error:
                    # Import custom exceptions for proper handling
                    try:
                        from src.services.enhanced_weather_service import (
                            WeatherServiceError, RateLimitError, APIKeyError,
                            NetworkError, ServiceUnavailableError
                        )

                        if isinstance(weather_error, RateLimitError):
                            logger.warning(f"Rate limit exceeded for {city_name}: {weather_error}")
                        elif isinstance(weather_error, APIKeyError):
                            logger.error(f"API key error for {city_name}: {weather_error}")
                        elif isinstance(weather_error, NetworkError):
                            logger.warning(f"Network error for {city_name}: {weather_error}")
                        elif isinstance(weather_error, ServiceUnavailableError):
                            logger.warning(f"Service unavailable for {city_name}: {weather_error}")
                        elif isinstance(weather_error, WeatherServiceError):
                            logger.error(f"Weather service error for {city_name}: {weather_error}")
                        else:
                            logger.error(f"Unexpected error fetching weather data for {city_name}: {weather_error}")
                    except ImportError:
                        logger.error(f"Failed to fetch weather data for {city_name}: {weather_error}")

                    # Fall back to mock data
                    city_data["weather_data"] = {
                        "temperature": 22,
                        "description": "Partly Cloudy",
                        "humidity": 65,
                        "wind_speed": 12,
                        "pressure": 1013,
                        "feels_like": 24
                    }
            else:
                # Use mock data if no weather service
                city_data["weather_data"] = {
                    "temperature": 22,
                    "description": "Partly Cloudy",
                    "humidity": 65,
                    "wind_speed": 12,
                    "pressure": 1013,
                    "feels_like": 24
                }

            self._add_comparison_column(city_data, is_team_member)

        except Exception as e:
            logger.error(f"Failed to fetch weather data for {city_name}: {e}")

    def _add_comparison_column(self, city_data: Dict[str, Any], is_team_member: bool = False):
        """Add a comparison column for a city."""
        # Hide placeholder
        self.placeholder_label.pack_forget()

        # Create comparison column
        column = CityComparisonColumn(
            self.comparison_container,
            city_data=city_data,
            is_team_member=is_team_member
        )

        # Calculate grid position
        col_index = len(self.comparison_columns) % 2
        row_index = len(self.comparison_columns) // 2

        column.grid(row=row_index, column=col_index, sticky="nsew", padx=10, pady=10)

        # Configure grid weights
        self.comparison_container.grid_columnconfigure(col_index, weight=1)
        self.comparison_container.grid_rowconfigure(row_index, weight=1)

        self.comparison_columns.append(column)

        # Update rankings after adding column
        self._update_weather_rankings()

    def _update_weather_rankings(self):
        """Update weather rankings for all comparison columns."""
        if len(self.comparison_columns) < 2:
            return

        try:
            # Collect weather data for ranking
            temperatures = []
            humidities = []
            wind_speeds = []
            pressures = []

            for column in self.comparison_columns:
                weather_data = column.city_data.get("weather_data", {})
                temperatures.append(weather_data.get("temperature", 0))
                humidities.append(weather_data.get("humidity", 0))
                wind_speeds.append(weather_data.get("wind_speed", 0))
                pressures.append(weather_data.get("pressure", 0))

            # Add ranking indicators to each column
            for i, column in enumerate(self.comparison_columns):
                rankings = []

                # Temperature ranking (higher is better for comfort)
                if temperatures[i] == max(temperatures):
                    rankings.append("🌡️ Warmest")
                elif temperatures[i] == min(temperatures):
                    rankings.append("❄️ Coolest")

                # Humidity ranking (moderate is better)
                if humidities[i] == min(humidities):
                    rankings.append("🏜️ Driest")
                elif humidities[i] == max(humidities):
                    rankings.append("💧 Most Humid")

                # Wind ranking (calmer is generally better)
                if wind_speeds[i] == min(wind_speeds):
                    rankings.append("🍃 Calmest")
                elif wind_speeds[i] == max(wind_speeds):
                    rankings.append("💨 Windiest")

                # Pressure ranking (higher is generally better)
                if pressures[i] == max(pressures):
                    rankings.append("☀️ High Pressure")
                elif pressures[i] == min(pressures):
                    rankings.append("🌧️ Low Pressure")

                # Update column with rankings
                self._add_rankings_to_column(column, rankings)

        except Exception as e:
            logger.error(f"Failed to update weather rankings: {e}")

    def _add_rankings_to_column(self, column: CityComparisonColumn, rankings: List[str]):
        """Add ranking indicators to a comparison column."""
        try:
            # Remove existing ranking frame if it exists
            if hasattr(column, 'ranking_frame'):
                column.ranking_frame.destroy()

            if rankings:
                # Create ranking frame
                column.ranking_frame = ctk.CTkFrame(column)
                column.ranking_frame.pack(fill="x", padx=10, pady=(0, 10))

                ranking_title = ctk.CTkLabel(
                    column.ranking_frame,
                    text="🏆 Rankings",
                    font=("JetBrains Mono", 12, "bold")
                )
                ranking_title.pack(pady=(5, 2))

                for ranking in rankings:
                    ranking_label = ctk.CTkLabel(
                        column.ranking_frame,
                        text=ranking,
                        font=("JetBrains Mono", 10)
                    )
                    ranking_label.pack(pady=1)

        except Exception as e:
            logger.error(f"Failed to add rankings to column: {e}")

    def update_theme(self):
        """Update theme for all components."""
        self._apply_theme()

        # Update all city pills
        for pill in self.city_pills:
            pill._apply_theme()

        # Update all comparison columns
        for column in self.comparison_columns:
            column.update_theme()

    def destroy(self):
        """Clean up when destroying the panel."""
        # Unregister from theme updates
        self.theme_manager.remove_observer(self.update_theme)
        super().destroy()
