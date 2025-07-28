"""Enhanced Hunter Theme Dashboard UI

Glasmorphic weather dashboard with Hunter theme styling,
3D glass panels, and weather-responsive visual effects.
"""

import customtkinter as ctk
from typing import Dict, Any, Optional, Callable
from .components.hunter_glass import (
    HunterGlassButton,
    HunterGlassFrame,
    HunterGlassPanel,
    HunterGlassLabel,
    HunterGlassEntry,
    HunterColors
)
from .components.hunter_widgets import (
    Hunter3DButton,
    Hunter3DEntry,
    Hunter3DFrame
)
from ..features.temperature_graph.advanced_chart_widget import AdvancedChartWidget
from ..features.temperature_graph.models import ChartConfig, ChartType, TimeRange

# Configure CustomTkinter globally
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Brand constant
BRAND_NAME = "CodeFront Weather Capstone"

class HunterTypography:
    """Hunter theme typography standards"""
    FONT_FAMILY = "Segoe UI"
    HEADER_FONT = (FONT_FAMILY, 24, "bold")
    BODY_FONT = (FONT_FAMILY, 12, "normal")
    BUTTON_FONT = (FONT_FAMILY, 12, "normal")
    
    PRIMARY_TEXT = "#C0C0C0"      # Hunter silver
    SECONDARY_TEXT = ("#C0C0C0", "#999999")  # Dimmed silver with dark variant
    ACCENT_TEXT = "#355E3B"       # Hunter green

