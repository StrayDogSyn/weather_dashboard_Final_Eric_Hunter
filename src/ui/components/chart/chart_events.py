"""Chart Events Mixin for Temperature Chart Component.

This module provides the ChartEventsMixin class that handles mouse interactions,
event processing, and user input management for the temperature chart.
"""

from typing import Optional, Tuple

import matplotlib.dates as mdates


class ChartEventsMixin:
    """Mixin for chart event handling and user interactions."""

    def setup_event_handlers(self):
        """Setup all event handlers for the chart."""
        self._setup_mouse_events()
        self._setup_resize_events()
        self._setup_keyboard_events()

    def _setup_mouse_events(self):
        """Setup mouse event handlers."""
        # Mouse motion for tooltips
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_motion)

        # Mouse clicks for interactions
        self.canvas.mpl_connect("button_press_event", self._on_mouse_click)

        # Mouse leave to hide tooltips
        self.canvas.mpl_connect("axes_leave_event", self._on_mouse_leave)

    def _setup_resize_events(self):
        """Setup resize event handlers."""
        self.canvas.mpl_connect("resize_event", self._on_resize)

    def _setup_keyboard_events(self):
        """Setup keyboard event handlers."""
        self.canvas.mpl_connect("key_press_event", self._on_key_press)

    def _on_mouse_motion(self, event):
        """Handle mouse motion for enhanced interactive tooltips with trend analysis."""
        if event.inaxes != self.ax or not hasattr(self, "temperature_data"):
            self.hide_tooltip()
            return

        # Get mouse coordinates
        x_coord = event.xdata
        y_coord = event.ydata

        if x_coord is None or y_coord is None:
            self.hide_tooltip()
            return

        # Find nearest data point with improved detection
        nearest_point = self._find_nearest_data_point(x_coord, y_coord)

        if nearest_point:
            # Format enhanced tooltip content
            tooltip_content = self._format_tooltip_content(nearest_point)
            trend_info = self._calculate_trend_info(nearest_point)

            # Convert matplotlib coordinates to widget coordinates
            widget_x, widget_y = self._convert_coordinates(event.x, event.y)

            # Show enhanced tooltip
            self.show_tooltip(widget_x, widget_y, tooltip_content, trend_info)

            # Highlight the data point
            self._highlight_nearest_point(nearest_point)
        else:
            self.hide_tooltip()
            self._clear_highlight()

    def _on_mouse_click(self, event):
        """Handle mouse click events."""
        if event.inaxes != self.ax:
            return

        # Handle different click types
        if event.button == 1:  # Left click
            self._handle_left_click(event)
        elif event.button == 3:  # Right click
            self._handle_right_click(event)

    def _on_mouse_leave(self, event):
        """Handle mouse leave events."""
        self.hide_tooltip()

    def _on_resize(self, event):
        """Handle resize events."""
        # Refresh chart layout
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _on_key_press(self, event):
        """Handle keyboard events."""
        if event.key == "r":  # Refresh
            self._refresh_chart_data()
        elif event.key == "e":  # Export
            self.export_chart("png")
        elif event.key == "1":  # 24h view
            self.change_timeframe("24h")
        elif event.key == "2":  # 7d view
            self.change_timeframe("7d")
        elif event.key == "3":  # 30d view
            self.change_timeframe("30d")

    def _find_nearest_data_point(self, x_coord: float, y_coord: float) -> Optional[dict]:
        """Find the nearest data point with improved detection algorithm."""
        if not hasattr(self, "temperature_data") or not self.temperature_data:
            return None

        min_distance = float("inf")
        nearest_point = None

        # Get axis limits for normalization
        x_range = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
        y_range = self.ax.get_ylim()[1] - self.ax.get_ylim()[0]

        for i, (date, temp) in enumerate(zip(self.dates, self.temperatures)):
            # Convert date to matplotlib format
            date_num = mdates.date2num(date)

            # Normalize coordinates for better distance calculation
            norm_x_dist = (date_num - x_coord) / x_range
            norm_y_dist = (temp - y_coord) / y_range

            # Calculate normalized distance
            distance = (norm_x_dist**2 + norm_y_dist**2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_point = {
                    "index": i,
                    "date": date,
                    "temperature": temp,
                    "distance": distance,
                    "x_coord": date_num,
                    "y_coord": temp,
                }

        # Improved threshold based on data density
        threshold = 0.05 if len(self.dates) > 50 else 0.1
        if nearest_point and nearest_point["distance"] < threshold:
            return nearest_point

        return None

    def _format_tooltip_content(self, point_data: dict) -> str:
        """Format enhanced tooltip content with professional styling."""
        date = point_data["date"]
        temp = point_data["temperature"]

        # Format date based on current timeframe
        if self.current_timeframe == "24h":
            date_str = date.strftime("%H:%M")
            time_label = "Time"
        elif self.current_timeframe == "7d":
            date_str = date.strftime("%m/%d %H:%M")
            time_label = "Date/Time"
        else:  # 30d
            date_str = date.strftime("%m/%d/%Y")
            time_label = "Date"

        # Create enhanced tooltip content with better formatting
        content = f"📅 {time_label}: {date_str}\n🌡️ Temperature: {temp:.1f}°C"

        # Add temperature classification
        if temp < 0:
            temp_class = "Freezing"
        elif temp < 10:
            temp_class = "Cold"
        elif temp < 20:
            temp_class = "Cool"
        elif temp < 25:
            temp_class = "Comfortable"
        elif temp < 30:
            temp_class = "Warm"
        else:
            temp_class = "Hot"

        content += f"\n🏷️ Condition: {temp_class}"

        # Add additional weather data if available
        if hasattr(self, "humidity_data") and self.humidity_data:
            try:
                humidity = self.humidity_data[point_data["index"]]
                content += f"\n💧 Humidity: {humidity}%"
            except (IndexError, KeyError):
                pass

        if hasattr(self, "wind_data") and self.wind_data:
            try:
                wind = self.wind_data[point_data["index"]]
                content += f"\n💨 Wind: {wind} km/h"
            except (IndexError, KeyError):
                pass

        return content

    def _calculate_trend_info(self, point_data: dict) -> str:
        """Calculate trend analysis for the selected point."""
        index = point_data["index"]
        temp = point_data["temperature"]

        # Calculate trend based on surrounding points
        trend_info = ""

        # Look at previous and next points for trend
        if index > 0 and index < len(self.temperatures) - 1:
            prev_temp = self.temperatures[index - 1]
            next_temp = self.temperatures[index + 1]

            # Calculate trend direction
            if temp > prev_temp and temp > next_temp:
                trend_info = "📈 Peak Temperature"
            elif temp < prev_temp and temp < next_temp:
                trend_info = "📉 Temperature Low"
            elif temp > prev_temp:
                trend_info = "⬆️ Rising Trend"
            elif temp < prev_temp:
                trend_info = "⬇️ Falling Trend"
            else:
                trend_info = "➡️ Stable"

            # Add temperature change info
            temp_change = temp - prev_temp
            if abs(temp_change) > 0.1:
                change_str = f"{temp_change:+.1f}°C"
                trend_info += f" ({change_str})"

        elif index == 0 and len(self.temperatures) > 1:
            next_temp = self.temperatures[index + 1]
            if temp > next_temp:
                trend_info = "📈 Starting High"
            elif temp < next_temp:
                trend_info = "📉 Starting Low"
            else:
                trend_info = "➡️ Stable Start"

        elif index == len(self.temperatures) - 1 and len(self.temperatures) > 1:
            prev_temp = self.temperatures[index - 1]
            if temp > prev_temp:
                trend_info = "📈 Ending High"
            elif temp < prev_temp:
                trend_info = "📉 Ending Low"
            else:
                trend_info = "➡️ Stable End"

        return trend_info

    def _highlight_nearest_point(self, point_data: dict):
        """Highlight the nearest data point on the chart."""
        if hasattr(self, "highlight_point"):
            self.highlight_point.remove()

        # Create highlight marker
        self.highlight_point = self.ax.scatter(
            point_data["x_coord"],
            point_data["y_coord"],
            s=100,
            c="#00ff88",
            marker="o",
            edgecolors="white",
            linewidths=2,
            zorder=10,
            alpha=0.8,
        )

        # Refresh canvas
        self.canvas.draw_idle()

    def _clear_highlight(self):
        """Clear the highlighted data point."""
        if hasattr(self, "highlight_point"):
            try:
                self.highlight_point.remove()
                self.canvas.draw_idle()
            except (ValueError, AttributeError):
                pass
            finally:
                delattr(self, "highlight_point")

    def _convert_coordinates(self, mpl_x: float, mpl_y: float) -> Tuple[int, int]:
        """Convert matplotlib coordinates to widget coordinates."""
        # Get canvas dimensions
        self.canvas.get_tk_widget().winfo_width()
        canvas_height = self.canvas.get_tk_widget().winfo_height()

        # Convert coordinates
        widget_x = int(mpl_x)
        widget_y = int(canvas_height - mpl_y)

        return widget_x, widget_y

    def _handle_left_click(self, event):
        """Handle left mouse click events."""
        # Find clicked data point
        clicked_point = self._find_nearest_data_point(event.xdata, event.ydata)

        if clicked_point:
            # Highlight the clicked point
            self._highlight_data_point(clicked_point)

            # Show detailed information
            self._show_point_details(clicked_point)

    def _handle_right_click(self, event):
        """Handle right mouse click events (context menu)."""
        # Create context menu options
        menu_options = [
            ("Export as PNG", self._context_export_png),
            ("Export as PDF", self._context_export_pdf),
            ("Refresh Data", self._refresh_chart_data),
            ("Reset Zoom", self._reset_chart_zoom),
        ]

        # Show context menu (simplified implementation)
        self._show_context_menu(event.x, event.y, menu_options)

    def _highlight_data_point(self, point_data: dict):
        """Highlight a specific data point on the chart."""
        if hasattr(self, "highlight_point"):
            self.highlight_point.remove()

        # Create highlight marker
        date_num = mdates.date2num(point_data["date"])
        self.highlight_point = self.ax.scatter(
            [date_num], [point_data["temperature"]], color="#ffff00", s=100, zorder=10, alpha=0.8
        )

        self.canvas.draw_idle()

    def _show_point_details(self, point_data: dict):
        """Show detailed information about a data point."""
        details = self._format_tooltip_content(point_data)
        self.show_notification(f"Selected Point:\n{details}", "info")

    def _show_context_menu(self, x: int, y: int, options: list):
        """Show context menu at specified coordinates."""
        # Simple implementation - show notification with options
        menu_text = "Right-click options:\n" + "\n".join([opt[0] for opt in options])
        self.show_notification(menu_text, "info")

    def _refresh_chart_data(self):
        """Refresh chart data from source."""
        if hasattr(self, "update_forecast"):
            # Trigger data refresh
            self.show_notification("Refreshing chart data...", "info")
            # Note: Actual refresh logic would be implemented in the main class

    def _reset_chart_zoom(self):
        """Reset chart zoom to default view."""
        if hasattr(self, "dates") and hasattr(self, "temperatures"):
            self.set_chart_limits(self.dates, self.temperatures)
            self.canvas.draw_idle()
            self.show_notification("Chart zoom reset", "info")

    def enable_interactive_features(self):
        """Enable all interactive features."""
        self.setup_event_handlers()

        # Enable matplotlib navigation toolbar features
        self.canvas.get_tk_widget().configure(cursor="crosshair")

    def disable_interactive_features(self):
        """Disable interactive features."""
        # Disconnect event handlers
        self.canvas.mpl_disconnect("motion_notify_event")
        self.canvas.mpl_disconnect("button_press_event")
        self.canvas.mpl_disconnect("axes_leave_event")
        self.canvas.mpl_disconnect("resize_event")
        self.canvas.mpl_disconnect("key_press_event")

        # Reset cursor
        self.canvas.get_tk_widget().configure(cursor="")

        # Hide tooltip
        self.hide_tooltip()

    def _context_export_png(self):
        """Helper method for context menu PNG export."""
        self.export_chart("png")

    def _context_export_pdf(self):
        """Helper method for context menu PDF export."""
        self.export_chart("pdf")
