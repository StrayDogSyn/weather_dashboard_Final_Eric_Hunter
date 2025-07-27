"""UI components for team collaboration feature.

This module contains reusable UI components and widgets used throughout
the team collaboration interface.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from ...ui.components.base_components import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry, GlassProgressBar
)
from .models import TeamMember, CityData, TeamComparison, ActivityItem
from ...utils.logger import LoggerMixin


class MemberCard(GlassFrame, LoggerMixin):
    """Card widget for displaying team member information."""
    
    def __init__(self, parent, member: TeamMember, **kwargs):
        """Initialize member card.
        
        Args:
            parent: Parent widget
            member: Team member data
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.member = member
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the member card UI."""
        self.grid_columnconfigure(1, weight=1)
        
        # Avatar (placeholder)
        avatar_label = GlassLabel(
            self,
            text="👤",
            font=("Segoe UI", 20)
        )
        avatar_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        
        # Member info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(10, 5))
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Name and username
        name_label = GlassLabel(
            info_frame,
            text=self.member.name,
            font=("Segoe UI", 14, "bold")
        )
        name_label.grid(row=0, column=0, sticky="w")
        
        username_label = GlassLabel(
            info_frame,
            text=f"@{self.member.username}",
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
            text=self.member.role.title(),
            font=("Segoe UI", 10),
            text_color=role_colors.get(self.member.role, "#757575")
        )
        role_label.grid(row=0, column=1, sticky="e", padx=(10, 0))
        
        # Stats
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        
        stats_text = f"🏙️ {self.member.cities_shared} cities • 📊 {self.member.contributions} contributions"
        stats_label = GlassLabel(
            stats_frame,
            text=stats_text,
            font=("Segoe UI", 10),
            text_color="#666666"
        )
        stats_label.pack(anchor="w")
    
    def update_member(self, member: TeamMember):
        """Update the displayed member data."""
        self.member = member
        # Clear and rebuild UI
        for widget in self.winfo_children():
            widget.destroy()
        self._setup_ui()


class CityCard(GlassFrame, LoggerMixin):
    """Card widget for displaying shared city information."""
    
    def __init__(self, parent, city: CityData, on_select: Callable = None, 
                 on_view_details: Callable = None, **kwargs):
        """Initialize city card.
        
        Args:
            parent: Parent widget
            city: City data
            on_select: Callback for city selection
            on_view_details: Callback for viewing details
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.city = city
        self.on_select = on_select
        self.on_view_details = on_view_details
        self.is_selected = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the city card UI."""
        self.grid_columnconfigure(1, weight=1)
        
        # Selection checkbox
        self.selection_var = ctk.BooleanVar()
        self.selection_var.trace("w", self._on_selection_changed)
        
        selection_check = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.selection_var,
            width=20
        )
        selection_check.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        
        # City info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(10, 5))
        info_frame.grid_columnconfigure(0, weight=1)
        
        # City name and country
        name_label = GlassLabel(
            info_frame,
            text=self.city.display_name,
            font=("Segoe UI", 14, "bold")
        )
        name_label.grid(row=0, column=0, sticky="w")
        
        # Location coordinates
        location_label = GlassLabel(
            info_frame,
            text=f"📍 {self.city.latitude:.4f}, {self.city.longitude:.4f}",
            font=("Segoe UI", 10),
            text_color="#888888"
        )
        location_label.grid(row=1, column=0, sticky="w")
        
        # Favorite indicator
        if self.city.is_favorite:
            fav_label = GlassLabel(
                info_frame,
                text="⭐",
                font=("Segoe UI", 14)
            )
            fav_label.grid(row=0, column=1, sticky="e")
        
        # Weather info and meta
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        meta_frame.grid_columnconfigure(0, weight=1)
        
        # Weather summary (if available)
        if self.city.current_weather:
            temp = self.city.current_weather.get("temperature", "N/A")
            condition = self.city.current_weather.get("condition", "")
            weather_text = f"🌡️ {temp}°C"
            if condition:
                weather_text += f" • {condition}"
            
            weather_label = GlassLabel(
                meta_frame,
                text=weather_text,
                font=("Segoe UI", 11)
            )
            weather_label.grid(row=0, column=0, sticky="w")
        
        # Shared by and date
        shared_text = f"Shared by {self.city.shared_by} • {self._format_date(self.city.shared_at)}"
        shared_label = GlassLabel(
            meta_frame,
            text=shared_text,
            font=("Segoe UI", 9),
            text_color="#888888"
        )
        shared_label.grid(row=1, column=0, sticky="w")
        
        # Action buttons
        if self.on_view_details:
            actions_frame = ctk.CTkFrame(meta_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=1, rowspan=2, sticky="e")
            
            view_button = GlassButton(
                actions_frame,
                text="👁️ View",
                width=70,
                height=28,
                command=lambda: self.on_view_details(self.city)
            )
            view_button.pack()
        
        # Tags (if any)
        if self.city.tags:
            tags_text = " ".join([f"#{tag}" for tag in self.city.tags[:3]])
            if len(self.city.tags) > 3:
                tags_text += f" +{len(self.city.tags) - 3}"
            
            tags_label = GlassLabel(
                meta_frame,
                text=tags_text,
                font=("Segoe UI", 9),
                text_color="#4CAF50"
            )
            tags_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))
    
    def _on_selection_changed(self, *args):
        """Handle selection change."""
        self.is_selected = self.selection_var.get()
        if self.on_select:
            self.on_select(self.city, self.is_selected)
    
    def _format_date(self, date: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} min ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return date.strftime("%m/%d")
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self.selection_var.set(selected)


class ComparisonCard(GlassFrame, LoggerMixin):
    """Card widget for displaying team comparisons."""
    
    def __init__(self, parent, comparison: TeamComparison, 
                 on_view: Callable = None, on_export: Callable = None, **kwargs):
        """Initialize comparison card.
        
        Args:
            parent: Parent widget
            comparison: Team comparison data
            on_view: Callback for viewing comparison
            on_export: Callback for exporting comparison
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.comparison = comparison
        self.on_view = on_view
        self.on_export = on_export
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the comparison card UI."""
        self.grid_columnconfigure(1, weight=1)
        
        # Comparison icon
        icon_label = GlassLabel(
            self,
            text="📊",
            font=("Segoe UI", 16)
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        
        # Comparison info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(10, 5))
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = GlassLabel(
            info_frame,
            text=self.comparison.title,
            font=("Segoe UI", 14, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Cities count and metrics
        details_text = f"{self.comparison.cities_count} cities • {self.comparison.metrics_count} metrics"
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
        
        if self.on_view:
            view_button = GlassButton(
                actions_frame,
                text="👁️ View",
                width=70,
                height=28,
                command=lambda: self.on_view(self.comparison)
            )
            view_button.pack(side="top", pady=(0, 5))
        
        if self.on_export:
            export_button = GlassButton(
                actions_frame,
                text="💾 Export",
                width=70,
                height=28,
                command=lambda: self.on_export(self.comparison)
            )
            export_button.pack(side="top")
        
        # Meta info
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        
        # Created by and date
        created_text = f"Created by {self.comparison.created_by} • {self._format_date(self.comparison.created_at)}"
        created_label = GlassLabel(
            meta_frame,
            text=created_text,
            font=("Segoe UI", 9),
            text_color="#888888"
        )
        created_label.pack(anchor="w")
    
    def _format_date(self, date: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} min ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return date.strftime("%Y-%m-%d")


class ActivityCard(GlassFrame, LoggerMixin):
    """Card widget for displaying activity items."""
    
    def __init__(self, parent, activity: ActivityItem, **kwargs):
        """Initialize activity card.
        
        Args:
            parent: Parent widget
            activity: Activity item data
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.activity = activity
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the activity card UI."""
        self.grid_columnconfigure(1, weight=1)
        
        # Activity type icon
        icon_label = GlassLabel(
            self,
            text=self.activity.icon,
            font=("Segoe UI", 14)
        )
        icon_label.grid(row=0, column=0, padx=10, pady=10)
        
        # Activity details
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        details_frame.grid_columnconfigure(0, weight=1)
        
        # Description
        desc_label = GlassLabel(
            details_frame,
            text=self.activity.description,
            font=("Segoe UI", 12)
        )
        desc_label.grid(row=0, column=0, sticky="w")
        
        # Timestamp and user
        meta_text = f"{self.activity.user} • {self._format_date(self.activity.timestamp)}"
        meta_label = GlassLabel(
            details_frame,
            text=meta_text,
            font=("Segoe UI", 10),
            text_color="#888888"
        )
        meta_label.grid(row=1, column=0, sticky="w")
    
    def _format_date(self, date: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} min ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return date.strftime("%Y-%m-%d")


class ComparisonViewer(ctk.CTkToplevel, LoggerMixin):
    """Popup window for viewing detailed comparison data."""
    
    def __init__(self, parent, comparison: TeamComparison, **kwargs):
        """Initialize comparison viewer.
        
        Args:
            parent: Parent widget
            comparison: Team comparison to display
            **kwargs: Additional window arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.comparison = comparison
        
        self.title(f"Comparison: {comparison.title}")
        self.geometry("800x600")
        self.transient(parent)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"800x600+{x}+{y}")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the viewer UI."""
        # Content frame
        content_frame = ctk.CTkScrollableFrame(self)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text=self.comparison.title,
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Comparison table
        if self.comparison.data:
            self._create_comparison_table(content_frame)
        else:
            no_data_label = ctk.CTkLabel(
                content_frame,
                text="No comparison data available",
                text_color="#888888"
            )
            no_data_label.pack(pady=20)
    
    def _create_comparison_table(self, parent):
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
        for i, metric in enumerate(self.comparison.metrics):
            metric_label = ctk.CTkLabel(
                header_frame,
                text=metric.replace("_", " ").title(),
                font=("Segoe UI", 12, "bold")
            )
            metric_label.grid(row=0, column=i+1, padx=10, pady=5)
        
        # Data rows
        for row, (city_name, city_data) in enumerate(self.comparison.data.items()):
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
            for i, metric in enumerate(self.comparison.metrics):
                value = city_data.get(metric, "N/A")
                if isinstance(value, (int, float)):
                    value = f"{value:.1f}"
                
                value_label = ctk.CTkLabel(
                    row_frame,
                    text=str(value),
                    font=("Segoe UI", 11)
                )
                value_label.grid(row=0, column=i+1, padx=10, pady=5)


class CityDetailsViewer(ctk.CTkToplevel, LoggerMixin):
    """Popup window for viewing detailed city information."""
    
    def __init__(self, parent, city: CityData, **kwargs):
        """Initialize city details viewer.
        
        Args:
            parent: Parent widget
            city: City data to display
            **kwargs: Additional window arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.city = city
        
        self.title(f"City Details: {city.city_name}")
        self.geometry("500x400")
        self.transient(parent)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"500x400+{x}+{y}")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the viewer UI."""
        # Content frame
        content_frame = ctk.CTkScrollableFrame(self)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # City header
        header_label = ctk.CTkLabel(
            content_frame,
            text=f"{self.city.city_name}, {self.city.country}",
            font=("Segoe UI", 18, "bold")
        )
        header_label.pack(pady=(0, 20))
        
        # Location
        location_label = ctk.CTkLabel(
            content_frame,
            text=f"📍 {self.city.latitude:.4f}, {self.city.longitude:.4f}",
            font=("Segoe UI", 12)
        )
        location_label.pack(pady=(0, 10))
        
        # Weather data
        if self.city.current_weather:
            weather_frame = ctk.CTkFrame(content_frame)
            weather_frame.pack(fill="x", pady=(0, 10))
            
            weather_title = ctk.CTkLabel(
                weather_frame,
                text="Current Weather",
                font=("Segoe UI", 14, "bold")
            )
            weather_title.pack(pady=(10, 5))
            
            for key, value in self.city.current_weather.items():
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
            text=f"Shared by: {self.city.shared_by}",
            font=("Segoe UI", 11)
        )
        shared_label.pack(anchor="w", padx=10, pady=2)
        
        date_label = ctk.CTkLabel(
            meta_frame,
            text=f"Shared on: {self._format_date(self.city.shared_at)}",
            font=("Segoe UI", 11)
        )
        date_label.pack(anchor="w", padx=10, pady=2)
        
        if self.city.description:
            desc_label = ctk.CTkLabel(
                meta_frame,
                text=f"Description: {self.city.description}",
                font=("Segoe UI", 11)
            )
            desc_label.pack(anchor="w", padx=10, pady=2)
        
        if self.city.tags:
            tags_label = ctk.CTkLabel(
                meta_frame,
                text=f"Tags: {', '.join(self.city.tags)}",
                font=("Segoe UI", 11)
            )
            tags_label.pack(anchor="w", padx=10, pady=(2, 10))
    
    def _format_date(self, date: datetime) -> str:
        """Format datetime for display."""
        return date.strftime("%Y-%m-%d %H:%M")


class SelectedCitiesDisplay(ctk.CTkFrame, LoggerMixin):
    """Widget for displaying selected cities for comparison."""
    
    def __init__(self, parent, on_remove_city: Callable = None, **kwargs):
        """Initialize selected cities display.
        
        Args:
            parent: Parent widget
            on_remove_city: Callback for removing city from selection
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        LoggerMixin.__init__(self)
        
        self.on_remove_city = on_remove_city
        self.selected_cities: List[str] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the display UI."""
        # This will be populated when cities are added
        pass
    
    def update_selected_cities(self, cities: List[str]):
        """Update the list of selected cities."""
        self.selected_cities = cities.copy()
        
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        if not self.selected_cities:
            no_selection_label = GlassLabel(
                self,
                text="No cities selected",
                text_color="#888888"
            )
            no_selection_label.pack()
            return
        
        # Display selected cities
        for city_name in self.selected_cities:
            city_frame = ctk.CTkFrame(self, fg_color="transparent")
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
                command=lambda c=city_name: self._remove_city(c)
            )
            remove_button.pack(side="left", padx=(5, 0))
    
    def _remove_city(self, city_name: str):
        """Remove city from selection."""
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
        message_label = ctk.CTkLabel(
            content_frame,
            text=self.message,
            font=("Segoe UI", 14)
        )
        message_label.pack(pady=(0, 20))
    
    def update_message(self, message: str):
        """Update the loading message."""
        self.message = message
        # Find and update the message label
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and hasattr(child, 'cget'):
                        try:
                            if child.cget('text') == self.message:
                                child.configure(text=message)
                                break
                        except:
                            pass


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
        """Update status message."""
        self.status_label.configure(text=message)
    
    def update_last_sync(self, sync_time: datetime = None):
        """Update last sync time display."""
        if sync_time is None:
            sync_time = datetime.now()
        
        self.last_sync_label.configure(text=f"Last sync: {sync_time.strftime('%H:%M:%S')}")


# Utility functions for creating dialogs
def create_share_city_dialog(parent, current_weather_data: Dict[str, Any], 
                           on_share: Callable) -> Optional[ctk.CTkToplevel]:
    """Create dialog for sharing city data."""
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