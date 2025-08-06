"""Component-specific styles for the weather dashboard."""


class ComponentStyles:
    """Centralized component styles."""

    # Weather Card Styles
    WEATHER_CARD = {
        "corner_radius": 15,
        "fg_color": ("#ffffff", "#2b2b2b"),
        "border_width": 1,
        "border_color": ("#e0e0e0", "#404040"),
    }

    # Current Weather Card
    CURRENT_WEATHER_CARD = {**WEATHER_CARD, "height": 200}

    # Forecast Card
    FORECAST_CARD = {**WEATHER_CARD, "width": 120, "height": 160}

    # Metric Card
    METRIC_CARD = {**WEATHER_CARD, "width": 140, "height": 100}

    # Activity Card
    ACTIVITY_CARD = {**WEATHER_CARD, "height": 120}

    # Button Styles
    PRIMARY_BUTTON = {
        "corner_radius": 8,
        "height": 35,
        "font": ("Segoe UI", 12, "bold"),
        "fg_color": "#1f538d",
        "hover_color": "#14375e",
    }

    SECONDARY_BUTTON = {
        "corner_radius": 8,
        "height": 35,
        "font": ("Segoe UI", 12),
        "fg_color": ("#f0f0f0", "#404040"),
        "hover_color": ("#e0e0e0", "#505050"),
        "text_color": ("#333333", "#ffffff"),
    }

    ICON_BUTTON = {
        "corner_radius": 6,
        "width": 30,
        "height": 30,
        "font": ("Segoe UI", 14),
        "fg_color": "transparent",
        "hover_color": ("#f0f0f0", "#404040"),
    }

    # Entry Styles
    SEARCH_ENTRY = {
        "corner_radius": 8,
        "height": 35,
        "width": 450,
        "font": ("Segoe UI", 12),
        "placeholder_text_color": ("#999999", "#666666"),
        "border_width": 1,
        "border_color": ("#cccccc", "#555555"),
    }

    SETTINGS_ENTRY = {
        "corner_radius": 6,
        "height": 32,
        "font": ("Segoe UI", 11),
        "border_width": 1,
        "border_color": ("#cccccc", "#555555"),
    }

    # Label Styles
    TITLE_LABEL = {
        "font": ("Segoe UI", 18, "bold"),
        "text_color": ("#333333", "#ffffff")
    }

    SUBTITLE_LABEL = {
        "font": ("Segoe UI", 14, "bold"),
        "text_color": ("#555555", "#cccccc")
    }

    BODY_LABEL = {"font": ("Segoe UI", 12), "text_color": ("#666666", "#aaaaaa")}

    SMALL_LABEL = {"font": ("Segoe UI", 10), "text_color": ("#888888", "#888888")}

    # Temperature Labels
    TEMPERATURE_LARGE = {
        "font": ("Segoe UI", 36, "bold"),
        "text_color": ("#1f538d", "#4a9eff")
    }

    TEMPERATURE_MEDIUM = {
        "font": ("Segoe UI", 18, "bold"),
        "text_color": ("#1f538d", "#4a9eff")
    }

    TEMPERATURE_SMALL = {"font": ("Segoe UI", 14), "text_color": ("#1f538d", "#4a9eff")}

    # Frame Styles
    MAIN_FRAME = {"corner_radius": 0, "fg_color": ("#f8f9fa", "#1a1a1a")}

    CONTENT_FRAME = {
        "corner_radius": 10,
        "fg_color": ("#ffffff", "#2b2b2b"),
        "border_width": 1,
        "border_color": ("#e0e0e0", "#404040"),
    }

    SECTION_FRAME = {"corner_radius": 8, "fg_color": ("#f8f9fa", "#333333")}

    # Tab Styles
    TAB_VIEW = {
        "corner_radius": 10,
        "border_width": 1,
        "border_color": ("#e0e0e0", "#404040"),
        "segmented_button_fg_color": ("#f0f0f0", "#404040"),
        "segmented_button_selected_color": ("#1f538d", "#1f538d"),
        "segmented_button_selected_hover_color": ("#14375e", "#14375e"),
    }

    # Status Bar Styles
    STATUS_BAR = {"height": 30, "corner_radius": 0, "fg_color": ("#f0f0f0", "#2b2b2b")}

    STATUS_LABEL = {"font": ("Segoe UI", 11), "text_color": ("#666666", "#cccccc")}

    # Progress Bar Styles
    PROGRESS_BAR = {
        "corner_radius": 10,
        "height": 20,
        "progress_color": "#1f538d",
        "fg_color": ("#e0e0e0", "#404040"),
    }

    # Switch Styles
    SWITCH = {
        "progress_color": "#1f538d",
        "button_color": ("#ffffff", "#ffffff"),
        "button_hover_color": ("#f0f0f0", "#f0f0f0"),
    }

    # Slider Styles
    SLIDER = {
        "progress_color": "#1f538d",
        "button_color": ("#ffffff", "#ffffff"),
        "button_hover_color": ("#f0f0f0", "#f0f0f0"),
    }

    # Option Menu Styles
    OPTION_MENU = {
        "corner_radius": 6,
        "font": ("Segoe UI", 11),
        "fg_color": ("#ffffff", "#404040"),
        "button_color": ("#f0f0f0", "#505050"),
        "button_hover_color": ("#e0e0e0", "#606060"),
    }

    # Scrollable Frame Styles
    SCROLLABLE_FRAME = {
        "corner_radius": 8,
        "fg_color": ("#ffffff", "#2b2b2b"),
        "scrollbar_button_color": ("#cccccc", "#555555"),
        "scrollbar_button_hover_color": ("#aaaaaa", "#666666"),
    }

    # Text Box Styles
    TEXT_BOX = {
        "corner_radius": 8,
        "font": ("Consolas", 11),
        "fg_color": ("#ffffff", "#2b2b2b"),
        "border_width": 1,
        "border_color": ("#cccccc", "#555555"),
    }

    # Color Indicators
    COLORS = {
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#f44336",
        "info": "#2196F3",
        "primary": "#1f538d",
        "secondary": "#6c757d",
    }

    # Weather Condition Colors
    WEATHER_COLORS = {
        "sunny": "#FFD700",
        "cloudy": "#87CEEB",
        "rainy": "#4682B4",
        "snowy": "#F0F8FF",
        "stormy": "#696969",
        "foggy": "#D3D3D3",
    }

    @classmethod
    def get_weather_color(cls, condition):
        """Get color for weather condition.

        Args:
            condition: Weather condition string

        Returns:
            Color hex code
        """
        condition_lower = condition.lower()

        if any(word in condition_lower for word in ["sun", "clear", "bright"]):
            return cls.WEATHER_COLORS["sunny"]
        elif any(word in condition_lower for word in ["cloud", "overcast"]):
            return cls.WEATHER_COLORS["cloudy"]
        elif any(word in condition_lower for word in ["rain", "drizzle", "shower"]):
            return cls.WEATHER_COLORS["rainy"]
        elif any(word in condition_lower for word in ["snow", "blizzard", "flurr"]):
            return cls.WEATHER_COLORS["snowy"]
        elif any(word in condition_lower for word in ["storm", "thunder", "lightning"]):
            return cls.WEATHER_COLORS["stormy"]
        elif any(word in condition_lower for word in ["fog", "mist", "haze"]):
            return cls.WEATHER_COLORS["foggy"]
        else:
            return cls.COLORS["info"]

    @classmethod
    def get_temperature_color(cls, temp_celsius):
        """Get color based on temperature.

        Args:
            temp_celsius: Temperature in Celsius

        Returns:
            Color hex code
        """
        if temp_celsius >= 30:
            return "#FF4444"  # Hot - Red
        elif temp_celsius >= 20:
            return "#FF8800"  # Warm - Orange
        elif temp_celsius >= 10:
            return "#FFDD00"  # Mild - Yellow
        elif temp_celsius >= 0:
            return "#00AAFF"  # Cool - Blue
        else:
            return "#0066CC"  # Cold - Dark Blue
