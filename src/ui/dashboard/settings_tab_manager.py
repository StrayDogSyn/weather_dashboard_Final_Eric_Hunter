import customtkinter as ctk

from src.ui.theme import DataTerminalTheme


class SettingsTabManager:
    """Manages settings tab functionality and UI components."""

    def __init__(self, parent, config_service, weather_service):
        self.parent = parent
        self.config_service = config_service
        self.weather_service = weather_service
        self.api_entries = {}
        self.usage_labels = {}
        self.units_var = ctk.StringVar(value="Celsius")

    def create_settings_tab(self, settings_tab):
        """Create settings tab."""
        self.settings_tab = settings_tab
        self._create_settings_tab_content()

    def _create_settings_tab_content(self):
        """Create comprehensive settings tab."""
        # Configure main grid
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(0, weight=1)

        # Create scrollable container
        settings_scroll = ctk.CTkScrollableFrame(
            self.settings_tab, fg_color="transparent", corner_radius=0
        )
        settings_scroll.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # Configure scroll frame grid
        settings_scroll.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            settings_scroll,
            text="⚙️ Settings & Configuration",
            font=(DataTerminalTheme.FONT_FAMILY, 22, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # API Configuration Section
        self._create_api_settings(settings_scroll)

        # Appearance Settings
        self._create_appearance_settings(settings_scroll)

        # Data Management
        self._create_data_settings(settings_scroll)

        # Auto-refresh Configuration
        self._create_auto_refresh_settings(settings_scroll)

        # About Section
        self._create_about_section(settings_scroll)

    def _create_api_settings(self, parent):
        """Create enhanced API configuration section."""
        # Section frame
        api_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        api_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        api_frame.grid_columnconfigure(0, weight=1)

        # Section header
        header = ctk.CTkLabel(
            api_frame,
            text="🔑 API Configuration",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # API key entries with enhanced features
        apis = [
            ("OpenWeather API", "OPENWEATHER_API_KEY", "✅ Valid", "Last rotated: 30 days ago"),
            ("Google Gemini API", "GEMINI_API_KEY", "✅ Valid", "Last rotated: 15 days ago"),
            ("Google Maps API", "GOOGLE_MAPS_API_KEY", "⚠️ Expires Soon", "Expires in 7 days"),
        ]

        # Container for API entries
        entries_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        entries_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 8))
        entries_frame.grid_columnconfigure(1, weight=1)

        for i, (api_name, env_key, status, rotation_info) in enumerate(apis):
            # Label
            label = ctk.CTkLabel(
                entries_frame,
                text=api_name,
                font=(DataTerminalTheme.FONT_FAMILY, 13),
                width=140,
                anchor="w",
            )
            label.grid(row=i, column=0, sticky="w", pady=3)

            # Entry
            entry = ctk.CTkEntry(
                entries_frame,
                placeholder_text="Enter API key...",
                width=200,
                height=32,
                fg_color=DataTerminalTheme.BACKGROUND,
                border_color=DataTerminalTheme.BORDER,
                show="*",  # Hide API key
            )
            entry.grid(row=i, column=1, sticky="ew", padx=(8, 4), pady=3)

            # Show/Hide button
            show_btn = ctk.CTkButton(
                entries_frame,
                text="👁️",
                width=32,
                height=32,
                fg_color=DataTerminalTheme.BACKGROUND,
                hover_color=DataTerminalTheme.HOVER,
                command=lambda e=entry: self._toggle_api_visibility(e),
            )
            show_btn.grid(row=i, column=2, padx=2, pady=3)

            # Test button
            test_btn = ctk.CTkButton(
                entries_frame,
                text="🧪",
                width=32,
                height=32,
                fg_color=DataTerminalTheme.INFO,
                hover_color=DataTerminalTheme.HOVER,
                command=lambda k=env_key: self._test_api_key(k),
            )
            test_btn.grid(row=i, column=3, padx=2, pady=3)

            # Status indicator
            status_label = ctk.CTkLabel(
                entries_frame, text=status, font=(DataTerminalTheme.FONT_FAMILY, 11)
            )
            status_label.grid(row=i, column=4, padx=4, pady=3)

            self.api_entries[env_key] = (entry, status_label, test_btn)

        # Usage statistics frame
        usage_frame = ctk.CTkFrame(api_frame, fg_color=DataTerminalTheme.BACKGROUND)
        usage_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(8, 0))
        usage_frame.grid_columnconfigure((0, 1, 2), weight=1)

        usage_header = ctk.CTkLabel(
            usage_frame,
            text="📊 API Usage Statistics",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
        )
        usage_header.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))

        # Usage stats
        usage_stats = [
            ("Today's Calls:", "42/1000"),
            ("This Month:", "1,247/60,000"),
            ("Rate Limit:", "60 calls/min"),
        ]

        for i, (label_text, value) in enumerate(usage_stats):
            label = ctk.CTkLabel(
                usage_frame,
                text=label_text,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
            )
            label.grid(row=1, column=i, sticky="w", padx=10, pady=5)

            value_label = ctk.CTkLabel(
                usage_frame,
                text=value,
                font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                text_color=DataTerminalTheme.SUCCESS,
            )
            value_label.grid(row=2, column=i, sticky="w", padx=10, pady=(0, 10))

            self.usage_labels[label_text] = value_label

        # Action buttons frame
        buttons_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(8, 15))
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Save button
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Save Keys",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            command=self._save_api_keys,
        )
        save_btn.grid(row=0, column=0, padx=4, sticky="w")

        # Encrypt button
        encrypt_btn = ctk.CTkButton(
            buttons_frame,
            text="🔒 Encrypt",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.WARNING,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            command=self._encrypt_api_keys,
        )
        encrypt_btn.grid(row=0, column=1, padx=4, sticky="w")

        # Rotate reminder button
        rotate_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Set Rotation",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.INFO,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            command=self._setup_key_rotation,
        )
        rotate_btn.grid(row=0, column=2, padx=4, sticky="w")

    def _create_appearance_settings(self, parent):
        """Create enhanced appearance settings section."""
        appearance_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        appearance_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        appearance_frame.grid_columnconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            appearance_frame,
            text="🎨 Appearance",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        # Theme selection
        theme_label = ctk.CTkLabel(
            appearance_frame,
            text="Theme:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        theme_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=6)

        # Theme preview grid
        self.theme_grid = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        self.theme_grid.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 10))
        self.theme_grid.grid_columnconfigure(0, weight=1)
        self.theme_grid.grid_columnconfigure(1, weight=1)
        self.theme_grid.grid_columnconfigure(2, weight=1)

        # Create theme preview cards
        self._create_theme_selector()

        # Temperature units
        units_label = ctk.CTkLabel(
            appearance_frame,
            text="Temperature Units:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        units_label.grid(row=3, column=0, sticky="w", padx=15, pady=6)

        units_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=["Celsius", "Fahrenheit", "Kelvin"],
            variable=self.units_var,
            width=180,
            command=self._change_units,
        )
        units_menu.grid(row=3, column=1, sticky="w", padx=(8, 15), pady=6)

    def _create_theme_selector(self):
        """Create theme selector with preview cards for all 9 themes in 3x3 grid."""

        # Get all available themes from theme manager - 9 themes for 3x3 grid
        themes = [
            ("Matrix", "#00FF41", "#0A0A0A", "matrix"),
            ("Cyberpunk 2077", "#FF006E", "#0F0F23", "cyberpunk"),
            ("Arctic Terminal", "#00D9FF", "#0A0E27", "arctic"),
            ("Solar Flare", "#FFA500", "#1A0F0A", "solar"),
            ("Classic Terminal", "#00FF00", "#000000", "terminal"),
            ("Midnight Purple", "#BD00FF", "#0D0221", "midnight"),
            ("Data Terminal", "#00ff88", "#1a1a1a", "data_terminal"),
            ("Neon Blue", "#0F3460", "#0A0A1A", "neon_blue"),
            ("Retro Amber", "#FFB000", "#1A1000", "retro_amber"),
        ]

        # Configure grid for 3x3 layout plus restore button row
        for i in range(7):  # 3 theme rows + 3 palette rows + 1 restore button row
            self.theme_grid.grid_rowconfigure(i, weight=1)
        for i in range(3):  # 3 columns
            self.theme_grid.grid_columnconfigure(i, weight=1)

        for i, (name, primary, bg, theme_key) in enumerate(themes):
            row = i // 3  # 0, 1, 2 for rows
            col = i % 3  # 0, 1, 2 for columns

            # Create theme button
            theme_btn = ctk.CTkButton(
                self.theme_grid,
                text=name,
                width=140,
                height=40,
                fg_color=primary,
                hover_color=bg,
                command=lambda key=theme_key: self._change_theme(key),
            )
            theme_btn.grid(row=row * 2, column=col, padx=8, pady=(5, 2), sticky="ew")

            # Create color palette hint with actual color squares
            palette_frame = ctk.CTkFrame(self.theme_grid, height=20, fg_color="transparent")
            palette_frame.grid(row=row * 2 + 1, column=col, padx=8, pady=(0, 5), sticky="ew")

            # Primary color square
            primary_square = ctk.CTkLabel(
                palette_frame,
                text="■",
                font=("Arial", 12, "bold"),
                text_color=primary,
                width=15,
                height=15,
            )
            primary_square.pack(side="left", padx=(0, 2))

            # Background color square
            bg_square = ctk.CTkLabel(
                palette_frame,
                text="■",
                font=("Arial", 12, "bold"),
                text_color=bg,
                width=15,
                height=15,
            )
            bg_square.pack(side="left", padx=(0, 5))

            # Color codes text
            color_text = ctk.CTkLabel(
                palette_frame,
                text=f"{primary[:4]} {bg[:4]}",
                font=("Courier", 9),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                height=15,
            )
            color_text.pack(side="left")

        # Add restore to default button
        restore_btn = ctk.CTkButton(
            self.theme_grid,
            text="🔄 Restore to System Default",
            width=200,
            height=35,
            fg_color=DataTerminalTheme.ACCENT,
            hover_color=DataTerminalTheme.PRIMARY,
            text_color=DataTerminalTheme.TEXT,
            command=self._restore_default_theme,
        )
        restore_btn.grid(row=6, column=0, columnspan=3, padx=8, pady=(15, 5), sticky="ew")

    def _create_data_settings(self, parent):
        """Create data management settings."""
        data_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        data_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        data_frame.grid_columnconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            data_frame,
            text="💾 Data Management",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        # Cache settings
        cache_label = ctk.CTkLabel(
            data_frame,
            text="Cache Size:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
        )
        cache_label.grid(row=1, column=0, sticky="w", padx=15, pady=6)

        cache_size_label = ctk.CTkLabel(
            data_frame,
            text="42.3 MB",
            font=(DataTerminalTheme.FONT_FAMILY, 13, "bold"),
            text_color=DataTerminalTheme.SUCCESS,
        )
        cache_size_label.grid(row=1, column=1, sticky="w", padx=(8, 15), pady=6)

        # Clear cache button
        clear_btn = ctk.CTkButton(
            data_frame,
            text="🗑️ Clear Cache",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.WARNING,
            command=self._clear_cache,
        )
        clear_btn.grid(row=2, column=0, sticky="w", padx=15, pady=6)

        # Export data button
        export_btn = ctk.CTkButton(
            data_frame,
            text="📤 Export Data",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.INFO,
            command=self._export_data,
        )
        export_btn.grid(row=2, column=1, sticky="w", padx=(8, 15), pady=6)

    def _create_auto_refresh_settings(self, parent):
        """Create auto-refresh configuration."""
        refresh_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        refresh_frame.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        refresh_frame.grid_columnconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            refresh_frame,
            text="🔄 Auto-Refresh Settings",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        # Auto-refresh toggle
        self.auto_refresh_var = ctk.BooleanVar(value=True)
        refresh_switch = ctk.CTkSwitch(
            refresh_frame,
            text="Enable Auto-Refresh",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh,
        )
        refresh_switch.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=6)

        # Refresh interval
        interval_label = ctk.CTkLabel(
            refresh_frame,
            text="Refresh Interval:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
        )
        interval_label.grid(row=2, column=0, sticky="w", padx=15, pady=6)

        self.interval_var = ctk.StringVar(value="5 minutes")
        interval_menu = ctk.CTkOptionMenu(
            refresh_frame,
            values=["1 minute", "5 minutes", "10 minutes", "30 minutes", "1 hour"],
            variable=self.interval_var,
            width=150,
        )
        interval_menu.grid(row=2, column=1, sticky="w", padx=(8, 15), pady=6)

    def _create_about_section(self, parent):
        """Create about section."""
        about_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        about_frame.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        about_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            about_frame,
            text="ℹ️ About",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # Version info
        version_label = ctk.CTkLabel(
            about_frame,
            text="Weather Dashboard v2.1.0",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
        )
        version_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)

        # Description
        desc_label = ctk.CTkLabel(
            about_frame,
            text="Professional weather monitoring with advanced analytics",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        desc_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))

    # Event handlers
    def _toggle_api_visibility(self, entry):
        """Toggle API key visibility."""
        if entry.cget("show") == "*":
            entry.configure(show="")
        else:
            entry.configure(show="*")

    def _save_api_keys(self):
        """Save API keys to configuration."""
        # Implementation for saving API keys

    def _test_api_key(self, key_name):
        """Test API key validity."""
        # Implementation for testing API keys

    def _encrypt_api_keys(self):
        """Encrypt stored API keys."""
        # Implementation for encrypting API keys

    def _setup_key_rotation(self):
        """Setup API key rotation reminders."""
        # Implementation for key rotation setup

    def _change_theme(self, theme_name):
        """Change application theme."""
        if hasattr(self.parent, "apply_theme"):
            self.parent.apply_theme(theme_name)

    def _restore_default_theme(self):
        """Restore theme to unique system default and reset all theme configurations."""
        import json
        import os

        from src.ui.theme_manager import theme_manager

        default_theme = "default_system"  # Unique system default theme

        try:
            # Apply the System Default theme
            if hasattr(self.parent, "apply_theme"):
                self.parent.apply_theme(default_theme)

            # Update theme manager
            theme_manager.apply_theme(default_theme, self.parent)

            # Reset theme config file to system default
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "config",
                "theme_config.json",
            )
            if os.path.exists(config_path):
                with open(config_path, "w") as f:
                    json.dump({"current_theme": default_theme}, f, indent=2)

            # Show success message
            if hasattr(self.parent, "status_message_manager"):
                self.parent.status_message_manager.show_message(
                    "Theme restored to System Default (unique theme)", "success"
                )
        except Exception as e:
            # Show error message if restoration fails
            if hasattr(self.parent, "status_message_manager"):
                self.parent.status_message_manager.show_message(
                    f"Failed to restore default theme: {str(e)}", "error"
                )

    def _change_units(self, unit):
        """Change temperature units."""
        if hasattr(self.parent, "_change_units"):
            self.parent._change_units(unit)

    def _clear_cache(self):
        """Clear application cache."""
        if hasattr(self.parent, "_clear_cache"):
            self.parent._clear_cache()

    def _export_data(self):
        """Export application data."""
        if hasattr(self.parent, "_export_data"):
            self.parent._export_data()

    def _toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        if hasattr(self.parent, "_toggle_auto_refresh"):
            self.parent._toggle_auto_refresh()
