"""UI Components Mixin

Contains all UI creation and display methods for the activity suggester.
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Dict
from ui.theme import DataTerminalTheme
import threading


class UIComponentsMixin:
    """Mixin class containing UI component creation and management methods."""
    
    def _create_ui(self) -> None:
        """Create the main UI components."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create header and suggestions area
        self._create_header()
        self._create_suggestions_area()
    
    def _create_header(self) -> None:
        """Create header with AI status, weather info, and controls."""
        header_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # Title and status row
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            title_frame,
            text="🎯 Activity Suggestions",
            font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
            text_color=DataTerminalTheme.TEXT
        )
        title_label.pack(side="left")
        
        # AI Status
        self.ai_status_label = ctk.CTkLabel(
            title_frame,
            text=self._get_ai_status_text(),
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.ai_status_label.pack(side="right", padx=(10, 0))
        
        # Weather and controls row
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Weather display
        self.weather_label = ctk.CTkLabel(
            controls_frame,
            text="🌡️ Loading weather...",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.weather_label.pack(side="left")
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            width=100,
            height=32,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            fg_color=DataTerminalTheme.SUCCESS,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._refresh_suggestions
        )
        self.refresh_btn.pack(side="right")
        
        # Category filters
        filter_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            filter_frame,
            text="Filter by category:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT
        ).pack(side="left", padx=(0, 10))
        
        categories = ["All", "Outdoor", "Indoor", "Fitness", "Creative", "Social"]
        self.category_buttons = {}
        self.selected_category = "All"
        
        for cat in categories:
            btn = ctk.CTkButton(
                filter_frame,
                text=cat,
                width=80,
                height=28,
                font=(DataTerminalTheme.FONT_FAMILY, 11),
                fg_color=DataTerminalTheme.CARD_BG,
                hover_color=DataTerminalTheme.HOVER,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
                command=lambda c=cat: self._filter_category(c)
            )
            btn.pack(side="left", padx=3)
            self.category_buttons[cat] = btn
        
        # Set "All" as active
        self.category_buttons["All"].configure(
            fg_color=DataTerminalTheme.PRIMARY,
            border_color=DataTerminalTheme.PRIMARY
        )
    
    def _create_suggestions_area(self) -> None:
        """Create scrollable area for activity cards."""
        self.suggestions_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        self.suggestions_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.suggestions_frame,
            text="🔄 Generating AI suggestions...",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.loading_label.pack(pady=50)
    
    def _filter_category(self, category: str) -> None:
        """Filter suggestions by category."""
        # Update button states
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.configure(
                    fg_color=DataTerminalTheme.PRIMARY,
                    border_color=DataTerminalTheme.PRIMARY
                )
            else:
                btn.configure(
                    fg_color=DataTerminalTheme.CARD_BG,
                    border_color=DataTerminalTheme.BORDER
                )
        
        self.selected_category = category
        self._display_suggestions()
    
    def _display_suggestions(self) -> None:
        """Display activity suggestions in cards."""
        # Clear existing content
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'suggestions') or not self.suggestions:
            no_data_label = ctk.CTkLabel(
                self.suggestions_frame,
                text="No suggestions available. Click refresh to generate new ones.",
                font=(DataTerminalTheme.FONT_FAMILY, 14),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            no_data_label.pack(pady=50)
            return
        
        # Filter suggestions by category
        filtered_suggestions = self.suggestions
        if self.selected_category != "All":
            filtered_suggestions = [
                s for s in self.suggestions 
                if s.get('category', '').lower() == self.selected_category.lower()
            ]
        
        if not filtered_suggestions:
            no_data_label = ctk.CTkLabel(
                self.suggestions_frame,
                text=f"No {self.selected_category.lower()} activities found.",
                font=(DataTerminalTheme.FONT_FAMILY, 14),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            no_data_label.pack(pady=50)
            return
        
        # Create activity cards
        for i, activity in enumerate(filtered_suggestions):
            self._create_activity_card(activity, i)
    
    def _create_activity_card(self, activity: Dict, index: int) -> None:
        """Create an individual activity card."""
        # Card frame
        card = ctk.CTkFrame(
            self.suggestions_frame,
            fg_color=DataTerminalTheme.BG,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        card.pack(fill="x", padx=10, pady=5)
        
        # Card content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header row with title and category
        header_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 8))
        
        # Activity name
        name_label = ctk.CTkLabel(
            header_row,
            text=activity.get('name', 'Unknown Activity'),
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT
        )
        name_label.pack(side="left")
        
        # Category badge
        category = activity.get('category', 'General')
        category_colors = {
            'Outdoor': DataTerminalTheme.SUCCESS,
            'Indoor': DataTerminalTheme.PRIMARY,
            'Fitness': DataTerminalTheme.WARNING,
            'Creative': DataTerminalTheme.INFO,
            'Social': DataTerminalTheme.ACCENT
        }
        
        category_label = ctk.CTkLabel(
            header_row,
            text=category,
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color="white",
            fg_color=category_colors.get(category, DataTerminalTheme.TEXT_SECONDARY),
            corner_radius=12,
            width=60,
            height=20
        )
        category_label.pack(side="right")
        
        # Description
        desc_text = activity.get('description', 'No description available')
        desc_label = ctk.CTkLabel(
            content_frame,
            text=desc_text,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            wraplength=400,
            justify="left"
        )
        desc_label.pack(anchor="w", pady=(0, 8))
        
        # Details row
        details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        details_frame.pack(fill="x", pady=(0, 10))
        
        # Duration and difficulty
        duration = activity.get('duration', 'Unknown')
        difficulty = activity.get('difficulty', 'Unknown')
        
        details_text = f"⏱️ {duration} | 📊 {difficulty}"
        if 'weather_suitability' in activity:
            details_text += f" | 🌤️ {activity['weather_suitability'][:30]}..."
        
        details_label = ctk.CTkLabel(
            details_frame,
            text=details_text,
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        details_label.pack(side="left")
        
        # Action buttons
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        # Rating buttons
        rating_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        rating_frame.pack(side="left")
        
        ctk.CTkLabel(
            rating_frame,
            text="Rate:",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        # Star rating buttons
        for i in range(1, 6):
            star_btn = ctk.CTkButton(
                rating_frame,
                text="⭐",
                width=25,
                height=25,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                fg_color="transparent",
                hover_color=DataTerminalTheme.HOVER,
                command=lambda rating=i, act=activity: self._rate_activity(act, rating)
            )
            star_btn.pack(side="left", padx=1)
        
        # Details button
        details_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Details",
            width=80,
            height=25,
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            fg_color=DataTerminalTheme.INFO,
            hover_color=DataTerminalTheme.INFO,
            command=lambda act=activity: self._show_activity_details(act)
        )
        details_btn.pack(side="right")
    
    def _update_weather_display(self) -> None:
        """Update weather information in header."""
        if hasattr(self, 'current_weather') and self.current_weather:
            temp = self.current_weather.get('temperature', 'N/A')
            condition = self.current_weather.get('condition', 'Unknown')
            self.weather_label.configure(
                text=f"🌡️ {temp}°C | {condition}"
            )
        else:
            self.weather_label.configure(text="Weather unavailable")
    
    def _update_ai_status(self) -> None:
        """Update AI service status display."""
        if hasattr(self, 'ai_status_label'):
            self.ai_status_label.configure(text=self._get_ai_status_text())
    
    def _show_temporary_message(self, message: str) -> None:
        """Show a temporary message in the suggestions area."""
        # Clear existing content
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        # Show message
        message_label = ctk.CTkLabel(
            self.suggestions_frame,
            text=message,
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.SUCCESS
        )
        message_label.pack(pady=50)
        
        # Auto-refresh after 2 seconds
        self.after(2000, self._display_suggestions)
    
    def _show_error(self) -> None:
        """Show error message when suggestion generation fails."""
        # Clear existing content
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.suggestions_frame,
            text="❌ Failed to generate suggestions.\nPlease check your internet connection and API keys.",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.ERROR
        )
        error_label.pack(pady=50)
        
        # Re-enable refresh button
        self.refresh_btn.configure(state="normal", text="🔄 Refresh")
    
    def _refresh_suggestions(self) -> None:
        """Refresh activity suggestions."""
        # Clear existing content and show loading
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        # Create new loading label
        self.loading_label = ctk.CTkLabel(
            self.suggestions_frame,
            text="🔄 Generating AI suggestions...",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.loading_label.pack(pady=50)
        self.refresh_btn.configure(state="disabled", text="Loading...")
        
        # Run in background thread
        threading.Thread(target=self._fetch_suggestions, daemon=True).start()