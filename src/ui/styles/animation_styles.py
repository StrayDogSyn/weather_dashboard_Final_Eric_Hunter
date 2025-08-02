"""Animation definitions and configurations for the weather dashboard."""

import math


class AnimationStyles:
    """Centralized animation configurations."""

    # Animation Durations (in milliseconds)
    DURATIONS = {"fast": 150, "normal": 300, "slow": 500, "very_slow": 1000}

    # Easing Functions
    EASING = {
        "linear": lambda t: t,
        "ease_in": lambda t: t * t,
        "ease_out": lambda t: 1 - (1 - t) * (1 - t),
        "ease_in_out": lambda t: 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t),
        "bounce": lambda t: 1 - abs(math.cos(t * math.pi * 2.5)) * (1 - t),
        "elastic": lambda t: (
            math.sin(13 * math.pi / 2 * t) * math.pow(2, 10 * (t - 1)) if t != 0 and t != 1 else t
        ),
    }

    # Fade Animations
    FADE_IN = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "from_alpha": 0.0,
        "to_alpha": 1.0,
    }

    FADE_OUT = {
        "duration": DURATIONS["normal"],
        "easing": "ease_in",
        "from_alpha": 1.0,
        "to_alpha": 0.0,
    }

    # Slide Animations
    SLIDE_IN_LEFT = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "from_x": -100,
        "to_x": 0,
    }

    SLIDE_IN_RIGHT = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "from_x": 100,
        "to_x": 0,
    }

    SLIDE_IN_UP = {"duration": DURATIONS["normal"], "easing": "ease_out", "from_y": 50, "to_y": 0}

    SLIDE_IN_DOWN = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "from_y": -50,
        "to_y": 0,
    }

    # Scale Animations
    SCALE_IN = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "from_scale": 0.8,
        "to_scale": 1.0,
    }

    SCALE_OUT = {
        "duration": DURATIONS["normal"],
        "easing": "ease_in",
        "from_scale": 1.0,
        "to_scale": 0.8,
    }

    BOUNCE_IN = {
        "duration": DURATIONS["slow"],
        "easing": "bounce",
        "from_scale": 0.3,
        "to_scale": 1.0,
    }

    # Pulse Animation
    PULSE = {
        "duration": DURATIONS["very_slow"],
        "easing": "ease_in_out",
        "from_scale": 1.0,
        "to_scale": 1.05,
        "repeat": True,
        "reverse": True,
    }

    # Ripple Effect
    RIPPLE = {
        "duration": DURATIONS["slow"],
        "easing": "ease_out",
        "max_radius": 100,
        "opacity_start": 0.3,
        "opacity_end": 0.0,
    }

    # Shimmer Effect
    SHIMMER = {
        "duration": DURATIONS["very_slow"],
        "easing": "linear",
        "gradient_width": 100,
        "repeat": True,
    }

    # Loading Animations
    LOADING_SPINNER = {
        "duration": DURATIONS["very_slow"],
        "easing": "linear",
        "rotation_degrees": 360,
        "repeat": True,
    }

    LOADING_DOTS = {
        "duration": DURATIONS["slow"],
        "easing": "ease_in_out",
        "dot_count": 3,
        "delay_between_dots": 100,
        "repeat": True,
    }

    # Weather-specific Animations
    WEATHER_CARD_ENTER = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "fade_in": True,
        "slide_up": 30,
        "scale_from": 0.95,
    }

    FORECAST_CARD_STAGGER = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "stagger_delay": 100,
        "fade_in": True,
        "slide_up": 20,
    }

    TEMPERATURE_UPDATE = {
        "duration": DURATIONS["fast"],
        "easing": "ease_in_out",
        "scale_peak": 1.1,
        "color_transition": True,
    }

    # Micro-interactions
    BUTTON_HOVER = {
        "duration": DURATIONS["fast"],
        "easing": "ease_out",
        "scale_to": 1.02,
        "shadow_increase": 2,
    }

    BUTTON_PRESS = {"duration": 100, "easing": "ease_in", "scale_to": 0.98}

    CARD_HOVER = {
        "duration": DURATIONS["fast"],
        "easing": "ease_out",
        "lift_distance": 5,
        "shadow_blur": 15,
    }

    # Search Animations
    SEARCH_FOCUS = {
        "duration": DURATIONS["fast"],
        "easing": "ease_out",
        "border_glow": True,
        "scale_to": 1.02,
    }

    SEARCH_SUGGESTIONS = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "fade_in": True,
        "slide_down": 10,
    }

    # Tab Animations
    TAB_SWITCH = {
        "duration": DURATIONS["normal"],
        "easing": "ease_in_out",
        "fade_out_duration": DURATIONS["fast"],
        "fade_in_delay": DURATIONS["fast"],
        "slide_distance": 20,
    }

    # Error/Success Animations
    ERROR_SHAKE = {
        "duration": DURATIONS["slow"],
        "easing": "ease_in_out",
        "shake_distance": 10,
        "shake_count": 3,
    }

    SUCCESS_CHECKMARK = {
        "duration": DURATIONS["slow"],
        "easing": "ease_out",
        "draw_duration": DURATIONS["normal"],
        "scale_in": True,
    }

    # Progress Animations
    PROGRESS_BAR = {"duration": DURATIONS["normal"], "easing": "ease_out", "smooth_fill": True}

    # Notification Animations
    NOTIFICATION_SLIDE_IN = {
        "duration": DURATIONS["normal"],
        "easing": "ease_out",
        "from_x": 300,
        "to_x": 0,
        "fade_in": True,
    }

    NOTIFICATION_SLIDE_OUT = {
        "duration": DURATIONS["normal"],
        "easing": "ease_in",
        "from_x": 0,
        "to_x": 300,
        "fade_out": True,
    }

    # Stagger Configurations
    STAGGER_DELAYS = {"fast": 50, "normal": 100, "slow": 200}

    # Animation Presets
    PRESETS = {
        "gentle_entrance": {
            "fade_in": FADE_IN,
            "slide_up": SLIDE_IN_UP,
            "scale_in": {**SCALE_IN, "from_scale": 0.95},
        },
        "dramatic_entrance": {
            "fade_in": FADE_IN,
            "bounce_in": BOUNCE_IN,
            "slide_up": {**SLIDE_IN_UP, "from_y": 100},
        },
        "smooth_transition": {
            "fade_out": {**FADE_OUT, "duration": DURATIONS["fast"]},
            "fade_in": {**FADE_IN, "duration": DURATIONS["fast"]},
        },
        "weather_update": {
            "temperature_change": TEMPERATURE_UPDATE,
            "card_refresh": WEATHER_CARD_ENTER,
        },
    }

    @classmethod
    def get_staggered_delay(cls, index, delay_type="normal"):
        """Get staggered delay for animations.

        Args:
            index: Item index
            delay_type: Type of delay (fast, normal, slow)

        Returns:
            Delay in milliseconds
        """
        base_delay = cls.STAGGER_DELAYS.get(delay_type, cls.STAGGER_DELAYS["normal"])
        return index * base_delay

    @classmethod
    def get_easing_function(cls, easing_name):
        """Get easing function by name.

        Args:
            easing_name: Name of easing function

        Returns:
            Easing function
        """
        return cls.EASING.get(easing_name, cls.EASING["ease_out"])

    @classmethod
    def create_custom_animation(cls, duration=None, easing=None, **kwargs):
        """Create custom animation configuration.

        Args:
            duration: Animation duration
            easing: Easing function name
            **kwargs: Additional animation properties

        Returns:
            Animation configuration dictionary
        """
        config = {"duration": duration or cls.DURATIONS["normal"], "easing": easing or "ease_out"}
        config.update(kwargs)
        return config

    @classmethod
    def get_responsive_duration(cls, base_duration, performance_mode=False):
        """Get responsive animation duration based on performance.

        Args:
            base_duration: Base duration in milliseconds
            performance_mode: Whether to reduce duration for performance

        Returns:
            Adjusted duration
        """
        if performance_mode:
            return max(base_duration // 2, 100)  # Minimum 100ms
        return base_duration

    @classmethod
    def should_animate(cls, performance_mode=False, reduced_motion=False):
        """Check if animations should be enabled.

        Args:
            performance_mode: Whether performance mode is enabled
            reduced_motion: Whether reduced motion is preferred

        Returns:
            Boolean indicating if animations should run
        """
        if reduced_motion:
            return False
        if performance_mode:
            return False  # Could be made configurable
        return True
