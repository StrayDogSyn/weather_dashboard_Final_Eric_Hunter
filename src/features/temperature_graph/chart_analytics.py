#!/usr/bin/env python3
"""
Chart Analytics and Export

Handles analytics calculations, data export functionality, and statistical
analysis for the advanced temperature chart widget.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
import io
import base64
from PIL import Image
from ...core.models import TemperatureDataPoint
from ...utils.logger import LoggerMixin


@dataclass
class ChartAnalytics:
    """Analytics data for temperature chart."""
    avg_temp: float
    min_temp: float
    max_temp: float
    temp_range: float
    avg_humidity: float
    avg_wind_speed: float
    dominant_condition: str
    data_points: int
    time_span: timedelta
    trend_direction: str  # 'rising', 'falling', 'stable'
    trend_strength: float  # 0-1
    

@dataclass
class ExportSettings:
    """Settings for chart export."""
    format: str = 'png'  # png, jpg, pdf, svg
    dpi: int = 300
    width: int = 1920
    height: int = 1080
    include_data: bool = True
    include_analytics: bool = True
    transparent_bg: bool = False
    

class ChartAnalyticsEngine(LoggerMixin):
    """Handles analytics calculations and export functionality."""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.export_settings = ExportSettings()
        
    def calculate_analytics(self, data: List[TemperatureDataPoint]) -> ChartAnalytics:
        """Calculate comprehensive analytics for temperature data."""
        if not data:
            return self._empty_analytics()
        
        try:
            # Basic statistics
            temperatures = [point.temperature for point in data]
            humidities = [point.humidity for point in data]
            wind_speeds = [point.wind_speed for point in data]
            conditions = [point.condition for point in data]
            
            avg_temp = np.mean(temperatures)
            min_temp = np.min(temperatures)
            max_temp = np.max(temperatures)
            temp_range = max_temp - min_temp
            
            avg_humidity = np.mean(humidities)
            avg_wind_speed = np.mean(wind_speeds)
            
            # Dominant weather condition
            condition_counts = {}
            for condition in conditions:
                condition_counts[condition] = condition_counts.get(condition, 0) + 1
            dominant_condition = max(condition_counts, key=condition_counts.get)
            
            # Time span
            timestamps = [point.timestamp for point in data]
            time_span = max(timestamps) - min(timestamps)
            
            # Trend analysis
            trend_direction, trend_strength = self._calculate_trend(data)
            
            return ChartAnalytics(
                avg_temp=avg_temp,
                min_temp=min_temp,
                max_temp=max_temp,
                temp_range=temp_range,
                avg_humidity=avg_humidity,
                avg_wind_speed=avg_wind_speed,
                dominant_condition=dominant_condition,
                data_points=len(data),
                time_span=time_span,
                trend_direction=trend_direction,
                trend_strength=trend_strength
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating analytics: {e}")
            return self._empty_analytics()
    
    def _empty_analytics(self) -> ChartAnalytics:
        """Return empty analytics object."""
        return ChartAnalytics(
            avg_temp=0.0,
            min_temp=0.0,
            max_temp=0.0,
            temp_range=0.0,
            avg_humidity=0.0,
            avg_wind_speed=0.0,
            dominant_condition="Unknown",
            data_points=0,
            time_span=timedelta(0),
            trend_direction="stable",
            trend_strength=0.0
        )
    
    def _calculate_trend(self, data: List[TemperatureDataPoint]) -> Tuple[str, float]:
        """Calculate temperature trend direction and strength."""
        if len(data) < 2:
            return "stable", 0.0
        
        try:
            # Convert to numpy arrays for analysis
            timestamps = np.array([point.timestamp.timestamp() for point in data])
            temperatures = np.array([point.temperature for point in data])
            
            # Linear regression to find trend
            coeffs = np.polyfit(timestamps, temperatures, 1)
            slope = coeffs[0]
            
            # Calculate correlation coefficient for trend strength
            correlation = np.corrcoef(timestamps, temperatures)[0, 1]
            trend_strength = abs(correlation)
            
            # Determine trend direction
            if abs(slope) < 1e-6:  # Very small slope
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "rising"
            else:
                trend_direction = "falling"
            
            return trend_direction, trend_strength
            
        except Exception as e:
            self.logger.error(f"Error calculating trend: {e}")
            return "stable", 0.0
    
    def export_chart(self, export_path: str, settings: Optional[ExportSettings] = None) -> bool:
        """Export chart with current data and settings."""
        if settings:
            self.export_settings = settings
        
        try:
            if not hasattr(self.parent, 'fig') or not self.parent.fig:
                self.logger.error("No chart figure available for export")
                return False
            
            # Save the chart
            export_path = Path(export_path)
            
            # Configure export settings
            save_kwargs = {
                'dpi': self.export_settings.dpi,
                'bbox_inches': 'tight',
                'transparent': self.export_settings.transparent_bg,
                'facecolor': 'none' if self.export_settings.transparent_bg else 'white'
            }
            
            # Set figure size
            fig_width = self.export_settings.width / self.export_settings.dpi
            fig_height = self.export_settings.height / self.export_settings.dpi
            self.parent.fig.set_size_inches(fig_width, fig_height)
            
            # Save chart
            self.parent.fig.savefig(export_path, format=self.export_settings.format, **save_kwargs)
            
            # Export additional data if requested
            if self.export_settings.include_data:
                self._export_data(export_path.with_suffix('.json'))
            
            if self.export_settings.include_analytics:
                self._export_analytics(export_path.with_suffix('_analytics.json'))
            
            self.logger.info(f"Chart exported successfully to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting chart: {e}")
            return False
    
    def _export_data(self, data_path: Path):
        """Export raw temperature data to JSON."""
        try:
            if not hasattr(self.parent, 'current_data') or not self.parent.current_data:
                return
            
            # Convert data to serializable format
            export_data = []
            for point in self.parent.current_data:
                export_data.append({
                    'timestamp': point.timestamp.isoformat(),
                    'temperature': point.temperature,
                    'feels_like': point.feels_like,
                    'humidity': point.humidity,
                    'wind_speed': point.wind_speed,
                    'pressure': point.pressure,
                    'condition': point.condition,
                    'location': point.location
                })
            
            # Save to JSON
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_timestamp': datetime.now().isoformat(),
                    'data_points': len(export_data),
                    'data': export_data
                }, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
    
    def _export_analytics(self, analytics_path: Path):
        """Export analytics data to JSON."""
        try:
            if not hasattr(self.parent, 'current_data') or not self.parent.current_data:
                return
            
            analytics = self.calculate_analytics(self.parent.current_data)
            
            # Convert to serializable format
            analytics_data = {
                'export_timestamp': datetime.now().isoformat(),
                'analytics': {
                    'average_temperature': analytics.avg_temp,
                    'minimum_temperature': analytics.min_temp,
                    'maximum_temperature': analytics.max_temp,
                    'temperature_range': analytics.temp_range,
                    'average_humidity': analytics.avg_humidity,
                    'average_wind_speed': analytics.avg_wind_speed,
                    'dominant_condition': analytics.dominant_condition,
                    'data_points': analytics.data_points,
                    'time_span_hours': analytics.time_span.total_seconds() / 3600,
                    'trend_direction': analytics.trend_direction,
                    'trend_strength': analytics.trend_strength
                }
            }
            
            # Save to JSON
            with open(analytics_path, 'w', encoding='utf-8') as f:
                json.dump(analytics_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error exporting analytics: {e}")
    
    def show_export_dialog(self):
        """Show export configuration dialog."""
        try:
            export_dialog = ctk.CTkToplevel(self.parent)
            export_dialog.title("Export Chart")
            export_dialog.geometry("500x600")
            export_dialog.configure(fg_color=("#1a1a1a", "#1a1a1a"))
            
            # Center dialog
            export_dialog.update_idletasks()
            x = (export_dialog.winfo_screenwidth() // 2) - 250
            y = (export_dialog.winfo_screenheight() // 2) - 300
            export_dialog.geometry(f"500x600+{x}+{y}")
            
            # Main frame
            main_frame = ctk.CTkScrollableFrame(
                export_dialog,
                fg_color=("#F8F8F8", "#2A2A2A"),
                corner_radius=15
            )
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="📊 Export Chart Configuration",
                font=("Segoe UI", 18, "bold"),
                text_color=("#FFFFFF", "#E0E0E0")
            )
            title_label.pack(pady=(20, 30))
            
            # Format selection
            format_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            format_frame.pack(fill="x", pady=10)
            
            format_label = ctk.CTkLabel(
                format_frame,
                text="Export Format:",
                font=("Segoe UI", 14, "bold")
            )
            format_label.pack(anchor="w")
            
            format_var = ctk.StringVar(value=self.export_settings.format)
            format_menu = ctk.CTkOptionMenu(
                format_frame,
                values=["png", "jpg", "pdf", "svg"],
                variable=format_var
            )
            format_menu.pack(fill="x", pady=(5, 0))
            
            # Resolution settings
            resolution_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            resolution_frame.pack(fill="x", pady=10)
            
            resolution_label = ctk.CTkLabel(
                resolution_frame,
                text="Resolution (DPI):",
                font=("Segoe UI", 14, "bold")
            )
            resolution_label.pack(anchor="w")
            
            dpi_var = ctk.StringVar(value=str(self.export_settings.dpi))
            dpi_entry = ctk.CTkEntry(
                resolution_frame,
                textvariable=dpi_var,
                placeholder_text="300"
            )
            dpi_entry.pack(fill="x", pady=(5, 0))
            
            # Size settings
            size_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            size_frame.pack(fill="x", pady=10)
            
            size_label = ctk.CTkLabel(
                size_frame,
                text="Image Size (Width x Height):",
                font=("Segoe UI", 14, "bold")
            )
            size_label.pack(anchor="w")
            
            size_inner_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
            size_inner_frame.pack(fill="x", pady=(5, 0))
            
            width_var = ctk.StringVar(value=str(self.export_settings.width))
            width_entry = ctk.CTkEntry(
                size_inner_frame,
                textvariable=width_var,
                placeholder_text="1920",
                width=100
            )
            width_entry.pack(side="left")
            
            x_label = ctk.CTkLabel(size_inner_frame, text=" x ", font=("Segoe UI", 12))
            x_label.pack(side="left", padx=5)
            
            height_var = ctk.StringVar(value=str(self.export_settings.height))
            height_entry = ctk.CTkEntry(
                size_inner_frame,
                textvariable=height_var,
                placeholder_text="1080",
                width=100
            )
            height_entry.pack(side="left")
            
            # Options
            options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            options_frame.pack(fill="x", pady=20)
            
            options_label = ctk.CTkLabel(
                options_frame,
                text="Export Options:",
                font=("Segoe UI", 14, "bold")
            )
            options_label.pack(anchor="w", pady=(0, 10))
            
            # Checkboxes
            include_data_var = ctk.BooleanVar(value=self.export_settings.include_data)
            include_data_cb = ctk.CTkCheckBox(
                options_frame,
                text="Include raw data (JSON)",
                variable=include_data_var
            )
            include_data_cb.pack(anchor="w", pady=2)
            
            include_analytics_var = ctk.BooleanVar(value=self.export_settings.include_analytics)
            include_analytics_cb = ctk.CTkCheckBox(
                options_frame,
                text="Include analytics (JSON)",
                variable=include_analytics_var
            )
            include_analytics_cb.pack(anchor="w", pady=2)
            
            transparent_var = ctk.BooleanVar(value=self.export_settings.transparent_bg)
            transparent_cb = ctk.CTkCheckBox(
                options_frame,
                text="Transparent background",
                variable=transparent_var
            )
            transparent_cb.pack(anchor="w", pady=2)
            
            # Buttons
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=20)
            
            def export_action():
                try:
                    # Update settings
                    self.export_settings.format = format_var.get()
                    self.export_settings.dpi = int(dpi_var.get())
                    self.export_settings.width = int(width_var.get())
                    self.export_settings.height = int(height_var.get())
                    self.export_settings.include_data = include_data_var.get()
                    self.export_settings.include_analytics = include_analytics_var.get()
                    self.export_settings.transparent_bg = transparent_var.get()
                    
                    # Show file dialog
                    from tkinter import filedialog
                    
                    file_types = {
                        'png': [("PNG files", "*.png")],
                        'jpg': [("JPEG files", "*.jpg")],
                        'pdf': [("PDF files", "*.pdf")],
                        'svg': [("SVG files", "*.svg")]
                    }
                    
                    filename = filedialog.asksaveasfilename(
                        title="Export Chart",
                        defaultextension=f".{self.export_settings.format}",
                        filetypes=file_types.get(self.export_settings.format, [("All files", "*.*")])
                    )
                    
                    if filename:
                        success = self.export_chart(filename)
                        if success:
                            # Show success message
                            success_dialog = ctk.CTkToplevel(export_dialog)
                            success_dialog.title("Export Successful")
                            success_dialog.geometry("300x150")
                            
                            success_label = ctk.CTkLabel(
                                success_dialog,
                                text="✅ Chart exported successfully!",
                                font=("Segoe UI", 14)
                            )
                            success_label.pack(pady=30)
                            
                            ok_button = ctk.CTkButton(
                                success_dialog,
                                text="OK",
                                command=success_dialog.destroy
                            )
                            ok_button.pack(pady=10)
                            
                            export_dialog.destroy()
                        
                except ValueError as e:
                    # Show error for invalid input
                    error_label = ctk.CTkLabel(
                        main_frame,
                        text=f"❌ Invalid input: {e}",
                        text_color="red"
                    )
                    error_label.pack(pady=5)
                    export_dialog.after(3000, error_label.destroy)
            
            export_button = ctk.CTkButton(
                button_frame,
                text="📊 Export Chart",
                command=export_action,
                height=40
            )
            export_button.pack(side="left", padx=(0, 10))
            
            cancel_button = ctk.CTkButton(
                button_frame,
                text="Cancel",
                command=export_dialog.destroy,
                height=40,
                fg_color="gray"
            )
            cancel_button.pack(side="left")
            
        except Exception as e:
            self.logger.error(f"Error showing export dialog: {e}")
    
    def get_chart_as_base64(self, format='png', dpi=150) -> Optional[str]:
        """Get chart as base64 encoded string for embedding."""
        try:
            if not hasattr(self.parent, 'fig') or not self.parent.fig:
                return None
            
            # Save to bytes buffer
            buffer = io.BytesIO()
            self.parent.fig.savefig(
                buffer,
                format=format,
                dpi=dpi,
                bbox_inches='tight',
                facecolor='white'
            )
            buffer.seek(0)
            
            # Encode to base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            
            return image_base64
            
        except Exception as e:
            self.logger.error(f"Error converting chart to base64: {e}")
            return None
    
    def generate_analytics_report(self, data: List[TemperatureDataPoint]) -> str:
        """Generate a comprehensive analytics report."""
        try:
            analytics = self.calculate_analytics(data)
            
            report = f"""📊 TEMPERATURE ANALYTICS REPORT
{'='*50}

📈 TEMPERATURE STATISTICS:
• Average Temperature: {analytics.avg_temp:.1f}°C
• Minimum Temperature: {analytics.min_temp:.1f}°C
• Maximum Temperature: {analytics.max_temp:.1f}°C
• Temperature Range: {analytics.temp_range:.1f}°C

🌡️ ENVIRONMENTAL CONDITIONS:
• Average Humidity: {analytics.avg_humidity:.1f}%
• Average Wind Speed: {analytics.avg_wind_speed:.1f} m/s
• Dominant Weather: {analytics.dominant_condition}

📊 DATA OVERVIEW:
• Total Data Points: {analytics.data_points:,}
• Time Span: {analytics.time_span.days} days, {analytics.time_span.seconds//3600} hours
• Trend Direction: {analytics.trend_direction.title()}
• Trend Strength: {analytics.trend_strength:.2f} (0=weak, 1=strong)

📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}"""
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating analytics report: {e}")
            return "Error generating analytics report."