"""Main team collaboration widget with UI layout and event handling.

This module contains the main widget class that provides the user interface
for team collaboration features.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
import logging
import asyncio
import threading
from datetime import datetime

from ...ui.components.base_components import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry, GlassProgressBar
)
from ...utils.logger import LoggerMixin
from .models import CollaborationConfig
from .collaboration_controller import CollaborationController


class TeamCollaborationWidget(ctk.CTkFrame, LoggerMixin):
    """Team collaboration widget for weather data sharing."""

    def __init__(self, parent, github_service, **kwargs):
        """Initialize team collaboration widget.

        Args:
            parent: Parent widget
            github_service: GitHub service instance
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)

        # Initialize controller
        self.controller = CollaborationController(github_service)
        
        # Set up controller callbacks
        self.controller.on_data_updated = self._on_data_updated
        self.controller.on_sync_completed = self._on_sync_completed
        self.controller.on_error = self._on_error

        # UI state
        self.selected_cities: List[str] = []
        self.current_weather_data: Optional[Dict[str, Any]] = None

        # External callbacks
        self.on_city_selected: Optional[Callable[[str], None]] = None
        self.on_comparison_created: Optional[Callable] = None

        # Setup UI
        self._setup_ui()

        # Load initial data
        self._load_initial_data()

        # Start auto-sync if enabled
        self.controller.start_auto_sync()

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

    def _create_main_content(self):
        """Create main content area with tabs."""
        # Tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Cities tab
        self.cities_tab = self.tabview.add("🏙️ Shared Cities")
        self._create_cities_tab()

        # Weather data tab
        self.weather_data_tab = self.tabview.add("🌤️ Team Weather")
        self._create_weather_data_tab()

        # Analysis tab
        self.analysis_tab = self.tabview.add("📊 City Analysis")
        self._create_analysis_tab()

        # Comparisons tab
        self.comparisons_tab = self.tabview.add("📈 Team Comparisons")
        self._create_comparisons_tab()

        # Activity tab
        self.activity_tab = self.tabview.add("📋 Team Activity")
        self._create_activity_tab()

        # Team tab
        self.team_tab = self.tabview.add("👥 Team Members")
        self._create_team_tab()

    def _create_cities_tab(self):
        """Create the shared cities tab."""
        # Cities tab content
        cities_frame = GlassFrame(self.cities_tab)
        cities_frame.pack(fill="both", expand=True, padx=10, pady=10)
        cities_frame.grid_columnconfigure(0, weight=1)
        cities_frame.grid_rowconfigure(1, weight=1)

        # Cities controls
        controls_frame = ctk.CTkFrame(cities_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls_frame.grid_columnconfigure(1, weight=1)

        # Add city button
        add_city_button = GlassButton(
            controls_frame,
            text="➕ Add Current City",
            command=self._add_current_city
        )
        add_city_button.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Search entry
        self.city_search_entry = GlassEntry(
            controls_frame,
            placeholder_text="🔍 Search cities..."
        )
        self.city_search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.city_search_entry.bind("<KeyRelease>", self._on_city_search)

        # Refresh button
        refresh_button = GlassButton(
            controls_frame,
            text="🔄 Refresh",
            width=80,
            command=self._refresh_cities
        )
        refresh_button.grid(row=0, column=2, sticky="e")

        # Cities list
        self.cities_listbox = tk.Listbox(
            cities_frame,
            font=("Segoe UI", 11),
            selectmode="extended"
        )
        self.cities_listbox.grid(row=1, column=0, sticky="nsew")
        self.cities_listbox.bind("<Double-Button-1>", self._on_city_double_click)

        # Scrollbar for cities list
        cities_scrollbar = ctk.CTkScrollbar(cities_frame, command=self.cities_listbox.yview)
        cities_scrollbar.grid(row=1, column=1, sticky="ns")
        self.cities_listbox.configure(yscrollcommand=cities_scrollbar.set)

    def _create_comparisons_tab(self):
        """Create the team comparisons tab."""
        comparisons_frame = GlassFrame(self.comparisons_tab)
        comparisons_frame.pack(fill="both", expand=True, padx=10, pady=10)
        comparisons_frame.grid_columnconfigure(0, weight=1)
        comparisons_frame.grid_rowconfigure(1, weight=1)

        # Comparisons controls
        comp_controls_frame = ctk.CTkFrame(comparisons_frame, fg_color="transparent")
        comp_controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Create comparison button
        create_comp_button = GlassButton(
            comp_controls_frame,
            text="📊 Create Comparison",
            command=self._create_comparison
        )
        create_comp_button.pack(side="left", padx=(0, 10))

        # Comparisons list
        self.comparisons_listbox = tk.Listbox(
            comparisons_frame,
            font=("Segoe UI", 11)
        )
        self.comparisons_listbox.grid(row=1, column=0, sticky="nsew")
        self.comparisons_listbox.bind("<Double-Button-1>", self._on_comparison_double_click)

        # Scrollbar for comparisons list
        comp_scrollbar = ctk.CTkScrollbar(comparisons_frame, command=self.comparisons_listbox.yview)
        comp_scrollbar.grid(row=1, column=1, sticky="ns")
        self.comparisons_listbox.configure(yscrollcommand=comp_scrollbar.set)

    def _create_activity_tab(self):
        """Create the team activity tab."""
        activity_frame = GlassFrame(self.activity_tab)
        activity_frame.pack(fill="both", expand=True, padx=10, pady=10)
        activity_frame.grid_columnconfigure(0, weight=1)
        activity_frame.grid_rowconfigure(0, weight=1)

        # Activity list
        self.activity_listbox = tk.Listbox(
            activity_frame,
            font=("Segoe UI", 10)
        )
        self.activity_listbox.grid(row=0, column=0, sticky="nsew")

        # Scrollbar for activity list
        activity_scrollbar = ctk.CTkScrollbar(activity_frame, command=self.activity_listbox.yview)
        activity_scrollbar.grid(row=0, column=1, sticky="ns")
        self.activity_listbox.configure(yscrollcommand=activity_scrollbar.set)

    def _create_team_tab(self):
        """Create the team members tab."""
        team_frame = GlassFrame(self.team_tab)
        team_frame.pack(fill="both", expand=True, padx=10, pady=10)
        team_frame.grid_columnconfigure(0, weight=1)
        team_frame.grid_rowconfigure(1, weight=1)

        # Team controls
        team_controls_frame = ctk.CTkFrame(team_frame, fg_color="transparent")
        team_controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Invite member button
        invite_button = GlassButton(
            team_controls_frame,
            text="👥 Invite Member",
            command=self._invite_team_member
        )
        invite_button.pack(side="left")

        # Team members list
        self.team_listbox = tk.Listbox(
            team_frame,
            font=("Segoe UI", 11)
        )
        self.team_listbox.grid(row=1, column=0, sticky="nsew")

        # Scrollbar for team list
        team_scrollbar = ctk.CTkScrollbar(team_frame, command=self.team_listbox.yview)
        team_scrollbar.grid(row=1, column=1, sticky="ns")
        self.team_listbox.configure(yscrollcommand=team_scrollbar.set)

    def _create_status_bar(self):
        """Create status bar with sync information."""
        self.status_bar = GlassFrame(self)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.status_bar.grid_columnconfigure(1, weight=1)

        # Sync status
        self.sync_status_label = GlassLabel(
            self.status_bar,
            text="Ready",
            font=("Segoe UI", 10)
        )
        self.sync_status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        # Progress bar
        self.progress_bar = GlassProgressBar(self.status_bar)
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.progress_bar.set(0)

        # Stats
        self.stats_label = GlassLabel(
            self.status_bar,
            text="",
            font=("Segoe UI", 10)
        )
        self.stats_label.grid(row=0, column=2, sticky="e", padx=10, pady=5)

    def set_weather_data(self, weather_data: Dict[str, Any]):
        """Set current weather data for sharing."""
        self.current_weather_data = weather_data

    def _load_initial_data(self):
        """Load initial data from GitHub."""
        try:
            # Update connection status
            if self.controller.github_service:
                self.connection_label.configure(text="🟢 Connected")
            else:
                self.connection_label.configure(text="🔴 Disconnected")

            # Load data
            self._refresh_all_data()

        except Exception as e:
            self.logger.error(f"Error loading initial data: {e}")
            self._show_error(f"Failed to load data: {e}")

    def _refresh_all_data(self):
        """Refresh all data displays."""
        self._refresh_cities()
        self._refresh_weather_data()
        self._refresh_comparisons()
        self._refresh_activity()
        self._refresh_team_members()
        self._update_stats()

    def _refresh_cities(self):
        """Refresh the cities list."""
        self.cities_listbox.delete(0, tk.END)
        for city in self.controller.shared_cities:
            display_text = f"{city.name} - {city.temperature}°F"
            self.cities_listbox.insert(tk.END, display_text)

    def _refresh_comparisons(self):
        """Refresh the comparisons list."""
        self.comparisons_listbox.delete(0, tk.END)
        for comparison in self.controller.team_comparisons:
            display_text = f"{comparison.name} ({len(comparison.cities)} cities)"
            self.comparisons_listbox.insert(tk.END, display_text)

    def _refresh_activity(self):
        """Refresh the activity list."""
        self.activity_listbox.delete(0, tk.END)
        activities = self.controller.get_recent_activities()
        for activity in activities:
            timestamp = activity.timestamp.strftime("%H:%M")
            display_text = f"{timestamp} - {activity.user}: {activity.action} {activity.target}"
            self.activity_listbox.insert(tk.END, display_text)

    def _refresh_team_members(self):
        """Refresh the team members list."""
        self.team_listbox.delete(0, tk.END)
        for member in self.controller.team_members:
            status = "🟢" if member.is_online else "🔴"
            display_text = f"{status} {member.name} ({member.role})"
            self.team_listbox.insert(tk.END, display_text)

    def _update_stats(self):
        """Update statistics display."""
        stats = self.controller.get_collaboration_stats()
        
        # Include new metrics from optimized service
        base_stats = f"Cities: {stats['total_cities']} | Comparisons: {stats['total_comparisons']} | Members: {stats['team_members']}"
        
        if 'service_metrics' in stats:
            metrics = stats['service_metrics']
            cache_info = f" | Cache: {metrics.get('cache_hits', 0)}/{metrics.get('cache_requests', 0)}"
            base_stats += cache_info
            
        if 'data_freshness' in stats:
            freshness = stats['data_freshness']
            if freshness:
                base_stats += f" | Updated: {freshness.strftime('%H:%M')}"
        
        self.stats_label.configure(text=base_stats)

    # Event handlers
    def _manual_sync(self):
        """Handle manual sync button click."""
        self.sync_status_label.configure(text="Syncing...")
        self.progress_bar.set(0.5)
        
        # Sync in background thread
        threading.Thread(target=self._perform_sync, daemon=True).start()

    def _perform_sync(self):
        """Perform synchronization in background."""
        try:
            # Refresh team data first
            self.controller.refresh_team_data()
            
            # Then sync with remote
            success = self.controller.sync_with_remote()
            
            # Update UI in main thread
            self.after(0, self._sync_completed, success)
        except Exception as e:
            self.logger.error(f"Error during sync: {e}")
            self.after(0, self._sync_completed, False)

    def _sync_completed(self, success: bool):
        """Handle sync completion."""
        if success:
            self.sync_status_label.configure(text="Sync completed")
            self.progress_bar.set(1.0)
        else:
            self.sync_status_label.configure(text="Sync failed")
            self.progress_bar.set(0)
        
        # Reset after delay
        self.after(3000, lambda: self.sync_status_label.configure(text="Ready"))
        self.after(3000, lambda: self.progress_bar.set(0))

    def _add_current_city(self):
        """Add current weather data as shared city."""
        if not self.current_weather_data:
            messagebox.showwarning("No Data", "No current weather data available to share.")
            return

        try:
            # Create city data from current weather
            city_data = self._create_city_data_from_weather(self.current_weather_data)
            
            if self.controller.add_shared_city(city_data):
                self._refresh_cities()
                messagebox.showinfo("Success", f"Added {city_data.name} to shared cities.")
            else:
                messagebox.showwarning("Duplicate", f"{city_data.name} is already shared.")
                
        except Exception as e:
            self.logger.error(f"Error adding current city: {e}")
            self._show_error(f"Failed to add city: {e}")

    def _create_city_data_from_weather(self, weather_data):
        """Create city data object from weather data."""
        # This would create a proper CityData object based on the weather data structure
        # Implementation depends on the actual CityData class structure
        return type('CityData', (), {
            'name': weather_data.get('location', 'Unknown'),
            'temperature': weather_data.get('temperature', 0),
            'condition': weather_data.get('condition', ''),
            'humidity': weather_data.get('humidity', 0),
            'wind_speed': weather_data.get('wind_speed', 0),
            'timestamp': weather_data.get('timestamp', 'Unknown')
        })()

    # Callback methods
    def _on_data_updated(self):
        """Handle data update from controller."""
        self.after(0, self._refresh_all_data)

    def _on_sync_completed(self):
        """Handle sync completion from controller."""
        self.after(0, lambda: self._refresh_all_data())

    def _on_error(self, error_message: str):
        """Handle error from controller."""
        self.after(0, lambda: self._show_error(error_message))

    def _show_error(self, message: str):
        """Show error message to user."""
        messagebox.showerror("Error", message)

    # Placeholder methods for additional functionality
    def _on_city_search(self, event=None):
        """Handle city search."""
        pass

    def _on_city_double_click(self, event=None):
        """Handle city double-click."""
        pass

    def _create_comparison(self):
        """Create a new team comparison."""
        pass

    def _on_comparison_double_click(self, event=None):
        """Handle comparison double-click."""
        pass

    def _invite_team_member(self):
        """Invite a new team member."""
        pass

    def _show_settings(self):
        """Show settings dialog."""
        pass

    def _create_weather_data_tab(self):
        """Create the team weather data tab."""
        weather_frame = GlassFrame(self.weather_data_tab)
        weather_frame.pack(fill="both", expand=True, padx=10, pady=10)
        weather_frame.grid_columnconfigure(0, weight=1)
        weather_frame.grid_rowconfigure(1, weight=1)

        # Weather data controls
        weather_controls_frame = ctk.CTkFrame(weather_frame, fg_color="transparent")
        weather_controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Refresh weather button
        refresh_weather_button = GlassButton(
            weather_controls_frame,
            text="🔄 Refresh Weather",
            command=self._refresh_weather_data
        )
        refresh_weather_button.pack(side="left", padx=(0, 10))
        
        # Load team data button
        load_data_button = GlassButton(
            weather_controls_frame,
            text="📥 Load Team Data",
            command=self._load_team_data
        )
        load_data_button.pack(side="left", padx=(0, 10))
        
        # Clear cache button
        clear_cache_button = GlassButton(
            weather_controls_frame,
            text="🗑️ Clear Cache",
            command=self._clear_cache
        )
        clear_cache_button.pack(side="left", padx=(0, 10))

        # Weather data list
        self.weather_data_listbox = tk.Listbox(
            weather_frame,
            font=("Segoe UI", 11)
        )
        self.weather_data_listbox.grid(row=1, column=0, sticky="nsew")

        # Scrollbar for weather data list
        weather_scrollbar = ctk.CTkScrollbar(weather_frame, command=self.weather_data_listbox.yview)
        weather_scrollbar.grid(row=1, column=1, sticky="ns")
        self.weather_data_listbox.configure(yscrollcommand=weather_scrollbar.set)

    def _create_analysis_tab(self):
        """Create the city analysis tab."""
        analysis_frame = GlassFrame(self.analysis_tab)
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=10)
        analysis_frame.grid_columnconfigure(0, weight=1)
        analysis_frame.grid_rowconfigure(1, weight=1)

        # Analysis controls
        analysis_controls_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        analysis_controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Generate analysis button
        generate_analysis_button = GlassButton(
            analysis_controls_frame,
            text="📊 Generate Analysis",
            command=self._generate_analysis
        )
        generate_analysis_button.pack(side="left", padx=(0, 10))
        
        # Export analysis button
        export_analysis_button = GlassButton(
            analysis_controls_frame,
            text="💾 Export Analysis",
            command=self._export_analysis
        )
        export_analysis_button.pack(side="left", padx=(0, 10))

        # Analysis results
        self.analysis_text = tk.Text(
            analysis_frame,
            font=("Segoe UI", 10),
            wrap=tk.WORD
        )
        self.analysis_text.grid(row=1, column=0, sticky="nsew")

        # Scrollbar for analysis text
        analysis_scrollbar = ctk.CTkScrollbar(analysis_frame, command=self.analysis_text.yview)
        analysis_scrollbar.grid(row=1, column=1, sticky="ns")
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)

    def _refresh_weather_data(self):
        """Refresh the team weather data."""
        try:
            self.weather_data_listbox.delete(0, tk.END)
            
            # Load team weather data using the optimized service
            weather_data = self.controller.load_team_weather_data()
            
            if weather_data:
                for city, data in weather_data.items():
                    if isinstance(data, dict) and 'temperature' in data:
                        temp = data.get('temperature', 'N/A')
                        condition = data.get('condition', 'Unknown')
                        humidity = data.get('humidity', 'N/A')
                        display_text = f"{city} - {temp}°F, {condition}, Humidity: {humidity}%"
                        self.weather_data_listbox.insert(tk.END, display_text)
                    else:
                        # Handle list of weather records
                        if isinstance(data, list) and data:
                            latest = data[-1]  # Get most recent
                            temp = latest.get('temperature', 'N/A')
                            condition = latest.get('condition', 'Unknown')
                            display_text = f"{city} - {temp}°F, {condition} (Latest)"
                            self.weather_data_listbox.insert(tk.END, display_text)
            else:
                self.weather_data_listbox.insert(tk.END, "No team weather data available")
                
        except Exception as e:
            self.logger.error(f"Error refreshing weather data: {e}")
            self.weather_data_listbox.insert(tk.END, f"Error loading weather data: {e}")

    def _generate_analysis(self):
        """Generate city analysis."""
        try:
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, "Generating analysis...\n")
            
            # Get cities analysis from the optimized service
            analysis_data = self.controller.get_cities_analysis()
            
            if analysis_data:
                analysis_text = "=== CITY WEATHER ANALYSIS ===\n\n"
                
                for city, analysis in analysis_data.items():
                    analysis_text += f"📍 {city.upper()}\n"
                    analysis_text += f"   Average Temperature: {analysis.get('avg_temp', 'N/A')}°F\n"
                    analysis_text += f"   Temperature Range: {analysis.get('min_temp', 'N/A')}°F - {analysis.get('max_temp', 'N/A')}°F\n"
                    analysis_text += f"   Most Common Condition: {analysis.get('common_condition', 'N/A')}\n"
                    analysis_text += f"   Average Humidity: {analysis.get('avg_humidity', 'N/A')}%\n"
                    analysis_text += f"   Data Points: {analysis.get('data_count', 0)}\n\n"
                
                # Add performance metrics
                metrics = self.controller.get_team_performance_metrics()
                if metrics:
                    analysis_text += "=== PERFORMANCE METRICS ===\n\n"
                    analysis_text += f"Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.1%}\n"
                    analysis_text += f"Average Response Time: {metrics.get('avg_response_time', 0):.2f}s\n"
                    analysis_text += f"Total Requests: {metrics.get('total_requests', 0)}\n"
                    analysis_text += f"Error Rate: {metrics.get('error_rate', 0):.1%}\n"
                
                self.analysis_text.delete(1.0, tk.END)
                self.analysis_text.insert(tk.END, analysis_text)
            else:
                self.analysis_text.delete(1.0, tk.END)
                self.analysis_text.insert(tk.END, "No analysis data available. Please ensure team weather data is loaded.")
                
        except Exception as e:
             self.logger.error(f"Error generating analysis: {e}")
             self.analysis_text.delete(1.0, tk.END)
             self.analysis_text.insert(tk.END, f"Error generating analysis: {e}")
    
    def _load_team_data(self):
        """Load team data in background thread."""
        def load_data():
            try:
                self.after(0, lambda: self.sync_status_label.configure(text="Loading team data..."))
                self.after(0, lambda: self.progress_bar.set(0.3))
                
                # Load team weather data
                weather_data = self.controller.load_team_weather_data()
                
                self.after(0, lambda: self.progress_bar.set(0.7))
                
                # Refresh UI
                self.after(0, self._refresh_weather_data)
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self.sync_status_label.configure(text="Team data loaded"))
                
                # Reset after delay
                self.after(3000, lambda: self.sync_status_label.configure(text="Ready"))
                self.after(3000, lambda: self.progress_bar.set(0))
                
            except Exception as e:
                self.logger.error(f"Error loading team data: {e}")
                self.after(0, lambda: self.sync_status_label.configure(text="Load failed"))
                self.after(0, lambda: self.progress_bar.set(0))
                self.after(0, lambda: self._show_error(f"Failed to load team data: {e}"))
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def _clear_cache(self):
        """Clear the team data cache."""
        try:
            self.controller.clear_team_data_cache()
            self.sync_status_label.configure(text="Cache cleared")
            
            # Reset after delay
            self.after(2000, lambda: self.sync_status_label.configure(text="Ready"))
            
            messagebox.showinfo("Success", "Team data cache has been cleared.")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            self._show_error(f"Failed to clear cache: {e}")
    
    def _export_analysis(self):
        """Export the current analysis to a file."""
        try:
            from tkinter import filedialog
            
            # Get current analysis text
            analysis_content = self.analysis_text.get(1.0, tk.END)
            
            if not analysis_content.strip() or analysis_content.strip() == "Generating analysis...":
                messagebox.showwarning("No Data", "No analysis data to export. Please generate analysis first.")
                return
            
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Analysis"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Team Weather Analysis Export\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*50}\n\n")
                    f.write(analysis_content)
                
                messagebox.showinfo("Success", f"Analysis exported to {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exporting analysis: {e}")
            self._show_error(f"Failed to export analysis: {e}")