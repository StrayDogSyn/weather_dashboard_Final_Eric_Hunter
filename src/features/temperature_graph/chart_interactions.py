#!/usr/bin/env python3
"""
Chart Interaction Handlers

Contains all mouse, keyboard, and user interaction handlers for the
advanced temperature chart widget.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (TRAE 2.0 Phase 3)
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Optional, Tuple, Callable
from .chart_models import GlassmorphicTooltip
from ...ui.components.glass import GlassFrame, GlassButton
from ...utils.logger import LoggerMixin


class ChartInteractionHandler(LoggerMixin):
    """Handles all chart interactions including mouse, keyboard, and touch events."""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.tooltip: Optional[GlassmorphicTooltip] = None
        self.hover_point: Optional[Tuple[float, float]] = None
        self.selected_range: Optional[Tuple[datetime, datetime]] = None
        self.is_dragging = False
        self.drag_start: Optional[Tuple[float, float]] = None
        
        # Interaction state
        self.zoom_factor = 1.0
        self.pan_offset = (0, 0)
        
    def setup_event_handlers(self):
        """Setup all event handlers for chart interactions."""
        if hasattr(self.parent, 'canvas') and self.parent.canvas:
            canvas = self.parent.canvas
            
            # Mouse events
            canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
            canvas.mpl_connect('button_press_event', self._on_mouse_press)
            canvas.mpl_connect('button_release_event', self._on_mouse_release)
            canvas.mpl_connect('scroll_event', self._on_mouse_scroll)
            
            # Keyboard events
            canvas.mpl_connect('key_press_event', self._on_key_press)
            
            # Focus events
            canvas.get_tk_widget().bind('<Enter>', self._on_mouse_enter)
            canvas.get_tk_widget().bind('<Leave>', self._on_mouse_leave)
            
            # Make canvas focusable for keyboard events
            canvas.get_tk_widget().focus_set()
            canvas.get_tk_widget().bind('<Button-1>', lambda e: canvas.get_tk_widget().focus_set())
    
    def _on_mouse_move(self, event):
        """Handle mouse movement over chart."""
        if not event.inaxes or not hasattr(self.parent, 'current_data'):
            self._hide_tooltip()
            return
        
        try:
            # Find nearest data point
            nearest_point = self._find_nearest_point(event.xdata, event.ydata)
            
            if nearest_point:
                self.hover_point = (event.xdata, event.ydata)
                self._show_data_tooltip(event, nearest_point)
            else:
                self._hide_tooltip()
                
        except Exception as e:
            self.logger.error(f"Error in mouse move handler: {e}")
    
    def _on_mouse_press(self, event):
        """Handle mouse button press."""
        if not event.inaxes:
            return
        
        try:
            if event.button == 1:  # Left click
                self.is_dragging = True
                self.drag_start = (event.xdata, event.ydata)
                
                # Check for data point click
                nearest_point = self._find_nearest_point(event.xdata, event.ydata)
                if nearest_point:
                    self._show_point_details(event, nearest_point)
                    
            elif event.button == 3:  # Right click
                self._show_context_menu(event)
                
        except Exception as e:
            self.logger.error(f"Error in mouse press handler: {e}")
    
    def _on_mouse_release(self, event):
        """Handle mouse button release."""
        if not event.inaxes:
            return
        
        try:
            if event.button == 1 and self.is_dragging:  # Left click release
                self.is_dragging = False
                
                if self.drag_start:
                    # Check if this was a drag operation for selection
                    drag_distance = ((event.xdata - self.drag_start[0])**2 + 
                                   (event.ydata - self.drag_start[1])**2)**0.5
                    
                    if drag_distance > 0.1:  # Minimum drag distance
                        self._handle_selection_drag(self.drag_start, (event.xdata, event.ydata))
                
                self.drag_start = None
                
        except Exception as e:
            self.logger.error(f"Error in mouse release handler: {e}")
    
    def _on_mouse_scroll(self, event):
        """Handle mouse scroll for zooming."""
        if not event.inaxes:
            return
        
        try:
            # Zoom in/out based on scroll direction
            zoom_factor = 1.1 if event.step > 0 else 0.9
            self._zoom_at_point(event.xdata, event.ydata, zoom_factor)
            
        except Exception as e:
            self.logger.error(f"Error in mouse scroll handler: {e}")
    
    def _on_key_press(self, event):
        """Handle keyboard shortcuts."""
        try:
            key = event.key.lower() if event.key else ''
            
            if key == 'r':
                self.parent.refresh_chart()
            elif key == 'e':
                self.parent._show_export_dialog()
            elif key == 'h':
                self.parent._show_help_dialog()
            elif key == 'escape':
                self._reset_zoom()
            elif key == 'left':
                self._pan_left()
            elif key == 'right':
                self._pan_right()
            elif key == 'up':
                self._pan_up()
            elif key == 'down':
                self._pan_down()
            elif key == '+':
                self._zoom_in()
            elif key == '-':
                self._zoom_out()
                
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")
    
    def _on_mouse_enter(self, event):
        """Handle mouse entering chart area."""
        if hasattr(self.parent, 'canvas'):
            self.parent.canvas.get_tk_widget().configure(cursor="crosshair")
    
    def _on_mouse_leave(self, event):
        """Handle mouse leaving chart area."""
        if hasattr(self.parent, 'canvas'):
            self.parent.canvas.get_tk_widget().configure(cursor="")
        self._hide_tooltip()
    
    def _find_nearest_point(self, x, y, threshold=0.1):
        """Find the nearest data point to mouse coordinates."""
        if not hasattr(self.parent, 'current_data') or not self.parent.current_data:
            return None
        
        try:
            import matplotlib.dates as mdates
            
            min_distance = float('inf')
            nearest_point = None
            
            for point in self.parent.current_data:
                # Convert datetime to matplotlib date number
                point_x = mdates.date2num(point.timestamp)
                point_y = point.temperature
                
                # Calculate distance (normalized)
                distance = ((x - point_x)**2 + (y - point_y)**2)**0.5
                
                if distance < min_distance and distance < threshold:
                    min_distance = distance
                    nearest_point = point
            
            return nearest_point
            
        except Exception as e:
            self.logger.error(f"Error finding nearest point: {e}")
            return None
    
    def _show_data_tooltip(self, event, data_point):
        """Show tooltip with data point information."""
        try:
            # Hide existing tooltip
            self._hide_tooltip()
            
            # Create tooltip content
            content = f"""🕒 {data_point.timestamp.strftime('%Y-%m-%d %H:%M')}
