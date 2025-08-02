"""City Comparison Panel for team collaboration and multi-city weather comparison."""

import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

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
        
        # City name
        city_name = self.city_data.get("city_name", "Unknown City")
        self.city_label = ctk.CTkLabel(
            header_frame,
            text=f"🏙️ {city_name}",
            font=("JetBrains Mono", 18, "bold")
        )
        self.city_label.pack()
        
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
        
        self._setup_ui()
        self._apply_theme()
        
        # Register for theme updates
        self.theme_manager.add_observer(self.update_theme)
    
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
        self.activity_btn.pack(side="left")
        
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
        
        self.clear_btn = ctk.CTkButton(
            control_buttons_frame,
            text="🗑️ Clear All",
            command=self._clear_all_selections,
            font=("JetBrains Mono", 12, "bold"),
            width=120
        )
        self.clear_btn.pack(side="left")
        
        # Store dropdown references
        self.city_dropdowns = [self.city1_dropdown, self.city2_dropdown, self.city3_dropdown, self.city4_dropdown]
        self.selected_dropdown_cities = [None, None, None, None]  # Track selections by dropdown index
        
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
        """Sync team data from GitHub and populate dropdowns."""
        try:
            self.sync_btn.configure(text="🔄 Syncing...", state="disabled")
            self.update()
            
            team_cities = self.github_service.force_refresh()
            
            if team_cities:
                # Extract unique city names for dropdowns
                city_names = list(set([team_city.city_name for team_city in team_cities]))
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
                
                # Store team data for later use
                self.team_cities_data = {}
                for team_city in team_cities:
                    if team_city.city_name not in self.team_cities_data:
                        self.team_cities_data[team_city.city_name] = []
                    self.team_cities_data[team_city.city_name].append({
                        "city_name": team_city.city_name,
                        "member_name": team_city.member_name,
                        "last_updated": team_city.last_updated,
                        "weather_data": team_city.weather_data
                    })
                
                logger.info(f"Synced {len(team_cities)} team cities, {len(city_names)} unique cities")
            else:
                # No team data available, show message
                logger.warning("No team cities data available")
                for dropdown in self.city_dropdowns:
                    dropdown.configure(values=["No team data available"])
                    dropdown.set("No team data available")
            
        except Exception as e:
            logger.error(f"Failed to sync team data: {e}")
            # Show error in dropdowns
            for dropdown in self.city_dropdowns:
                dropdown.configure(values=["Error loading data"])
                dropdown.set("Error loading data")
        finally:
            self.sync_btn.configure(text="🔄 Sync Team Data", state="normal")
    
    def _show_share_dialog(self):
        """Show dialog for sharing current city."""
        # TODO: Implement share dialog
        logger.info("Share dialog not implemented yet")
    
    def _show_activity_feed(self):
        """Show team activity feed."""
        # TODO: Implement activity feed window
        logger.info("Activity feed not implemented yet")
    
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
        logger.info(f"Selected {city_name} in dropdown {dropdown_index}")
    
    def _compare_selected_cities(self):
        """Compare the selected cities from dropdowns."""
        # Get selected cities (filter out None values)
        selected_cities = [city for city in self.selected_dropdown_cities if city is not None]
        
        if len(selected_cities) < 2:
            logger.warning("Please select at least 2 cities to compare")
            return
        
        # Clear existing comparison columns
        self._clear_comparison_display()
        
        # Add comparison columns for selected cities
        for city_name in selected_cities:
            if city_name in getattr(self, 'team_cities_data', {}):
                # Use the first team member's data for this city
                city_data = self.team_cities_data[city_name][0]
                self._add_comparison_column(city_data, is_team_member=True)
            else:
                # Fallback to mock data if team data not available
                self._fetch_and_add_city(city_name, is_team_member=False)
        
        logger.info(f"Comparing {len(selected_cities)} cities: {', '.join(selected_cities)}")
    
    def _clear_all_selections(self):
        """Clear all dropdown selections and comparison display."""
        # Reset all dropdowns
        for dropdown in self.city_dropdowns:
            dropdown.set("Select a city...")
        
        # Clear selection tracking
        self.selected_dropdown_cities = [None, None, None, None]
        
        # Clear comparison display
        self._clear_comparison_display()
        
        logger.info("Cleared all selections")
    
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
            # Try to get real weather data if weather service is available
            if self.weather_service:
                try:
                    weather_data = self.weather_service.get_weather(city_name)
                    city_data = {
                        "city_name": city_name,
                        "weather_data": {
                            "temperature": weather_data.get("temperature", 0),
                            "description": weather_data.get("description", "Unknown"),
                            "humidity": weather_data.get("humidity", 0),
                            "wind_speed": weather_data.get("wind_speed", 0),
                            "pressure": weather_data.get("pressure", 0),
                            "feels_like": weather_data.get("feels_like", 0)
                        }
                    }
                except Exception as weather_error:
                    logger.warning(f"Failed to fetch real weather data for {city_name}, using mock data: {weather_error}")
                    # Fall back to mock data
                    city_data = {
                        "city_name": city_name,
                        "weather_data": {
                            "temperature": 22,
                            "description": "Partly Cloudy",
                            "humidity": 65,
                            "wind_speed": 12,
                            "pressure": 1013,
                            "feels_like": 24
                        }
                    }
            else:
                # Use mock data if no weather service
                city_data = {
                    "city_name": city_name,
                    "weather_data": {
                        "temperature": 22,
                        "description": "Partly Cloudy",
                        "humidity": 65,
                        "wind_speed": 12,
                        "pressure": 1013,
                        "feels_like": 24
                    }
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