"""Layout configurations and grid styles for the weather dashboard."""


class LayoutStyles:
    """Centralized layout configurations."""

    # Main Window Layout
    WINDOW = {"geometry": "1400x900", "min_size": (1200, 800), "title": "PROJECT CODEFRONT - Advanced Weather Intelligence System v3.5"}

    # Grid Configurations
    MAIN_GRID = {"sticky": "nsew", "padx": 10, "pady": 10}

    TAB_GRID = {"row": 1, "column": 0, "sticky": "nsew", "padx": 20, "pady": (0, 20)}

    HEADER_GRID = {"row": 0, "column": 0, "sticky": "ew", "padx": 20, "pady": 20}

    STATUS_BAR_GRID = {"row": 2, "column": 0, "sticky": "ew"}

    # Weather Tab Layout
    WEATHER_TAB = {
        "current_weather": {
            "row": 0,
            "column": 0,
            "columnspan": 2,
            "sticky": "ew",
            "padx": 10,
            "pady": 10,
        },
        "metrics": {
            "row": 1,
            "column": 0,
            "columnspan": 2,
            "sticky": "ew",
            "padx": 10,
            "pady": 5
        },
        "forecast": {
            "row": 2,
            "column": 0,
            "columnspan": 2,
            "sticky": "ew",
            "padx": 10,
            "pady": 5
        },
        "additional_metrics": {
            "row": 3,
            "column": 0,
            "columnspan": 2,
            "sticky": "ew",
            "padx": 10,
            "pady": 5,
        },
    }

    # Current Weather Card Layout
    CURRENT_WEATHER_LAYOUT = {
        "city_label": {
            "row": 0,
            "column": 0,
            "columnspan": 2,
            "sticky": "w",
            "padx": 20,
            "pady": (15, 5),
        },
        "temperature_label": {
            "row": 1,
            "column": 0,
            "sticky": "w",
            "padx": 20,
            "pady": 5
        },
        "unit_toggle": {"row": 1, "column": 1, "sticky": "e", "padx": 20, "pady": 5},
        "condition_label": {
            "row": 2,
            "column": 0,
            "columnspan": 2,
            "sticky": "w",
            "padx": 20,
            "pady": (0, 15),
        },
    }

    # Metrics Grid Layout
    METRICS_GRID = {"columns": 3, "rows": 2, "padx": 5, "pady": 5, "sticky": "nsew"}

    # Forecast Cards Layout
    FORECAST_CARDS = {"columns": 5, "padx": 5, "pady": 5, "sticky": "ew"}

    # Settings Tab Layout
    SETTINGS_SECTIONS = {
        "api_settings": {"row": 0, "column": 0, "sticky": "ew", "padx": 10, "pady": 5},
        "appearance_settings": {
            "row": 1,
            "column": 0,
            "sticky": "ew",
            "padx": 10,
            "pady": 5
        },
        "data_settings": {"row": 2, "column": 0, "sticky": "ew", "padx": 10, "pady": 5},
        "auto_refresh_settings": {
            "row": 3,
            "column": 0,
            "sticky": "ew",
            "padx": 10,
            "pady": 5
        },
        "about_section": {"row": 4, "column": 0, "sticky": "ew", "padx": 10, "pady": 5},
    }

    # Activities Tab Layout
    ACTIVITIES_LAYOUT = {
        "header": {"row": 0, "column": 0, "sticky": "ew", "padx": 20, "pady": (20, 10)},
        "content": {
            "row": 1, "column": 0, "sticky": "nsew", "padx": 20, "pady": (0, 20)
        },
    }

    # Comparison Tab Layout
    COMPARISON_LAYOUT = {
        "panel": {"row": 0, "column": 0, "sticky": "nsew", "padx": 20, "pady": 20}
    }

    # Maps Tab Layout
    MAPS_LAYOUT = {
        "controls": {
            "row": 0, "column": 0, "sticky": "ew", "padx": 20, "pady": (20, 10)
        },
        "map_display": {
            "row": 1, "column": 0, "sticky": "nsew", "padx": 20, "pady": (0, 20)
        },
    }

    # Padding Configurations
    PADDING = {"small": 5, "medium": 10, "large": 20, "xlarge": 30}

    # Spacing Configurations
    SPACING = {"tight": 2, "normal": 5, "loose": 10, "wide": 15}

    # Component Sizes
    SIZES = {
        "button_height": 35,
        "entry_height": 32,
        "card_corner_radius": 15,
        "button_corner_radius": 8,
        "entry_corner_radius": 6,
        "status_bar_height": 30,
    }

    # Responsive Breakpoints
    BREAKPOINTS = {"small": 800, "medium": 1200, "large": 1600}

    # Search Bar Layout
    SEARCH_BAR = {
        "entry": {"side": "left", "fill": "x", "expand": True, "padx": (0, 10)},
        "button": {"side": "right", "padx": 0},
    }

    # Form Layouts
    FORM_LAYOUT = {
        "label_width": 120,
        "entry_width": 200,
        "button_width": 100,
        "row_height": 40,
        "section_spacing": 20,
    }

    # Card Layouts
    CARD_LAYOUTS = {
        "weather_card": {"width": 300, "height": 200, "padding": 15},
        "forecast_card": {"width": 120, "height": 160, "padding": 10},
        "metric_card": {"width": 140, "height": 100, "padding": 10},
        "activity_card": {"width": 250, "height": 120, "padding": 15},
    }

    # Header Layout
    HEADER_LAYOUT = {
        "title": {"side": "left", "padx": 0},
        "search": {"side": "right", "padx": 0}
    }

    # Status Bar Layout
    STATUS_BAR_LAYOUT = {
        "status_label": {"side": "left", "padx": 10, "pady": 5},
        "connection_indicator": {"side": "left", "padx": (0, 10)},
        "time_label": {"side": "right", "padx": 10, "pady": 5},
    }

    @classmethod
    def get_responsive_columns(cls, window_width):
        """Get number of columns based on window width.

        Args:
            window_width: Current window width

        Returns:
            Number of columns for responsive layout
        """
        if window_width < cls.BREAKPOINTS["small"]:
            return 1
        elif window_width < cls.BREAKPOINTS["medium"]:
            return 2
        elif window_width < cls.BREAKPOINTS["large"]:
            return 3
        else:
            return 4

    @classmethod
    def get_card_size(cls, card_type, window_width):
        """Get card size based on type and window width.

        Args:
            card_type: Type of card
            window_width: Current window width

        Returns:
            Dictionary with width and height
        """
        base_size = cls.CARD_LAYOUTS.get(card_type, cls.CARD_LAYOUTS["weather_card"])

        # Scale down for smaller screens
        if window_width < cls.BREAKPOINTS["small"]:
            scale = 0.8
        elif window_width < cls.BREAKPOINTS["medium"]:
            scale = 0.9
        else:
            scale = 1.0

        return {
            "width": int(base_size["width"] * scale),
            "height": int(base_size["height"] * scale),
            "padding": int(base_size["padding"] * scale),
        }

    @classmethod
    def configure_grid_weights(cls, widget, rows=None, columns=None):
        """Configure grid weights for responsive layout.

        Args:
            widget: Widget to configure
            rows: Number of rows (optional)
            columns: Number of columns (optional)
        """
        if rows:
            for i in range(rows):
                widget.grid_rowconfigure(i, weight=1)

        if columns:
            for i in range(columns):
                widget.grid_columnconfigure(i, weight=1)
