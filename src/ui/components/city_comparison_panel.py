"""City Comparison Panel for team collaboration and multi-city weather comparison."""

import customtkinter as ctk
import tkinter as tk
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
        self.clear_btn.pack(side="left")
        
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
        """Sync team data from GitHub and populate dropdowns."""
        try:
            self.sync_btn.configure(text="🔄 Syncing...", state="disabled")
            self.update()
            
            team_cities = self.github_service.force_refresh()
            
            if team_cities:
                # Extract unique city names for dropdowns, filtering out empty/invalid entries
                city_names = list(set([
                    team_city.city_name.strip() for team_city in team_cities 
                    if team_city.city_name and team_city.city_name.strip() and team_city.city_name.strip() != "N/A"
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
        
        # Team collaboration insights
        if team_cities:
            insights.append(f"👥 Team Collaboration Insights:")
            insights.append(f"   • {len(team_cities)} team cities out of {len(city_names)} compared")
            insights.append(f"   • Team cities: {', '.join(team_cities)}")
            
            # Find best weather for team meetups
            if team_cities and len(team_cities) > 1:
                team_temps = [temperatures[city_names.index(city)] for city in team_cities if city in city_names]
                if team_temps:
                    best_temp_city = team_cities[team_temps.index(max(team_temps))]
                    insights.append(f"   🏢 Best weather for team meetup: {best_temp_city}")
        else:
            insights.append(f"👥 No team cities in current comparison")
            insights.append(f"   • Consider adding team member locations for collaboration insights")
        
        # Overall recommendations
        insights.append("")
        insights.append(f"📋 Travel Recommendations:")
        if temperatures:
            if temp_range > 20:
                insights.append(f"   • Pack for varied climates - temperature varies by {temp_range:.1f}°C")
            best_weather_city = city_names[temperatures.index(max(temperatures))] if avg_temp < 20 else city_names[temperatures.index(min(temperatures))]
            insights.append(f"   • Most comfortable weather: {best_weather_city}")
        
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
        """Export comparison data to a file."""
        try:
            from tkinter import filedialog
            import json
            from datetime import datetime
            
            # Prepare export data
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "comparison_summary": insights_content,
                "cities_data": []
            }
            
            # Add detailed city data
            for column in self.comparison_columns:
                city_data = column.city_data
                export_data["cities_data"].append({
                    "city_name": city_data.get("city_name", "Unknown"),
                    "is_team_member": column.is_team_member,
                    "weather_data": city_data.get("weather_data", {}),
                    "member_name": city_data.get("member_name", None)
                })
            
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Comparison Data"
            )
            
            if filename:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Weather Comparison Report\n")
                        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write(insights_content)
                        f.write("\n\n=== Detailed City Data ===\n")
                        for city in export_data["cities_data"]:
                            f.write(f"\n{city['city_name']}:\n")
                            if city['is_team_member']:
                                f.write(f"  Team Member: {city.get('member_name', 'Unknown')}\n")
                            weather = city['weather_data']
                            f.write(f"  Temperature: {weather.get('temperature', 'N/A')}°C\n")
                            f.write(f"  Humidity: {weather.get('humidity', 'N/A')}%\n")
                            f.write(f"  Wind Speed: {weather.get('wind_speed', 'N/A')} km/h\n")
                            f.write(f"  Description: {weather.get('description', 'N/A')}\n")
                
                logger.info(f"Comparison data exported to {filename}")
                
        except Exception as e:
            logger.error(f"Failed to export comparison data: {e}")
    
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
