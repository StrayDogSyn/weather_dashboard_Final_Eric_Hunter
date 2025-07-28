"""UI card components for team collaboration features.

This module contains card-based UI components for displaying team members,
cities, comparisons, and activities in the team collaboration interface.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime

import customtkinter as ctk

from src.ui.components.glass import GlassFrame, GlassLabel, GlassButton
from src.utils.logger import LoggerMixin
from .models import TeamMember, CityData, TeamComparison, TeamActivity


class MemberCard(GlassFrame, LoggerMixin):
    """Card widget for displaying team member information."""
    
    def __init__(self, parent, member: TeamMember, on_click: Optional[Callable] = None, **kwargs):
        """Initialize member card.
        
        Args:
            parent: Parent widget
            member: Team member data
            on_click: Optional callback for card clicks
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.member = member
        self.on_click = on_click
        
        self._setup_ui()
        
        # Bind click events
        if self.on_click:
            self.bind("<Button-1>", lambda e: self.on_click(self.member))
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda e: self.on_click(self.member))
    
    def _setup_ui(self):
        """Setup the member card UI."""
        self.grid_columnconfigure(1, weight=1)
        
        # Avatar placeholder
        avatar_label = GlassLabel(
            self,
            text="👤",
            font=("Segoe UI", 20)
        )
        avatar_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        
        # Member info frame
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=5)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Name and username
        name_text = f"{self.member.name} (@{self.member.username})"
        name_label = GlassLabel(
            info_frame,
            text=name_text,
            font=("Segoe UI", 12, "bold")
        )
        name_label.grid(row=0, column=0, sticky="w")
        
        # Role
        role_label = GlassLabel(
            info_frame,
            text=self.member.role,
            font=("Segoe UI", 10),
            text_color="#888888"
        )
        role_label.grid(row=1, column=0, sticky="w")
        
        # Stats frame
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 5))
        
        # Cities shared
        cities_text = f"Cities: {self.member.cities_shared}"
        cities_label = GlassLabel(
            stats_frame,
            text=cities_text,
            font=("Segoe UI", 9)
        )
        cities_label.pack(side="left", padx=(0, 10))
        
        # Last active
        if self.member.last_active:
            last_active_text = f"Active: {self._format_date(self.member.last_active)}"
            active_label = GlassLabel(
                stats_frame,
                text=last_active_text,
                font=("Segoe UI", 9)
            )
            active_label.pack(side="left")
    
    def _format_date(self, date: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return date.strftime("%m/%d")


class CityCard(GlassFrame, LoggerMixin):
    """Card widget for displaying shared city information."""
    
    def __init__(self, parent, city: CityData, on_click: Optional[Callable] = None, 
                 on_favorite: Optional[Callable] = None, **kwargs):
        """Initialize city card.
        
        Args:
            parent: Parent widget
            city: City data
            on_click: Optional callback for card clicks
            on_favorite: Optional callback for favorite toggle
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.city = city
        self.on_click = on_click
        self.on_favorite = on_favorite
        
        self._setup_ui()
        
        # Bind click events
        if self.on_click:
            self.bind("<Button-1>", lambda e: self.on_click(self.city))
    
    def _setup_ui(self):
        """Setup the city card UI."""
        self.grid_columnconfigure(1, weight=1)
        
        # Weather icon
        weather_icon = self._get_weather_icon()
        icon_label = GlassLabel(
            self,
            text=weather_icon,
            font=("Segoe UI", 16)
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        
        # City info frame
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=5)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # City name and coordinates
        city_text = f"{self.city.city_name}, {self.city.country}"
        if self.city.coordinates:
            lat, lon = self.city.coordinates
            city_text += f" ({lat:.2f}, {lon:.2f})"
        
        name_label = GlassLabel(
            info_frame,
            text=city_text,
            font=("Segoe UI", 12, "bold")
        )
        name_label.grid(row=0, column=0, sticky="w")
        
        # Weather summary
        if self.city.weather_summary:
            weather_label = GlassLabel(
                info_frame,
                text=self.city.weather_summary,
                font=("Segoe UI", 10),
                text_color="#888888"
            )
            weather_label.grid(row=1, column=0, sticky="w")
        
        # Action buttons frame
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 5))
        
        # Favorite button
        fav_text = "⭐" if self.city.is_favorite else "☆"
        fav_button = GlassButton(
            actions_frame,
            text=fav_text,
            width=30,
            height=25,
            command=self._toggle_favorite
        )
        fav_button.pack(side="left", padx=(0, 5))
        
        # Shared by info
        if self.city.shared_by:
            shared_text = f"Shared by {self.city.shared_by}"
            if self.city.shared_date:
                shared_text += f" on {self.city.shared_date.strftime('%m/%d')}"
            
            shared_label = GlassLabel(
                actions_frame,
                text=shared_text,
                font=("Segoe UI", 9),
                text_color="#666666"
            )
            shared_label.pack(side="left")
    
    def _get_weather_icon(self) -> str:
        """Get weather icon based on conditions."""
        if not self.city.weather_summary:
            return "🌍"
        
        summary = self.city.weather_summary.lower()
        if "sunny" in summary or "clear" in summary:
            return "☀️"
        elif "cloudy" in summary or "overcast" in summary:
            return "☁️"
        elif "rain" in summary:
            return "🌧️"
        elif "snow" in summary:
            return "❄️"
        elif "storm" in summary:
            return "⛈️"
        else:
            return "🌤️"
    
    def _toggle_favorite(self):
        """Toggle favorite status."""
        if self.on_favorite:
            self.on_favorite(self.city)
        
        # Update UI
        self.city.is_favorite = not self.city.is_favorite
        self._update_favorite_button()
    
    def _update_favorite_button(self):
        """Update favorite button appearance."""
        fav_text = "⭐" if self.city.is_favorite else "☆"
        # Find and update the favorite button
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, GlassButton):
                        child.configure(text=fav_text)
                        break


class ComparisonCard(GlassFrame, LoggerMixin):
    """Card widget for displaying team comparison information."""
    
    def __init__(self, parent, comparison: TeamComparison, 
                 on_view: Optional[Callable] = None, **kwargs):
        """Initialize comparison card.
        
        Args:
            parent: Parent widget
            comparison: Team comparison data
            on_view: Optional callback for viewing comparison
            **kwargs: Additional widget arguments
        """
        super().__init__(parent, **kwargs)
        LoggerMixin.__init__(self)
        
        self.comparison = comparison
        self.on_view = on_view
        
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
        
        # Comparison info frame
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=5)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = GlassLabel(
            info_frame,
            text=self.comparison.title,
            font=("Segoe UI", 12, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Metrics
        metrics_text = f"Metrics: {', '.join(self.comparison.metrics)}"
        metrics_label = GlassLabel(
            info_frame,
            text=metrics_text,
            font=("Segoe UI", 10),
            text_color="#888888"
        )
        metrics_label.grid(row=1, column=0, sticky="w")
        
        # Actions frame
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 5))
        
        # View button
        if self.on_view:
            view_button = GlassButton(
                actions_frame,
                text="View",
                width=60,
                height=25,
                command=lambda: self.on_view(self.comparison)
            )
            view_button.pack(side="left", padx=(0, 5))
        
        # Created info
        created_text = f"Created: {self.comparison.created_date.strftime('%m/%d')}"
        if self.comparison.created_by:
            created_text += f" by {self.comparison.created_by}"
        
        created_label = GlassLabel(
            actions_frame,
            text=created_text,
            font=("Segoe UI", 9),
            text_color="#666666"
        )
        created_label.pack(side="left")


class ActivityCard(GlassFrame, LoggerMixin):
    """Card widget for displaying team activity information."""
    
    def __init__(self, parent, activity: TeamActivity, **kwargs):
        """Initialize activity card.
        
        Args:
            parent: Parent widget
            activity: Team activity data
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