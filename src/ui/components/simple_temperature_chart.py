from datetime import datetime, timedelta

import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.ui.theme import DataTerminalTheme


class SimpleTemperatureChart(ctk.CTkFrame):
    """Simple temperature chart without complex mixins."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_chart()

    def setup_chart(self):
        """Setup matplotlib chart."""
        # Create figure with dark theme
        plt.style.use("dark_background")
        self.fig = Figure(figsize=(10, 6), facecolor=DataTerminalTheme.BACKGROUND)
        self.ax = self.fig.add_subplot(111)

        # Style the chart
        self.ax.set_facecolor(DataTerminalTheme.CARD_BG)
        self.ax.grid(True, alpha=0.2, color=DataTerminalTheme.CHART_GRID)

        # Set labels
        self.ax.set_xlabel("Time", color=DataTerminalTheme.TEXT)
        self.ax.set_ylabel("Temperature (°C)", color=DataTerminalTheme.TEXT)
        self.ax.set_title(
            "Temperature Forecast", color=DataTerminalTheme.PRIMARY, fontsize=16, fontweight="bold"
        )

        # Configure ticks
        self.ax.tick_params(colors=DataTerminalTheme.TEXT)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Generate sample data
        self.update_with_sample_data()

    def update_with_sample_data(self):
        """Update chart with sample data."""
        # Generate time points
        now = datetime.now()
        hours = [now + timedelta(hours=i) for i in range(24)]

        # Generate temperature data
        base_temp = 20
        temps = [base_temp + 5 * np.sin(i / 4) + np.random.normal(0, 1) for i in range(24)]

        # Clear and plot
        self.ax.clear()
        self.ax.plot(
            hours, temps, color=DataTerminalTheme.PRIMARY, linewidth=2, marker="o", markersize=4
        )

        # Fill area under curve
        self.ax.fill_between(hours, temps, alpha=0.2, color=DataTerminalTheme.PRIMARY)

        # Format x-axis
        self.ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M"))
        self.fig.autofmt_xdate()

        # Redraw
        self.canvas.draw()

    def update_with_forecast(self, forecast_data):
        """Update chart with real forecast data."""
        # Implementation for real data
