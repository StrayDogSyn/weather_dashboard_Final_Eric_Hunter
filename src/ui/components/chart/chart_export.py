"""Chart Export Mixin for Temperature Chart Component.

This module provides the ChartExportMixin class that handles chart export
functionality for PNG, PDF, and other formats.
"""

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
from typing import Optional, Dict, Any
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox


class ChartExportMixin:
    """Mixin for chart export functionality."""
    
    def export_chart(self, format_type: str = 'png', filename: Optional[str] = None):
        """Export chart to specified format."""
        try:
            if format_type.lower() == 'png':
                self._export_png(filename)
            elif format_type.lower() == 'pdf':
                self._export_pdf(filename)
            else:
                self.show_notification(f"Unsupported format: {format_type}", "error")
                
        except Exception as e:
            self.show_notification(f"Export failed: {str(e)}", "error")
            
    def _export_png(self, filename: Optional[str] = None):
        """Export chart as PNG image."""
        if not filename:
            filename = self._get_export_filename('png')
            
        if not filename:
            return  # User cancelled
            
        # Configure export settings
        export_settings = self._get_png_export_settings()
        
        # Save the figure
        self.fig.savefig(
            filename,
            **export_settings
        )
        
        self.show_notification(f"Chart exported to {os.path.basename(filename)}", "info")
        
    def _export_pdf(self, filename: Optional[str] = None):
        """Export chart as PDF document."""
        if not filename:
            filename = self._get_export_filename('pdf')
            
        if not filename:
            return  # User cancelled
            
        # Configure export settings
        export_settings = self._get_pdf_export_settings()
        
        # Create PDF with metadata
        with PdfPages(filename) as pdf:
            # Save the figure to PDF
            pdf.savefig(
                self.fig,
                **export_settings
            )
            
            # Add metadata
            metadata = self._get_export_metadata()
            pdf.infodict().update(metadata)
            
        self.show_notification(f"Chart exported to {os.path.basename(filename)}", "info")
        
    def _get_export_filename(self, format_type: str) -> Optional[str]:
        """Get filename for export through file dialog."""
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timeframe = getattr(self, 'current_timeframe', '24h')
        default_name = f"temperature_chart_{timeframe}_{timestamp}.{format_type}"
        
        # File type filters
        if format_type == 'png':
            filetypes = [("PNG files", "*.png"), ("All files", "*.*")]
        elif format_type == 'pdf':
            filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*.*")]
            
        # Show save dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=filetypes,
            initialname=default_name,
            title=f"Export Chart as {format_type.upper()}"
        )
        
        return filename if filename else None
        
    def _get_png_export_settings(self) -> Dict[str, Any]:
        """Get PNG export settings."""
        return {
            'dpi': 300,
            'bbox_inches': 'tight',
            'pad_inches': 0.2,
            'facecolor': '#1a1a1a',
            'edgecolor': 'none',
            'transparent': False,
            'format': 'png'
        }
        
    def _get_pdf_export_settings(self) -> Dict[str, Any]:
        """Get PDF export settings."""
        return {
            'bbox_inches': 'tight',
            'pad_inches': 0.3,
            'facecolor': '#1a1a1a',
            'edgecolor': 'none',
            'format': 'pdf'
        }
        
    def _get_export_metadata(self) -> Dict[str, str]:
        """Get metadata for exported files."""
        timeframe = getattr(self, 'current_timeframe', '24h')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            'Title': f'Temperature Chart ({timeframe})',
            'Author': 'Weather Dashboard',
            'Subject': 'Temperature Analysis Chart',
            'Creator': 'Weather Dashboard Application',
            'Producer': 'matplotlib',
            'CreationDate': timestamp,
            'Keywords': f'weather, temperature, chart, {timeframe}'
        }
        
    def export_data_csv(self, filename: Optional[str] = None):
        """Export chart data as CSV file."""
        try:
            if not hasattr(self, 'dates') or not hasattr(self, 'temperatures'):
                self.show_notification("No data available for export", "error")
                return
                
            if not filename:
                filename = self._get_export_filename('csv')
                
            if not filename:
                return  # User cancelled
                
            # Prepare data for CSV
            csv_data = self._prepare_csv_data()
            
            # Write CSV file
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                csvfile.write(csv_data)
                
            self.show_notification(f"Data exported to {os.path.basename(filename)}", "info")
            
        except Exception as e:
            self.show_notification(f"CSV export failed: {str(e)}", "error")
            
    def _prepare_csv_data(self) -> str:
        """Prepare data for CSV export."""
        lines = []
        
        # Header
        headers = ['Date', 'Time', 'Temperature (°C)']
        
        # Add additional data columns if available
        if hasattr(self, 'humidity_data') and self.humidity_data:
            headers.append('Humidity (%)')
        if hasattr(self, 'wind_data') and self.wind_data:
            headers.append('Wind Speed (km/h)')
        if hasattr(self, 'pressure_data') and self.pressure_data:
            headers.append('Pressure (hPa)')
            
        lines.append(','.join(headers))
        
        # Data rows
        for i, (date, temp) in enumerate(zip(self.dates, self.temperatures)):
            row = [
                date.strftime('%Y-%m-%d'),
                date.strftime('%H:%M:%S'),
                str(temp)
            ]
            
            # Add additional data if available
            if hasattr(self, 'humidity_data') and self.humidity_data and i < len(self.humidity_data):
                row.append(str(self.humidity_data[i]))
            elif 'Humidity (%)' in headers:
                row.append('')
                
            if hasattr(self, 'wind_data') and self.wind_data and i < len(self.wind_data):
                row.append(str(self.wind_data[i]))
            elif 'Wind Speed (km/h)' in headers:
                row.append('')
                
            if hasattr(self, 'pressure_data') and self.pressure_data and i < len(self.pressure_data):
                row.append(str(self.pressure_data[i]))
            elif 'Pressure (hPa)' in headers:
                row.append('')
                
            lines.append(','.join(row))
            
        return '\n'.join(lines)
        
    def export_chart_with_data(self, format_type: str = 'pdf'):
        """Export chart with accompanying data table."""
        try:
            filename = self._get_export_filename(format_type)
            if not filename:
                return
                
            if format_type.lower() == 'pdf':
                self._export_pdf_with_data(filename)
            else:
                self.show_notification("Data export only supported for PDF format", "error")
                
        except Exception as e:
            self.show_notification(f"Export with data failed: {str(e)}", "error")
            
    def _export_pdf_with_data(self, filename: str):
        """Export PDF with chart and data table."""
        with PdfPages(filename) as pdf:
            # First page: Chart
            pdf.savefig(self.fig, **self._get_pdf_export_settings())
            
            # Second page: Data table
            self._create_data_table_page(pdf)
            
            # Add metadata
            metadata = self._get_export_metadata()
            metadata['Title'] += ' with Data'
            pdf.infodict().update(metadata)
            
        self.show_notification(f"Chart with data exported to {os.path.basename(filename)}", "info")
        
    def _create_data_table_page(self, pdf: PdfPages):
        """Create a data table page for PDF export."""
        # Create new figure for data table
        fig, ax = plt.subplots(figsize=(8.5, 11))  # Letter size
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.95, 'Temperature Data', 
                horizontalalignment='center', 
                fontsize=16, fontweight='bold',
                transform=ax.transAxes)
        
        # Prepare table data
        table_data = self._prepare_table_data()
        
        if table_data:
            # Create table
            table = ax.table(
                cellText=table_data['data'],
                colLabels=table_data['headers'],
                cellLoc='center',
                loc='center',
                bbox=[0.1, 0.1, 0.8, 0.8]
            )
            
            # Style table
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.5)
            
            # Header styling
            for i in range(len(table_data['headers'])):
                table[(0, i)].set_facecolor('#00ff88')
                table[(0, i)].set_text_props(weight='bold', color='black')
                
        # Save table page
        pdf.savefig(fig, bbox_inches='tight', pad_inches=0.5)
        plt.close(fig)
        
    def _prepare_table_data(self) -> Dict[str, Any]:
        """Prepare data for table display."""
        if not hasattr(self, 'dates') or not self.dates:
            return None
            
        headers = ['Date/Time', 'Temperature (°C)']
        data = []
        
        # Add additional columns if data available
        has_humidity = hasattr(self, 'humidity_data') and self.humidity_data
        has_wind = hasattr(self, 'wind_data') and self.wind_data
        
        if has_humidity:
            headers.append('Humidity (%)')
        if has_wind:
            headers.append('Wind (km/h)')
            
        # Limit to reasonable number of rows for table
        max_rows = 50
        step = max(1, len(self.dates) // max_rows)
        
        for i in range(0, len(self.dates), step):
            if i >= len(self.temperatures):
                break
                
            row = [
                self.dates[i].strftime('%m/%d %H:%M'),
                f"{self.temperatures[i]:.1f}"
            ]
            
            if has_humidity and i < len(self.humidity_data):
                row.append(f"{self.humidity_data[i]}")
            elif has_humidity:
                row.append('-')
                
            if has_wind and i < len(self.wind_data):
                row.append(f"{self.wind_data[i]:.1f}")
            elif has_wind:
                row.append('-')
                
            data.append(row)
            
        return {
            'headers': headers,
            'data': data
        }
        
    def quick_export_png(self):
        """Quick export to PNG with default settings."""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timeframe = getattr(self, 'current_timeframe', '24h')
            filename = f"temperature_chart_{timeframe}_{timestamp}.png"
            
            # Export to current directory
            self.fig.savefig(filename, **self._get_png_export_settings())
            
            self.show_notification(f"Quick export: {filename}", "info")
            
        except Exception as e:
            self.show_notification(f"Quick export failed: {str(e)}", "error")
            
    def get_export_formats(self) -> list:
        """Get list of supported export formats."""
        return ['png', 'pdf', 'csv']
        
    def validate_export_data(self) -> bool:
        """Validate that data is available for export."""
        return (hasattr(self, 'dates') and self.dates and 
                hasattr(self, 'temperatures') and self.temperatures)