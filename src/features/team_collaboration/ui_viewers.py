"""UI viewer components for team collaboration features.

This module contains popup windows and detailed viewers for displaying
comprehensive information about comparisons, cities, and other data.
"""

from typing import Dict, Any, Optional
from datetime import datetime

import customtkinter as ctk

from src.ui.components.glass import GlassLabel
from src.utils.logger import LoggerMixin
from .models import TeamComparison, CityData


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
        
        # Coordinates
        if self.city.coordinates:
            lat, lon = self.city.coordinates
            coords_label = ctk.CTkLabel(
                content_frame,
                text=f"Coordinates: {lat:.4f}, {lon:.4f}",
                font=("Segoe UI", 12)
            )
            coords_label.pack(pady=(0, 10))
        
        # Weather summary
        if self.city.weather_summary:
            weather_frame = ctk.CTkFrame(content_frame)
            weather_frame.pack(fill="x", pady=(0, 10))
            
            weather_title = ctk.CTkLabel(
                weather_frame,
                text="Current Weather",
                font=("Segoe UI", 14, "bold")
            )
            weather_title.pack(pady=(10, 5))
            
            weather_label = ctk.CTkLabel(
                weather_frame,
                text=self.city.weather_summary,
                font=("Segoe UI", 12)
            )
            weather_label.pack(pady=(0, 10))
        
        # Sharing info
        if self.city.shared_by:
            sharing_frame = ctk.CTkFrame(content_frame)
            sharing_frame.pack(fill="x", pady=(0, 10))
            
            sharing_title = ctk.CTkLabel(
                sharing_frame,
                text="Sharing Information",
                font=("Segoe UI", 14, "bold")
            )
            sharing_title.pack(pady=(10, 5))
            
            shared_by_label = ctk.CTkLabel(
                sharing_frame,
                text=f"Shared by: {self.city.shared_by}",
                font=("Segoe UI", 12)
            )
            shared_by_label.pack(pady=(0, 5))
            
            if self.city.shared_date:
                shared_date_label = ctk.CTkLabel(
                    sharing_frame,
                    text=f"Shared on: {self.city.shared_date.strftime('%Y-%m-%d %H:%M')}",
                    font=("Segoe UI", 12)
                )
                shared_date_label.pack(pady=(0, 10))
        
        # Tags
        if self.city.tags:
            tags_frame = ctk.CTkFrame(content_frame)
            tags_frame.pack(fill="x", pady=(0, 10))
            
            tags_title = ctk.CTkLabel(
                tags_frame,
                text="Tags",
                font=("Segoe UI", 14, "bold")
            )
            tags_title.pack(pady=(10, 5))
            
            tags_text = ", ".join(self.city.tags)
            tags_label = ctk.CTkLabel(
                tags_frame,
                text=tags_text,
                font=("Segoe UI", 12)
            )
            tags_label.pack(pady=(0, 10))
        
        # Description
        if hasattr(self.city, 'description') and self.city.description:
            desc_frame = ctk.CTkFrame(content_frame)
            desc_frame.pack(fill="x", pady=(0, 10))
            
            desc_title = ctk.CTkLabel(
                desc_frame,
                text="Description",
                font=("Segoe UI", 14, "bold")
            )
            desc_title.pack(pady=(10, 5))
            
            desc_label = ctk.CTkLabel(
                desc_frame,
                text=self.city.description,
                font=("Segoe UI", 12),
                wraplength=400
            )
            desc_label.pack(pady=(0, 10))