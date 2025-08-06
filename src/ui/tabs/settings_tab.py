import customtkinter as ctk
import tkinter as tk
from ..components.glass_button import GlassButton
from ..components.glassmorphic_panel import GlassmorphicPanel

class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, config_service):
        super().__init__(parent, fg_color="transparent")
        self.config_service = config_service
        self.setup_ui()
        
    def setup_ui(self):
        # Scrollable container
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=("#2B2B2B", "#1A1A1A"),
            scrollbar_button_hover_color=("#3B3B3B", "#2A2A2A")
        )
        self.scroll.pack(fill="both", expand=True)
        
        # Title
        self.create_header()
        
        # Settings sections
        self.create_api_section()
        self.create_appearance_section()
        self.create_performance_section()
        self.create_data_section()
    
    def create_header(self):
        """Create settings header"""
        header_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        title = ctk.CTkLabel(
            header_frame,
            text="⚙️ Settings & Configuration",
            font=("Arial", 28, "bold"),
            text_color="#00D4FF"
        )
        title.pack(side="left")
        
        # Save indicator
        self.save_indicator = ctk.CTkLabel(
            header_frame,
            text="✓ All changes saved",
            font=("Arial", 12),
            text_color="#4ECDC4"
        )
        self.save_indicator.pack(side="right")
        self.save_indicator.pack_forget()  # Hidden by default
    
    def create_api_section(self):
        """Create API configuration section"""
        section = self.create_section("🔑 API Configuration")
        
        apis = [
            ("OpenWeather API", "OPENWEATHER_API_KEY", "Weather data"),
            ("Google Gemini API", "GEMINI_API_KEY", "AI features"),
            ("Google Maps API", "GOOGLE_MAPS_API_KEY", "Location services"),
            ("GitHub Token", "GITHUB_TOKEN", "Team collaboration")
        ]
        
        for api_name, key, description in apis:
            self.create_api_input(section, api_name, key, description)
    
    def create_section(self, title: str) -> ctk.CTkFrame:
        """Create glassmorphic section"""
        section = GlassmorphicPanel(self.scroll)
        section.pack(fill="x", padx=30, pady=10)
        
        # Section title
        title_label = ctk.CTkLabel(
            section,
            text=title,
            font=("Arial", 18, "bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 15))
        
        return section
    
    def create_api_input(self, parent, name, key, description):
        """Create styled API input field"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=8)
        
        # Left side - API info
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=name,
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        )
        name_label.pack(anchor="w")
        
        desc_label = ctk.CTkLabel(
            info_frame,
            text=description,
            font=("Arial", 11),
            text_color="#999999"
        )
        desc_label.pack(anchor="w")
        
        # Right side - Input and validation
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(side="right")
        
        # API key input
        api_input = ctk.CTkEntry(
            input_frame,
            width=300,
            height=35,
            placeholder_text="Enter API key...",
            fg_color=("#2B2B2B", "#1A1A1A"),
            border_color=("#3B3B3B", "#2A2A2A"),
            text_color="#FFFFFF",
            show="•"  # Hide API key
        )
        api_input.pack(side="left", padx=(0, 10))
        
        # Validation indicator
        status_label = ctk.CTkLabel(
            input_frame,
            text="✓",
            font=("Arial", 16),
            text_color="#4ECDC4",
            width=30
        )
        status_label.pack(side="left")
        
        # Toggle visibility button
        toggle_btn = ctk.CTkButton(
            input_frame,
            text="👁",
            width=35,
            height=35,
            fg_color=("#2B2B2B", "#1A1A1A"),
            hover_color=("#3B3B3B", "#2A2A2A"),
            command=lambda: self.toggle_visibility(api_input)
        )
        toggle_btn.pack(side="left", padx=(0, 5))
        
        # Test button
        test_btn = ctk.CTkButton(
            input_frame,
            text="Test",
            width=60,
            height=35,
            fg_color=("#00D4FF", "#0099CC"),
            hover_color=("#0099CC", "#007799"),
            command=lambda: self.test_api(key, status_label)
        )
        test_btn.pack(side="left")
    
    def create_appearance_section(self):
        """Create appearance settings with theme previews"""
        section = self.create_section("🎨 Appearance")
        
        # Theme selector with preview cards
        theme_frame = ctk.CTkFrame(section, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        themes = [
            ("Matrix", "#00FF00", "#000000", "High contrast green"),
            ("Cyberpunk 2077", "#FF006E", "#0A0A0A", "Neon pink accents"),
            ("Arctic Terminal", "#00D4FF", "#0D1117", "Cool blue tones"),
            ("Solar Flare", "#FFA500", "#1A0F00", "Warm orange glow"),
            ("Mystic Purple", "#9B59B6", "#1A0F1F", "Deep purple theme"),
            ("Midnight Blue", "#1E90FF", "#0A0A1F", "Classic blue")
        ]
        
        # Theme grid
        theme_grid = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_grid.pack(fill="x")
        
        for i, (name, accent, bg, desc) in enumerate(themes):
            col = i % 3
            row = i // 3
            
            theme_card = self.create_theme_card(
                theme_grid, name, accent, bg, desc
            )
            theme_card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        
        # Glass effect intensity
        self.create_slider_setting(
            section,
            "Glass Effect Intensity",
            "Adjust transparency and blur",
            0.1, 0.5, 0.3
        )
        
        # Animation speed
        self.create_slider_setting(
            section,
            "Animation Speed",
            "UI animation duration",
            0.1, 1.0, 0.3
        )
    
    def create_performance_section(self):
        """Create performance settings section"""
        section = self.create_section("⚡ Performance")
        
        # Performance options
        options = [
            ("Enable caching", "cache_enabled"),
            ("Auto-refresh weather", "auto_refresh"),
            ("Background updates", "background_updates"),
            ("Hardware acceleration", "hardware_accel")
        ]
        
        for option_text, option_key in options:
            self.create_toggle_option(section, option_text, option_key)
    
    def create_data_section(self):
        """Create data management section"""
        section = self.create_section("💾 Data Management")
        
        # Data management buttons
        button_frame = ctk.CTkFrame(section, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=15)
        
        export_btn = ctk.CTkButton(
            button_frame,
            text="📤 Export Data",
            fg_color=("#4ECDC4", "#3ABAB0"),
            hover_color=("#3ABAB0", "#2A9A90"),
            command=self.export_data
        )
        export_btn.pack(side="left", padx=(0, 10))
        
        import_btn = ctk.CTkButton(
            button_frame,
            text="📥 Import Data",
            fg_color=("#FFB74D", "#FF9800"),
            hover_color=("#FF9800", "#F57C00"),
            command=self.import_data
        )
        import_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear Cache",
            fg_color=("#F44336", "#D32F2F"),
            hover_color=("#D32F2F", "#B71C1C"),
            command=self.clear_cache
        )
        clear_btn.pack(side="left")
    
    def create_toggle_option(self, parent, text, key):
        """Create a toggle option"""
        option_frame = ctk.CTkFrame(parent, fg_color="transparent")
        option_frame.pack(fill="x", padx=20, pady=8)
        
        option_label = ctk.CTkLabel(
            option_frame,
            text=text,
            font=("Arial", 14),
            text_color="#FFFFFF"
        )
        option_label.pack(side="left")
        
        toggle = ctk.CTkSwitch(
            option_frame,
            text="",
            fg_color=("#2B2B2B", "#1A1A1A"),
            progress_color="#00D4FF",
            button_color="#FFFFFF",
            button_hover_color="#CCCCCC"
        )
        toggle.pack(side="right")
    
    def toggle_visibility(self, entry):
        """Toggle API key visibility"""
        if entry.cget("show") == "•":
            entry.configure(show="")
        else:
            entry.configure(show="•")
    
    def test_api(self, key, status_label):
        """Test API connection"""
        # Placeholder for API testing logic
        status_label.configure(text="⏳", text_color="#FFB74D")
        # Simulate API test
        self.after(2000, lambda: status_label.configure(text="✓", text_color="#4ECDC4"))
    
    def export_data(self):
        """Export application data"""
        pass
    
    def import_data(self):
        """Import application data"""
        pass
    
    def clear_cache(self):
        """Clear application cache"""
        pass
    
    def create_theme_card(self, parent, name, accent_color, bg_color, description):
        """Create a theme preview card"""
        card = ctk.CTkFrame(
            parent,
            fg_color=("#2B2B2B", "#1A1A1A"),
            corner_radius=12,
            border_width=2,
            border_color=("#3B3B3B", "#2A2A2A")
        )
        
        # Theme preview
        preview_frame = ctk.CTkFrame(
            card,
            fg_color=bg_color,
            corner_radius=8,
            height=60
        )
        preview_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        # Accent color indicator
        accent_dot = ctk.CTkFrame(
            preview_frame,
            fg_color=accent_color,
            corner_radius=15,
            width=30,
            height=30
        )
        accent_dot.pack(side="left", padx=10, pady=15)
        
        # Preview text
        preview_text = ctk.CTkLabel(
            preview_frame,
            text="Aa",
            font=("Arial", 16, "bold"),
            text_color=accent_color
        )
        preview_text.pack(side="left", padx=(0, 10), pady=15)
        
        # Theme info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=name,
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        )
        name_label.pack(anchor="w")
        
        desc_label = ctk.CTkLabel(
            info_frame,
            text=description,
            font=("Arial", 10),
            text_color="#999999"
        )
        desc_label.pack(anchor="w")
        
        # Click handler
        def on_click(event=None):
            self.apply_theme(name, accent_color, bg_color)
        
        card.bind("<Button-1>", on_click)
        preview_frame.bind("<Button-1>", on_click)
        card.bind("<Enter>", lambda e: card.configure(border_color=("#00D4FF", "#0099CC")))
        card.bind("<Leave>", lambda e: card.configure(border_color=("#3B3B3B", "#2A2A2A")))
        
        return card
    
    def create_slider_setting(self, parent, title, description, min_val, max_val, default_val):
        """Create a slider setting with label"""
        setting_frame = ctk.CTkFrame(parent, fg_color="transparent")
        setting_frame.pack(fill="x", padx=20, pady=15)
        
        # Left side - info
        info_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        title_label = ctk.CTkLabel(
            info_frame,
            text=title,
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(anchor="w")
        
        desc_label = ctk.CTkLabel(
            info_frame,
            text=description,
            font=("Arial", 11),
            text_color="#AAAAAA"
        )
        desc_label.pack(anchor="w")
        
        # Right side - slider and value
        control_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        control_frame.pack(side="right")
        
        # Value label
        value_label = ctk.CTkLabel(
            control_frame,
            text=f"{default_val:.1f}",
            font=("Arial", 12),
            text_color="#00D4FF",
            width=40
        )
        value_label.pack(side="right", padx=(10, 0))
        
        # Slider
        slider = ctk.CTkSlider(
            control_frame,
            from_=min_val,
            to=max_val,
            number_of_steps=int((max_val - min_val) * 10),
            width=200,
            fg_color=("#3B3B3B", "#2A2A2A"),
            progress_color="#00D4FF",
            button_color="#FFFFFF",
            button_hover_color="#CCCCCC",
            command=lambda val: value_label.configure(text=f"{val:.1f}")
        )
        slider.set(default_val)
        slider.pack(side="right")
    
    def apply_theme(self, name, accent_color, bg_color):
        """Apply selected theme"""
        # Placeholder for theme application logic
        print(f"Applying theme: {name} with accent {accent_color} and background {bg_color}")