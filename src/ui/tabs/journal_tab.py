"""Weather Journal Tab with Rich Text Editor."""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import customtkinter as ctk

from ...services.database.database_service import DatabaseService
from ..components.glassmorphic import GlassmorphicFrame
from ..components.glassmorphic.glass_button import GlassButton
from ...utils.error_wrapper import ensure_main_thread


class WeatherJournalTab(ctk.CTkFrame):
    """Weather Journal Tab with rich text editing capabilities."""
    
    def __init__(self, parent, weather_service=None, db_service=None):
        """Initialize the Weather Journal Tab with glassmorphic design."""
        super().__init__(parent)
        
        self.weather_service = weather_service
        self.db_service = db_service or DatabaseService()
        self.entries = []
        self.current_entry_id = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Initialize UI components
        self.setup_ui()
        
        # Load existing entries or create mock data
        self.load_entries_with_fallback()
    
    def setup_ui(self):
        """Set up the journal interface with improved layout."""
        try:
            # Main scrollable container
            self.main_container = ctk.CTkScrollableFrame(
                self,
                fg_color="transparent"
            )
            self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            self.main_container.grid_columnconfigure(0, weight=1)
            
            # Create sections
            self.create_header()
            self.create_entry_section()
            self.create_entries_list()
        except Exception as e:
            print(f"Error setting up journal UI: {e}")
            self.create_fallback_ui()
    
    def create_header(self):
        """Create glassmorphic header"""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # Title with glow effect
        title = ctk.CTkLabel(
            header_frame,
            text="📝 Weather Journal",
            font=("Arial", 24, "bold"),
            text_color="#00D4FF"
        )
        title.pack(side="left")
        
        # Weather info display
        self.weather_info_label = ctk.CTkLabel(
            header_frame,
            text="Weather: Loading...",
            font=("Arial", 12),
            text_color="#CCCCCC"
        )
        self.weather_info_label.pack(side="right")
        
        # Update weather info
        self.update_weather_info()
    
    def create_entry_section(self):
        """Create glassmorphic entry section"""
        from ..components.glassmorphic import GlassPanel
        
        # Entry container with glass effect
        entry_container = GlassPanel(self.main_container)
        entry_container.configure(fg_color=("#2B2B2B", "#1A1A1A"))
        entry_container.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        entry_container.grid_columnconfigure(0, weight=1)
        
        # Entry title input with glass styling
        self.title_entry = ctk.CTkEntry(
            entry_container,
            placeholder_text="✨ What's on your mind today?",
            height=45,
            font=("Arial", 16),
            fg_color=("#2B2B2B", "#1A1A1A"),
            border_color="#00D4FF",
            text_color="#FFFFFF"
        )
        self.title_entry.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # Rich text editor with glass frame
        text_container = ctk.CTkFrame(
            entry_container,
            fg_color=("#2B2B2B", "#1A1A1A"),
            corner_radius=15
        )
        text_container.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        text_container.grid_columnconfigure(0, weight=1)
        
        # Rich text editor
        self.text_editor = scrolledtext.ScrolledText(
            text_container,
            height=8,
            wrap=tk.WORD,
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="#FFFFFF",
            insertbackground="#00D4FF",
            selectbackground="#00D4FF",
            relief="flat",
            borderwidth=0
        )
        self.text_editor.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        
        # Mood and controls frame
        controls_frame = ctk.CTkFrame(entry_container, fg_color="transparent")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Mood selector with glass buttons
        mood_label = ctk.CTkLabel(
            controls_frame,
            text="Mood:",
            font=("Arial", 12),
            text_color="#CCCCCC"
        )
        mood_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        self.mood_var = tk.StringVar(value="neutral")
        moods = ["😊 Happy", "😐 Neutral", "😢 Sad", "😎 Excited", "😴 Tired"]
        
        mood_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        mood_frame.grid(row=0, column=1, sticky="w")
        
        for i, mood in enumerate(moods):
            btn = ctk.CTkRadioButton(
                mood_frame,
                text=mood,
                variable=self.mood_var,
                value=mood.split()[1].lower(),
                text_color="#CCCCCC",
                fg_color="#00D4FF",
                hover_color="#0099CC"
            )
            btn.grid(row=0, column=i, padx=8, sticky="w")
        
        # Action buttons with glass effect
        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        # Save button
        save_btn = GlassButton(
            button_frame,
            text="💾 Save Entry",
            command=self.save_entry,
            width=120,
            height=35
        )
        save_btn.pack(side="left", padx=(0, 10))
        
        # Add weather button
        weather_btn = GlassButton(
            button_frame,
            text="🌤️ Add Weather",
            command=self.add_weather_to_entry,
            width=120,
            height=35
        )
        weather_btn.pack(side="left", padx=10)
        
        # Clear button
        clear_btn = GlassButton(
            button_frame,
            text="🗑️ Clear",
            command=self.clear_entry_form,
            width=100,
            height=35
        )
        clear_btn.pack(side="right")
    

    
    def create_entries_list(self):
        """Create glassmorphic entries list section."""
        from ..components.glassmorphic import GlassPanel
        
        # List container with glass effect
        list_container = GlassPanel(self.main_container)
        list_container.configure(fg_color=("#2B2B2B", "#1A1A1A"))
        list_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(1, weight=1)
        
        # Header with search
        header_frame = ctk.CTkFrame(list_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # List title
        list_title = ctk.CTkLabel(
            header_frame,
            text="📚 Journal Entries",
            font=("Arial", 18, "bold"),
            text_color="#FFFFFF"
        )
        list_title.grid(row=0, column=0, sticky="w")
        
        # Search entry with glass styling
        self.search_entry = ctk.CTkEntry(
            header_frame,
            placeholder_text="🔍 Search entries...",
            height=35,
            font=("Arial", 12),
            fg_color=("#2B2B2B", "#1A1A1A"),
            border_color="#00D4FF",
            text_color="#FFFFFF",
            width=250
        )
        self.search_entry.grid(row=0, column=1, sticky="e", padx=(20, 0))
        self.search_entry.bind("<KeyRelease>", self.filter_entries)
        
        # Scrollable entries list
        self.entries_scrollable = ctk.CTkScrollableFrame(
            list_container,
            fg_color="transparent"
        )
        self.entries_scrollable.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.entries_scrollable.grid_columnconfigure(0, weight=1)
    
    @ensure_main_thread
    def update_weather_info(self):
        """Update weather information display."""
        try:
            if self.weather_service:
                weather_data = self.weather_service.get_current_weather()
                if weather_data:
                    weather_text = f"Weather: {weather_data.get('temperature', 'N/A')}°C, {weather_data.get('condition', 'N/A')} in {weather_data.get('location', 'Unknown')}"
                    self.weather_info_label.configure(text=weather_text)
                else:
                    self.weather_info_label.configure(text="Weather: Unable to fetch current weather")
            else:
                self.weather_info_label.configure(text="Weather: Service not available")
        except Exception as e:
            self.weather_info_label.configure(text=f"Weather: Error - {str(e)}")
    
    def add_weather_to_entry(self):
        """Add current weather information to the text entry."""
        try:
            if self.weather_service:
                weather_data = self.weather_service.get_current_weather()
                if weather_data:
                    weather_text = f"\n\n🌤️ Weather Update ({datetime.now().strftime('%Y-%m-%d %H:%M')}):\n"
                    weather_text += f"Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
                    weather_text += f"Condition: {weather_data.get('condition', 'N/A')}\n"
                    weather_text += f"Location: {weather_data.get('location', 'Unknown')}\n"
                    weather_text += f"Humidity: {weather_data.get('humidity', 'N/A')}%\n"
                    weather_text += f"Wind: {weather_data.get('wind_speed', 'N/A')} km/h\n"
                    
                    # Insert at current cursor position
                    self.text_editor.insert(tk.INSERT, weather_text)
                else:
                    messagebox.showwarning("Weather", "Unable to fetch current weather data")
            else:
                messagebox.showwarning("Weather", "Weather service not available")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add weather data: {str(e)}")
    
    def save_entry(self):
        """Save journal entry with weather data."""
        try:
            title = self.title_entry.get().strip()
            content = self.text_editor.get("1.0", tk.END).strip()
            mood = self.mood_var.get()
            
            if not title:
                messagebox.showwarning("Validation", "Please enter a title for your entry")
                return
            
            if not content:
                messagebox.showwarning("Validation", "Please enter some content for your entry")
                return
            
            # Get current weather data
            weather_data = {}
            try:
                if self.weather_service:
                    current_weather = self.weather_service.get_current_weather()
                    if current_weather:
                        weather_data = {
                            "temperature": current_weather.get('temperature'),
                            "condition": current_weather.get('condition'),
                            "location": current_weather.get('location'),
                            "humidity": current_weather.get('humidity'),
                            "wind_speed": current_weather.get('wind_speed')
                        }
            except Exception as e:
                print(f"Warning: Could not fetch weather data: {e}")
            
            # Create entry
            entry = {
                "id": self.current_entry_id or str(uuid.uuid4()),
                "title": title,
                "content": content,
                "mood": mood,
                "timestamp": datetime.now().isoformat(),
                "weather": weather_data
            }
            
            # Save to database
            if self.current_entry_id:
                # Update existing entry
                self.db_service.update_journal_entry(entry)
                messagebox.showinfo("Success", "Entry updated successfully!")
            else:
                # Save new entry
                self.db_service.save_journal_entry(entry)
                messagebox.showinfo("Success", "Entry saved successfully!")
            
            # Refresh entries list and clear form
            self.load_entries()
            self.clear_entry_form()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entry: {str(e)}")
    
    def clear_entry_form(self):
        """Clear the entry form."""
        self.title_entry.delete(0, tk.END)
        self.text_editor.delete("1.0", tk.END)
        self.mood_var.set("neutral")
        self.current_entry_id = None
        self.update_weather_info()
    
    def load_entries_with_fallback(self):
        """Load entries with fallback to mock data."""
        try:
            if self.db_service:
                self.entries = self.db_service.get_journal_entries()
            else:
                self.entries = []
            
            # If no entries, create some mock data for demonstration
            if not self.entries:
                self.create_mock_entries()
            
            self.display_entries()
        except Exception as e:
            print(f"Error loading entries: {e}")
            self.create_mock_entries()
            self.display_entries()
    
    def create_mock_entries(self):
        """Create mock journal entries for demonstration."""
        from datetime import datetime, timedelta
        
        mock_entries = [
            {
                "id": "mock_1",
                "title": "Beautiful Sunny Day",
                "content": "Today was absolutely wonderful! The sun was shining brightly, and I decided to take a long walk in the park. The weather was perfect - not too hot, not too cold. I saw families having picnics and children playing on the playground. It really lifted my spirits and reminded me to appreciate the simple pleasures in life.",
                "mood": "happy",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "weather": {
                    "temperature": 22,
                    "condition": "Sunny",
                    "humidity": 45,
                    "wind_speed": 8
                }
            },
            {
                "id": "mock_2",
                "title": "Rainy Day Reflections",
                "content": "It's been raining all day today. There's something peaceful about the sound of raindrops on the window. I spent most of the day indoors, reading a good book and sipping hot tea. Sometimes these quiet, contemplative days are exactly what we need to recharge and reflect on life.",
                "mood": "neutral",
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "weather": {
                    "temperature": 15,
                    "condition": "Rainy",
                    "humidity": 85,
                    "wind_speed": 12
                }
            },
            {
                "id": "mock_3",
                "title": "Exciting News!",
                "content": "I got some amazing news today that I've been waiting for months! All the hard work and patience has finally paid off. I'm so excited about this new opportunity and can't wait to see where it leads. Celebrating tonight with friends and family!",
                "mood": "excited",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "weather": {
                    "temperature": 18,
                    "condition": "Partly Cloudy",
                    "humidity": 60,
                    "wind_speed": 5
                }
            }
        ]
        
        self.entries = mock_entries
    
    def load_entries(self):
        """Load and display journal entries."""
        try:
            if self.db_service:
                self.entries = self.db_service.get_journal_entries()
            else:
                self.entries = []
            self.display_entries()
        except Exception as e:
            print(f"Error loading entries: {e}")
            self.entries = []
            self.display_entries()
    
    def create_fallback_ui(self):
        """Create a simple fallback UI when glassmorphic components fail."""
        # Simple container
        fallback_frame = ctk.CTkFrame(
            self,
            fg_color=("#2B2B2B", "#1A1A1A"),
            corner_radius=10
        )
        fallback_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        fallback_frame.grid_columnconfigure(0, weight=1)
        fallback_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            fallback_frame,
            text="📖 Weather Journal",
            font=("Arial", 24, "bold"),
            text_color="#FFFFFF"
        )
        title_label.grid(row=0, column=0, pady=20)
        
        # Scrollable content
        self.entries_scrollable = ctk.CTkScrollableFrame(
            fallback_frame,
            fg_color="transparent"
        )
        self.entries_scrollable.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.entries_scrollable.grid_columnconfigure(0, weight=1)
        
        # Create mock entries for demonstration
        self.create_mock_entries()
        self.display_entries_simple()
    
    def display_entries(self, filtered_entries=None):
        """Display entries in glassmorphic cards with error handling."""
        try:
            # Clear existing entries
            if hasattr(self, 'entries_scrollable'):
                for widget in self.entries_scrollable.winfo_children():
                    widget.destroy()
            
            entries_to_show = filtered_entries if filtered_entries is not None else self.entries
            
            if not entries_to_show:
                self.show_no_entries_message()
                return
            
            # Sort entries by timestamp (newest first)
            entries_to_show.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            for i, entry in enumerate(entries_to_show):
                try:
                    self.create_entry_card(entry, i)
                except Exception as e:
                    print(f"Error creating entry card {i}: {e}")
                    self.create_simple_entry_card(entry, i)
        except Exception as e:
            print(f"Error displaying entries: {e}")
            self.display_entries_simple()
    
    def show_no_entries_message(self):
        """Show message when no entries are available."""
        try:
            from ..components.glassmorphic import GlassPanel
            no_entries_panel = GlassPanel(self.entries_scrollable)
            no_entries_panel.configure(fg_color=("#2B2B2B", "#1A1A1A"))
            no_entries_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=20)
            
            no_entries_label = ctk.CTkLabel(
                no_entries_panel,
                text="📝 No journal entries yet. Start writing your first entry above!",
                font=("Arial", 14),
                text_color="#CCCCCC"
            )
            no_entries_label.pack(pady=30)
        except Exception as e:
            print(f"Error showing no entries message: {e}")
            # Simple fallback
            simple_label = ctk.CTkLabel(
                self.entries_scrollable,
                text="📝 No journal entries available",
                font=("Arial", 14),
                text_color="#CCCCCC"
            )
            simple_label.grid(row=0, column=0, pady=30)
    
    def display_entries_simple(self):
        """Simple fallback method to display entries."""
        for i, entry in enumerate(self.entries):
            self.create_simple_entry_card(entry, i)
    
    def create_entry_card(self, entry, row):
        """Create a glassmorphic card for displaying an entry."""
        from ..components.glassmorphic import GlassPanel, GlassButton
        
        # Entry card with glass effect
        card_frame = GlassPanel(self.entries_scrollable)
        card_frame.configure(fg_color=("#2B2B2B", "#1A1A1A"))
        card_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        card_frame.grid_columnconfigure(1, weight=1)
        
        # Mood emoji with glow effect
        mood_emoji = {
            "happy": "😊",
            "neutral": "😐",
            "sad": "😢",
            "excited": "😎",
            "tired": "😴"
        }.get(entry.get('mood', 'neutral'), "😐")
        
        mood_frame = ctk.CTkFrame(card_frame, fg_color=("#2B2B2B", "#1A1A1A"), corner_radius=15, width=60, height=60)
        mood_frame.grid(row=0, column=0, rowspan=3, padx=15, pady=15, sticky="n")
        mood_frame.grid_propagate(False)
        
        mood_label = ctk.CTkLabel(
            mood_frame,
            text=mood_emoji,
            font=("Arial", 28)
        )
        mood_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Entry info frame with glass styling
        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=15, pady=15)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Title with enhanced styling
        title_label = ctk.CTkLabel(
            info_frame,
            text=f"✨ {entry.get('title', 'Untitled')}",
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        # Timestamp with enhanced styling
        try:
            timestamp = datetime.fromisoformat(entry.get('timestamp', ''))
            time_text = timestamp.strftime('%B %d, %Y at %I:%M %p')
        except:
            time_text = entry.get('timestamp', 'Unknown time')
        
        time_label = ctk.CTkLabel(
            info_frame,
            text=f"📅 {time_text}",
            font=("Arial", 11),
            text_color="#CCCCCC",
            anchor="w"
        )
        time_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        # Content preview with glass background
        content = entry.get('content', '')
        preview = content[:150] + "..." if len(content) > 150 else content
        preview = preview.replace('\n', ' ')  # Remove line breaks for preview
        
        content_frame = ctk.CTkFrame(
            info_frame,
            fg_color=("#2B2B2B", "#1A1A1A"),
            corner_radius=10
        )
        content_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        
        content_label = ctk.CTkLabel(
            content_frame,
            text=preview,
            font=("Arial", 12),
            text_color="#CCCCCC",
            anchor="w",
            wraplength=400
        )
        content_label.pack(padx=12, pady=8, anchor="w")
        
        # Weather info with enhanced styling
        weather = entry.get('weather', {})
        if weather and weather.get('temperature'):
            weather_frame = ctk.CTkFrame(
                info_frame,
                fg_color=("#2B2B2B", "#1A1A1A"),
                corner_radius=8
            )
            weather_frame.grid(row=3, column=0, sticky="w", pady=(8, 0))
            
            weather_text = f"🌡️ {weather.get('temperature')}°C | {weather.get('condition', 'N/A')}"
            weather_label = ctk.CTkLabel(
                weather_frame,
                text=weather_text,
                font=("Arial", 11),
                text_color="#00D4FF"
            )
            weather_label.pack(padx=10, pady=5)
        
        # Action buttons with glass effect
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, rowspan=3, padx=15, pady=15)
        
        edit_btn = GlassButton(
            button_frame,
            text="✏️ Edit",
            command=lambda e=entry: self.edit_entry(e),
            width=70,
            height=35
        )
        edit_btn.grid(row=0, column=0, pady=5)
        
        delete_btn = GlassButton(
            button_frame,
            text="🗑️ Delete",
            command=lambda e=entry: self.delete_entry(e),
            width=70,
            height=35,
            fg_color=("#8B0000", "#A52A2A"),
            hover_color=("#A52A2A", "#CD5C5C")
        )
        delete_btn.grid(row=1, column=0, pady=5)
    
    def create_simple_entry_card(self, entry, row):
        """Create a simple entry card as fallback."""
        # Simple card frame
        card_frame = ctk.CTkFrame(
            self.entries_scrollable,
            fg_color=("#2B2B2B", "#1A1A1A"),
            corner_radius=10
        )
        card_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        card_frame.grid_columnconfigure(1, weight=1)
        
        # Mood emoji
        mood_emoji = {
            "happy": "😊",
            "neutral": "😐",
            "sad": "😢",
            "excited": "😎",
            "tired": "😴"
        }.get(entry.get('mood', 'neutral'), "😐")
        
        mood_label = ctk.CTkLabel(
            card_frame,
            text=mood_emoji,
            font=("Arial", 24)
        )
        mood_label.grid(row=0, column=0, rowspan=3, padx=15, pady=15)
        
        # Entry info
        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=15, pady=15)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            info_frame,
            text=f"✨ {entry.get('title', 'Untitled')}",
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        # Timestamp
        try:
            from datetime import datetime
            timestamp = datetime.fromisoformat(entry.get('timestamp', ''))
            time_text = timestamp.strftime('%B %d, %Y at %I:%M %p')
        except:
            time_text = entry.get('timestamp', 'Unknown time')
        
        time_label = ctk.CTkLabel(
            info_frame,
            text=f"📅 {time_text}",
            font=("Arial", 11),
            text_color="#CCCCCC",
            anchor="w"
        )
        time_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        # Content preview
        content = entry.get('content', '')
        preview = content[:100] + "..." if len(content) > 100 else content
        preview = preview.replace('\n', ' ')
        
        content_label = ctk.CTkLabel(
            info_frame,
            text=preview,
            font=("Arial", 12),
            text_color="#CCCCCC",
            anchor="w",
            wraplength=300
        )
        content_label.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        
        # Weather info
        weather = entry.get('weather', {})
        if weather and weather.get('temperature'):
            weather_text = f"🌡️ {weather.get('temperature')}°C | {weather.get('condition', 'N/A')}"
            weather_label = ctk.CTkLabel(
                info_frame,
                text=weather_text,
                font=("Arial", 11),
                text_color="#00D4FF",
                anchor="w"
            )
            weather_label.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        
        # Simple action buttons
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, rowspan=3, padx=15, pady=15)
        
        edit_btn = ctk.CTkButton(
            button_frame,
            text="✏️ Edit",
            command=lambda e=entry: self.edit_entry(e),
            width=70,
            height=35,
            fg_color="#0078D4",
            hover_color="#106EBE"
        )
        edit_btn.grid(row=0, column=0, pady=5)
        
        delete_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Delete",
            command=lambda e=entry: self.delete_entry(e),
            width=70,
            height=35,
            fg_color="#8B0000",
            hover_color="#A52A2A"
        )
        delete_btn.grid(row=1, column=0, pady=5)
    
    def edit_entry(self, entry):
        """Load entry for editing."""
        self.current_entry_id = entry.get('id')
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, entry.get('title', ''))
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", entry.get('content', ''))
        
        self.mood_var.set(entry.get('mood', 'neutral'))
        
        # Scroll to top
        self.main_container.focus_set()
    
    def delete_entry(self, entry):
        """Delete an entry after confirmation."""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{entry.get('title', 'this entry')}'?"):
            try:
                self.db_service.delete_journal_entry(entry.get('id'))
                self.load_entries()
                messagebox.showinfo("Success", "Entry deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete entry: {str(e)}")
    
    def filter_entries(self, event=None):
        """Filter entries based on search text."""
        search_text = self.search_entry.get().lower().strip()
        
        filtered = []
        for entry in self.entries:
            # Check search text in title, content, and mood
            if search_text:
                title_match = search_text in entry.get('title', '').lower()
                content_match = search_text in entry.get('content', '').lower()
                mood_match = search_text in entry.get('mood', '').lower()
                
                if title_match or content_match or mood_match:
                    filtered.append(entry)
            else:
                # If no search text, show all entries
                filtered.append(entry)
        
        self.display_entries(filtered)