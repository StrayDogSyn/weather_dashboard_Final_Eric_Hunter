"""Advanced ML-powered City Comparison Panel with AI insights and recommendations."""

import json
import logging
import threading
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional

# Matplotlib for embedding charts
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk

from ...services.weather import EnhancedWeatherService
from ...services.github_team_service import GitHubTeamService

# Services
from ...services.weather.ml_weather_service import (
    MLWeatherService,
    RecommendationResult,
    SimilarityResult,
    WeatherProfile,
)
from ..theme_manager import ThemeManager
from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class PreferenceDialog(ctk.CTkToplevel):
    """Dialog for collecting user weather preferences."""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.preferences = {}
        self.theme_manager = ThemeManager()

        self._setup_ui()
        self._center_window()

        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.focus()

    def _setup_ui(self):
        """Setup the preference dialog UI."""
        self.title("🧠 Weather Preferences")
        self.geometry("500x600")
        self.resizable(False, False)

        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame, text="🌤️ Tell us your ideal weather!", font=("JetBrains Mono", 18, "bold")
        )
        title_label.pack(pady=(20, 30))

        # Preference controls
        self._create_preference_controls(main_frame)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20))

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, width=100)
        cancel_btn.pack(side="left", padx=(0, 10))

        recommend_btn = ctk.CTkButton(
            button_frame,
            text="🎯 Get Recommendations",
            command=self._get_recommendations,
            width=200,
        )
        recommend_btn.pack(side="right")

    def _create_preference_controls(self, parent):
        """Create preference input controls."""
        # Temperature preference
        temp_frame = ctk.CTkFrame(parent, fg_color="transparent")
        temp_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            temp_frame, text="🌡️ Ideal Temperature (°C):", font=("JetBrains Mono", 12, "bold")
        ).pack(anchor="w")
        self.temp_slider = ctk.CTkSlider(temp_frame, from_=-10, to=40, number_of_steps=50)
        self.temp_slider.set(20)
        self.temp_slider.pack(fill="x", pady=(5, 0))

        self.temp_value = ctk.CTkLabel(temp_frame, text="20°C")
        self.temp_value.pack(anchor="w")
        self.temp_slider.configure(command=lambda v: self.temp_value.configure(text=f"{v:.1f}°C"))

        # Humidity preference
        humidity_frame = ctk.CTkFrame(parent, fg_color="transparent")
        humidity_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            humidity_frame, text="💧 Ideal Humidity (%):", font=("JetBrains Mono", 12, "bold")
        ).pack(anchor="w")
        self.humidity_slider = ctk.CTkSlider(humidity_frame, from_=20, to=90, number_of_steps=70)
        self.humidity_slider.set(50)
        self.humidity_slider.pack(fill="x", pady=(5, 0))

        self.humidity_value = ctk.CTkLabel(humidity_frame, text="50%")
        self.humidity_value.pack(anchor="w")
        self.humidity_slider.configure(
            command=lambda v: self.humidity_value.configure(text=f"{v:.1f}%")
        )

        # Wind speed preference
        wind_frame = ctk.CTkFrame(parent, fg_color="transparent")
        wind_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            wind_frame, text="💨 Ideal Wind Speed (m/s):", font=("JetBrains Mono", 12, "bold")
        ).pack(anchor="w")
        self.wind_slider = ctk.CTkSlider(wind_frame, from_=0, to=15, number_of_steps=30)
        self.wind_slider.set(5)
        self.wind_slider.pack(fill="x", pady=(5, 0))

        self.wind_value = ctk.CTkLabel(wind_frame, text="5.0 m/s")
        self.wind_value.pack(anchor="w")
        self.wind_slider.configure(command=lambda v: self.wind_value.configure(text=f"{v:.1f} m/s"))

        # Pressure preference
        pressure_frame = ctk.CTkFrame(parent, fg_color="transparent")
        pressure_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            pressure_frame, text="🌀 Ideal Pressure (hPa):", font=("JetBrains Mono", 12, "bold")
        ).pack(anchor="w")
        self.pressure_slider = ctk.CTkSlider(pressure_frame, from_=980, to=1040, number_of_steps=60)
        self.pressure_slider.set(1013)
        self.pressure_slider.pack(fill="x", pady=(5, 0))

        self.pressure_value = ctk.CTkLabel(pressure_frame, text="1013 hPa")
        self.pressure_value.pack(anchor="w")
        self.pressure_slider.configure(
            command=lambda v: self.pressure_value.configure(text=f"{v:.0f} hPa")
        )

        # UV Index preference
        uv_frame = ctk.CTkFrame(parent, fg_color="transparent")
        uv_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(uv_frame, text="☀️ Max UV Index:", font=("JetBrains Mono", 12, "bold")).pack(
            anchor="w"
        )
        self.uv_slider = ctk.CTkSlider(uv_frame, from_=1, to=12, number_of_steps=11)
        self.uv_slider.set(6)
        self.uv_slider.pack(fill="x", pady=(5, 0))

        self.uv_value = ctk.CTkLabel(uv_frame, text="6")
        self.uv_value.pack(anchor="w")
        self.uv_slider.configure(command=lambda v: self.uv_value.configure(text=f"{v:.0f}"))

        # Weather type preference
        type_frame = ctk.CTkFrame(parent, fg_color="transparent")
        type_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            type_frame, text="🌈 Preferred Weather Type:", font=("JetBrains Mono", 12, "bold")
        ).pack(anchor="w")
        self.weather_type = ctk.CTkOptionMenu(
            type_frame,
            values=[
                "☁️ Cool & Cloudy",
                "🔥 Warm & Dry",
                "🌧️ Mild & Humid",
                "❄️ Cool & Crisp",
                "🌴 Tropical",
            ],
        )
        self.weather_type.pack(fill="x", pady=(5, 0))

    def _get_recommendations(self):
        """Collect preferences and get recommendations."""
        self.preferences = {
            "temperature": self.temp_slider.get(),
            "humidity": self.humidity_slider.get(),
            "wind_speed": self.wind_slider.get(),
            "pressure": self.pressure_slider.get(),
            "uv_index": self.uv_slider.get(),
            "weather_type": self.weather_type.get(),
        }

        self.callback(self.preferences)
        self.destroy()

    def _center_window(self):
        """Center the dialog on the parent window."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"500x600+{x}+{y}")

class MLComparisonPanel(ctk.CTkFrame):
    """Advanced ML-powered city comparison panel."""

    def __init__(
        self,
        parent,
        weather_service: EnhancedWeatherService = None,
        github_service: GitHubTeamService = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.weather_service = weather_service
        self.github_service = github_service
        self.ml_service = MLWeatherService()
        self.theme_manager = ThemeManager()
        self.error_handler = ErrorHandler(self)

        # Data storage
        self.weather_profiles: List[WeatherProfile] = []
        self.team_cities_data: Dict[str, List[Dict]] = {}
        self.current_similarity_result: Optional[SimilarityResult] = None
        self.current_recommendation: Optional[RecommendationResult] = None

        # UI components
        self.chart_canvas = None
        self.current_chart_type = "similarity"

        self._setup_ui()
        self._apply_theme()

        # Register for theme updates
        self.theme_manager.add_observer(self.update_theme)

        # Load team data
        if self.github_service:
            threading.Thread(target=self._load_team_data, daemon=True).start()

        logger.info("ML Comparison Panel initialized")

    def _setup_ui(self):
        """Setup the ML comparison panel UI."""
        # Main container with scrollable frame
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        self._create_header()

        # Control panel
        self._create_control_panel()

        # Visualization area
        self._create_visualization_area()

        # Insights panel
        self._create_insights_panel()

    def _create_header(self):
        """Create the header section."""
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", pady=(0, 20))

        # Title with AI emoji
        title_label = ctk.CTkLabel(
            header_frame, text="🧠 AI-Powered Weather Analysis", font=("JetBrains Mono", 20, "bold")
        )
        title_label.pack(pady=20)

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Advanced ML insights • Similarity scoring • Smart recommendations",
            font=("JetBrains Mono", 12),
            text_color=("#666666", "#AAAAAA"),
        )
        subtitle_label.pack(pady=(0, 20))

    def _create_control_panel(self):
        """Create the control panel with city selection and analysis options."""
        control_frame = ctk.CTkFrame(self.main_container)
        control_frame.pack(fill="x", pady=(0, 20))

        # City selection section
        city_section = ctk.CTkFrame(control_frame)
        city_section.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            city_section, text="🏙️ City Selection", font=("JetBrains Mono", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # City input frame
        city_input_frame = ctk.CTkFrame(city_section, fg_color="transparent")
        city_input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.city_entry = ctk.CTkEntry(
            city_input_frame,
            placeholder_text="Enter city name...",
            font=("JetBrains Mono", 12),
            width=200,
        )
        self.city_entry.pack(side="left", padx=(0, 10))
        self.city_entry.bind("<Return>", lambda e: self._add_city())

        add_city_btn = ctk.CTkButton(
            city_input_frame, text="➕ Add City", command=self._add_city, width=100
        )
        add_city_btn.pack(side="left", padx=(0, 10))

        clear_btn = ctk.CTkButton(
            city_input_frame, text="🗑️ Clear All", command=self._clear_cities, width=100
        )
        clear_btn.pack(side="left")

        # Selected cities display
        self.cities_display = ctk.CTkTextbox(city_section, height=60, font=("JetBrains Mono", 11))
        self.cities_display.pack(fill="x", padx=10, pady=(0, 10))

        # Analysis buttons
        analysis_frame = ctk.CTkFrame(control_frame)
        analysis_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            analysis_frame, text="🔬 Analysis Tools", font=("JetBrains Mono", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        button_grid = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        button_grid.pack(fill="x", padx=10, pady=(0, 10))

        # Row 1
        row1 = ctk.CTkFrame(button_grid, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 5))

        ctk.CTkButton(
            row1,
            text="🔥 Similarity Heatmap",
            command=lambda: self._show_visualization("similarity"),
            width=150,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            row1,
            text="🎯 Weather Clusters",
            command=lambda: self._show_visualization("clusters"),
            width=150,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            row1,
            text="📊 Radar Chart",
            command=lambda: self._show_visualization("radar"),
            width=150,
        ).pack(side="left")

        # Row 2
        row2 = ctk.CTkFrame(button_grid, fg_color="transparent")
        row2.pack(fill="x")

        ctk.CTkButton(
            row2, text="🧠 Get Recommendations", command=self._show_preference_dialog, width=180
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            row2, text="📈 Detailed Analysis", command=self._show_detailed_analysis, width=150
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            row2, text="💾 Export Results", command=self._export_analysis, width=120
        ).pack(side="left")

    def _create_visualization_area(self):
        """Create the visualization area for charts."""
        viz_frame = ctk.CTkFrame(self.main_container)
        viz_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Visualization header
        viz_header = ctk.CTkFrame(viz_frame)
        viz_header.pack(fill="x", padx=20, pady=(20, 10))

        self.viz_title = ctk.CTkLabel(
            viz_header, text="📊 Visualization Area", font=("JetBrains Mono", 16, "bold")
        )
        self.viz_title.pack(side="left")

        # Chart type selector
        self.chart_selector = ctk.CTkOptionMenu(
            viz_header,
            values=["Similarity Heatmap", "Weather Clusters", "Radar Chart"],
            command=self._on_chart_type_changed,
        )
        self.chart_selector.pack(side="right")

        # Chart container
        self.chart_frame = ctk.CTkFrame(viz_frame)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Initial placeholder
        self.placeholder_label = ctk.CTkLabel(
            self.chart_frame,
            text="Add cities and select an analysis type to view visualizations",
            font=("JetBrains Mono", 14),
            text_color=("#888888", "#AAAAAA"),
        )
        self.placeholder_label.pack(expand=True)

    def _create_insights_panel(self):
        """Create the insights panel for AI-generated insights."""
        insights_frame = ctk.CTkFrame(self.main_container)
        insights_frame.pack(fill="x", pady=(0, 20))

        # Insights header
        ctk.CTkLabel(
            insights_frame,
            text="🧠 AI Insights & Recommendations",
            font=("JetBrains Mono", 16, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Insights display
        self.insights_display = ctk.CTkTextbox(
            insights_frame, height=200, font=("JetBrains Mono", 11)
        )
        self.insights_display.pack(fill="x", padx=20, pady=(0, 20))

        # Initial insights text
        self.insights_display.insert(
            "1.0",
            "🤖 AI insights will appear here after analysis...\n\n"
            + "• Add cities to compare\n"
            + "• Run similarity analysis\n"
            + "• Get personalized recommendations\n"
            + "• Explore weather clusters",
        )
        self.insights_display.configure(state="disabled")

    def _apply_theme(self):
        """Apply the current theme."""
        # Theme will be applied automatically by CustomTkinter
        # Refresh current visualization with new theme
        if (
            hasattr(self, "current_chart_type")
            and self.current_chart_type
            and len(self.weather_profiles) >= 2
        ):
            self._show_visualization(self.current_chart_type)

    def _load_team_data(self):
        """Load team data in background."""
        try:
            if self.github_service:
                team_data = self.github_service.get_team_cities()
                self.team_cities_data = team_data
                logger.info(f"Loaded team data for {len(team_data)} cities")
        except Exception as e:
            logger.error(f"Error loading team data: {e}")

    def _add_city(self):
        """Add a city to the analysis."""
        city_name = self.city_entry.get().strip()

        # Validate input using error handler
        if not city_name:
            self.error_handler.show_validation_error(self.city_entry, "Please enter a city name")
            return

        if len(city_name) < 2:
            self.error_handler.show_validation_error(
                self.city_entry, "City name must be at least 2 characters long"
            )
            return

        if len(city_name) > 50:
            self.error_handler.show_validation_error(
                self.city_entry, "City name is too long (max 50 characters)"
            )
            return

        # Check if city already added
        if any(profile.city_name.lower() == city_name.lower() for profile in self.weather_profiles):
            self.error_handler.show_toast(f"{city_name} is already in the analysis", "warning")
            return

        # Clear any previous validation errors
        self.error_handler.clear_validation_error(self.city_entry)

        # Fetch weather data
        try:
            weather_data = self.weather_service.get_current_weather(city_name)
            if not weather_data:
                self.error_handler.show_api_error(
                    f"Could not fetch weather data for {city_name}",
                    "Please check the city name and try again",
                )
                return

            # Check if it's a team member city
            is_team_member = city_name in self.team_cities_data
            member_name = None
            if is_team_member and self.team_cities_data[city_name]:
                first_member = self.team_cities_data[city_name][0]
                if isinstance(first_member, dict):
                    member_name = first_member.get("name", "Unknown")
                else:
                    member_name = "Unknown"

            # Create weather profile
            profile = WeatherProfile(
                city_name=city_name,
                temperature=weather_data.get("temperature", 0),
                humidity=weather_data.get("humidity", 0),
                wind_speed=weather_data.get("wind_speed", 0),
                pressure=weather_data.get("pressure", 1013),
                uv_index=weather_data.get("uv_index", 0),
                visibility=weather_data.get("visibility", 10),
                feels_like=weather_data.get("feels_like", weather_data.get("temperature", 0)),
                is_team_member=is_team_member,
                member_name=member_name,
            )

            self.weather_profiles.append(profile)
            self._update_cities_display()
            self.city_entry.delete(0, "end")

            logger.info(f"Added city: {city_name}")

        except Exception as e:
            # Handle weather service errors using the error handler
            self.error_handler.handle_error(
                e,
                context=f"adding city {city_name} to ML analysis",
                show_user_message=True,
                fallback_action=lambda: None,
            )

    def _clear_cities(self):
        """Clear all cities from analysis."""
        self.weather_profiles.clear()
        self._update_cities_display()
        self._clear_visualization()
        self._clear_insights()
        logger.info("Cleared all cities")

    def _update_cities_display(self):
        """Update the cities display."""
        self.cities_display.configure(state="normal")
        self.cities_display.delete("1.0", "end")

        if not self.weather_profiles:
            self.cities_display.insert("1.0", "No cities added yet...")
        else:
            text = f"Cities in analysis ({len(self.weather_profiles)}):\n\n"
            for i, profile in enumerate(self.weather_profiles, 1):
                team_indicator = " 👥" if profile.is_team_member else ""
                text += f"{i}. {profile.city_name}{team_indicator} - {profile.temperature:.1f}°C, {profile.humidity:.0f}% humidity\n"
            self.cities_display.insert("1.0", text)

        self.cities_display.configure(state="disabled")

    def _show_visualization(self, chart_type: str):
        """Show the selected visualization."""
        if len(self.weather_profiles) < 2:
            messagebox.showwarning(
                "Insufficient Data", "Please add at least 2 cities for analysis."
            )
            return

        self.current_chart_type = chart_type
        self._clear_visualization()

        try:
            # Get current theme
            current_theme = self.theme_manager.get_current_theme() if self.theme_manager else None

            # Hide placeholder
            if hasattr(self, "placeholder_label"):
                self.placeholder_label.pack_forget()

            # Create the appropriate chart
            if chart_type == "similarity":
                fig = self.ml_service.create_similarity_heatmap(
                    self.weather_profiles, figsize=(8, 6), theme=current_theme
                )
                self.viz_title.configure(text="🔥 Weather Similarity Heatmap")
            elif chart_type == "clusters":
                fig = self.ml_service.create_cluster_visualization(
                    self.weather_profiles, figsize=(10, 6), theme=current_theme
                )
                self.viz_title.configure(text="🎯 Weather Clusters Analysis")
            elif chart_type == "radar":
                city_names = [profile.city_name for profile in self.weather_profiles]
                fig = self.ml_service.create_radar_chart(
                    self.weather_profiles, city_names, figsize=(8, 8), theme=current_theme
                )
                self.viz_title.configure(text="📊 Weather Profile Radar Chart")
            else:
                return

            # Configure figure for embedding
            fig.patch.set_facecolor("none")  # Transparent background
            fig.tight_layout(pad=1.0)

            # Create canvas frame for better control
            if not hasattr(self, "canvas_frame") or self.canvas_frame is None or not self.canvas_frame.winfo_exists():
                self.canvas_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
                self.canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

            # Embed the chart with proper CustomTkinter integration
            self.chart_canvas = FigureCanvasTkAgg(fig, self.canvas_frame)
            self.chart_canvas.draw()

            # Configure the tkinter widget for CustomTkinter
            canvas_widget = self.chart_canvas.get_tk_widget()
            canvas_widget.configure(highlightthickness=0, relief="flat")
            canvas_widget.pack(fill="both", expand=True)

            # Store figure reference for theme updates
            self.current_figure = fig

            # Generate insights based on chart type
            self._generate_chart_insights(chart_type)

        except Exception as e:
            logger.error(f"Error creating {chart_type} visualization: {e}")
            messagebox.showerror("Visualization Error", f"Error creating {chart_type}: {str(e)}")
            self._show_placeholder()

    def _on_chart_type_changed(self, selection: str):
        """Handle chart type selection change."""
        chart_map = {
            "Similarity Heatmap": "similarity",
            "Weather Clusters": "clusters",
            "Radar Chart": "radar",
        }

        chart_type = chart_map.get(selection)
        if chart_type:
            self._show_visualization(chart_type)

    def _clear_visualization(self):
        """Clear the current visualization."""
        # Properly cleanup matplotlib canvas
        if hasattr(self, "chart_canvas") and self.chart_canvas:
            try:
                self.chart_canvas.get_tk_widget().destroy()
                if hasattr(self.chart_canvas, "figure"):
                    plt.close(self.chart_canvas.figure)
                self.chart_canvas = None
            except Exception as e:
                logger.warning(f"Error cleaning up chart canvas: {e}")

        # Clear canvas frame
        if hasattr(self, "canvas_frame") and self.canvas_frame is not None and self.canvas_frame.winfo_exists():
            self.canvas_frame.destroy()
            self.canvas_frame = None

        # Clear current figure reference
        if hasattr(self, "current_figure"):
            try:
                plt.close(self.current_figure)
            except Exception:
                pass
            self.current_figure = None

        # Reset title
        self.viz_title.configure(text="📊 Select a visualization type")

        # Show placeholder
        self._show_placeholder()

        # Clear insights
        self._clear_insights()

    def _show_placeholder(self):
        """Show placeholder text when no visualization is selected."""
        if not hasattr(self, "placeholder_label") or self.placeholder_label is None or not self.placeholder_label.winfo_exists():
            self.placeholder_label = ctk.CTkLabel(
                self.chart_frame,
                text="Select a visualization type from the dropdown above\nto see ML-powered weather analysis",
                font=ctk.CTkFont(size=14),
                text_color=("gray60", "gray40"),
            )
        self.placeholder_label.pack(expand=True)

    def _generate_chart_insights(self, chart_type: str):
        """Generate AI insights based on the current chart."""
        try:
            insights = []

            if chart_type == "similarity":
                # Calculate similarity insights
                similarity_matrix = self.ml_service.calculate_similarity_matrix(
                    self.weather_profiles
                )
                if similarity_matrix.size > 0:
                    # Find most similar pair
                    max_similarity = 0
                    most_similar_pair = None

                    for i in range(len(self.weather_profiles)):
                        for j in range(i + 1, len(self.weather_profiles)):
                            similarity = similarity_matrix[i][j]
                            if similarity > max_similarity:
                                max_similarity = similarity
                                most_similar_pair = (
                                    self.weather_profiles[i].city_name,
                                    self.weather_profiles[j].city_name,
                                )

                    if most_similar_pair:
                        insights.append(
                            f"🎯 Most Similar Cities: {most_similar_pair[0]} and {most_similar_pair[1]} ({max_similarity:.1%} similarity)"
                        )

                        # Get detailed similarity analysis
                        similarity_result = self.ml_service.get_city_similarity(
                            most_similar_pair[0], most_similar_pair[1], self.weather_profiles
                        )
                        insights.append(
                            f"📊 Key Factors: {', '.join(similarity_result.dominant_factors)}"
                        )
                        insights.append(f"💡 {similarity_result.recommendation}")

            elif chart_type == "clusters":
                # Generate cluster insights
                clusters = self.ml_service.perform_weather_clustering(self.weather_profiles)
                insights.append(f"🎯 Identified {len(clusters)} distinct weather patterns:")

                for cluster in clusters:
                    insights.append(f"\n{cluster.emoji} {cluster.cluster_name}:")
                    insights.append(f"   Cities: {', '.join(cluster.cities)}")
                    insights.append(f"   {cluster.description}")
                    if cluster.characteristics:
                        avg_temp = cluster.characteristics.get("avg_temperature", 0)
                        insights.append(f"   Average temperature: {avg_temp:.1f}°C")

            elif chart_type == "radar":
                # Generate radar chart insights
                insights.append("📊 Weather Profile Analysis:")

                # Find extremes
                [p.temperature for p in self.weather_profiles]
                [p.humidity for p in self.weather_profiles]

                hottest_city = max(self.weather_profiles, key=lambda p: p.temperature)
                coldest_city = min(self.weather_profiles, key=lambda p: p.temperature)
                most_humid = max(self.weather_profiles, key=lambda p: p.humidity)
                least_humid = min(self.weather_profiles, key=lambda p: p.humidity)

                insights.append(
                    f"🔥 Hottest: {hottest_city.city_name} ({hottest_city.temperature:.1f}°C)"
                )
                insights.append(
                    f"❄️ Coolest: {coldest_city.city_name} ({coldest_city.temperature:.1f}°C)"
                )
                insights.append(
                    f"💧 Most Humid: {most_humid.city_name} ({most_humid.humidity:.0f}%)"
                )
                insights.append(
                    f"🏜️ Least Humid: {least_humid.city_name} ({least_humid.humidity:.0f}%)"
                )

            # Update insights display
            self._update_insights(insights)

        except Exception as e:
            logger.error(f"Error generating insights: {e}")

    def _show_preference_dialog(self):
        """Show the weather preference dialog."""
        if len(self.weather_profiles) < 1:
            messagebox.showwarning(
                "No Data", "Please add at least 1 city before getting recommendations."
            )
            return

        PreferenceDialog(self, self._handle_preferences)

    def _handle_preferences(self, preferences: Dict[str, Any]):
        """Handle user preferences and generate recommendations."""
        try:
            recommendation = self.ml_service.recommend_city_by_preferences(
                preferences, self.weather_profiles
            )

            if recommendation:
                self.current_recommendation = recommendation

                insights = [
                    f"🎯 Recommended City: {recommendation.recommended_city}",
                    f"🎪 Match Score: {recommendation.match_percentage:.1f}%",
                    f"🏷️ Weather Type: {recommendation.cluster_info.emoji} {recommendation.cluster_info.cluster_name}",
                    "",
                    "📋 Why this city matches your preferences:",
                ]

                for reason in recommendation.reasons:
                    insights.append(f"   ✓ {reason}")

                insights.extend(
                    [
                        "",
                        f"📊 Cluster Description: {recommendation.cluster_info.description}",
                        "",
                        "🔍 Comparison with your preferences:",
                    ]
                )

                comp_data = recommendation.comparison_data
                if "differences" in comp_data:
                    diffs = comp_data["differences"]
                    insights.append(
                        f"   Temperature difference: {diffs.get('temperature', 0):.1f}°C"
                    )
                    insights.append(f"   Humidity difference: {diffs.get('humidity', 0):.1f}%")
                    insights.append(
                        f"   Wind speed difference: {diffs.get('wind_speed', 0):.1f} m/s"
                    )

                self._update_insights(insights)

            else:
                self.error_handler.show_api_error(
                    "Could not generate recommendations",
                    "Please try again with different preferences",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="generating ML recommendations",
                show_user_message=True,
                fallback_action=lambda: None,
            )

    def _show_detailed_analysis(self):
        """Show detailed analysis in a new window."""
        if len(self.weather_profiles) < 2:
            messagebox.showwarning(
                "Insufficient Data", "Please add at least 2 cities for detailed analysis."
            )
            return

        # Create detailed analysis window
        analysis_window = ctk.CTkToplevel(self)
        analysis_window.title("🔬 Detailed Weather Analysis")
        analysis_window.geometry("800x600")

        # Analysis content
        analysis_text = ctk.CTkTextbox(analysis_window, font=("JetBrains Mono", 11))
        analysis_text.pack(fill="both", expand=True, padx=20, pady=20)

        # Generate detailed analysis
        try:
            analysis_content = self._generate_detailed_analysis()
            analysis_text.insert("1.0", analysis_content)
            analysis_text.configure(state="disabled")
        except Exception as e:
            analysis_text.insert("1.0", f"Error generating analysis: {str(e)}")

    def _generate_detailed_analysis(self) -> str:
        """Generate detailed analysis text."""
        analysis = []
        analysis.append("🔬 DETAILED WEATHER ANALYSIS REPORT")
        analysis.append("=" * 50)
        analysis.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        analysis.append(f"Cities analyzed: {len(self.weather_profiles)}")
        analysis.append("")

        # City overview
        analysis.append("📊 CITY OVERVIEW")
        analysis.append("-" * 20)
        for i, profile in enumerate(self.weather_profiles, 1):
            team_status = " (Team Member)" if profile.is_team_member else ""
            analysis.append(f"{i}. {profile.city_name}{team_status}")
            analysis.append(f"   Temperature: {profile.temperature:.1f}°C")
            analysis.append(f"   Humidity: {profile.humidity:.0f}%")
            analysis.append(f"   Wind Speed: {profile.wind_speed:.1f} m/s")
            analysis.append(f"   Pressure: {profile.pressure:.0f} hPa")
            analysis.append("")

        # Similarity analysis
        if len(self.weather_profiles) >= 2:
            analysis.append("🔥 SIMILARITY ANALYSIS")
            analysis.append("-" * 25)

            similarity_matrix = self.ml_service.calculate_similarity_matrix(self.weather_profiles)
            if similarity_matrix.size > 0:
                for i in range(len(self.weather_profiles)):
                    for j in range(i + 1, len(self.weather_profiles)):
                        city1 = self.weather_profiles[i].city_name
                        city2 = self.weather_profiles[j].city_name
                        similarity = similarity_matrix[i][j]
                        analysis.append(f"{city1} ↔ {city2}: {similarity:.1%} similarity")
                analysis.append("")

        # Clustering analysis
        clusters = self.ml_service.perform_weather_clustering(self.weather_profiles)
        if clusters:
            analysis.append("🎯 WEATHER CLUSTERS")
            analysis.append("-" * 20)

            for cluster in clusters:
                analysis.append(f"{cluster.emoji} {cluster.cluster_name}")
                analysis.append(f"   Description: {cluster.description}")
                analysis.append(f"   Cities: {', '.join(cluster.cities)}")
                if cluster.characteristics:
                    analysis.append(
                        f"   Avg Temperature: {cluster.characteristics.get('avg_temperature', 0):.1f}°C"
                    )
                    analysis.append(
                        f"   Avg Humidity: {cluster.characteristics.get('avg_humidity', 0):.0f}%"
                    )
                analysis.append("")

        # Statistical summary
        analysis.append("📈 STATISTICAL SUMMARY")
        analysis.append("-" * 25)

        temps = [p.temperature for p in self.weather_profiles]
        humidities = [p.humidity for p in self.weather_profiles]
        wind_speeds = [p.wind_speed for p in self.weather_profiles]

        analysis.append(f"Temperature range: {min(temps):.1f}°C to {max(temps):.1f}°C")
        analysis.append(f"Average temperature: {sum(temps)/len(temps):.1f}°C")
        analysis.append(f"Humidity range: {min(humidities):.0f}% to {max(humidities):.0f}%")
        analysis.append(f"Average humidity: {sum(humidities)/len(humidities):.0f}%")
        analysis.append(f"Wind speed range: {min(wind_speeds):.1f} to {max(wind_speeds):.1f} m/s")
        analysis.append("")

        return "\n".join(analysis)

    def _export_analysis(self):
        """Export analysis results to file."""
        if not self.weather_profiles:
            messagebox.showwarning("No Data", "No analysis data to export.")
            return

        try:
            # Ask user for file location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Analysis Results",
            )

            if not filename:
                return

            # Prepare export data
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "cities": [],
                "analysis_type": self.current_chart_type,
                "insights": self.insights_display.get("1.0", "end").strip(),
            }

            # Add city data
            for profile in self.weather_profiles:
                city_data = {
                    "name": profile.city_name,
                    "temperature": profile.temperature,
                    "humidity": profile.humidity,
                    "wind_speed": profile.wind_speed,
                    "pressure": profile.pressure,
                    "is_team_member": profile.is_team_member,
                    "member_name": profile.member_name,
                }
                export_data["cities"].append(city_data)

            # Add similarity matrix if available
            if len(self.weather_profiles) >= 2:
                similarity_matrix = self.ml_service.calculate_similarity_matrix(
                    self.weather_profiles
                )
                if similarity_matrix.size > 0:
                    export_data["similarity_matrix"] = similarity_matrix.tolist()

            # Add clustering results
            clusters = self.ml_service.perform_weather_clustering(self.weather_profiles)
            if clusters:
                export_data["clusters"] = []
                for cluster in clusters:
                    cluster_data = {
                        "id": cluster.cluster_id,
                        "name": cluster.cluster_name,
                        "emoji": cluster.emoji,
                        "description": cluster.description,
                        "cities": cluster.cities,
                        "characteristics": cluster.characteristics,
                    }
                    export_data["clusters"].append(cluster_data)

            # Add recommendation if available
            if self.current_recommendation:
                rec = self.current_recommendation
                export_data["recommendation"] = {
                    "city": rec.recommended_city,
                    "match_percentage": rec.match_percentage,
                    "reasons": rec.reasons,
                    "cluster_info": {
                        "name": rec.cluster_info.cluster_name,
                        "emoji": rec.cluster_info.emoji,
                        "description": rec.cluster_info.description,
                    },
                    "comparison_data": rec.comparison_data,
                }

            # Write to file
            if filename.endswith(".json"):
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            else:
                # Export as text
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self._generate_detailed_analysis())

            messagebox.showinfo("Export Complete", f"Analysis exported to {filename}")
            logger.info(f"Exported analysis to {filename}")

        except Exception as e:
            logger.error(f"Error exporting analysis: {e}")
            messagebox.showerror("Export Error", f"Error exporting analysis: {str(e)}")

    def _update_insights(self, insights: List[str]):
        """Update the insights display."""
        self.insights_display.configure(state="normal")
        self.insights_display.delete("1.0", "end")

        timestamp = datetime.now().strftime("%H:%M:%S")
        content = f"🕒 Analysis completed at {timestamp}\n\n" + "\n".join(insights)

        self.insights_display.insert("1.0", content)
        self.insights_display.configure(state="disabled")

    def _clear_insights(self):
        """Clear the insights display."""
        self.insights_display.configure(state="normal")
        self.insights_display.delete("1.0", "end")
        self.insights_display.insert("1.0", "🤖 AI insights will appear here after analysis...")
        self.insights_display.configure(state="disabled")

    def update_theme(self, theme_name: str = None):
        """Update the theme."""
        self._apply_theme()

        # Update current visualization with new theme
        if hasattr(self, "current_chart_type") and self.current_chart_type:
            self._refresh_visualization_theme()

    def _refresh_visualization_theme(self):
        """Refresh the current visualization with updated theme."""
        if (
            hasattr(self, "current_chart_type")
            and self.current_chart_type
            and len(self.weather_profiles) >= 2
        ):
            # Store current chart type
            chart_type = self.current_chart_type
            # Recreate visualization with new theme
            self._show_visualization(chart_type)

    def destroy(self):
        """Clean up resources."""
        # Unregister from theme updates
        self.theme_manager.remove_observer(self.update_theme)

        # Clean up error handler
        if hasattr(self, "error_handler"):
            self.error_handler.cleanup()

        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
        super().destroy()
