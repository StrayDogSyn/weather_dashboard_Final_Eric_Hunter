"""Advanced Analytics Mixin for Temperature Chart Component.

This module provides comprehensive weather analytics with multiple chart types,
advanced statistical analysis, and interactive data exploration capabilities.
"""

from typing import Any, Dict

import numpy as np
from scipy import stats


class ChartAnalyticsMixin:
    """Mixin for advanced weather analytics and data analysis."""

    def __init_analytics__(self):
        """Initialize analytics components."""
        self.chart_types = {
            "line": "Line Chart",
            "area": "Area Chart",
            "bar": "Bar Chart",
            "candlestick": "Candlestick",
            "heatmap": "Heatmap",
            "scatter": "Scatter Plot",
        }

        self.metrics = {
            "temperature": "Temperature (°C)",
            "humidity": "Humidity (%)",
            "pressure": "Pressure (hPa)",
            "wind_speed": "Wind Speed (km/h)",
            "precipitation": "Precipitation (mm)",
            "feels_like": "Feels Like (°C)",
        }

        self.timeframes = {
            "24h": "24 Hours",
            "48h": "48 Hours",
            "7d": "7 Days",
            "14d": "14 Days",
            "30d": "30 Days",
            "1y": "1 Year",
        }

        self.current_chart_type = "line"
        self.current_metrics = ["temperature"]
        self.show_trend_lines = True
        self.show_statistics = True
        self.comparison_data = None

    def create_analytics_controls(self):
        """Create advanced analytics control panel."""
        # Chart type selector
        self._create_chart_type_selector()

        # Metrics selector
        self._create_metrics_selector()

        # Timeframe selector (enhanced)
        self._create_enhanced_timeframe_selector()

        # Analysis options
        self._create_analysis_options()

        # Comparison tools
        self._create_comparison_tools()

    def _create_chart_type_selector(self):
        """Create chart type selection controls."""
        import customtkinter as ctk

        self.chart_type_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Chart type dropdown
        self.chart_type_var = ctk.StringVar(value="Line Chart")
        self.chart_type_dropdown = ctk.CTkOptionMenu(
            self.chart_type_frame,
            values=list(self.chart_types.values()),
            variable=self.chart_type_var,
            command=self._on_chart_type_change,
            width=120,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2a2a2a",
            button_color="#00ff88",
            button_hover_color="#00cc6a",
            text_color="#ffffff",
        )

    def _create_metrics_selector(self):
        """Create metrics selection controls."""
        import customtkinter as ctk

        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Metrics checkboxes
        self.metric_vars = {}
        self.metric_checkboxes = {}

        for i, (key, label) in enumerate(self.metrics.items()):
            var = ctk.BooleanVar(value=(key == "temperature"))
            self.metric_vars[key] = var

            checkbox = ctk.CTkCheckBox(
                self.metrics_frame,
                text=label,
                variable=var,
                command=self._on_metrics_change,
                font=ctk.CTkFont(size=10),
                text_color="#ffffff",
                fg_color="#00ff88",
                hover_color="#00cc6a",
                checkmark_color="#000000",
            )

            row = i // 3
            col = i % 3
            checkbox.grid(row=row, column=col, padx=5, pady=2, sticky="w")
            self.metric_checkboxes[key] = checkbox

    def _create_enhanced_timeframe_selector(self):
        """Create enhanced timeframe selection with more options."""
        import customtkinter as ctk

        self.enhanced_timeframe_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Enhanced timeframe buttons
        button_config = {
            "width": 60,
            "height": 32,
            "corner_radius": 8,
            "font": ctk.CTkFont(size=10, weight="bold"),
            "border_width": 1,
            "border_color": "#00ff88",
            "hover_color": "#1a4d3a",
            "text_color": "#ffffff",
            "fg_color": "#1a1a1a",
        }

        self.enhanced_timeframe_buttons = {}

        for i, (value, label) in enumerate(self.timeframes.items()):
            button = ctk.CTkButton(
                self.enhanced_timeframe_frame,
                text=value.upper(),
                command=lambda tf=value: self._handle_enhanced_timeframe_click(tf),
                **button_config,
            )
            button.grid(row=0, column=i, padx=2)
            self.enhanced_timeframe_buttons[value] = button

    def _create_analysis_options(self):
        """Create analysis options panel."""
        import customtkinter as ctk

        self.analysis_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Trend lines toggle
        self.trend_var = ctk.BooleanVar(value=True)
        self.trend_checkbox = ctk.CTkCheckBox(
            self.analysis_frame,
            text="Show Trend Lines",
            variable=self.trend_var,
            command=self._on_analysis_option_change,
            font=ctk.CTkFont(size=10),
            text_color="#ffffff",
            fg_color="#00ff88",
        )
        self.trend_checkbox.grid(row=0, column=0, padx=5, sticky="w")

        # Statistics toggle
        self.stats_var = ctk.BooleanVar(value=True)
        self.stats_checkbox = ctk.CTkCheckBox(
            self.analysis_frame,
            text="Show Statistics",
            variable=self.stats_var,
            command=self._on_analysis_option_change,
            font=ctk.CTkFont(size=10),
            text_color="#ffffff",
            fg_color="#00ff88",
        )
        self.stats_checkbox.grid(row=0, column=1, padx=5, sticky="w")

        # Extreme weather detection
        self.extreme_var = ctk.BooleanVar(value=False)
        self.extreme_checkbox = ctk.CTkCheckBox(
            self.analysis_frame,
            text="Highlight Extremes",
            variable=self.extreme_var,
            command=self._on_analysis_option_change,
            font=ctk.CTkFont(size=10),
            text_color="#ffffff",
            fg_color="#ff6b6b",
        )
        self.extreme_checkbox.grid(row=0, column=2, padx=5, sticky="w")

    def _create_comparison_tools(self):
        """Create comparison and overlay tools."""
        import customtkinter as ctk

        self.comparison_frame = ctk.CTkFrame(self, fg_color="transparent")

        # Historical comparison button
        self.historical_btn = ctk.CTkButton(
            self.comparison_frame,
            text="📈 Historical",
            width=100,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            text_color="#00ff88",
            command=self._toggle_historical_comparison,
        )
        self.historical_btn.grid(row=0, column=0, padx=3)

        # Multi-city comparison button
        self.multicity_btn = ctk.CTkButton(
            self.comparison_frame,
            text="🌍 Cities",
            width=100,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            text_color="#00ff88",
            command=self._toggle_multicity_comparison,
        )
        self.multicity_btn.grid(row=0, column=1, padx=3)

    def create_advanced_chart(self, data: Dict[str, Any]):
        """Create advanced chart with selected type and metrics."""
        # Clear previous chart
        self.ax.clear()

        # Apply chart type
        if self.current_chart_type == "line":
            self._create_line_chart(data)
        elif self.current_chart_type == "area":
            self._create_area_chart(data)
        elif self.current_chart_type == "bar":
            self._create_bar_chart(data)
        elif self.current_chart_type == "candlestick":
            self._create_candlestick_chart(data)
        elif self.current_chart_type == "heatmap":
            self._create_heatmap_chart(data)
        elif self.current_chart_type == "scatter":
            self._create_scatter_chart(data)

        # Add analytics overlays
        self._add_analytics_overlays(data)

        # Update chart styling
        self._apply_analytics_styling()

        # Refresh display
        self.canvas.draw()

    def _create_line_chart(self, data: Dict[str, Any]):
        """Create enhanced line chart with multiple metrics."""
        colors = ["#00ff88", "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57"]

        for i, metric in enumerate(self.current_metrics):
            if metric in data and data[metric]:
                times = data.get("times", [])
                values = data[metric]

                color = colors[i % len(colors)]

                # Main line with enhanced styling
                line = self.ax.plot(
                    times,
                    values,
                    color=color,
                    linewidth=2.5,
                    alpha=0.9,
                    label=self.metrics.get(metric, metric),
                    marker="o",
                    markersize=4,
                    markerfacecolor=color,
                    markeredgecolor="white",
                    markeredgewidth=0.5,
                )[0]

                # Add glow effect
                self.ax.plot(times, values, color=color, linewidth=6, alpha=0.2)

    def _create_area_chart(self, data: Dict[str, Any]):
        """Create area chart with gradient fills."""
        colors = ["#00ff88", "#ff6b6b", "#4ecdc4", "#45b7d1"]

        for i, metric in enumerate(self.current_metrics):
            if metric in data and data[metric]:
                times = data.get("times", [])
                values = data[metric]

                color = colors[i % len(colors)]

                # Create area fill
                self.ax.fill_between(
                    times, values, alpha=0.3, color=color, label=self.metrics.get(metric, metric)
                )

                # Add border line
                self.ax.plot(times, values, color=color, linewidth=2, alpha=0.8)

    def _create_bar_chart(self, data: Dict[str, Any]):
        """Create bar chart for discrete time periods."""
        if not self.current_metrics or not data:
            return

        times = data.get("times", [])
        if not times:
            return

        # Convert times to numeric for bar positioning
        x_pos = np.arange(len(times))
        bar_width = 0.8 / len(self.current_metrics)

        colors = ["#00ff88", "#ff6b6b", "#4ecdc4", "#45b7d1"]

        for i, metric in enumerate(self.current_metrics):
            if metric in data and data[metric]:
                values = data[metric]
                offset = (i - len(self.current_metrics) / 2 + 0.5) * bar_width

                bars = self.ax.bar(
                    x_pos + offset,
                    values,
                    bar_width,
                    color=colors[i % len(colors)],
                    alpha=0.8,
                    label=self.metrics.get(metric, metric),
                    edgecolor="white",
                    linewidth=0.5,
                )

                # Add value labels on bars
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    self.ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 0.1,
                        f"{value:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        color="white",
                        alpha=0.8,
                    )

        # Set x-axis labels
        self.ax.set_xticks(x_pos)
        if len(times) <= 24:  # Show all labels for short periods
            labels = [t.strftime("%H:%M") if hasattr(t, "strftime") else str(t) for t in times]
        else:  # Show every nth label for longer periods
            step = max(1, len(times) // 12)
            labels = [
                t.strftime("%m/%d") if hasattr(t, "strftime") and i % step == 0 else ""
                for i, t in enumerate(times)
            ]
        self.ax.set_xticklabels(labels, rotation=45)

    def _add_analytics_overlays(self, data: Dict[str, Any]):
        """Add analytical overlays like trend lines and statistics."""
        if self.show_trend_lines:
            self._add_trend_lines(data)

        if self.show_statistics:
            self._add_statistics_overlay(data)

        if self.extreme_var.get():
            self._highlight_extreme_values(data)

    def _add_trend_lines(self, data: Dict[str, Any]):
        """Add trend lines to the chart."""
        colors = ["#ffff00", "#ff9500", "#00ffff", "#ff00ff"]

        for i, metric in enumerate(self.current_metrics):
            if metric in data and data[metric] and len(data[metric]) > 2:
                times = data.get("times", [])
                values = data[metric]

                # Convert times to numeric for trend calculation
                if times and hasattr(times[0], "timestamp"):
                    x_numeric = [t.timestamp() for t in times]
                else:
                    x_numeric = list(range(len(values)))

                # Calculate trend line
                try:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(
                        x_numeric, values
                    )
                    trend_line = [slope * x + intercept for x in x_numeric]

                    # Plot trend line
                    self.ax.plot(
                        times,
                        trend_line,
                        color=colors[i % len(colors)],
                        linestyle="--",
                        linewidth=1.5,
                        alpha=0.7,
                        label=f"{metric} trend (R²={r_value**2:.3f})",
                    )
                except Exception as e:
                    print(f"Error calculating trend for {metric}: {e}")

    def _add_statistics_overlay(self, data: Dict[str, Any]):
        """Add statistical information overlay."""
        stats_text = []

        for metric in self.current_metrics:
            if metric in data and data[metric]:
                values = data[metric]

                mean_val = np.mean(values)
                std_val = np.std(values)
                min_val = np.min(values)
                max_val = np.max(values)

                stats_text.append(
                    f"{self.metrics.get(metric, metric)}:\n"
                    f"  Mean: {mean_val:.1f}\n"
                    f"  Std: {std_val:.1f}\n"
                    f"  Range: {min_val:.1f} - {max_val:.1f}"
                )

        if stats_text:
            # Add statistics text box
            stats_str = "\n\n".join(stats_text)
            self.ax.text(
                0.02,
                0.98,
                stats_str,
                transform=self.ax.transAxes,
                fontsize=8,
                verticalalignment="top",
                bbox=dict(
                    boxstyle="round,pad=0.5", facecolor="#1a1a1a", alpha=0.8, edgecolor="#00ff88"
                ),
                color="white",
            )

    def _highlight_extreme_values(self, data: Dict[str, Any]):
        """Highlight extreme weather values."""
        for metric in self.current_metrics:
            if metric in data and data[metric]:
                times = data.get("times", [])
                values = data[metric]

                # Calculate thresholds for extremes
                mean_val = np.mean(values)
                std_val = np.std(values)

                upper_threshold = mean_val + 2 * std_val
                lower_threshold = mean_val - 2 * std_val

                # Highlight extreme points
                for i, (time, value) in enumerate(zip(times, values)):
                    if value > upper_threshold or value < lower_threshold:
                        color = "#ff4444" if value > upper_threshold else "#4444ff"

                        # Add extreme value marker
                        self.ax.scatter(
                            time,
                            value,
                            s=100,
                            color=color,
                            marker="*",
                            alpha=0.8,
                            edgecolors="white",
                            linewidth=1,
                            zorder=10,
                        )

                        # Add annotation
                        self.ax.annotate(
                            f"EXTREME\n{value:.1f}",
                            (time, value),
                            xytext=(10, 10),
                            textcoords="offset points",
                            fontsize=7,
                            color=color,
                            weight="bold",
                            ha="left",
                        )

    def _apply_analytics_styling(self):
        """Apply enhanced styling for analytics charts."""
        # Enhanced legend
        if self.ax.get_legend_handles_labels()[0]:  # Check if there are legend items
            legend = self.ax.legend(
                loc="upper right",
                frameon=True,
                fancybox=True,
                shadow=True,
                framealpha=0.9,
                facecolor="#1a1a1a",
                edgecolor="#00ff88",
                fontsize=9,
            )
            legend.get_frame().set_linewidth(1.5)

        # Enhanced grid
        self.ax.grid(True, alpha=0.3, color="#00ff88", linestyle="-", linewidth=0.5)

        # Enhanced axis labels
        self.ax.set_xlabel("Time", fontsize=12, color="#00ff88", weight="bold")

        if len(self.current_metrics) == 1:
            ylabel = self.metrics.get(self.current_metrics[0], "Value")
        else:
            ylabel = "Multiple Metrics"

        self.ax.set_ylabel(ylabel, fontsize=12, color="#00ff88", weight="bold")

        # Enhanced title
        chart_type_name = self.chart_types.get(self.current_chart_type, "Chart")
        timeframe_name = self.timeframes.get(self.current_timeframe, self.current_timeframe)

        title = f"{chart_type_name} - {timeframe_name}"
        if len(self.current_metrics) > 1:
            title += f" ({len(self.current_metrics)} metrics)"

        self.ax.set_title(title, fontsize=14, color="#00ff88", weight="bold", pad=20)

    # Event handlers
    def _on_chart_type_change(self, value: str):
        """Handle chart type change."""
        # Find chart type key from display value
        for key, display in self.chart_types.items():
            if display == value:
                self.current_chart_type = key
                break

        self._refresh_analytics_chart()

    def _on_metrics_change(self):
        """Handle metrics selection change."""
        self.current_metrics = [key for key, var in self.metric_vars.items() if var.get()]

        if not self.current_metrics:
            # Ensure at least one metric is selected
            self.metric_vars["temperature"].set(True)
            self.current_metrics = ["temperature"]

        self._refresh_analytics_chart()

    def _handle_enhanced_timeframe_click(self, timeframe: str):
        """Handle enhanced timeframe selection."""
        self.current_timeframe = timeframe
        self._update_enhanced_timeframe_buttons()
        self._refresh_analytics_chart()

    def _update_enhanced_timeframe_buttons(self):
        """Update enhanced timeframe button states."""
        for tf, button in self.enhanced_timeframe_buttons.items():
            if tf == self.current_timeframe:
                button.configure(fg_color="#00ff88", text_color="#000000")
            else:
                button.configure(fg_color="#1a1a1a", text_color="#ffffff")

    def _on_analysis_option_change(self):
        """Handle analysis option changes."""
        self.show_trend_lines = self.trend_var.get()
        self.show_statistics = self.stats_var.get()
        self._refresh_analytics_chart()

    def _toggle_historical_comparison(self):
        """Toggle historical data comparison."""
        # Implementation for historical comparison
        print("Historical comparison toggled")

    def _toggle_multicity_comparison(self):
        """Toggle multi-city comparison."""
        # Implementation for multi-city comparison
        print("Multi-city comparison toggled")

    def _refresh_analytics_chart(self):
        """Refresh the analytics chart with current settings."""
        if hasattr(self, "forecast_data") and self.forecast_data:
            # Process current data with new settings
            processed_data = self.process_forecast_data(self.forecast_data)
            self.create_advanced_chart(processed_data)
        else:
            # Generate sample data for current settings
            sample_data = self.generate_realistic_data(self.current_timeframe)
            self.create_advanced_chart(sample_data)