class HunterDashboardUI:
    """
    Hunter-themed dashboard UI with dark slate, hunter green, and silver colors.
    
    Features:
    - Hunter theme color scheme
    - Weather display and controls
    - Modern dark interface
    - Responsive layout
    """
    
    def __init__(self, parent, weather_service, database, settings, github_service=None):
        self.parent = parent
        self.weather_service = weather_service
        self.database = database
        self.settings = settings
        self.github_service = github_service
        
        # Configure main window background
        if hasattr(parent, 'configure'):
            parent.configure(bg="#2F4F4F")  # Hunter dark slate background
        
        # Initialize UI
        self.create_ui()
    
    def create_ui(self):
        """Create main UI structure with CustomTkinter"""
        # Main container using CustomTkinter frame
        self.main_container = ctk.CTkFrame(
            self.parent,
            fg_color="#2F4F4F",  # Hunter dark slate
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True)
        
        # Create UI sections
        self.create_header()
        self.create_main_content()
        self.create_navigation()
        
        # Apply 3D enhancements
        self.apply_all_3d_enhancements()
        
        # Initialize weather features
        self.initialize_weather_features()
    
    def create_header(self):
        """Create header with Hunter glass styling"""
        # Header frame using Hunter glass component
        self.header_frame = HunterGlassFrame(self.main_container)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Main header label with CustomTkinter
        self.main_header = HunterGlassLabel(
            self.header_frame,
            text=BRAND_NAME,
            font=("Segoe UI", 24, "bold"),
            text_color="#C0C0C0"
        )
        self.main_header.pack(pady=20)
    
    def create_main_content(self):
        """Create CustomTkinter TabView with Hunter theme"""
        self.tabview = ctk.CTkTabview(
            self.main_container,
            fg_color="#2F4F4F",                 # Hunter dark slate
            segmented_button_fg_color="#355E3B", # Hunter green active
            segmented_button_selected_color="#355E3B", # Hunter green selected
            segmented_button_unselected_color="#1C1C1C", # Hunter black inactive
            text_color="#C0C0C0",               # Hunter silver text
            corner_radius=12,
            border_width=1,
            border_color=("#C0C0C0", "#808080")  # Semi-transparent silver
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add tabs
        self.tabview.add("Weather")
        self.tabview.add("Temperature Graph")
        self.tabview.add("Weather Journal")
        self.tabview.add("Activity Suggester")
        self.tabview.add("Team Collaboration")
        self.tabview.add("Settings")
        
        self.create_weather_tab()
        self.initialize_feature_tabs()
    
    def create_weather_tab(self):
        """Create main weather tab"""
        weather_tab = self.tabview.tab("Weather")
        
        # Main weather panel
        self.weather_panel = HunterGlassPanel(weather_tab)
        self.weather_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status label
        self.weather_status_label = HunterGlassLabel(
            self.weather_panel,
            text="🌤️ Weather data will appear here",
            font=("Segoe UI", 14, "normal")
        )
        self.weather_status_label.pack(pady=20)
        
        # Location input frame
        self.location_frame = HunterGlassFrame(self.weather_panel)
        self.location_frame.pack(fill="x", padx=20, pady=10)
        
        # Location label and entry
        location_label = HunterGlassLabel(self.location_frame, text="Location:")
        location_label.pack(side="left", padx=(10, 5))
        
        self.location_entry = HunterGlassEntry(
            self.location_frame,
            placeholder_text="Enter city name...",
            width=200
        )
        self.location_entry.pack(side="left", padx=5)
        
        # Update button
        self.update_button = HunterGlassButton(
            self.location_frame,
            text="🔄 Update Weather",
            width=150
        )
        self.update_button.pack(side="left", padx=10)
        
        self.create_weather_display()
    
    def create_weather_display(self):
        """Create weather data display"""
        # Weather display frame
        self.weather_display_frame = HunterGlassFrame(self.weather_panel)
        self.weather_display_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Temperature display
        self.temp_label = HunterGlassLabel(
            self.weather_display_frame,
            text="--°C",
            font=("Segoe UI", 48, "bold")
        )
        self.temp_label.pack(pady=20)
        
        # Location display
        self.location_label = HunterGlassLabel(
            self.weather_display_frame,
            text="Unknown Location",
            font=("Segoe UI", 18, "normal")
        )
        self.location_label.pack(pady=5)
        
        # Condition display
        self.condition_label = HunterGlassLabel(
            self.weather_display_frame,
            text="",
            font=("Segoe UI", 14, "normal"),
            text_color="#355E3B"
        )
        self.condition_label.pack(pady=5)
    
    def create_temperature_graph_tab(self):
        """Create advanced interactive temperature visualization"""
        from ..features.temperature_graph.advanced_chart_widget import AdvancedChartWidget
        from ..features.temperature_graph.models import ChartConfig, ChartType, TimeRange
        from ..features.temperature_graph.chart_controller import ChartController
        
        temp_tab = self.tabview.tab("Temperature Graph")
        
        # Create advanced chart configuration
        chart_config = ChartConfig(
            chart_type=ChartType.LINE,
            time_range=TimeRange.LAST_24_HOURS,
            show_annotations=True,
            show_grid=True,
            show_legend=True
        )
        
        # Create chart controller
        chart_controller = ChartController(
            database_manager=self.database,
            config=chart_config
        )
        
        # Create advanced temperature chart widget
        self.advanced_chart = AdvancedChartWidget(
            temp_tab,
            chart_controller=chart_controller
        )
        self.advanced_chart.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initialize with sample data if no weather service data available
        self.advanced_chart.refresh_chart()
    
    def create_weather_journal_tab(self):
        """Create weather journal with text editing"""
        import tkinter as tk
        from datetime import datetime
        
        journal_tab = self.tabview.tab("Weather Journal")
        
        # Journal container
        journal_frame = HunterGlassFrame(journal_tab)
        journal_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = HunterGlassLabel(
            journal_frame,
            text="📝 Weather Journal",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Current entry info
        if hasattr(self, 'current_weather_data') and self.current_weather_data:
            weather_info = f"Today: {self.current_weather_data.get('temperature', 'N/A')}°C"
        else:
            weather_info = f"Today: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        info_label = HunterGlassLabel(journal_frame, text=weather_info)
        info_label.pack(pady=5)
        
        # Text area
        text_frame = tk.Frame(journal_frame, bg='#2F4F4F')
        text_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.journal_text = tk.Text(
            text_frame,
            bg='#1C1C1C',
            fg='#C0C0C0',
            insertbackground='#C0C0C0',
            font=('Segoe UI', 11),
            wrap='word',
            height=12
        )
        self.journal_text.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, bg='#355E3B')
        scrollbar.pack(side="right", fill="y")
        self.journal_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.journal_text.yview)
        
        # Save button
        save_btn = HunterGlassButton(
            journal_frame,
            text="💾 Save Entry",
            command=self.save_journal_entry
        )
        save_btn.pack(pady=10)
    
    def create_activity_suggester_tab(self):
        """Create AI activity suggestions"""
        activity_tab = self.tabview.tab("Activity Suggester")
        
        # Container
        suggester_frame = HunterGlassFrame(activity_tab)
        suggester_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = HunterGlassLabel(
            suggester_frame,
            text="🤖 Activity Suggester",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Generate suggestions based on current weather
        suggestions = self.generate_activity_suggestions()
        
        # Suggestions container
        suggestions_frame = HunterGlassFrame(suggester_frame)
        suggestions_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Display suggestions
        for i, suggestion in enumerate(suggestions[:4]):
            suggestion_frame = HunterGlassFrame(suggestions_frame)
            suggestion_frame.pack(fill="x", pady=5, padx=5)
            
            suggestion_label = HunterGlassLabel(
                suggestion_frame,
                text=f"💡 {suggestion}",
                font=("Segoe UI", 12, "normal"),
                wraplength=400
            )
            suggestion_label.pack(padx=10, pady=8)
        
        # Refresh button
        refresh_btn = HunterGlassButton(
            suggester_frame,
            text="🔄 Get New Suggestions",
            command=self.refresh_suggestions
        )
        refresh_btn.pack(pady=10)
    
    def generate_activity_suggestions(self):
        """Generate weather-based activity suggestions"""
        if hasattr(self, 'current_weather_data') and self.current_weather_data:
            temp = self.current_weather_data.get('temperature', 20)
            condition = self.current_weather_data.get('description', 'clear').lower()
        else:
            temp = 25  # Default
            condition = 'clear'
        
        suggestions = []
        if temp > 25:
            suggestions.extend(["Go for a swim", "Have a picnic", "Outdoor BBQ"])
        elif temp > 15:
            suggestions.extend(["Take a walk", "Go cycling", "Visit a park"])
        else:
            suggestions.extend(["Visit a museum", "Read a book", "Indoor activities"])
        
        if 'rain' in condition:
            suggestions.extend(["Try a new recipe", "Watch movies", "Board games"])
        elif 'clear' in condition:
            suggestions.extend(["Go hiking", "Photography walk", "Outdoor yoga"])
        
        return suggestions[:6]
    
    def refresh_suggestions(self):
        """Refresh activity suggestions"""
        self.create_activity_suggester_tab()
    
    def save_journal_entry(self):
        """Save journal entry"""
        content = self.journal_text.get("1.0", "end-1c")
        if content.strip():
            print(f"Saving journal entry: {content[:50]}...")
            # TODO: Save to database
        else:
            print("No content to save")
    
    def initialize_feature_tabs(self):
        """Initialize all feature tab content"""
        self.create_temperature_graph_tab()
        self.create_weather_journal_tab()
        self.create_activity_suggester_tab()
        self.create_team_collaboration_tab()
        self.create_placeholder_tabs()
    
    def create_team_collaboration_tab(self):
        """Create team collaboration interface with real export data"""
        team_tab = self.tabview.tab("Team Collaboration")
        
        # Main container with scrollable frame
        main_frame = HunterGlassFrame(team_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=("#F0F8FF", "#1E1E1E"),
            corner_radius=15
        )
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Title
        title_label = HunterGlassLabel(
            scrollable_frame,
            text="👥 Team Weather Collaboration",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(15, 10))
        
        # GitHub status and refresh button
        status_frame = HunterGlassFrame(scrollable_frame)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        github_service = getattr(self, 'github_service', None)
        if github_service:
            github_status = "🟢 GitHub Connected - Export Data Available"
        else:
            github_status = "🟡 GitHub Service Not Available"
            
        self.github_status_label = HunterGlassLabel(
            status_frame, 
            text=github_status,
            font=("Segoe UI", 12, "normal")
        )
        self.github_status_label.pack(side="left", padx=10, pady=10)
        
        # Refresh button
        refresh_button = HunterGlassButton(
            status_frame,
            text="🔄 Refresh Data",
            width=120,
            command=self.refresh_team_data
        )
        refresh_button.pack(side="right", padx=10, pady=10)
        
        # Team Statistics Section
        stats_frame = HunterGlassFrame(scrollable_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_title = HunterGlassLabel(
            stats_frame,
            text="📊 Team Statistics",
            font=("Segoe UI", 16, "bold")
        )
        stats_title.pack(pady=(10, 5))
        
        # Statistics grid
        self.stats_grid = HunterGlassFrame(stats_frame)
        self.stats_grid.pack(fill="x", padx=10, pady=10)
        
        # City Comparison Section
        comparison_frame = HunterGlassFrame(scrollable_frame)
        comparison_frame.pack(fill="x", padx=10, pady=10)
        
        comparison_title = HunterGlassLabel(
            comparison_frame,
            text="🌍 City Comparisons",
            font=("Segoe UI", 16, "bold")
        )
        comparison_title.pack(pady=(10, 5))
        
        # Comparison content
        self.comparison_content = HunterGlassFrame(comparison_frame)
        self.comparison_content.pack(fill="x", padx=10, pady=10)
        
        # Recent Activity Section
        activity_frame = HunterGlassFrame(scrollable_frame)
        activity_frame.pack(fill="x", padx=10, pady=10)
        
        activity_title = HunterGlassLabel(
            activity_frame,
            text="📈 Recent Team Activity",
            font=("Segoe UI", 16, "bold")
        )
        activity_title.pack(pady=(10, 5))
        
        # Activity content
        self.activity_content = HunterGlassFrame(activity_frame)
        self.activity_content.pack(fill="x", padx=10, pady=10)
        
        # Load initial data
        self.load_team_collaboration_data()
    
    def refresh_team_data(self):
        """Refresh team collaboration data"""
        try:
            github_service = getattr(self, 'github_service', None)
            if github_service:
                # Force refresh export data
                export_data = github_service.fetch_export_data(force_refresh=True)
                if export_data:
                    self.github_status_label.configure(text="🟢 Data Refreshed Successfully")
                    self.load_team_collaboration_data()
                else:
                    self.github_status_label.configure(text="🔴 Failed to Refresh Data")
            else:
                self.github_status_label.configure(text="🟡 GitHub Service Not Available")
        except Exception as e:
            print(f"Error refreshing team data: {e}")
            self.github_status_label.configure(text="🔴 Error Refreshing Data")
    
    def load_team_collaboration_data(self):
        """Load and display team collaboration data"""
        try:
            github_service = getattr(self, 'github_service', None)
            if not github_service:
                self._show_no_github_message()
                return
            
            # Get export data
            export_data = github_service.get_export_data()
            if not export_data:
                self._show_no_data_message()
                return
            
            # Update statistics
            self._update_team_statistics(export_data.team_summary)
            
            # Update city comparisons
            self._update_city_comparisons(export_data.cities_analysis)
            
            # Update recent activity
            self._update_recent_activity(export_data)
            
        except Exception as e:
            print(f"Error loading team collaboration data: {e}")
            self._show_error_message(str(e))
    
    def _show_no_github_message(self):
        """Show message when GitHub service is not available"""
        # Clear existing content
        for widget in self.stats_grid.winfo_children():
            widget.destroy()
        for widget in self.comparison_content.winfo_children():
            widget.destroy()
        for widget in self.activity_content.winfo_children():
            widget.destroy()
        
        # Show message
        message = HunterGlassLabel(
            self.stats_grid,
            text="GitHub service not configured.\nPlease check your configuration.",
            font=("Segoe UI", 12, "normal"),
            text_color="#FF6B6B"
        )
        message.pack(pady=20)
    
    def _show_no_data_message(self):
        """Show message when no export data is available"""
        # Clear existing content
        for widget in self.stats_grid.winfo_children():
            widget.destroy()
        for widget in self.comparison_content.winfo_children():
            widget.destroy()
        for widget in self.activity_content.winfo_children():
            widget.destroy()
        
        # Show message
        message = HunterGlassLabel(
            self.stats_grid,
            text="No export data available.\nTrying to fetch data...",
            font=("Segoe UI", 12, "normal"),
            text_color="#FFA500"
        )
        message.pack(pady=20)
    
    def _show_error_message(self, error: str):
        """Show error message"""
        # Clear existing content
        for widget in self.stats_grid.winfo_children():
            widget.destroy()
        
        # Show error
        message = HunterGlassLabel(
            self.stats_grid,
            text=f"Error loading data: {error}",
            font=("Segoe UI", 12, "normal"),
            text_color="#FF6B6B"
        )
        message.pack(pady=20)
    
    def _update_team_statistics(self, team_summary):
        """Update team statistics display"""
        # Clear existing stats
        for widget in self.stats_grid.winfo_children():
            widget.destroy()
        
        if not team_summary:
            return
        
        # Create stats grid
        stats_data = [
            ("👥 Total Members", str(team_summary.total_members)),
            ("🌍 Cities Tracked", str(team_summary.total_cities)),
            ("📊 Total Records", str(team_summary.total_records)),
            ("🌡️ Avg Temperature", f"{team_summary.temperature_stats.get('average', 0):.1f}°C"),
            ("💧 Avg Humidity", f"{team_summary.humidity_stats.get('average', 0):.1f}%"),
            ("💨 Avg Wind Speed", f"{team_summary.wind_stats.get('average', 0):.1f} m/s")
        ]
        
        # Create 2x3 grid
        for i, (label, value) in enumerate(stats_data):
            row = i // 2
            col = i % 2
            
            stat_frame = HunterGlassFrame(self.stats_grid)
            stat_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            label_widget = HunterGlassLabel(
                stat_frame,
                text=label,
                font=("Segoe UI", 10, "normal")
            )
            label_widget.pack(pady=(5, 0))
            
            value_widget = HunterGlassLabel(
                stat_frame,
                text=value,
                font=("Segoe UI", 14, "bold"),
                text_color="#355E3B"
            )
            value_widget.pack(pady=(0, 5))
        
        # Configure grid weights
        self.stats_grid.grid_columnconfigure(0, weight=1)
        self.stats_grid.grid_columnconfigure(1, weight=1)
    
    def _update_city_comparisons(self, cities_analysis):
        """Update city comparisons display"""
        # Clear existing comparisons
        for widget in self.comparison_content.winfo_children():
            widget.destroy()
        
        if not cities_analysis:
            return
        
        # Show top cities by records
        sorted_cities = sorted(
            cities_analysis.items(),
            key=lambda x: x[1].get('records', 0),
            reverse=True
        )[:5]  # Top 5 cities
        
        for city_name, city_data in sorted_cities:
            city_frame = HunterGlassFrame(self.comparison_content)
            city_frame.pack(fill="x", padx=5, pady=2)
            
            # City info
            city_info = f"🌍 {city_name} - {city_data.get('records', 0)} records"
            temp_info = f"🌡️ {city_data.get('temperature', {}).get('average', 0):.1f}°C"
            humidity_info = f"💧 {city_data.get('humidity', {}).get('average', 0):.1f}%"
            
            info_text = f"{city_info} | {temp_info} | {humidity_info}"
            
            city_label = HunterGlassLabel(
                city_frame,
                text=info_text,
                font=("Segoe UI", 10, "normal")
            )
            city_label.pack(pady=5, padx=10, anchor="w")
    
    def _update_recent_activity(self, export_data):
        """Update recent activity display"""
        # Clear existing activity
        for widget in self.activity_content.winfo_children():
            widget.destroy()
        
        if not export_data:
            return
        
        # Show export info
        export_info = export_data.export_info
        last_updated = export_info.get('export_date', 'Unknown')
        total_records = export_info.get('total_records', 0)
        
        activity_text = f"📅 Last Updated: {last_updated}\n📊 Total Records: {total_records}"
        
        if export_data.team_summary and export_data.team_summary.members:
            members_text = f"\n👥 Active Members: {', '.join(export_data.team_summary.members[:5])}"
            if len(export_data.team_summary.members) > 5:
                members_text += f" and {len(export_data.team_summary.members) - 5} more"
            activity_text += members_text
        
        activity_label = HunterGlassLabel(
            self.activity_content,
            text=activity_text,
            font=("Segoe UI", 11, "normal"),
            justify="left"
        )
        activity_label.pack(pady=10, padx=10, anchor="w")
    
    def create_placeholder_tabs(self):
        """Add placeholder content for remaining tabs"""
        placeholder_tabs = ["Settings"]
        
        for tab_name in placeholder_tabs:
            tab = self.tabview.tab(tab_name)
            content_text = "⚙️ Settings\n(Coming Soon)" if tab_name == "Settings" else f"{tab_name}\n(Coming Soon)"
            placeholder = HunterGlassLabel(
                tab,
                text=content_text,
                font=("Segoe UI", 16, "normal"),
                text_color=("#C0C0C0", "#999999")
            )
            placeholder.pack(expand=True)
    
    def create_navigation(self):
        """Create navigation with CustomTkinter buttons"""
        # Navigation frame
        self.navigation_frame = HunterGlassFrame(self.main_container)
        self.navigation_frame.pack(fill="x", side="bottom", padx=20, pady=(10, 20))
        
        self.add_navigation_buttons()
        
        # Footer branding
        self.footer_label = HunterGlassLabel(
            self.navigation_frame,
            text=BRAND_NAME,
            font=("Segoe UI", 12, "normal"),
            text_color=("#C0C0C0", "#808080")
        )
        self.footer_label.pack(pady=10)
        
        # Note: We'll add navigation buttons in Part 3
    
    def add_navigation_buttons(self):
        """Add navigation buttons to existing navigation frame"""
        nav_buttons_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        nav_buttons_frame.pack(pady=10)
        
        # Create navigation buttons
        self.weather_button = HunterGlassButton(nav_buttons_frame, text="🌤️ Weather", width=120)
        self.weather_button.pack(side="left", padx=5)
        
        self.settings_button = HunterGlassButton(nav_buttons_frame, text="⚙️ Settings", width=120)
        self.settings_button.pack(side="left", padx=5)
        
        self.about_button = HunterGlassButton(nav_buttons_frame, text="ℹ️ About", width=120)
        self.about_button.pack(side="left", padx=5)
    
    # Methods removed that caused fg_color errors:
    # - apply_hunter_theme_to_tabview()
    # - style_hunter_button()
    # - update_navigation_buttons()
    # - apply_hunter_typography()
    # These methods tried to use fg_color on standard tkinter widgets
    # We're replacing them with proper CustomTkinter components
    
    def update_weather_display(self, weather_dict):
        """Update weather display with new data."""
        try:
            # Update temperature
            if hasattr(self, 'temp_label') and 'temperature' in weather_dict:
                temp = weather_dict['temperature']
                self.temp_label.configure(text=f"{temp}°C")
            
            # Update location
            if hasattr(self, 'location_label') and 'location' in weather_dict:
                location = weather_dict['location']
                self.location_label.configure(text=location)
            
            # Update condition
            if hasattr(self, 'condition_label') and 'condition' in weather_dict:
                condition = weather_dict['condition']
                self.condition_label.configure(text=condition)
            
            # Update status
            if hasattr(self, 'weather_status_label'):
                self.weather_status_label.configure(text="🌤️ Weather data updated successfully")
            
        except Exception as e:
            print(f"Error updating weather display: {e}")
    
    def enhance_location_input(self):
        """Apply 3D styling to location input elements"""
        # Apply 3D border styling to existing location entry
        if hasattr(self, 'location_entry'):
            self.location_entry.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#2B2B2B", "#404040")
            )
        
        # Apply 3D styling to update button
        if hasattr(self, 'update_button'):
            self.update_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
    
    def enhance_navigation_buttons(self):
        """Apply 3D styling to existing navigation buttons"""
        # Apply 3D styling to existing navigation buttons
        if hasattr(self, 'weather_button'):
            self.weather_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
        
        if hasattr(self, 'settings_button'):
            self.settings_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
        
        if hasattr(self, 'about_button'):
            self.about_button.configure(
                border_width=3,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59"),
                hover_color=("#4A7C59", "#5D8F6A")
            )
    
    def add_3d_weather_panel(self):
        """Apply 3D styling to weather display frame"""
        # Apply 3D styling to existing weather display frame
        if hasattr(self, 'weather_display_frame'):
            self.weather_display_frame.configure(
                border_width=3,
                corner_radius=12,
                border_color=("#2B2B2B", "#404040"),
                fg_color=("#1A1A1A", "#2D2D2D")
            )
        
        # Apply enhanced styling to location frame
        if hasattr(self, 'location_frame'):
            self.location_frame.configure(
                border_width=2,
                corner_radius=8,
                border_color=("#355E3B", "#4A7C59")
            )
    
    def add_3d_status_panel(self):
        """Apply 3D styling to status elements"""
        # Apply enhanced styling to navigation frame
        if hasattr(self, 'navigation_frame'):
            self.navigation_frame.configure(
                border_width=2,
                corner_radius=8,
                border_color=("#2B2B2B", "#404040")
            )
        
        # Apply styling to main container
        if hasattr(self, 'main_container'):
            self.main_container.configure(
                border_width=1,
                corner_radius=10,
                border_color=("#355E3B", "#4A7C59")
            )
    
    def apply_all_3d_enhancements(self):
        """Apply all 3D enhancements to interface"""
        self.enhance_location_input()
        self.enhance_navigation_buttons()
        self.add_3d_weather_panel()
        self.add_3d_status_panel()
    
    def setup_weather_integration(self):
        """Connect weather service with debug"""
        
        def handle_weather_update():
            city = self.location_entry.get().strip()
            if not city or city == "Enter city name...":
                self.show_error_state("Enter city name")
                return
                
            self.show_loading_state(city)
            
            try:
                # Try different method names
                if hasattr(self.weather_service, 'get_weather'):
                    weather_data = self.weather_service.get_weather(city)
                elif hasattr(self.weather_service, 'get_current_weather'):
                    weather_data = self.weather_service.get_current_weather(city)
                else:
                    raise AttributeError("No weather method found")
                    
                if weather_data:
                    self.update_weather_display(weather_data)
                    self.show_success_state()
                else:
                    self.show_error_state("No data returned")
                    
            except Exception as e:
                self.show_error_state(f"Error: {str(e)[:25]}")
        
        def clear_placeholder_on_focus(event=None):
            """Clear placeholder text when user clicks on input field"""
            current_text = self.location_entry.get()
            if current_text == "Enter city name...":
                self.location_entry.delete(0, 'end')
        
        def restore_placeholder_on_focus_out(event=None):
            """Restore placeholder text if field is empty when focus is lost"""
            current_text = self.location_entry.get().strip()
            if not current_text:
                self.location_entry.delete(0, 'end')
                self.location_entry.insert(0, "Enter city name...")
        
        def clear_placeholder_on_key(event=None):
            """Clear placeholder text when user starts typing"""
            current_text = self.location_entry.get()
            if current_text == "Enter city name...":
                self.location_entry.delete(0, 'end')
        
        self.update_button.configure(command=handle_weather_update)
        self.location_entry.bind("<Return>", lambda e: handle_weather_update())
        
        # Add event handlers for automatic placeholder clearing
        self.location_entry.bind("<FocusIn>", clear_placeholder_on_focus)
        self.location_entry.bind("<FocusOut>", restore_placeholder_on_focus_out)
        self.location_entry.bind("<KeyPress>", clear_placeholder_on_key)
    
    def show_loading_state(self, city):
        """Show loading with 3D styling"""
        self.weather_status_label.configure(
            text=f"🔄 Fetching weather for {city}...",
            text_color="#C0C0C0"
        )
        self.update_button.configure(
            state="disabled",
            text="Loading...",
            fg_color="#2F4F4F"
        )
        self.parent.update()
    
    def show_success_state(self):
        """Show success with proper clearing"""
        self.weather_status_label.configure(
            text="✅ Weather updated",
            text_color="#4A7C59"
        )
        self.update_button.configure(
            state="normal",
            text="🔄 Update Weather",
            fg_color="#355E3B"
        )
        self.parent.after(2000, lambda: self.weather_status_label.configure(text=""))
    
    def test_weather_functionality(self):
        """Quick test of weather functionality"""
        self.location_entry.delete(0, 'end')
        self.location_entry.insert(0, "London")
        # Then click Update Weather button or press Enter
    
    def show_error_state(self, error_message):
        """Show error state"""
        self.weather_status_label.configure(
            text=f"❌ {error_message}",
            text_color="#FF6B6B"
        )
        self.update_button.configure(
            state="normal",
            text="🔄 Update Weather",
            fg_color="#355E3B"
        )
        self.parent.after(5000, lambda: self.weather_status_label.configure(text=""))
    
    def debug_weather_data(self, weather_data):
        """Debug weather data structure"""
        print("=== Weather Data Debug ===")
        print(f"Type: {type(weather_data)}")
        if hasattr(weather_data, '__dict__'):
            for attr, value in weather_data.__dict__.items():
                print(f"{attr}: {value}")
        print("========================")
    
    def update_weather_display(self, weather_data):
        """Update weather display with robust data handling"""
        
        # Debug first to see actual data structure
        self.debug_weather_data(weather_data)
        
        # Temperature (usually works)
        if hasattr(weather_data, 'temperature'):
            temp = weather_data.temperature
        elif hasattr(weather_data, 'temp'):
            temp = weather_data.temp
        else:
            temp = 0.0
            
        self.temp_label.configure(text=f"{temp:.1f}°C")
        
        # Location (usually works)
        if hasattr(weather_data, 'location'):
            location = weather_data.location
        elif hasattr(weather_data, 'city'):
            location = f"{weather_data.city}, {weather_data.country}"
        else:
            location = "Unknown Location"
            
        self.location_label.configure(text=location)
        
        # FIX: Weather condition - try multiple possible attributes
        condition = "Clear"  # Default
        possible_attrs = ['condition', 'description', 'weather', 'main', 'summary']
        
        for attr in possible_attrs:
            if hasattr(weather_data, attr):
                value = getattr(weather_data, attr)
                if value and str(value).strip():
                    condition = str(value).title()
                    break
        
        self.condition_label.configure(
            text=condition,
            text_color="#355E3B"  # Ensure visible color
        )
        
        # Apply background effect
        self.apply_weather_background_effect(condition)
        
        # Update entry field
        if hasattr(weather_data, 'location'):
            self.location_entry.delete(0, 'end')
            self.location_entry.insert(0, weather_data.location.split(',')[0])
        
        # Update advanced chart widget if available
        if hasattr(self, 'advanced_chart'):
            try:
                self.advanced_chart.update_current_weather(weather_data)
            except Exception as e:
                print(f"Failed to update chart: {e}")
    
    def update_weather_display_with_data(self, weather_data):
        """Legacy method - redirects to new robust method"""
        self.update_weather_display(weather_data)
    
    def apply_weather_background_effect(self, condition):
        """Apply background effects based on weather"""
        
        weather_effects = {
            "clear": "#355E3B",           # Light hunter green
            "clouds": "#2F4F4F",          # Dark slate overlay
            "rain": "#2F4F4F",            # Heavy slate
            "storm": "#1C1C1C",           # Very dark
            "snow": "#C0C0C0",            # Silver
            "mist": "#2F4F4F"             # Misty slate
        }
        
        # Find matching condition
        effect_color = "#355E3B"  # Default
        for key, color in weather_effects.items():
            if key in condition.lower():
                effect_color = color
                break
        
        # Apply to main container
        if hasattr(self, 'main_container'):
            self.main_container.configure(fg_color=effect_color)
    
    def initialize_weather_features(self):
        """Initialize weather integration"""
        self.setup_weather_integration()
        self.current_weather_data = None
        
        # Set placeholder
        self.location_entry.delete(0, 'end')
        self.location_entry.insert(0, "Enter city name...")
    
    def cleanup(self):
        """Cleanup resources."""
        pass