🌡️ Temperature: {data_point.temperature:.1f}°C
🤗 Feels like: {data_point.feels_like:.1f}°C
💧 Humidity: {data_point.humidity:.1f}%
🌬️ Wind: {data_point.wind_speed:.1f} m/s
☁️ Condition: {data_point.condition}"""
            
            # Get screen coordinates
            canvas = self.parent.canvas
            x, y = canvas.get_tk_widget().winfo_pointerxy()
            
            # Create and show tooltip
            self.tooltip = GlassmorphicTooltip(self.parent, x + 10, y - 50, content)
            self.tooltip.show_tooltip()
            
        except Exception as e:
            self.logger.error(f"Error showing tooltip: {e}")
    
    def _hide_tooltip(self):
        """Hide current tooltip."""
        if self.tooltip:
            try:
                self.tooltip.hide_tooltip()
                self.tooltip = None
            except:
                pass
    
    def _show_point_details(self, event, data_point):
        """Show detailed popup for clicked data point."""
        try:
            details_popup = ctk.CTkToplevel(self.parent)
            details_popup.title("Temperature Data Details")
            details_popup.geometry("400x300")
            details_popup.configure(fg_color=("#1a1a1a", "#1a1a1a"))
            
            # Center popup
            details_popup.update_idletasks()
            x = (details_popup.winfo_screenwidth() // 2) - 200
            y = (details_popup.winfo_screenheight() // 2) - 150
            details_popup.geometry(f"400x300+{x}+{y}")
            
            # Content frame
            content_frame = GlassFrame(
                details_popup,
                fg_color=("#F8F8F8", "#2A2A2A"),
                corner_radius=15
            )
            content_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                content_frame,
                text="📊 Temperature Data Point",
                font=("Segoe UI", 16, "bold"),
                text_color=("#FFFFFF", "#E0E0E0")
            )
            title_label.pack(pady=(20, 20))
            
            # Details
            details_text = f"""🕒 Timestamp: {data_point.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
🌡️ Temperature: {data_point.temperature:.2f}°C
🤗 Feels Like: {data_point.feels_like:.2f}°C
💧 Humidity: {data_point.humidity:.1f}%
🌬️ Wind Speed: {data_point.wind_speed:.1f} m/s
🏭 Pressure: {data_point.pressure:.1f} hPa
☁️ Condition: {data_point.condition}
📍 Location: {data_point.location}"""
            
            details_label = ctk.CTkLabel(
                content_frame,
                text=details_text,
                font=("Segoe UI", 12),
                text_color=("#CCCCCC", "#AAAAAA"),
                justify="left"
            )
            details_label.pack(pady=10, padx=20)
            
            # Close button
            close_button = GlassButton(
                content_frame,
                text="Close",
                command=details_popup.destroy,
                width=100,
                height=35
            )
            close_button.pack(pady=(10, 20))
            
        except Exception as e:
            self.logger.error(f"Error showing point details: {e}")
    
    def _show_context_menu(self, event):
        """Show context menu on right click."""
        try:
            context_menu = ctk.CTkToplevel(self.parent)
            context_menu.overrideredirect(True)
            context_menu.configure(fg_color=("#2A2A2A", "#1A1A1A"))
            
            # Position menu at mouse location
            x, y = self.parent.canvas.get_tk_widget().winfo_pointerxy()
            context_menu.geometry(f"+{x}+{y}")
            
            # Menu items
            menu_frame = GlassFrame(context_menu, corner_radius=8)
            menu_frame.pack(padx=5, pady=5)
            
            # Zoom options
            zoom_in_btn = GlassButton(
                menu_frame,
                text="🔍 Zoom In",
                command=lambda: [self._zoom_in(), context_menu.destroy()],
                width=120,
                height=30
            )
            zoom_in_btn.pack(pady=2)
            
            zoom_out_btn = GlassButton(
                menu_frame,
                text="🔍 Zoom Out",
                command=lambda: [self._zoom_out(), context_menu.destroy()],
                width=120,
                height=30
            )
            zoom_out_btn.pack(pady=2)
            
            reset_btn = GlassButton(
                menu_frame,
                text="🏠 Reset View",
                command=lambda: [self._reset_zoom(), context_menu.destroy()],
                width=120,
                height=30
            )
            reset_btn.pack(pady=2)
            
            # Export option
            export_btn = GlassButton(
                menu_frame,
                text="📊 Export Chart",
                command=lambda: [self.parent._show_export_dialog(), context_menu.destroy()],
                width=120,
                height=30
            )
            export_btn.pack(pady=2)
            
            # Auto-hide menu after 5 seconds
            context_menu.after(5000, context_menu.destroy)
            
            # Hide menu when clicking elsewhere
            def hide_menu(event):
                try:
                    context_menu.destroy()
                except:
                    pass
            
            self.parent.bind('<Button-1>', hide_menu, add='+')
            
        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
    
    def _handle_selection_drag(self, start_point, end_point):
        """Handle drag selection for zooming to specific area."""
        try:
            # Convert coordinates to datetime range
            import matplotlib.dates as mdates
            
            start_time = mdates.num2date(min(start_point[0], end_point[0]))
            end_time = mdates.num2date(max(start_point[0], end_point[0]))
            
            self.selected_range = (start_time, end_time)
            
            # Zoom to selected range
            if hasattr(self.parent, 'ax'):
                self.parent.ax.set_xlim(start_time, end_time)
                
                # Also adjust y-axis to fit data in range
                y_min = min(start_point[1], end_point[1])
                y_max = max(start_point[1], end_point[1])
                self.parent.ax.set_ylim(y_min, y_max)
                
                self.parent.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error handling selection drag: {e}")
    
    def _zoom_at_point(self, x, y, zoom_factor):
        """Zoom in/out at specific point."""
        try:
            if hasattr(self.parent, 'ax'):
                ax = self.parent.ax
                
                # Get current limits
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                
                # Calculate new limits centered on point
                x_range = (xlim[1] - xlim[0]) / zoom_factor
                y_range = (ylim[1] - ylim[0]) / zoom_factor
                
                new_xlim = (x - x_range/2, x + x_range/2)
                new_ylim = (y - y_range/2, y + y_range/2)
                
                ax.set_xlim(new_xlim)
                ax.set_ylim(new_ylim)
                
                self.parent.canvas.draw()
                
        except Exception as e:
            self.logger.error(f"Error zooming at point: {e}")
    
    def _zoom_in(self):
        """Zoom in on chart."""
        self.zoom_factor *= 1.2
        self._apply_zoom()
    
    def _zoom_out(self):
        """Zoom out on chart."""
        self.zoom_factor /= 1.2
        self._apply_zoom()
    
    def _reset_zoom(self):
        """Reset zoom to original view."""
        self.zoom_factor = 1.0
        self.pan_offset = (0, 0)
        self.selected_range = None
        
        if hasattr(self.parent, 'ax'):
            self.parent.ax.autoscale()
            self.parent.canvas.draw()
    
    def _apply_zoom(self):
        """Apply current zoom factor."""
        try:
            if hasattr(self.parent, 'ax'):
                # Implementation depends on specific zoom requirements
                self.parent.canvas.draw()
        except Exception as e:
            self.logger.error(f"Error applying zoom: {e}")
    
    def _pan_left(self):
        """Pan chart to the left."""
        self._pan(-0.1, 0)
    
    def _pan_right(self):
        """Pan chart to the right."""
        self._pan(0.1, 0)
    
    def _pan_up(self):
        """Pan chart up."""
        self._pan(0, 0.1)
    
    def _pan_down(self):
        """Pan chart down."""
        self._pan(0, -0.1)
    
    def _pan(self, dx, dy):
        """Pan chart by relative amounts."""
        try:
            if hasattr(self.parent, 'ax'):
                ax = self.parent.ax
                
                # Get current limits
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                
                # Calculate pan amounts
                x_range = xlim[1] - xlim[0]
                y_range = ylim[1] - ylim[0]
                
                x_pan = dx * x_range
                y_pan = dy * y_range
                
                # Apply pan
                ax.set_xlim(xlim[0] + x_pan, xlim[1] + x_pan)
                ax.set_ylim(ylim[0] + y_pan, ylim[1] + y_pan)
                
                self.parent.canvas.draw()
                
        except Exception as e:
            self.logger.error(f"Error panning chart: {e}")