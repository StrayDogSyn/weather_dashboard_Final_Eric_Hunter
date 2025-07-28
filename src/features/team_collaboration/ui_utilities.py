"""UI utility components for team collaboration features.

This module contains utility widgets like loading overlays, status bars,
and dialog creation functions for the team collaboration interface.
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from src.ui.components.glass import GlassFrame, GlassLabel, GlassButton
from src.utils.logger import LoggerMixin


class SelectedCitiesDisplay(ctk.CTkFrame, LoggerMixin):
    """Widget for displaying and managing selected cities."""
    
    def __init__(self, parent, on_remove_city: Optional[Callable] = None, **kwargs):
        """Initialize selected cities display.
        
        Args:
            parent: Parent widget
            on_remove_city: Optional callback for city removal
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.selected_cities = []
        self.on_remove_city = on_remove_city
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the display UI."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Selected Cities",
            font=("Segoe UI", 12, "bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Cities container
        self.cities_frame = ctk.CTkScrollableFrame(self, height=100)
        self.cities_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def update_selected_cities(self, cities: List[str]):
        """Update the list of selected cities.
        
        Args:
            cities: List of city names
        """
        self.selected_cities = cities.copy()
        
        # Clear existing widgets
        for widget in self.cities_frame.winfo_children():
            widget.destroy()
        
        # Add city widgets
        if not cities:
            no_cities_label = ctk.CTkLabel(
                self.cities_frame,
                text="No cities selected",
                text_color="#888888"
            )
            no_cities_label.pack(pady=10)
        else:
            for city_name in cities:
                self._create_city_widget(city_name)
    
    def _create_city_widget(self, city_name: str):
        """Create widget for a selected city.
        
        Args:
            city_name: Name of the city
        """
        city_frame = ctk.CTkFrame(self.cities_frame)
        city_frame.pack(fill="x", pady=2)
        
        # City name
        city_label = ctk.CTkLabel(
            city_frame,
            text=city_name,
            font=("Segoe UI", 11)
        )
        city_label.pack(side="left", padx=10, pady=5)
        
        # Remove button
        if self.on_remove_city:
            remove_button = GlassButton(
                city_frame,
                text="✕",
                width=20,
                height=20,
                command=lambda c=city_name: self._remove_city(c)
            )
            remove_button.pack(side="left", padx=(5, 0))
    
    def _remove_city(self, city_name: str):
        """Remove city from selection.
        
        Args:
            city_name: Name of the city to remove
        """
        if city_name in self.selected_cities:
            self.selected_cities.remove(city_name)
            if self.on_remove_city:
                self.on_remove_city(city_name)
            self.update_selected_cities(self.selected_cities)


class LoadingOverlay(ctk.CTkFrame):
    """Loading overlay widget."""
    
    def __init__(self, parent, message: str = "Loading...", **kwargs):
        """Initialize loading overlay.
        
        Args:
            parent: Parent widget
            message: Loading message to display
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        
        self.message = message
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the loading UI."""
        # Center the loading content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=0)
        
        # Loading indicator
        loading_label = ctk.CTkLabel(
            content_frame,
            text="🔄",
            font=("Segoe UI", 24)
        )
        loading_label.pack(pady=(20, 10))
        
        # Loading message
        self.message_label = ctk.CTkLabel(
            content_frame,
            text=self.message,
            font=("Segoe UI", 14)
        )
        self.message_label.pack(pady=(0, 20))
    
    def update_message(self, message: str):
        """Update the loading message.
        
        Args:
            message: New loading message
        """
        self.message = message
        self.message_label.configure(text=message)


class StatusBar(GlassFrame):
    """Status bar widget for displaying status messages."""
    
    def __init__(self, parent, **kwargs):
        """Initialize status bar.
        
        Args:
            parent: Parent widget
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the status bar UI."""
        self.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = GlassLabel(
            self,
            text="Ready",
            font=("Segoe UI", 10)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Last sync time
        self.last_sync_label = GlassLabel(
            self,
            text="Never synced",
            font=("Segoe UI", 10)
        )
        self.last_sync_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def update_status(self, message: str):
        """Update status message.
        
        Args:
            message: Status message to display
        """
        self.status_label.configure(text=message)
    
    def update_last_sync(self, sync_time: datetime = None):
        """Update last sync time display.
        
        Args:
            sync_time: Sync timestamp, defaults to current time
        """
        if sync_time is None:
            sync_time = datetime.now()
        
        self.last_sync_label.configure(text=f"Last sync: {sync_time.strftime('%H:%M:%S')}")


# Utility functions for creating dialogs
def create_share_city_dialog(parent, current_weather_data: Dict[str, Any], 
                           on_share: Callable) -> Optional[ctk.CTkToplevel]:
    """Create dialog for sharing city data.
    
    Args:
        parent: Parent widget
        current_weather_data: Current weather data dictionary
        on_share: Callback function for sharing
        
    Returns:
        Share dialog window or None if no data
    """
    if not current_weather_data:
        messagebox.showwarning("Warning", "No current weather data to share")
        return None
    
    # Create share dialog
    share_window = ctk.CTkToplevel(parent)
    share_window.title("Share City")
    share_window.geometry("400x300")
    share_window.transient(parent)
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
    city_name = current_weather_data.get("city", "Unknown")
    country = current_weather_data.get("country", "Unknown")
    
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
        """Handle city sharing."""
        tags = [tag.strip() for tag in tags_var.get().split(",") if tag.strip()]
        description = desc_text.get("1.0", "end-1c").strip()
        
        if on_share:
            on_share(tags, description)
        
        share_window.destroy()
    
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
    
    return share_window


def create_comparison_dialog(parent, available_cities: List[str], 
                           on_create: Callable) -> Optional[ctk.CTkToplevel]:
    """Create dialog for creating city comparisons.
    
    Args:
        parent: Parent widget
        available_cities: List of available cities
        on_create: Callback function for creating comparison
        
    Returns:
        Comparison dialog window or None if no cities
    """
    if not available_cities:
        messagebox.showwarning("Warning", "No cities available for comparison")
        return None
    
    # Create comparison dialog
    comp_window = ctk.CTkToplevel(parent)
    comp_window.title("Create Comparison")
    comp_window.geometry("500x400")
    comp_window.transient(parent)
    comp_window.grab_set()
    
    # Center window
    comp_window.update_idletasks()
    x = (comp_window.winfo_screenwidth() // 2) - (500 // 2)
    y = (comp_window.winfo_screenheight() // 2) - (400 // 2)
    comp_window.geometry(f"500x400+{x}+{y}")
    
    # Comparison form
    form_frame = ctk.CTkFrame(comp_window)
    form_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = ctk.CTkLabel(form_frame, text="Title:")
    title_label.pack(anchor="w", padx=10, pady=(10, 5))
    
    title_var = ctk.StringVar()
    title_entry = ctk.CTkEntry(form_frame, textvariable=title_var)
    title_entry.pack(fill="x", padx=10, pady=(0, 10))
    
    # Cities selection
    cities_label = ctk.CTkLabel(form_frame, text="Select Cities:")
    cities_label.pack(anchor="w", padx=10, pady=(10, 5))
    
    cities_frame = ctk.CTkScrollableFrame(form_frame, height=150)
    cities_frame.pack(fill="x", padx=10, pady=(0, 10))
    
    city_vars = {}
    for city in available_cities:
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(cities_frame, text=city, variable=var)
        checkbox.pack(anchor="w", padx=5, pady=2)
        city_vars[city] = var
    
    # Metrics selection
    metrics_label = ctk.CTkLabel(form_frame, text="Select Metrics:")
    metrics_label.pack(anchor="w", padx=10, pady=(10, 5))
    
    metrics_frame = ctk.CTkFrame(form_frame)
    metrics_frame.pack(fill="x", padx=10, pady=(0, 20))
    
    available_metrics = ["temperature", "humidity", "pressure", "wind_speed", "visibility"]
    metric_vars = {}
    for metric in available_metrics:
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(metrics_frame, text=metric.replace("_", " ").title(), variable=var)
        checkbox.pack(side="left", padx=5, pady=5)
        metric_vars[metric] = var
    
    # Buttons
    button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
    button_frame.pack(fill="x", padx=10)
    
    def create_comparison():
        """Handle comparison creation."""
        title = title_var.get().strip()
        selected_cities = [city for city, var in city_vars.items() if var.get()]
        selected_metrics = [metric for metric, var in metric_vars.items() if var.get()]
        
        if not title:
            messagebox.showerror("Error", "Please enter a title")
            return
        
        if len(selected_cities) < 2:
            messagebox.showerror("Error", "Please select at least 2 cities")
            return
        
        if not selected_metrics:
            messagebox.showerror("Error", "Please select at least 1 metric")
            return
        
        if on_create:
            on_create(title, selected_cities, selected_metrics)
        
        comp_window.destroy()
    
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
    
    return comp_window