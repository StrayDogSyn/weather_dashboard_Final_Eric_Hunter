import json
import sqlite3
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from ..theme import DataTerminalTheme


class WeatherJournal(ctk.CTkFrame):
    """Weather journal component with mood tracking."""

    def __init__(self, parent, weather_service, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.weather_service = weather_service
        self.current_mood = None
        self.current_weather_data = None

        # Setup database
        self._setup_database()

        # Create UI
        self._create_journal_ui()

        # Load existing entries
        self._load_entries()

    def _setup_database(self):
        """Initialize SQLite database for journal entries."""
        db_path = Path("data") / "weather_journal.db"
        db_path.parent.mkdir(exist_ok=True)

        self.conn = sqlite3.connect(str(db_path))
        self.cursor = self.conn.cursor()

        # Create table with schema compatible with journal_service
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_created TEXT NOT NULL,
                weather_data TEXT,
                mood_rating INTEGER CHECK(mood_rating >= 1 AND mood_rating <= 10),
                entry_content TEXT NOT NULL,
                tags TEXT,
                location TEXT,
                category TEXT,
                photos TEXT,
                template_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.conn.commit()

    def _create_journal_ui(self):
        """Create the journal interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create new entry section
        self._create_entry_section()

        # Create entries list section
        self._create_entries_list()

    def _create_entry_section(self):
        """Create new journal entry section."""
        entry_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        entry_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        # Title
        ctk.CTkLabel(
            entry_frame,
            text="📝 New Journal Entry",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # Weather info frame
        weather_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        weather_frame.pack(fill="x", padx=20, pady=5)

        self.weather_info_label = ctk.CTkLabel(
            weather_frame,
            text="🌤️ Weather will be auto-filled when you save",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.weather_info_label.pack(anchor="w")

        # Mood selection
        mood_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        mood_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            mood_frame,
            text="How are you feeling?",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 5))

        # Mood buttons
        moods = [
            ("😊", "Happy"),
            ("😐", "Neutral"),
            ("😢", "Sad"),
            ("⚡", "Energetic"),
            ("😴", "Tired"),
        ]

        mood_button_frame = ctk.CTkFrame(mood_frame, fg_color="transparent")
        mood_button_frame.pack(anchor="w")

        self.mood_buttons = {}
        for emoji, mood in moods:
            btn = ctk.CTkButton(
                mood_button_frame,
                text=f"{emoji} {mood}",
                width=100,
                height=35,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                fg_color=DataTerminalTheme.CARD_BG,
                hover_color=DataTerminalTheme.HOVER,
                border_width=2,
                border_color=DataTerminalTheme.BORDER,
                command=lambda m=mood: self._select_mood(m),
            )
            btn.pack(side="left", padx=5)
            self.mood_buttons[mood] = btn

        # Notes entry
        notes_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        notes_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            notes_frame,
            text="Your thoughts:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 5))

        self.notes_text = ctk.CTkTextbox(
            notes_frame,
            height=100,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            fg_color=DataTerminalTheme.BACKGROUND,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        self.notes_text.pack(fill="x")

        # Save button
        self.save_button = ctk.CTkButton(
            entry_frame,
            text="💾 Save Entry",
            height=40,
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._save_entry,
        )
        self.save_button.pack(pady=(10, 20))

    def _select_mood(self, mood: str):
        """Select a mood."""
        self.current_mood = mood

        # Update button styles
        for mood_name, button in self.mood_buttons.items():
            if mood_name == mood:
                button.configure(
                    fg_color=DataTerminalTheme.PRIMARY, border_color=DataTerminalTheme.PRIMARY
                )
            else:
                button.configure(
                    fg_color=DataTerminalTheme.CARD_BG, border_color=DataTerminalTheme.BORDER
                )

    def _create_entries_list(self):
        """Create entries list section."""
        list_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            list_frame,
            text="📖 Journal Entries",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        # Scrollable frame for entries
        self.entries_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.entries_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.entries_scroll.grid_columnconfigure(0, weight=1)

    def _load_entries(self):
        """Load existing journal entries."""
        try:
            self.cursor.execute("SELECT * FROM journal_entries ORDER BY created_at DESC LIMIT 10")
            entries = self.cursor.fetchall()

            for entry in entries:
                self._create_entry_widget(entry)

        except Exception as e:
            print(f"Error loading entries: {e}")

    def _create_entry_widget(self, entry_data):
        """Create a widget for a journal entry."""
        (
            entry_id,
            date_created,
            weather_data,
            mood_rating,
            entry_content,
            tags,
            location,
            category,
            photos,
            template_used,
            created_at,
            updated_at,
        ) = entry_data

        entry_widget = ctk.CTkFrame(
            self.entries_scroll,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        entry_widget.grid(sticky="ew", pady=5)
        entry_widget.grid_columnconfigure(0, weight=1)

        # Header with date and mood
        header_frame = ctk.CTkFrame(entry_widget, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)

        # Date
        if isinstance(date_created, str):
            date_obj = datetime.fromisoformat(date_created)
        else:
            date_obj = date_created
        date_str = date_obj.strftime("%B %d, %Y at %I:%M %p")
        ctk.CTkLabel(
            header_frame,
            text=date_str,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).grid(row=0, column=0, sticky="w")

        # Mood
        mood_emojis = {
            1: "😢",
            2: "😞",
            3: "😐",
            4: "🙂",
            5: "😊",
            6: "😄",
            7: "😁",
            8: "🤗",
            9: "😍",
            10: "🤩",
        }
        mood_emoji = mood_emojis.get(mood_rating, "😐")
        ctk.CTkLabel(
            header_frame,
            text=f"{mood_emoji} Mood: {mood_rating}/10",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.PRIMARY,
        ).grid(row=0, column=2, sticky="e")

        # Weather info
        weather_frame = ctk.CTkFrame(entry_widget, fg_color="transparent")
        weather_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)

        # Parse weather data if available
        if weather_data:
            try:
                import json

                weather_info = json.loads(weather_data)
                weather_text = f"🌤️ {location}: {weather_info.get('temperature', 'N/A')}°C, {weather_info.get('condition', 'N/A')}"
                if weather_info.get("humidity"):
                    weather_text += f" | Humidity: {weather_info['humidity']}%"
                if weather_info.get("wind_speed"):
                    weather_text += f" | Wind: {weather_info['wind_speed']} m/s"
            except (json.JSONDecodeError, KeyError):
                weather_text = f"🌤️ {location or 'Unknown location'}"
        else:
            weather_text = f"🌤️ {location or 'Unknown location'}"

        ctk.CTkLabel(
            weather_frame,
            text=weather_text,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        ).pack(anchor="w")

        # Notes
        if entry_content and entry_content.strip():
            notes_frame = ctk.CTkFrame(entry_widget, fg_color="transparent")
            notes_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 10))

            ctk.CTkLabel(
                notes_frame,
                text=entry_content,
                font=(DataTerminalTheme.FONT_FAMILY, 11),
                text_color=DataTerminalTheme.TEXT,
                wraplength=400,
                justify="left",
            ).pack(anchor="w")

    def _save_entry(self):
        """Save a new journal entry."""
        if not self.current_mood:
            # Show error - mood is required
            return

        notes = self.notes_text.get("1.0", "end-1c").strip()

        try:
            # Get current weather data
            if (
                hasattr(self.weather_service, "current_weather")
                and self.weather_service.current_weather
            ):
                weather_data = self.weather_service.current_weather
                city = weather_data.get("name", "Unknown")
                temp = weather_data.get("main", {}).get("temp")
                condition = weather_data.get("weather", [{}])[0].get("description", "")
                humidity = weather_data.get("main", {}).get("humidity")
                wind_speed = weather_data.get("wind", {}).get("speed")
                weather_json = json.dumps(weather_data)
            else:
                # Fallback values
                city = "Unknown"
                temp = None
                condition = "No data"
                humidity = None
                wind_speed = None
                weather_json = "{}"

            # Insert into database
            self.cursor.execute(
                """
                INSERT INTO journal_entries 
                (city, temperature, weather_condition, mood, notes, humidity, wind_speed, weather_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    city,
                    temp,
                    condition,
                    self.current_mood,
                    notes,
                    humidity,
                    wind_speed,
                    weather_json,
                ),
            )
            self.conn.commit()

            # Clear form
            self._clear_form()

            # Reload entries
            self._clear_entries_list()
            self._load_entries()

        except Exception as e:
            print(f"Error saving entry: {e}")

    def _clear_form(self):
        """Clear the entry form."""
        self.current_mood = None
        self.notes_text.delete("1.0", "end")

        # Reset mood buttons
        for button in self.mood_buttons.values():
            button.configure(
                fg_color=DataTerminalTheme.CARD_BG, border_color=DataTerminalTheme.BORDER
            )

    def _clear_entries_list(self):
        """Clear the entries list."""
        for widget in self.entries_scroll.winfo_children():
            widget.destroy()

    def update_weather_data(self, weather_data):
        """Update current weather data for journal entries."""
        self.current_weather_data = weather_data

        if weather_data:
            city = weather_data.get("name", "Unknown")
            temp = weather_data.get("main", {}).get("temp", "N/A")
            condition = weather_data.get("weather", [{}])[0].get("description", "N/A")

            self.weather_info_label.configure(
                text=f"🌤️ Current: {city}, {temp}°C, {condition.title()}"
            )

    def __del__(self):
        """Close database connection."""
        if hasattr(self, "conn"):
            self.conn.close()
