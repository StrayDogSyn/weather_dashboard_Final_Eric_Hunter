"""Journal tab manager for the weather dashboard."""

import json
import logging
import threading
from datetime import date, datetime
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional


from ...models.journal import JournalEntry, JournalRepository, JournalService, Mood
import customtkinter as ctk
from ..safe_widgets import (
    SafeCTkButton,
    SafeCTkComboBox,
    SafeCTkEntry,
    SafeCTkFrame,
    SafeCTkLabel,
    SafeCTkTextbox,
)
from ..components.glassmorphic.glass_panel import GlassPanel
from ..components.glassmorphic.glass_button import GlassButton
from ..components.glassmorphic.glassmorphic_frame import GlassmorphicFrame
from ..theme_manager import ThemeManager
from ..theme import DataTerminalTheme


class JournalTabManager:
    """Manages the journal tab UI and functionality."""

    def __init__(self, parent_frame, weather_service=None, theme_manager: ThemeManager = None):
        """Initialize journal tab manager."""
        self.logger = logging.getLogger(__name__)
        self.parent_frame = parent_frame
        self.weather_service = weather_service
        self.theme_manager = theme_manager or ThemeManager()

        # Initialize journal service
        self.journal_service = JournalService(
            repository=JournalRepository(), weather_service=weather_service
        )

        # UI state
        self.current_view = "list"  # list, create, edit, calendar, insights
        self.current_entry: Optional[JournalEntry] = None
        self.selected_date: Optional[date] = None
        self.search_query = ""
        self.filter_mood: Optional[Mood] = None
        self.filter_location = ""

        # UI components
        self.main_frame: Optional[SafeCTkFrame] = None
        self.toolbar_frame: Optional[SafeCTkFrame] = None
        self.content_frame: Optional[SafeCTkFrame] = None
        self.entry_form_frame: Optional[SafeCTkFrame] = None
        self.entry_list_frame: Optional[SafeCTkFrame] = None
        self.calendar_frame: Optional[SafeCTkFrame] = None
        self.insights_frame: Optional[SafeCTkFrame] = None

        # Form widgets
        self.title_entry: Optional[SafeCTkEntry] = None
        self.location_entry: Optional[SafeCTkEntry] = None
        self.mood_combo: Optional[SafeCTkComboBox] = None
        self.content_textbox: Optional[SafeCTkTextbox] = None
        self.tags_entry: Optional[SafeCTkEntry] = None

        # Auto-save timer
        self.auto_save_timer: Optional[threading.Timer] = None
        self.unsaved_changes = False

        self.logger.info("Journal tab manager initialized")

    def create_journal_tab(self) -> SafeCTkFrame:
        """Create and return the journal tab content."""
        try:
            # Main container with glassmorphic effect
            self.main_frame = GlassPanel(
                self.parent_frame,
                glass_opacity=0.05
            )
            self.main_frame.grid_columnconfigure(0, weight=1)
            self.main_frame.grid_rowconfigure(1, weight=1)

            # Create glassmorphic toolbar
            self._create_glassmorphic_toolbar()

            # Create content area with glassmorphic effect
            self.content_frame = GlassmorphicFrame(
                self.main_frame,
                glass_opacity=0.1
            )
            self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
            self.content_frame.grid_columnconfigure(0, weight=1)
            self.content_frame.grid_rowconfigure(0, weight=1)

            # Show initial view
            self._show_entry_list()

            self.logger.info("Journal tab created successfully")
            return self.main_frame

        except Exception as e:
            self.logger.error(f"Failed to create journal tab: {e}")
            # Return error frame
            error_frame = SafeCTkFrame(self.parent_frame)
            error_label = SafeCTkLabel(
                error_frame, text=f"Error creating journal tab: {str(e)}", text_color="red"
            )
            error_label.pack(pady=20)
            return error_frame

    def _create_glassmorphic_toolbar(self):
        """Create the glassmorphic toolbar with navigation and action buttons."""
        self.toolbar_frame = GlassmorphicFrame(
            self.main_frame,
            glass_opacity=0.15
        )
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        self.toolbar_frame.grid_columnconfigure(6, weight=1)  # Spacer column

        # Navigation buttons with glassmorphic styling
        GlassButton(
            self.toolbar_frame, 
            text="📝 New Entry", 
            command=self._show_create_entry, 
            width=120,
            height=40
        ).grid(row=0, column=0, padx=(0, 10))

        GlassButton(
            self.toolbar_frame, 
            text="📋 List", 
            command=self._show_entry_list, 
            width=100,
            height=40
        ).grid(row=0, column=1, padx=10)

        GlassButton(
            self.toolbar_frame, 
            text="📅 Calendar", 
            command=self._show_calendar, 
            width=100,
            height=40
        ).grid(row=0, column=2, padx=10)

        GlassButton(
            self.toolbar_frame, 
            text="📊 Insights", 
            command=self._show_insights, 
            width=100,
            height=40
        ).grid(row=0, column=3, padx=10)

        # Search entry with glassmorphic styling
        self.search_entry = ctk.CTkEntry(
            self.toolbar_frame, 
            placeholder_text="🔍 Search entries...", 
            width=200,
            height=40,
            fg_color="#FFFFFF1A",
            border_color="#FFFFFF33",
            text_color="#FFFFFF",
            placeholder_text_color="#FFFFFF80"
        )
        self.search_entry.grid(row=0, column=7, padx=10)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Filter mood combo with glassmorphic styling
        mood_values = ["All Moods"] + [mood.value for mood in Mood]
        self.mood_filter_combo = ctk.CTkComboBox(
            self.toolbar_frame, 
            values=mood_values, 
            command=self._on_filter_changed, 
            width=140,
            height=40,
            fg_color="#FFFFFF1A",
            border_color="#FFFFFF33",
            text_color="#FFFFFF",
            dropdown_fg_color="#000000CC",
            dropdown_text_color="#FFFFFF"
        )
        self.mood_filter_combo.set("All Moods")
        self.mood_filter_combo.grid(row=0, column=8, padx=10)

        # Export button with glassmorphic styling
        GlassButton(
            self.toolbar_frame, 
            text="💾 Export", 
            command=self._show_export_options, 
            width=100,
            height=40
        ).grid(row=0, column=9, padx=(10, 0))

    def _show_create_entry(self):
        """Show the create entry form."""
        self.current_view = "create"
        self.current_entry = None
        self._clear_content_frame()
        self._create_entry_form()

    def _show_edit_entry(self, entry: JournalEntry):
        """Show the edit entry form."""
        self.current_view = "edit"
        self.current_entry = entry
        self._clear_content_frame()
        self._create_entry_form(entry)

        # Start editing session for auto-save
        self.journal_service.start_editing_session(entry)

    def _show_entry_list(self):
        """Show the entry list view."""
        self.current_view = "list"
        self._clear_content_frame()
        self._create_entry_list()

    def _show_calendar(self):
        """Show the calendar view."""
        self.current_view = "calendar"
        self._clear_content_frame()
        self._create_calendar_view()

    def _show_insights(self):
        """Show the insights view."""
        self.current_view = "insights"
        self._clear_content_frame()
        self._create_insights_view()

    def _clear_content_frame(self):
        """Clear the content frame."""
        # End any editing session
        if self.current_view == "edit" and self.current_entry:
            self.journal_service.end_editing_session(save_changes=True)

        # Stop auto-save timer
        self._stop_auto_save_timer()

        # Clear frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _create_entry_form(self, entry: Optional[JournalEntry] = None):
        """Create the entry creation/editing form."""
        # Main form frame with glassmorphic effect
        form_frame = GlassmorphicFrame(
            self.content_frame,
            glass_opacity=0.15
        )
        form_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        form_frame.grid_columnconfigure(1, weight=1)

        # Title with glassmorphic styling
        title_text = "✨ Edit Entry" if entry else "✨ Create New Entry"
        ctk.CTkLabel(
            form_frame, 
            text=title_text, 
            font=("Arial", 24, "bold"),
            text_color="#00D4FF"
        ).grid(
            row=0, column=0, columnspan=2, pady=(0, 30)
        )

        # Entry title with glassmorphic input
        ctk.CTkLabel(
            form_frame, 
            text="📝 Title:",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        ).grid(row=1, column=0, sticky="w", pady=10)
        self.title_entry = ctk.CTkEntry(
            form_frame, 
            width=400,
            height=40,
            fg_color="#FFFFFF1A",
            border_color="#FFFFFF33",
            text_color="#FFFFFF",
            placeholder_text="Enter your journal title...",
            placeholder_text_color="#FFFFFF80"
        )
        self.title_entry.grid(row=1, column=1, sticky="ew", padx=(15, 0), pady=10)
        if entry and entry.title:
            self.title_entry.insert(0, entry.title)

        # Location with glassmorphic auto-fill button
        location_frame = ctk.CTkFrame(
            form_frame,
            fg_color="transparent"
        )
        location_frame.grid(row=2, column=1, sticky="ew", padx=(15, 0), pady=10)
        location_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form_frame, 
            text="📍 Location:",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        ).grid(row=2, column=0, sticky="w", pady=10)
        self.location_entry = ctk.CTkEntry(
            location_frame, 
            width=300,
            height=40,
            fg_color="#FFFFFF1A",
            border_color="#FFFFFF33",
            text_color="#FFFFFF",
            placeholder_text="Enter location...",
            placeholder_text_color="#FFFFFF80"
        )
        self.location_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        if entry and entry.location:
            self.location_entry.insert(0, entry.location)

        GlassButton(
            location_frame, 
            text="🌤️ Auto-fill Weather", 
            command=self._auto_fill_weather, 
            width=140,
            height=40
        ).grid(row=0, column=1)

        # Mood selector with glassmorphic styling
        ctk.CTkLabel(
            form_frame, 
            text="😊 Mood:",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        ).grid(row=3, column=0, sticky="w", pady=10)
        mood_values = [mood.value for mood in Mood]
        self.mood_combo = ctk.CTkComboBox(
            form_frame, 
            values=mood_values, 
            width=200,
            height=40,
            fg_color="#FFFFFF1A",
            border_color="#FFFFFF33",
            text_color="#FFFFFF",
            dropdown_fg_color="#000000CC",
            dropdown_text_color="#FFFFFF"
        )
        self.mood_combo.grid(row=3, column=1, sticky="w", padx=(15, 0), pady=10)
        if entry and entry.mood:
            self.mood_combo.set(entry.mood.value)

        # Content text area with glassmorphic styling
        ctk.CTkLabel(
            form_frame, 
            text="📖 Content:",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        ).grid(row=4, column=0, sticky="nw", pady=(10, 0))
        self.content_textbox = ctk.CTkTextbox(
            form_frame, 
            height=300, 
            width=500,
            fg_color="#FFFFFF0D",
            border_color="#FFFFFF33",
            text_color="#FFFFFF"
        )
        self.content_textbox.grid(row=4, column=1, sticky="ew", padx=(15, 0), pady=10)
        if entry and entry.content:
            self.content_textbox.insert("1.0", entry.content)

        # Tags with glassmorphic styling
        ctk.CTkLabel(
            form_frame, 
            text="🏷️ Tags (comma-separated):",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF"
        ).grid(
            row=5, column=0, sticky="w", pady=10
        )
        self.tags_entry = ctk.CTkEntry(
            form_frame, 
            width=400,
            height=40,
            fg_color="#FFFFFF1A",
            border_color="#FFFFFF33",
            text_color="#FFFFFF",
            placeholder_text="Enter tags separated by commas...",
            placeholder_text_color="#FFFFFF80"
        )
        self.tags_entry.grid(row=5, column=1, sticky="ew", padx=(15, 0), pady=10)
        if entry and entry.tags:
            self.tags_entry.insert(0, ", ".join(entry.tags))

        # Weather display with glassmorphic styling (if available)
        if entry and entry.weather_snapshot:
            weather_frame = ctk.CTkFrame(
                form_frame,
                fg_color="#FFFFFF0D",
                corner_radius=15
            )
            weather_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=15)

            ctk.CTkLabel(
                weather_frame, 
                text=f"🌤️ Weather: {entry.weather_display}", 
                font=("Arial", 12),
                text_color="#FFFFFFB3"
            ).pack(pady=10)

        # Action buttons with glassmorphic styling
        button_frame = ctk.CTkFrame(
            form_frame,
            fg_color="transparent"
        )
        button_frame.grid(row=7, column=0, columnspan=2, pady=30)

        GlassButton(
            button_frame, 
            text="💾 Save", 
            command=self._save_entry, 
            width=120,
            height=45
        ).pack(
            side="left", padx=10
        )

        GlassButton(
            button_frame, 
            text="❌ Cancel", 
            command=self._show_entry_list, 
            width=120,
            height=45
        ).pack(side="left", padx=10)

        if entry:
            GlassButton(
                button_frame,
                text="🗑️ Delete",
                command=lambda: self._delete_entry(entry),
                width=120,
                height=45
            ).pack(side="left", padx=10)

        # Bind change events for auto-save
        self._bind_change_events()

        # Auto-save status label with glassmorphic styling
        self.auto_save_label = ctk.CTkLabel(
            form_frame, 
            text="", 
            font=("Arial", 10), 
            text_color="#FFFFFF80"
        )
        self.auto_save_label.grid(row=8, column=0, columnspan=2, pady=10)

    def _bind_change_events(self):
        """Bind change events for auto-save functionality."""
        if self.title_entry:
            self.title_entry.bind("<KeyRelease>", self._on_content_changed)
        if self.location_entry:
            self.location_entry.bind("<KeyRelease>", self._on_content_changed)
        if self.content_textbox:
            self.content_textbox.bind("<KeyRelease>", self._on_content_changed)
        if self.tags_entry:
            self.tags_entry.bind("<KeyRelease>", self._on_content_changed)

    def _on_content_changed(self, event=None):
        """Handle content changes for auto-save."""
        if self.current_view in ["create", "edit"]:
            self.unsaved_changes = True
            if self.current_entry:
                self.journal_service.mark_unsaved_changes()
            self._start_auto_save_timer()

    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        self._stop_auto_save_timer()
        if self.current_view == "edit" and self.current_entry:
            self.auto_save_timer = threading.Timer(30.0, self._auto_save)
            self.auto_save_timer.start()

    def _stop_auto_save_timer(self):
        """Stop auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
            self.auto_save_timer = None

    def _auto_save(self):
        """Perform auto-save."""
        try:
            if self.current_view == "edit" and self.current_entry and self.unsaved_changes:
                self._update_entry_from_form()
                self.journal_service.update_entry(self.current_entry)
                self.unsaved_changes = False

                # Update status
                if self.auto_save_label:
                    self.auto_save_label.configure(
                        text=f"Auto-saved at {datetime.now().strftime('%H:%M:%S')}"
                    )

                self.logger.debug(f"Auto-saved entry: {self.current_entry.id}")

        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")

    def _auto_fill_weather(self):
        """Auto-fill weather data for current location."""
        if not self.weather_service or not self.location_entry:
            messagebox.showwarning(
                "Warning", "Weather service not available or location not specified."
            )
            return

        location = self.location_entry.get().strip()
        if not location:
            messagebox.showwarning("Warning", "Please enter a location first.")
            return

        try:
            weather_data = self.weather_service.get_current_weather(location)
            if weather_data:
                # Create or update current entry with weather data
                if not self.current_entry:
                    self.current_entry = JournalEntry(location=location)

                self.current_entry.weather_snapshot = self.journal_service._create_weather_snapshot(
                    weather_data
                )
                self.current_entry.latitude = getattr(weather_data, "latitude", None)
                self.current_entry.longitude = getattr(weather_data, "longitude", None)

                messagebox.showinfo(
                    "Success", f"Weather data filled: {self.current_entry.weather_display}"
                )

            else:
                messagebox.showerror("Error", "Could not retrieve weather data for this location.")

        except Exception as e:
            self.logger.error(f"Failed to auto-fill weather: {e}")
            messagebox.showerror("Error", f"Failed to retrieve weather data: {str(e)}")

    def _save_entry(self):
        """Save the current entry."""
        try:
            if self.current_view == "create":
                # Create new entry
                entry = JournalEntry(
                    title=self.title_entry.get().strip(),
                    content=self.content_textbox.get("1.0", "end-1c"),
                    location=self.location_entry.get().strip(),
                    mood=self._get_selected_mood(),
                )

                # Add tags
                tags_text = self.tags_entry.get().strip()
                if tags_text:
                    entry.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

                # Save entry
                saved_entry = self.journal_service.create_entry(
                    entry.title,
                    entry.content,
                    entry.location,
                    entry.mood,
                    auto_fill_weather=False,  # We handle weather manually
                )

                # Update with additional data
                saved_entry.tags = entry.tags
                if self.current_entry and self.current_entry.weather_snapshot:
                    saved_entry.weather_snapshot = self.current_entry.weather_snapshot
                    saved_entry.latitude = self.current_entry.latitude
                    saved_entry.longitude = self.current_entry.longitude

                self.journal_service.update_entry(saved_entry)

                messagebox.showinfo("Success", "Entry created successfully!")

            elif self.current_view == "edit" and self.current_entry:
                # Update existing entry
                self._update_entry_from_form()
                self.journal_service.update_entry(self.current_entry)
                messagebox.showinfo("Success", "Entry updated successfully!")

            # Return to list view
            self._show_entry_list()

        except Exception as e:
            self.logger.error(f"Failed to save entry: {e}")
            messagebox.showerror("Error", f"Failed to save entry: {str(e)}")

    def _update_entry_from_form(self):
        """Update current entry with form data."""
        if not self.current_entry:
            return

        self.current_entry.title = self.title_entry.get().strip()
        self.current_entry.content = self.content_textbox.get("1.0", "end-1c")
        self.current_entry.location = self.location_entry.get().strip()
        self.current_entry.mood = self._get_selected_mood()

        # Update tags
        tags_text = self.tags_entry.get().strip()
        self.current_entry.tags = (
            [tag.strip() for tag in tags_text.split(",") if tag.strip()] if tags_text else []
        )

        # Update content and word count
        self.current_entry.update_content(self.current_entry.content)

    def _get_selected_mood(self) -> Optional[Mood]:
        """Get selected mood from combo box."""
        if not self.mood_combo:
            return None

        mood_value = self.mood_combo.get()
        for mood in Mood:
            if mood.value == mood_value:
                return mood
        return None

    def _delete_entry(self, entry: JournalEntry):
        """Delete an entry with confirmation."""
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the entry '{entry.title or 'Untitled'}'?\n\nThis action cannot be undone.",
        )

        if result:
            try:
                self.journal_service.delete_entry(entry.id)
                messagebox.showinfo("Success", "Entry deleted successfully!")
                self._show_entry_list()
            except Exception as e:
                self.logger.error(f"Failed to delete entry: {e}")
                messagebox.showerror("Error", f"Failed to delete entry: {str(e)}")

    def _create_entry_list(self):
        """Create the entry list view with glassmorphic styling."""
        # Get filtered entries
        entries = self._get_filtered_entries()

        # List frame with glassmorphic styling
        list_frame = GlassmorphicFrame(self.content_frame, glass_opacity=0.1)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)

        # Header with glassmorphic styling
        header_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header_frame,
            text=f"📖 Journal Entries ({len(entries)})",
            font=("Arial", 20, "bold"),
            text_color="#FFFFFF"
        ).grid(row=0, column=0, sticky="w")

        # Sort options with glassmorphic styling
        sort_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        sort_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            sort_frame, 
            text="Sort by:", 
            font=("Arial", 12),
            text_color="#FFFFFFB3"
        ).pack(side="left", padx=(0, 10))
        sort_combo = ctk.CTkComboBox(
            sort_frame,
            values=["Date (Newest)", "Date (Oldest)", "Title", "Mood", "Location"],
            command=self._on_sort_changed,
            width=150,
            height=35,
            fg_color="#FFFFFF1A",
            border_color="#FFFFFF33",
            text_color="#FFFFFF",
            dropdown_fg_color="#1A1A1A"
        )
        sort_combo.set("Date (Newest)")
        sort_combo.pack(side="left")

        # Scrollable frame for entries with glassmorphic styling
        scrollable_frame = ctk.CTkScrollableFrame(
            list_frame, 
            height=400,
            fg_color="transparent",
            scrollbar_fg_color="#FFFFFF1A",
            scrollbar_button_color="#FFFFFF33"
        )
        scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        scrollable_frame.grid_columnconfigure(0, weight=1)

        # Display entries
        if not entries:
            ctk.CTkLabel(
                scrollable_frame,
                text="📝 No entries found. Create your first entry!",
                font=("Arial", 16),
                text_color="#FFFFFF80",
            ).grid(row=0, column=0, pady=50)
        else:
            for i, entry in enumerate(entries):
                self._create_entry_card(scrollable_frame, entry, i)

    def _create_entry_card(self, parent, entry: JournalEntry, row: int):
        """Create a glassmorphic card for displaying an entry in the list."""
        # Entry card frame with glassmorphic styling
        card_frame = GlassmorphicFrame(parent, glass_opacity=0.05)
        card_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        card_frame.grid_columnconfigure(1, weight=1)

        # Mood emoji with glassmorphic background
        mood_frame = ctk.CTkFrame(
            card_frame, 
            fg_color="#FFFFFF0D", 
            corner_radius=15,
            width=60,
            height=60
        )
        mood_frame.grid(row=0, column=0, rowspan=3, padx=15, pady=15, sticky="n")
        mood_frame.grid_propagate(False)
        
        mood_label = ctk.CTkLabel(
            mood_frame, 
            text=entry.mood.emoji if entry.mood else "📝", 
            font=("Arial", 28)
        )
        mood_label.place(relx=0.5, rely=0.5, anchor="center")

        # Entry info with transparent background
        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=15, pady=15)
        info_frame.grid_columnconfigure(0, weight=1)

        # Title and date with glassmorphic styling
        title_text = entry.title or "Untitled Entry"
        ctk.CTkLabel(
            info_frame, 
            text=title_text, 
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            info_frame,
            text=f"📅 {entry.date_str} at {entry.time_str}",
            font=("Arial", 11),
            text_color="#FFFFFF99",
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

        # Location and weather with glassmorphic styling
        if entry.location or entry.weather_snapshot:
            location_text = f"📍 {entry.location or 'Unknown location'}"
            if entry.weather_snapshot:
                location_text += f" • {entry.weather_display}"

            ctk.CTkLabel(
                info_frame, 
                text=location_text, 
                font=("Arial", 11), 
                text_color="#FFFFFF80"
            ).grid(row=2, column=0, sticky="w", pady=(3, 0))

        # Content preview with glassmorphic styling
        if entry.content:
            preview_text = (
                entry.content[:120] + "..." if len(entry.content) > 120 else entry.content
            )
            # Remove HTML tags for preview
            import re
            preview_text = re.sub(r"<[^>]+>", "", preview_text)

            ctk.CTkLabel(
                info_frame,
                text=preview_text,
                font=("Arial", 11),
                text_color="#FFFFFFB3",
                wraplength=400,
                justify="left",
            ).grid(row=3, column=0, sticky="w", pady=(8, 0))

        # Tags with glassmorphic styling
        if entry.tags:
            tags_text = " ".join([f"#{tag}" for tag in entry.tags[:3]])
            if len(entry.tags) > 3:
                tags_text += f" +{len(entry.tags) - 3} more"

            ctk.CTkLabel(
                info_frame, 
                text=f"🏷️ {tags_text}", 
                font=("Arial", 10), 
                text_color="#00D4FF"
            ).grid(row=4, column=0, sticky="w", pady=(5, 0))

        # Action buttons with glassmorphic styling
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, rowspan=3, padx=15, pady=15)

        GlassButton(
            button_frame,
            text="✏️ Edit",
            command=lambda e=entry: self._show_edit_entry(e),
            width=80,
            height=35,
        ).pack(pady=5)

        GlassButton(
            button_frame,
            text="👁️ View",
            command=lambda e=entry: self._show_entry_details(e),
            width=80,
            height=35,
        ).pack(pady=5)

    def _show_entry_details(self, entry: JournalEntry):
        """Show detailed view of an entry in a popup window."""
        # Create popup window
        popup = ctk.CTkToplevel(self.main_frame)
        popup.title(f"Entry: {entry.title or 'Untitled'}")
        popup.geometry("600x500")
        popup.transient(self.main_frame)
        popup.grab_set()

        # Main frame
        main_frame = SafeCTkFrame(popup)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = SafeCTkFrame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Mood and title
        mood_text = f"{entry.mood.emoji} {entry.mood.value}" if entry.mood else "📝 No mood"
        SafeCTkLabel(header_frame, text=mood_text, font=ctk.CTkFont(size=16)).grid(
            row=0, column=0, sticky="w"
        )

        SafeCTkLabel(
            header_frame,
            text=entry.title or "Untitled Entry",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # Metadata
        meta_text = f"📅 {entry.date_str} at {entry.time_str}"
        if entry.location:
            meta_text += f"\n📍 {entry.location}"
        if entry.weather_snapshot:
            meta_text += f"\n🌤️ {entry.weather_display}"
        if entry.tags:
            meta_text += f"\n🏷️ {', '.join(entry.tags)}"

        SafeCTkLabel(
            header_frame,
            text=meta_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # Content
        content_frame = SafeCTkFrame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        content_textbox = SafeCTkTextbox(content_frame, wrap="word")
        content_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        content_textbox.insert("1.0", entry.content or "No content")
        content_textbox.configure(state="disabled")

        # Close button
        SafeCTkButton(main_frame, text="Close", command=popup.destroy, width=100).grid(
            row=2, column=0, pady=(10, 0)
        )

    def _get_filtered_entries(self) -> List[JournalEntry]:
        """Get entries filtered by current search and filter criteria."""
        entries = self.journal_service.get_all_entries()

        # Apply search filter
        if self.search_query:
            entries = [e for e in entries if self._entry_matches_search(e, self.search_query)]

        # Apply mood filter
        if self.filter_mood:
            entries = [e for e in entries if e.mood == self.filter_mood]

        # Apply location filter
        if self.filter_location:
            entries = [
                e
                for e in entries
                if e.location and self.filter_location.lower() in e.location.lower()
            ]

        return entries

    def _entry_matches_search(self, entry: JournalEntry, query: str) -> bool:
        """Check if entry matches search query."""
        query = query.lower()

        # Search in title
        if entry.title and query in entry.title.lower():
            return True

        # Search in content
        if entry.content and query in entry.content.lower():
            return True

        # Search in location
        if entry.location and query in entry.location.lower():
            return True

        # Search in tags
        if entry.tags and any(query in tag.lower() for tag in entry.tags):
            return True

        return False

    def _on_search_changed(self, event=None):
        """Handle search query changes."""
        self.search_query = self.search_entry.get().strip()
        if self.current_view == "list":
            self._show_entry_list()

    def _on_filter_changed(self, value=None):
        """Handle filter changes."""
        mood_value = self.mood_filter_combo.get()
        if mood_value == "All Moods":
            self.filter_mood = None
        else:
            for mood in Mood:
                if mood.value == mood_value:
                    self.filter_mood = mood
                    break

        if self.current_view == "list":
            self._show_entry_list()

    def _on_sort_changed(self, value=None):
        """Handle sort option changes."""
        if self.current_view == "list":
            self._show_entry_list()

    def _create_calendar_view(self):
        """Create the calendar view for browsing entries by date."""
        # Calendar frame
        calendar_frame = SafeCTkFrame(self.content_frame)
        calendar_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        calendar_frame.grid_columnconfigure(1, weight=1)
        calendar_frame.grid_rowconfigure(0, weight=1)

        # Calendar widget (simplified - you might want to use a proper calendar widget)
        cal_widget_frame = SafeCTkFrame(calendar_frame)
        cal_widget_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        SafeCTkLabel(
            cal_widget_frame, text="📅 Calendar View", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)

        SafeCTkLabel(
            cal_widget_frame,
            text="Calendar widget would go here\n(Consider integrating tkcalendar)",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=20)

        # Entries for selected date
        entries_frame = SafeCTkFrame(calendar_frame)
        entries_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        entries_frame.grid_columnconfigure(0, weight=1)
        entries_frame.grid_rowconfigure(1, weight=1)

        SafeCTkLabel(
            entries_frame,
            text="Entries for Selected Date",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, pady=10)

        # Show recent entries as placeholder
        recent_entries = self.journal_service.get_all_entries()[:5]

        scrollable_entries = ctk.CTkScrollableFrame(entries_frame, height=300)
        scrollable_entries.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        scrollable_entries.grid_columnconfigure(0, weight=1)

        for i, entry in enumerate(recent_entries):
            self._create_entry_card(scrollable_entries, entry, i)

    def _create_insights_view(self):
        """Create the insights and analytics view."""
        # Get statistics
        stats = self.journal_service.get_comprehensive_statistics()

        # Main insights frame
        insights_frame = SafeCTkFrame(self.content_frame)
        insights_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        insights_frame.grid_columnconfigure(0, weight=1)
        insights_frame.grid_rowconfigure(0, weight=1)

        # Scrollable content
        scrollable_frame = ctk.CTkScrollableFrame(insights_frame)
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_frame.grid_columnconfigure(0, weight=1)

        # Title
        SafeCTkLabel(
            scrollable_frame, text="📊 Journal Insights", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20))

        row = 1

        # Basic statistics
        self._create_stats_section(
            scrollable_frame,
            "📈 Basic Statistics",
            {
                "Total Entries": stats.get("total_entries", 0),
                "Total Words": stats.get("total_words", 0),
                "Average Words per Entry": stats.get("average_words", 0),
                "Entries This Month": len(
                    self.journal_service.get_entries_by_date_range(
                        datetime.now().replace(day=1), datetime.now()
                    )
                ),
            },
            row,
        )
        row += 1

        # Mood statistics
        mood_stats = stats.get("mood_distribution", {})
        if mood_stats:
            mood_display = {
                f"{mood.emoji} {mood.value}": count for mood, count in mood_stats.items()
            }
            self._create_stats_section(scrollable_frame, "😊 Mood Distribution", mood_display, row)
            row += 1

        # Weather-mood insights
        weather_insights = stats.get("mood_weather_insights", {})
        if weather_insights.get("most_common_moods_by_weather"):
            weather_mood_display = {}
            for weather, data in weather_insights["most_common_moods_by_weather"].items():
                weather_mood_display[f"{weather}"] = (
                    f"{data['emoji']} {data['mood']} ({data['count']} times)"
                )

            self._create_stats_section(
                scrollable_frame, "🌤️ Weather & Mood Patterns", weather_mood_display, row
            )
            row += 1

        # Writing patterns
        writing_patterns = stats.get("writing_patterns", {})
        if writing_patterns.get("patterns"):
            patterns_display = {
                f"Pattern {i+1}": pattern for i, pattern in enumerate(writing_patterns["patterns"])
            }
            self._create_stats_section(
                scrollable_frame, "✍️ Writing Patterns", patterns_display, row
            )
            row += 1

        # Top tags
        tags = stats.get("tags", {})
        if tags:
            top_tags = dict(list(tags.items())[:5])
            self._create_stats_section(scrollable_frame, "🏷️ Top Tags", top_tags, row)
            row += 1

        # Word cloud button
        SafeCTkButton(
            scrollable_frame, text="☁️ Generate Word Cloud", command=self._show_word_cloud, width=200
        ).grid(row=row, column=0, pady=20)

    def _create_stats_section(self, parent, title: str, data: Dict[str, Any], row: int):
        """Create a statistics section."""
        # Section frame
        section_frame = SafeCTkFrame(parent)
        section_frame.grid(row=row, column=0, sticky="ew", pady=10)
        section_frame.grid_columnconfigure(0, weight=1)

        # Title
        SafeCTkLabel(section_frame, text=title, font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 5)
        )

        # Data
        for i, (key, value) in enumerate(data.items()):
            data_frame = SafeCTkFrame(section_frame)
            data_frame.grid(row=i + 1, column=0, sticky="ew", padx=10, pady=2)
            data_frame.grid_columnconfigure(1, weight=1)

            SafeCTkLabel(data_frame, text=str(key), font=ctk.CTkFont(size=12)).grid(
                row=0, column=0, sticky="w", padx=5, pady=2
            )

            SafeCTkLabel(
                data_frame,
                text=str(value),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="blue",
            ).grid(row=0, column=1, sticky="e", padx=5, pady=2)

        # Add some padding at the bottom
        SafeCTkLabel(section_frame, text="").grid(row=len(data) + 1, column=0, pady=5)

    def _show_word_cloud(self):
        """Show word cloud in a popup window."""
        try:
            # Get word cloud data
            word_data = self.journal_service.get_word_cloud_data()

            if not word_data:
                messagebox.showinfo("Info", "No text data available for word cloud.")
                return

            # Create popup window
            popup = ctk.CTkToplevel(self.main_frame)
            popup.title("Word Cloud")
            popup.geometry("600x400")
            popup.transient(self.main_frame)
            popup.grab_set()

            # Display word frequencies as text (since we don't have wordcloud library)
            main_frame = SafeCTkFrame(popup)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            main_frame.grid_columnconfigure(0, weight=1)
            main_frame.grid_rowconfigure(1, weight=1)

            SafeCTkLabel(
                main_frame, text="☁️ Word Frequencies", font=ctk.CTkFont(size=18, weight="bold")
            ).grid(row=0, column=0, pady=(0, 10))

            # Scrollable word list
            scrollable_frame = ctk.CTkScrollableFrame(main_frame)
            scrollable_frame.grid(row=1, column=0, sticky="nsew")
            scrollable_frame.grid_columnconfigure(0, weight=1)

            # Sort words by frequency
            sorted_words = sorted(word_data.items(), key=lambda x: x[1], reverse=True)[:50]

            for i, (word, count) in enumerate(sorted_words):
                word_frame = SafeCTkFrame(scrollable_frame)
                word_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
                word_frame.grid_columnconfigure(1, weight=1)

                SafeCTkLabel(word_frame, text=word, font=ctk.CTkFont(size=12)).grid(
                    row=0, column=0, sticky="w", padx=5, pady=2
                )

                SafeCTkLabel(
                    word_frame,
                    text=str(count),
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="blue",
                ).grid(row=0, column=1, sticky="e", padx=5, pady=2)

            # Close button
            SafeCTkButton(main_frame, text="Close", command=popup.destroy, width=100).grid(
                row=2, column=0, pady=(10, 0)
            )

        except Exception as e:
            self.logger.error(f"Failed to show word cloud: {e}")
            messagebox.showerror("Error", f"Failed to generate word cloud: {str(e)}")

    def _show_export_options(self):
        """Show export options dialog."""
        # Create popup window
        popup = ctk.CTkToplevel(self.main_frame)
        popup.title("Export Journal")
        popup.geometry("400x300")
        popup.transient(self.main_frame)
        popup.grab_set()

        # Main frame
        main_frame = SafeCTkFrame(popup)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        # Title
        SafeCTkLabel(
            main_frame, text="💾 Export Journal", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20))

        # Export options
        SafeCTkButton(
            main_frame,
            text="📄 Export to JSON",
            command=lambda: self._export_json(popup),
            width=200,
            height=40,
        ).grid(row=1, column=0, pady=10)

        SafeCTkButton(
            main_frame,
            text="📋 Export to PDF",
            command=lambda: self._export_pdf(popup),
            width=200,
            height=40,
        ).grid(row=2, column=0, pady=10)

        SafeCTkButton(
            main_frame,
            text="📊 Export Statistics",
            command=lambda: self._export_statistics(popup),
            width=200,
            height=40,
        ).grid(row=3, column=0, pady=10)

        # Close button
        SafeCTkButton(main_frame, text="Cancel", command=popup.destroy, width=100).grid(
            row=4, column=0, pady=(20, 0)
        )

    def _export_json(self, popup):
        """Export entries to JSON file."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export to JSON",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if file_path:
                success = self.journal_service.export_to_json(file_path)
                if success:
                    messagebox.showinfo("Success", f"Journal exported to {file_path}")
                    popup.destroy()
                else:
                    messagebox.showerror("Error", "Failed to export journal")

        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def _export_pdf(self, popup):
        """Export entries to PDF file."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export to PDF",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            )

            if file_path:
                entries = self.journal_service.get_all_entries()
                success = self.journal_service.export_to_pdf(file_path, entries)
                if success:
                    messagebox.showinfo("Success", f"Journal exported to {file_path}")
                    popup.destroy()
                else:
                    messagebox.showerror("Error", "Failed to export journal to PDF")

        except Exception as e:
            self.logger.error(f"Failed to export PDF: {e}")
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def _export_statistics(self, popup):
        """Export statistics to JSON file."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Statistics",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if file_path:
                stats = self.journal_service.get_comprehensive_statistics()

                # Convert Mood objects to strings for JSON serialization
                def convert_mood_keys(obj):
                    if isinstance(obj, dict):
                        new_dict = {}
                        for key, value in obj.items():
                            if hasattr(key, "value"):  # Mood object
                                new_key = key.value
                            else:
                                new_key = str(key)
                            new_dict[new_key] = convert_mood_keys(value)
                        return new_dict
                    elif isinstance(obj, list):
                        return [convert_mood_keys(item) for item in obj]
                    else:
                        return obj

                stats_json = convert_mood_keys(stats)

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(stats_json, f, indent=2, ensure_ascii=False, default=str)

                messagebox.showinfo("Success", f"Statistics exported to {file_path}")
                popup.destroy()

        except Exception as e:
            self.logger.error(f"Failed to export statistics: {e}")
            messagebox.showerror("Error", f"Failed to export statistics: {str(e)}")

    def cleanup(self):
        """Cleanup resources."""
        # End any editing session
        if self.current_view == "edit" and self.current_entry:
            self.journal_service.end_editing_session(save_changes=True)

        # Stop auto-save timer
        self._stop_auto_save_timer()

        # Cleanup journal service
        self.journal_service.cleanup()

        self.logger.info("Journal tab manager cleaned up")
