import customtkinter as ctk
from src.features.weather_journal import WeatherJournal
from datetime import datetime


class WeatherJournalUI(ctk.CTkFrame):
    """Weather journal UI component."""
    
    def __init__(self, parent, weather_service=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.weather_service = weather_service
        self.journal = WeatherJournal()
        self.current_weather = None
        
        self._create_ui()
        self._load_entries()
    
    def _create_ui(self):
        """Create journal interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Entry form
        self.entry_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=12)
        self.entry_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # Form title
        form_title = ctk.CTkLabel(
            self.entry_frame,
            text="📝 New Journal Entry",
            font=("JetBrains Mono", 16, "bold"),
            text_color="#00FFAB"
        )
        form_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Mood selector
        mood_frame = ctk.CTkFrame(self.entry_frame, fg_color="transparent")
        mood_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        mood_label = ctk.CTkLabel(
            mood_frame,
            text="How are you feeling?",
            font=("JetBrains Mono", 12),
            text_color="#B0B0B0"
        )
        mood_label.pack(anchor="w", pady=(0, 5))
        
        self.mood_buttons = []
        moods = [
            ("😊", "Happy"),
            ("😐", "Neutral"),
            ("😢", "Sad"),
            ("😴", "Tired"),
            ("😎", "Energetic"),
            ("😤", "Stressed")
        ]
        
        mood_btn_frame = ctk.CTkFrame(mood_frame, fg_color="transparent")
        mood_btn_frame.pack(anchor="w")
        
        self.selected_mood = ctk.StringVar(value="Neutral")
        self.selected_emoji = ctk.StringVar(value="😐")
        
        for emoji, mood in moods:
            btn = ctk.CTkButton(
                mood_btn_frame,
                text=f"{emoji} {mood}",
                width=100,
                height=35,
                fg_color="#2A2A2A",
                hover_color="#3A3A3A",
                command=lambda e=emoji, m=mood: self._select_mood(e, m)
            )
            btn.pack(side="left", padx=2)
            self.mood_buttons.append((btn, mood, emoji))
        
        # Notes entry
        notes_label = ctk.CTkLabel(
            self.entry_frame,
            text="Notes about today's weather:",
            font=("JetBrains Mono", 12),
            text_color="#B0B0B0"
        )
        notes_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        self.notes_text = ctk.CTkTextbox(
            self.entry_frame,
            height=100,
            fg_color="#2A2A2A",
            border_color="#333333",
            border_width=1
        )
        self.notes_text.pack(fill="x", padx=20, pady=(0, 15))
        
        # Save button
        self.save_btn = ctk.CTkButton(
            self.entry_frame,
            text="Save Entry",
            width=150,
            height=40,
            fg_color="#00FFAB",
            hover_color="#00FF88",
            text_color="#000000",
            font=("JetBrains Mono", 14, "bold"),
            command=self._save_entry
        )
        self.save_btn.pack(pady=(0, 20))
        
        # Entries list
        self.entries_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#1E1E1E",
            corner_radius=12,
            border_width=1,
            border_color="#333333"
        )
        self.entries_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # List title
        list_title = ctk.CTkLabel(
            self.entries_frame,
            text="📚 Recent Entries",
            font=("JetBrains Mono", 16, "bold"),
            text_color="#00FFAB"
        )
        list_title.pack(anchor="w", padx=20, pady=(15, 10))
    
    def _select_mood(self, emoji: str, mood: str):
        """Select mood and update button states."""
        self.selected_mood.set(mood)
        self.selected_emoji.set(emoji)
        
        # Update button appearances
        for btn, btn_mood, btn_emoji in self.mood_buttons:
            if btn_mood == mood:
                btn.configure(fg_color="#00FFAB", text_color="#000000")
            else:
                btn.configure(fg_color="#2A2A2A", text_color="#FFFFFF")
    
    def _save_entry(self):
        """Save journal entry."""
        notes = self.notes_text.get("1.0", "end-1c").strip()
        if not notes:
            return
        
        # Get current weather data
        location = "Unknown"
        weather = "Unknown"
        temp = 0.0
        
        if self.weather_service and hasattr(self, 'dashboard') and hasattr(self.dashboard, 'current_weather'):
            weather_data = self.dashboard.current_weather
            if weather_data:
                location = weather_data.location.name
                weather = weather_data.description
                temp = weather_data.temperature
        
        # Save entry
        self.journal.add_entry(
            location=location,
            weather_condition=weather,
            temperature=temp,
            mood_rating=self.selected_mood.get(),
            mood_emoji=self.selected_emoji.get(),
            notes=notes
        )
        
        # Clear form
        self.notes_text.delete("1.0", "end")
        
        # Reload entries
        self._load_entries()
        
        # Show success message
        if hasattr(self, 'dashboard'):
            self.dashboard._safe_update_status("Journal entry saved!")
    
    def _load_entries(self):
        """Load and display journal entries."""
        # Clear existing entries
        for widget in self.entries_frame.winfo_children():
            if widget.winfo_class() != "CTkLabel" or "Recent Entries" not in widget.cget("text"):
                widget.destroy()
        
        # Get recent entries
        entries = self.journal.get_entries(limit=10)
        
        if not entries:
            no_entries_label = ctk.CTkLabel(
                self.entries_frame,
                text="No entries yet. Create your first weather journal entry!",
                font=("JetBrains Mono", 12),
                text_color="#666666"
            )
            no_entries_label.pack(pady=20)
            return
        
        # Display entries
        for entry in entries:
            self._create_entry_widget(entry)
    
    def _create_entry_widget(self, entry):
        """Create widget for a single journal entry."""
        entry_frame = ctk.CTkFrame(
            self.entries_frame,
            fg_color="#2A2A2A",
            corner_radius=8,
            border_width=1,
            border_color="#333333"
        )
        entry_frame.pack(fill="x", padx=20, pady=5)
        
        # Header with date and mood
        header_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        # Date
        date_str = datetime.fromisoformat(entry['date_created']).strftime("%B %d, %Y at %I:%M %p")
        date_label = ctk.CTkLabel(
            header_frame,
            text=date_str,
            font=("JetBrains Mono", 11, "bold"),
            text_color="#00FFAB"
        )
        date_label.pack(side="left")
        
        # Mood
        mood_label = ctk.CTkLabel(
            header_frame,
            text=f"{entry.get('mood_emoji', '😐')} {entry['mood_rating']}/10",
            font=("JetBrains Mono", 11),
            text_color="#FFFFFF"
        )
        mood_label.pack(side="right")
        
        # Weather info
        location = entry.get('location', 'Unknown')
        weather_condition = entry.get('weather_condition', 'N/A')
        temperature = entry.get('temperature', 0)
        weather_info = f"📍 {location} • 🌤️ {weather_condition} • 🌡️ {temperature:.1f}°"
        weather_label = ctk.CTkLabel(
            entry_frame,
            text=weather_info,
            font=("JetBrains Mono", 10),
            text_color="#B0B0B0"
        )
        weather_label.pack(anchor="w", padx=15, pady=(0, 5))
        
        # Notes
        notes_text = entry.get('notes', 'No notes available')
        notes_label = ctk.CTkLabel(
            entry_frame,
            text=notes_text,
            font=("JetBrains Mono", 11),
            text_color="#FFFFFF",
            wraplength=400,
            justify="left"
        )
        notes_label.pack(anchor="w", padx=15, pady=(0, 10))
    
    def set_dashboard_reference(self, dashboard):
        """Set reference to main dashboard for weather data access."""
        self.dashboard = dashboard
    
    def update_weather_data(self, weather_data):
        """Update current weather data for journal entries."""
        self.current_weather = weather_data