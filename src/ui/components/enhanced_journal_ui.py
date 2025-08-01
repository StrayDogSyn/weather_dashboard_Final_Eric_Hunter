"""Enhanced Weather Journal UI Component

Provides a comprehensive journal interface with:
- Left sidebar: Entry list with thumbnails
- Main area: Rich text editor with toolbar
- Right panel: Mood selector, weather data, tags
- Bottom: Analytics dashboard with mood trends
- Export controls in header area
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from pathlib import Path

from src.services.journal_service import JournalService
from src.models.journal_models import JournalEntry
from src.ui.components.mood_analytics import MoodAnalyticsComponent
from src.utils.photo_manager import PhotoManager


class EnhancedJournalUI(ctk.CTkFrame):
    """Enhanced journal UI with comprehensive layout and features."""
    
    def __init__(self, parent, journal_service: JournalService, **kwargs):
        super().__init__(parent, **kwargs)
        self.journal_service = journal_service
        self.photo_manager = PhotoManager()
        self.current_entry: Optional[JournalEntry] = None
        self.entries_list: List[JournalEntry] = []
        
        # Configure main grid
        self.grid_columnconfigure(1, weight=3)  # Main area gets most space
        self.grid_columnconfigure(2, weight=1)  # Right panel
        self.grid_rowconfigure(1, weight=1)     # Content area
        
        self._create_ui()
        self._load_entries()
    
    def _create_ui(self):
        """Create the comprehensive journal interface."""
        # Header with export controls
        self._create_header()
        
        # Left sidebar - Entry list
        self._create_sidebar()
        
        # Main area - Rich text editor
        self._create_main_editor()
        
        # Right panel - Mood, weather, tags
        self._create_right_panel()
        
        # Bottom analytics dashboard
        self._create_analytics_panel()
    
    def _create_header(self):
        """Create header with title and export controls."""
        header_frame = ctk.CTkFrame(self, height=60, fg_color="#1A1A1A")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="📖 Weather Journal",
            font=("JetBrains Mono", 20, "bold"),
            text_color="#00FFAB"
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Export controls
        export_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        export_frame.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        
        self.new_entry_btn = ctk.CTkButton(
            export_frame,
            text="➕ New Entry",
            width=120,
            height=35,
            fg_color="#00FFAB",
            text_color="#000000",
            hover_color="#00CC88",
            command=self._new_entry
        )
        self.new_entry_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(
            export_frame,
            text="📤 Export",
            width=100,
            height=35,
            fg_color="#2A2A2A",
            hover_color="#3A3A3A",
            command=self._export_entries
        )
        self.export_btn.pack(side="left", padx=5)
    
    def _create_sidebar(self):
        """Create left sidebar with entry list and thumbnails."""
        sidebar_frame = ctk.CTkFrame(self, width=300, fg_color="#1E1E1E")
        sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 2), pady=5)
        sidebar_frame.grid_propagate(False)
        sidebar_frame.grid_rowconfigure(1, weight=1)
        
        # Sidebar header
        sidebar_header = ctk.CTkLabel(
            sidebar_frame,
            text="📚 Journal Entries",
            font=("JetBrains Mono", 14, "bold"),
            text_color="#00FFAB"
        )
        sidebar_header.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Search box
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._filter_entries)
        
        search_entry = ctk.CTkEntry(
            sidebar_frame,
            placeholder_text="🔍 Search entries...",
            textvariable=self.search_var,
            height=35,
            fg_color="#2A2A2A",
            border_color="#333333"
        )
        search_entry.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        
        # Scrollable entries list
        self.entries_scroll = ctk.CTkScrollableFrame(
            sidebar_frame,
            fg_color="#2A2A2A",
            corner_radius=8
        )
        self.entries_scroll.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.entries_scroll.grid_columnconfigure(0, weight=1)
    
    def _create_main_editor(self):
        """Create main area with rich text editor and toolbar."""
        main_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        main_frame.grid(row=1, column=1, sticky="nsew", padx=2, pady=5)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Editor toolbar
        toolbar_frame = ctk.CTkFrame(main_frame, height=50, fg_color="#2A2A2A")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        toolbar_frame.grid_propagate(False)
        
        # Formatting buttons
        format_buttons = [
            ("B", "Bold", self._format_bold),
            ("I", "Italic", self._format_italic),
            ("U", "Underline", self._format_underline),
            ("📷", "Add Photo", self._add_photo),
            ("🏷️", "Add Tag", self._add_tag)
        ]
        
        for i, (text, tooltip, command) in enumerate(format_buttons):
            btn = ctk.CTkButton(
                toolbar_frame,
                text=text,
                width=40,
                height=30,
                fg_color="#3A3A3A",
                hover_color="#4A4A4A",
                command=command
            )
            btn.pack(side="left", padx=2, pady=10)
        
        # Title entry
        self.title_var = ctk.StringVar()
        title_entry = ctk.CTkEntry(
            main_frame,
            textvariable=self.title_var,
            placeholder_text="Entry title...",
            height=40,
            font=("JetBrains Mono", 16, "bold"),
            fg_color="#2A2A2A",
            border_color="#333333"
        )
        title_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Rich text editor
        editor_frame = ctk.CTkFrame(main_frame, fg_color="#2A2A2A")
        editor_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        
        self.text_editor = tk.Text(
            editor_frame,
            wrap=tk.WORD,
            bg="#2A2A2A",
            fg="#FFFFFF",
            insertbackground="#00FFAB",
            selectbackground="#00FFAB",
            selectforeground="#000000",
            font=("JetBrains Mono", 11),
            relief="flat",
            borderwidth=0
        )
        self.text_editor.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Scrollbar for text editor
        scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self.text_editor.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.text_editor.configure(yscrollcommand=scrollbar.set)
        
        # Save button
        save_btn = ctk.CTkButton(
            main_frame,
            text="💾 Save Entry",
            height=40,
            fg_color="#00FFAB",
            text_color="#000000",
            hover_color="#00CC88",
            command=self._save_entry
        )
        save_btn.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
    
    def _create_right_panel(self):
        """Create right panel with mood selector, weather data, and tags."""
        right_frame = ctk.CTkFrame(self, width=250, fg_color="#1E1E1E")
        right_frame.grid(row=1, column=2, sticky="nsew", padx=(2, 5), pady=5)
        right_frame.grid_propagate(False)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Mood selector section
        mood_section = ctk.CTkFrame(right_frame, fg_color="#2A2A2A")
        mood_section.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        mood_section.grid_columnconfigure(0, weight=1)
        
        mood_label = ctk.CTkLabel(
            mood_section,
            text="😊 Mood Score",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#00FFAB"
        )
        mood_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        # Mood slider (1-10)
        self.mood_var = ctk.IntVar(value=5)
        mood_slider = ctk.CTkSlider(
            mood_section,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.mood_var,
            progress_color="#00FFAB",
            button_color="#00FFAB",
            button_hover_color="#00CC88"
        )
        mood_slider.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        self.mood_value_label = ctk.CTkLabel(
            mood_section,
            text="5/10",
            font=("JetBrains Mono", 10),
            text_color="#B0B0B0"
        )
        self.mood_value_label.grid(row=2, column=0, padx=15, pady=(0, 15))
        
        mood_slider.configure(command=self._update_mood_display)
        
        # Mood tags
        tags_label = ctk.CTkLabel(
            mood_section,
            text="🏷️ Mood Tags",
            font=("JetBrains Mono", 10, "bold"),
            text_color="#B0B0B0"
        )
        tags_label.grid(row=3, column=0, padx=15, pady=(0, 5), sticky="w")
        
        self.mood_tags_frame = ctk.CTkFrame(mood_section, fg_color="transparent")
        self.mood_tags_frame.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Predefined mood tags
        mood_tags = ["Happy", "Sad", "Anxious", "Calm", "Energetic", "Tired"]
        self.selected_mood_tags = set()
        
        for i, tag in enumerate(mood_tags):
            btn = ctk.CTkButton(
                self.mood_tags_frame,
                text=tag,
                width=60,
                height=25,
                fg_color="#3A3A3A",
                hover_color="#4A4A4A",
                font=("JetBrains Mono", 9),
                command=lambda t=tag: self._toggle_mood_tag(t)
            )
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
        
        # Weather data section
        weather_section = ctk.CTkFrame(right_frame, fg_color="#2A2A2A")
        weather_section.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        weather_section.grid_columnconfigure(0, weight=1)
        
        weather_label = ctk.CTkLabel(
            weather_section,
            text="🌤️ Weather Data",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#00FFAB"
        )
        weather_label.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        self.weather_info_frame = ctk.CTkFrame(weather_section, fg_color="transparent")
        self.weather_info_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Tags section
        tags_section = ctk.CTkFrame(right_frame, fg_color="#2A2A2A")
        tags_section.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        tags_section.grid_columnconfigure(0, weight=1)
        
        tags_header_label = ctk.CTkLabel(
            tags_section,
            text="🏷️ Entry Tags",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#00FFAB"
        )
        tags_header_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        self.tags_var = ctk.StringVar()
        tags_entry = ctk.CTkEntry(
            tags_section,
            textvariable=self.tags_var,
            placeholder_text="Add tags (comma separated)...",
            height=30,
            fg_color="#3A3A3A",
            border_color="#4A4A4A"
        )
        tags_entry.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
    
    def _create_analytics_panel(self):
        """Create bottom analytics dashboard."""
        analytics_frame = ctk.CTkFrame(self, height=200, fg_color="#1E1E1E")
        analytics_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        analytics_frame.grid_propagate(False)
        analytics_frame.grid_columnconfigure(0, weight=1)
        
        # Analytics header
        analytics_header = ctk.CTkLabel(
            analytics_frame,
            text="📊 Mood Trends & Analytics",
            font=("JetBrains Mono", 14, "bold"),
            text_color="#00FFAB"
        )
        analytics_header.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Create analytics component
        self.analytics_component = MoodAnalyticsComponent(
            analytics_frame,
            self.journal_service
        )
        self.analytics_component.get_frame().grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
    
    # Event handlers and utility methods
    def _new_entry(self):
        """Create a new journal entry."""
        self.current_entry = None
        self.title_var.set("")
        self.text_editor.delete(1.0, tk.END)
        self.mood_var.set(5)
        self.selected_mood_tags.clear()
        self.tags_var.set("")
        self._update_mood_tags_display()
        self._update_weather_display()
    
    def _save_entry(self):
        """Save the current journal entry."""
        title = self.title_var.get().strip()
        content = self.text_editor.get(1.0, tk.END).strip()
        
        if not title or not content:
            messagebox.showwarning("Validation Error", "Please provide both title and content.")
            return
        
        try:
            # Create or update entry
            entry_data = {
                'title': title,
                'content': content,
                'mood_score': self.mood_var.get(),
                'mood_tags': json.dumps(list(self.selected_mood_tags)),
                'tags': json.dumps([tag.strip() for tag in self.tags_var.get().split(',') if tag.strip()]),
                'date': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if self.current_entry:
                # Update existing entry
                entry_data['id'] = self.current_entry.id
                entry = JournalEntry(**entry_data)
                success = self.journal_service.update_entry(entry)
            else:
                # Create new entry
                entry = JournalEntry(**entry_data)
                success = self.journal_service.add_entry(entry)
            
            if success:
                messagebox.showinfo("Success", "Entry saved successfully!")
                self._load_entries()
                self.analytics_component.refresh_analytics()
            else:
                messagebox.showerror("Error", "Failed to save entry.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entry: {str(e)}")
    
    def _load_entries(self):
        """Load and display journal entries in sidebar."""
        try:
            self.entries_list = self.journal_service.get_entries(limit=50)
            self._update_entries_display()
        except Exception as e:
            print(f"Error loading entries: {e}")
    
    def _update_entries_display(self):
        """Update the entries display in sidebar."""
        # Clear existing entries
        for widget in self.entries_scroll.winfo_children():
            widget.destroy()
        
        # Add entries
        for i, entry in enumerate(self.entries_list):
            self._create_entry_widget(entry, i)
    
    def _create_entry_widget(self, entry: JournalEntry, index: int):
        """Create a widget for an entry in the sidebar."""
        entry_frame = ctk.CTkFrame(self.entries_scroll, fg_color="#3A3A3A", height=80)
        entry_frame.grid(row=index, column=0, padx=5, pady=2, sticky="ew")
        entry_frame.grid_propagate(False)
        entry_frame.grid_columnconfigure(1, weight=1)
        
        # Mood indicator
        mood_color = self._get_mood_color(entry.mood_score or 5)
        mood_indicator = ctk.CTkFrame(entry_frame, width=4, fg_color=mood_color)
        mood_indicator.grid(row=0, column=0, rowspan=3, sticky="ns", padx=(5, 10))
        
        # Entry title
        title_label = ctk.CTkLabel(
            entry_frame,
            text=entry.title or "Untitled",
            font=("JetBrains Mono", 11, "bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        title_label.grid(row=0, column=1, padx=5, pady=(10, 2), sticky="ew")
        
        # Entry date
        date_str = entry.date or entry.created_at or "Unknown date"
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        
        date_label = ctk.CTkLabel(
            entry_frame,
            text=date_str,
            font=("JetBrains Mono", 9),
            text_color="#B0B0B0",
            anchor="w"
        )
        date_label.grid(row=1, column=1, padx=5, pady=1, sticky="ew")
        
        # Entry preview
        preview_text = (entry.content or "")[:50] + "..." if len(entry.content or "") > 50 else (entry.content or "")
        preview_label = ctk.CTkLabel(
            entry_frame,
            text=preview_text,
            font=("JetBrains Mono", 9),
            text_color="#808080",
            anchor="w"
        )
        preview_label.grid(row=2, column=1, padx=5, pady=(1, 10), sticky="ew")
        
        # Click handler
        def on_click(event, e=entry):
            self._load_entry(e)
        
        entry_frame.bind("<Button-1>", on_click)
        for child in entry_frame.winfo_children():
            child.bind("<Button-1>", on_click)
    
    def _load_entry(self, entry: JournalEntry):
        """Load an entry into the editor."""
        self.current_entry = entry
        self.title_var.set(entry.title or "")
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(1.0, entry.content or "")
        self.mood_var.set(entry.mood_score or 5)
        
        # Load mood tags
        self.selected_mood_tags.clear()
        if entry.mood_tags:
            try:
                mood_tags = json.loads(entry.mood_tags)
                self.selected_mood_tags.update(mood_tags)
            except:
                pass
        
        # Load tags
        if entry.tags:
            try:
                tags = json.loads(entry.tags)
                self.tags_var.set(", ".join(tags))
            except:
                self.tags_var.set(entry.tags)
        else:
            self.tags_var.set("")
        
        self._update_mood_tags_display()
        self._update_mood_display()
    
    def _get_mood_color(self, mood_score: int) -> str:
        """Get color based on mood score."""
        if mood_score >= 8:
            return "#00FF00"  # Green
        elif mood_score >= 6:
            return "#FFFF00"  # Yellow
        elif mood_score >= 4:
            return "#FFA500"  # Orange
        else:
            return "#FF0000"  # Red
    
    def _update_mood_display(self, value=None):
        """Update mood display."""
        mood_value = int(self.mood_var.get())
        self.mood_value_label.configure(text=f"{mood_value}/10")
    
    def _toggle_mood_tag(self, tag: str):
        """Toggle a mood tag selection."""
        if tag in self.selected_mood_tags:
            self.selected_mood_tags.remove(tag)
        else:
            self.selected_mood_tags.add(tag)
        self._update_mood_tags_display()
    
    def _update_mood_tags_display(self):
        """Update mood tags display."""
        for widget in self.mood_tags_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                tag = widget.cget("text")
                if tag in self.selected_mood_tags:
                    widget.configure(fg_color="#00FFAB", text_color="#000000")
                else:
                    widget.configure(fg_color="#3A3A3A", text_color="#FFFFFF")
    
    def _update_weather_display(self):
        """Update weather information display."""
        # Clear existing weather info
        for widget in self.weather_info_frame.winfo_children():
            widget.destroy()
        
        # Add current weather info (placeholder)
        weather_label = ctk.CTkLabel(
            self.weather_info_frame,
            text="Weather data will be\nautomatically populated",
            font=("JetBrains Mono", 9),
            text_color="#B0B0B0",
            justify="center"
        )
        weather_label.pack(pady=10)
    
    def _filter_entries(self, *args):
        """Filter entries based on search term."""
        search_term = self.search_var.get().lower()
        if not search_term:
            self._update_entries_display()
            return
        
        # Filter entries
        filtered_entries = [
            entry for entry in self.entries_list
            if search_term in (entry.title or "").lower() or
               search_term in (entry.content or "").lower() or
               search_term in (entry.tags or "").lower()
        ]
        
        # Update display with filtered entries
        for widget in self.entries_scroll.winfo_children():
            widget.destroy()
        
        for i, entry in enumerate(filtered_entries):
            self._create_entry_widget(entry, i)
    
    def _export_entries(self):
        """Export journal entries."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Journal Entries"
            )
            
            if file_path:
                result = self.journal_service.export_entries(file_path)
                if "successfully" in result:
                    messagebox.showinfo("Success", result)
                else:
                    messagebox.showerror("Error", result)
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    # Formatting methods for rich text editor
    def _format_bold(self):
        """Apply bold formatting."""
        try:
            current_tags = self.text_editor.tag_names(tk.SEL_FIRST)
            if "bold" in current_tags:
                self.text_editor.tag_remove("bold", tk.SEL_FIRST, tk.SEL_LAST)
            else:
                self.text_editor.tag_add("bold", tk.SEL_FIRST, tk.SEL_LAST)
                self.text_editor.tag_config("bold", font=("JetBrains Mono", 11, "bold"))
        except tk.TclError:
            pass
    
    def _format_italic(self):
        """Apply italic formatting."""
        try:
            current_tags = self.text_editor.tag_names(tk.SEL_FIRST)
            if "italic" in current_tags:
                self.text_editor.tag_remove("italic", tk.SEL_FIRST, tk.SEL_LAST)
            else:
                self.text_editor.tag_add("italic", tk.SEL_FIRST, tk.SEL_LAST)
                self.text_editor.tag_config("italic", font=("JetBrains Mono", 11, "italic"))
        except tk.TclError:
            pass
    
    def _format_underline(self):
        """Apply underline formatting."""
        try:
            current_tags = self.text_editor.tag_names(tk.SEL_FIRST)
            if "underline" in current_tags:
                self.text_editor.tag_remove("underline", tk.SEL_FIRST, tk.SEL_LAST)
            else:
                self.text_editor.tag_add("underline", tk.SEL_FIRST, tk.SEL_LAST)
                self.text_editor.tag_config("underline", underline=True)
        except tk.TclError:
            pass
    
    def _add_photo(self):
        """Add photo to entry."""
        file_path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        
        if file_path:
            # Insert photo reference in text
            self.text_editor.insert(tk.INSERT, f"[Photo: {Path(file_path).name}]\n")
    
    def _add_tag(self):
        """Add tag to entry."""
        # Simple tag addition - could be enhanced with a dialog
        self.text_editor.insert(tk.INSERT, "#tag ")