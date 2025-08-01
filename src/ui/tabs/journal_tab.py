"""Weather Journal Tab Implementation

Provides a comprehensive journal interface with entry management,
search functionality, and weather integration.
"""

import logging
import weakref
from datetime import datetime
from typing import Dict, List, Optional, Any

import customtkinter as ctk
from tkinter import messagebox, filedialog

from ..safe_widgets import SafeCTkFrame, SafeCTkScrollableFrame, SafeCTkTextbox
from ..theme import DataTerminalTheme
from ...models.journal_entry import JournalEntry
from ...services.journal_service import JournalService
from ...services.enhanced_weather_service import EnhancedWeatherService
from ...utils.photo_manager import PhotoManager


class JournalTab(SafeCTkFrame):
    """Weather Journal tab implementation with comprehensive functionality."""
    
    def __init__(self, parent, journal_service: Optional[JournalService] = None, 
                 weather_service: Optional[EnhancedWeatherService] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Services
        self.journal_service = journal_service or JournalService()
        self.weather_service = weather_service
        self.photo_manager = PhotoManager()
        
        # State management
        self.current_entry: Optional[JournalEntry] = None
        self.entries_cache: List[JournalEntry] = []
        self.search_results: List[JournalEntry] = []
        
        # UI components (weak references for cleanup)
        self._ui_components: Dict[str, Any] = {}
        self._callbacks: weakref.WeakSet = weakref.WeakSet()
        
        # Setup UI
        self.setup_ui()
        self.load_entries()
        
        # Bind cleanup
        self.bind("<Destroy>", self._cleanup_callbacks)
    
    def setup_ui(self):
        """Setup journal UI components with proper error handling."""
        try:
            # Configure grid
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(1, weight=1)
            
            # Header
            self._create_header()
            
            # Main content area
            self._create_main_content()
            
            # Status bar
            self._create_status_bar()
            
        except Exception as e:
            logging.error(f"Error setting up journal UI: {e}")
            self._show_error("Failed to initialize journal interface")
    
    def _create_header(self):
        """Create header with title and controls."""
        try:
            header_frame = SafeCTkFrame(self, fg_color="transparent")
            header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
            header_frame.grid_columnconfigure(1, weight=1)
            
            # Title
            title_label = ctk.CTkLabel(
                header_frame,
                text="📔 Weather Journal",
                font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
                text_color=DataTerminalTheme.PRIMARY
            )
            title_label.grid(row=0, column=0, sticky="w")
            
            # Controls frame
            controls_frame = SafeCTkFrame(header_frame, fg_color="transparent")
            controls_frame.grid(row=0, column=1, sticky="e")
            
            # New entry button
            new_btn = ctk.CTkButton(
                controls_frame,
                text="+ New Entry",
                command=self._safe_new_entry,
                width=120,
                height=32,
                font=(DataTerminalTheme.FONT_FAMILY, 12, "bold")
            )
            new_btn.grid(row=0, column=0, padx=(0, 10))
            
            # Search entry
            self._ui_components['search_var'] = ctk.StringVar()
            search_entry = ctk.CTkEntry(
                controls_frame,
                placeholder_text="Search entries...",
                textvariable=self._ui_components['search_var'],
                width=200,
                height=32
            )
            search_entry.grid(row=0, column=1, padx=(0, 10))
            search_entry.bind("<KeyRelease>", self._safe_search)
            
            # Refresh button
            refresh_btn = ctk.CTkButton(
                controls_frame,
                text="🔄",
                command=self._safe_refresh,
                width=40,
                height=32
            )
            refresh_btn.grid(row=0, column=2)
            
            self._ui_components['header_frame'] = header_frame
            
        except Exception as e:
            logging.error(f"Error creating header: {e}")
    
    def _create_main_content(self):
        """Create main content area with journal list and editor."""
        try:
            # Left panel - Journal list
            self._create_journal_list()
            
            # Right panel - Entry editor
            self._create_entry_editor()
            
        except Exception as e:
            logging.error(f"Error creating main content: {e}")
    
    def _create_journal_list(self):
        """Create journal entries list with proper scrolling."""
        try:
            # List frame
            list_frame = SafeCTkFrame(self)
            list_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
            list_frame.grid_rowconfigure(1, weight=1)
            list_frame.configure(width=300)
            
            # List header
            list_header = ctk.CTkLabel(
                list_frame,
                text="Journal Entries",
                font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
                text_color=DataTerminalTheme.TEXT_PRIMARY
            )
            list_header.grid(row=0, column=0, pady=10, padx=15, sticky="w")
            
            # Scrollable entries list
            self._ui_components['entries_list'] = SafeCTkScrollableFrame(
                list_frame,
                fg_color=DataTerminalTheme.SURFACE
            )
            self._ui_components['entries_list'].grid(
                row=1, column=0, sticky="nsew", padx=10, pady=(0, 10)
            )
            
            self._ui_components['list_frame'] = list_frame
            
        except Exception as e:
            logging.error(f"Error creating journal list: {e}")
    
    def _create_entry_editor(self):
        """Create entry editor with all necessary controls."""
        try:
            # Editor frame
            editor_frame = SafeCTkFrame(self)
            editor_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
            editor_frame.grid_columnconfigure(0, weight=1)
            editor_frame.grid_rowconfigure(2, weight=1)
            
            # Editor header
            self._create_editor_header(editor_frame)
            
            # Entry metadata
            self._create_entry_metadata(editor_frame)
            
            # Text editor
            self._create_text_editor(editor_frame)
            
            # Editor controls
            self._create_editor_controls(editor_frame)
            
            self._ui_components['editor_frame'] = editor_frame
            
        except Exception as e:
            logging.error(f"Error creating entry editor: {e}")
    
    def _create_editor_header(self, parent):
        """Create editor header with title and date."""
        try:
            header_frame = SafeCTkFrame(parent, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
            header_frame.grid_columnconfigure(1, weight=1)
            
            # Entry title
            self._ui_components['title_var'] = ctk.StringVar(value="New Entry")
            title_entry = ctk.CTkEntry(
                header_frame,
                textvariable=self._ui_components['title_var'],
                font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
                height=40
            )
            title_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            
            # Date label
            self._ui_components['date_label'] = ctk.CTkLabel(
                header_frame,
                text=f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            self._ui_components['date_label'].grid(row=1, column=0, sticky="w")
            
            # Weather info
            self._ui_components['weather_label'] = ctk.CTkLabel(
                header_frame,
                text="Weather: Not loaded",
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            self._ui_components['weather_label'].grid(row=1, column=1, sticky="e")
            
        except Exception as e:
            logging.error(f"Error creating editor header: {e}")
    
    def _create_entry_metadata(self, parent):
        """Create metadata section for tags, mood, etc."""
        try:
            metadata_frame = SafeCTkFrame(parent, fg_color="transparent")
            metadata_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
            metadata_frame.grid_columnconfigure(1, weight=1)
            metadata_frame.grid_columnconfigure(3, weight=1)
            
            # Mood selection
            mood_label = ctk.CTkLabel(
                metadata_frame,
                text="Mood:",
                font=(DataTerminalTheme.FONT_FAMILY, 12)
            )
            mood_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
            
            self._ui_components['mood_var'] = ctk.StringVar(value="😐 Neutral")
            mood_menu = ctk.CTkOptionMenu(
                metadata_frame,
                variable=self._ui_components['mood_var'],
                values=["😊 Happy", "😐 Neutral", "😔 Sad", "😤 Angry", "😰 Anxious", "😴 Tired"],
                width=120
            )
            mood_menu.grid(row=0, column=1, sticky="w", padx=(0, 20))
            
            # Tags
            tags_label = ctk.CTkLabel(
                metadata_frame,
                text="Tags:",
                font=(DataTerminalTheme.FONT_FAMILY, 12)
            )
            tags_label.grid(row=0, column=2, sticky="w", padx=(0, 10))
            
            self._ui_components['tags_var'] = ctk.StringVar()
            tags_entry = ctk.CTkEntry(
                metadata_frame,
                textvariable=self._ui_components['tags_var'],
                placeholder_text="weather, outdoor, work...",
                width=200
            )
            tags_entry.grid(row=0, column=3, sticky="ew")
            
        except Exception as e:
            logging.error(f"Error creating entry metadata: {e}")
    
    def _create_text_editor(self, parent):
        """Create main text editor with formatting options."""
        try:
            # Text editor with scrollbar
            self._ui_components['content_text'] = SafeCTkTextbox(
                parent,
                font=(DataTerminalTheme.FONT_FAMILY, 14),
                wrap="word",
                height=400
            )
            self._ui_components['content_text'].grid(
                row=2, column=0, sticky="nsew", padx=15, pady=(0, 10)
            )
            
            # Set placeholder text
            placeholder = (
                "Write about your day and how the weather affected your mood...\n\n"
                "Tips:\n"
                "• Describe the weather conditions you experienced\n"
                "• Note how the weather made you feel\n"
                "• Record any weather-related activities\n"
                "• Add photos or observations"
            )
            self._ui_components['content_text'].insert("1.0", placeholder)
            
        except Exception as e:
            logging.error(f"Error creating text editor: {e}")
    
    def _create_editor_controls(self, parent):
        """Create editor control buttons."""
        try:
            controls_frame = SafeCTkFrame(parent, fg_color="transparent")
            controls_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=10)
            
            # Save button
            save_btn = ctk.CTkButton(
                controls_frame,
                text="💾 Save Entry",
                command=self._safe_save_entry,
                width=120,
                height=36,
                font=(DataTerminalTheme.FONT_FAMILY, 12, "bold")
            )
            save_btn.grid(row=0, column=0, padx=(0, 10))
            
            # Delete button
            delete_btn = ctk.CTkButton(
                controls_frame,
                text="🗑️ Delete",
                command=self._safe_delete_entry,
                width=100,
                height=36,
                fg_color=DataTerminalTheme.ERROR,
                hover_color=DataTerminalTheme.ERROR_HOVER
            )
            delete_btn.grid(row=0, column=1, padx=(0, 10))
            
            # Add photo button
            photo_btn = ctk.CTkButton(
                controls_frame,
                text="📷 Add Photo",
                command=self._safe_add_photo,
                width=120,
                height=36
            )
            photo_btn.grid(row=0, column=2, padx=(0, 10))
            
            # Export button
            export_btn = ctk.CTkButton(
                controls_frame,
                text="📤 Export",
                command=self._safe_export_entry,
                width=100,
                height=36
            )
            export_btn.grid(row=0, column=3)
            
        except Exception as e:
            logging.error(f"Error creating editor controls: {e}")
    
    def _create_status_bar(self):
        """Create status bar for feedback."""
        try:
            self._ui_components['status_label'] = ctk.CTkLabel(
                self,
                text="Ready",
                font=(DataTerminalTheme.FONT_FAMILY, 10),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                height=20
            )
            self._ui_components['status_label'].grid(
                row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10)
            )
            
        except Exception as e:
            logging.error(f"Error creating status bar: {e}")
    
    def load_entries(self):
        """Load journal entries with error handling."""
        try:
            self._update_status("Loading entries...")
            
            # Get entries from service
            if self.journal_service:
                self.entries_cache = self.journal_service.get_all_entries() or []
            else:
                self.entries_cache = []
            
            # Update UI
            self._populate_entries_list(self.entries_cache)
            self._update_status(f"Loaded {len(self.entries_cache)} entries")
            
        except Exception as e:
            logging.error(f"Error loading entries: {e}")
            self._show_error("Failed to load journal entries")
            self._update_status("Error loading entries")
    
    def _populate_entries_list(self, entries: List[JournalEntry]):
        """Populate the entries list with proper error handling."""
        try:
            if 'entries_list' not in self._ui_components:
                return
            
            # Clear existing entries
            for widget in self._ui_components['entries_list'].winfo_children():
                if hasattr(widget, 'destroy'):
                    widget.destroy()
            
            # Add entries
            for i, entry in enumerate(entries):
                if entry is None:
                    continue
                    
                self._create_entry_item(entry, i)
            
        except Exception as e:
            logging.error(f"Error populating entries list: {e}")
    
    def _create_entry_item(self, entry: JournalEntry, index: int):
        """Create a single entry item in the list."""
        try:
            if not entry or 'entries_list' not in self._ui_components:
                return
            
            # Entry frame
            entry_frame = SafeCTkFrame(
                self._ui_components['entries_list'],
                fg_color=DataTerminalTheme.SURFACE_VARIANT,
                corner_radius=8
            )
            entry_frame.grid(row=index, column=0, sticky="ew", padx=5, pady=2)
            entry_frame.grid_columnconfigure(0, weight=1)
            
            # Make clickable
            entry_frame.bind("<Button-1>", lambda e, ent=entry: self._safe_select_entry(ent))
            
            # Entry title
            title = getattr(entry, 'title', 'Untitled Entry') or 'Untitled Entry'
            title_label = ctk.CTkLabel(
                entry_frame,
                text=title[:30] + ("..." if len(title) > 30 else ""),
                font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                text_color=DataTerminalTheme.TEXT_PRIMARY,
                anchor="w"
            )
            title_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
            title_label.bind("<Button-1>", lambda e, ent=entry: self._safe_select_entry(ent))
            
            # Entry date and mood
            date_str = "Unknown date"
            if hasattr(entry, 'created_at') and entry.created_at:
                try:
                    if isinstance(entry.created_at, str):
                        date_obj = datetime.fromisoformat(entry.created_at.replace('Z', '+00:00'))
                    else:
                        date_obj = entry.created_at
                    date_str = date_obj.strftime('%m/%d %H:%M')
                except Exception:
                    date_str = str(entry.created_at)[:16]
            
            mood = getattr(entry, 'mood', '😐') or '😐'
            info_text = f"{date_str} • {mood}"
            
            info_label = ctk.CTkLabel(
                entry_frame,
                text=info_text,
                font=(DataTerminalTheme.FONT_FAMILY, 10),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                anchor="w"
            )
            info_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
            info_label.bind("<Button-1>", lambda e, ent=entry: self._safe_select_entry(ent))
            
        except Exception as e:
            logging.error(f"Error creating entry item: {e}")
    
    def _safe_select_entry(self, entry: JournalEntry):
        """Safely select and load an entry."""
        try:
            if not entry:
                return
            
            self.current_entry = entry
            self._load_entry_to_editor(entry)
            self._update_status(f"Loaded entry: {getattr(entry, 'title', 'Untitled')}")
            
        except Exception as e:
            logging.error(f"Error selecting entry: {e}")
            self._show_error("Failed to load selected entry")
    
    def _load_entry_to_editor(self, entry: JournalEntry):
        """Load entry data into the editor with proper error handling."""
        try:
            if not entry:
                return
            
            # Update title
            if 'title_var' in self._ui_components:
                title = getattr(entry, 'title', 'Untitled Entry') or 'Untitled Entry'
                self._ui_components['title_var'].set(title)
            
            # Update date
            if 'date_label' in self._ui_components:
                date_str = "Unknown date"
                if hasattr(entry, 'created_at') and entry.created_at:
                    try:
                        if isinstance(entry.created_at, str):
                            date_obj = datetime.fromisoformat(entry.created_at.replace('Z', '+00:00'))
                        else:
                            date_obj = entry.created_at
                        date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        date_str = str(entry.created_at)
                
                self._ui_components['date_label'].configure(text=f"Created: {date_str}")
            
            # Update mood
            if 'mood_var' in self._ui_components:
                mood = getattr(entry, 'mood', '😐 Neutral') or '😐 Neutral'
                self._ui_components['mood_var'].set(mood)
            
            # Update tags
            if 'tags_var' in self._ui_components:
                tags = getattr(entry, 'tags', []) or []
                if isinstance(tags, list):
                    tags_str = ', '.join(tags)
                else:
                    tags_str = str(tags) if tags else ''
                self._ui_components['tags_var'].set(tags_str)
            
            # Update content
            if 'content_text' in self._ui_components:
                content = getattr(entry, 'content', '') or ''
                self._ui_components['content_text'].delete("1.0", "end")
                self._ui_components['content_text'].insert("1.0", content)
            
            # Update weather info
            if 'weather_label' in self._ui_components:
                weather_info = "Weather: Not available"
                if hasattr(entry, 'weather_data') and entry.weather_data:
                    try:
                        weather = entry.weather_data
                        if isinstance(weather, dict):
                            temp = weather.get('temperature', 'N/A')
                            condition = weather.get('condition', 'Unknown')
                            weather_info = f"Weather: {temp}°F, {condition}"
                        else:
                            weather_info = f"Weather: {str(weather)[:30]}"
                    except Exception:
                        weather_info = "Weather: Error loading"
                
                self._ui_components['weather_label'].configure(text=weather_info)
            
        except Exception as e:
            logging.error(f"Error loading entry to editor: {e}")
    
    def _safe_new_entry(self):
        """Safely create a new entry."""
        try:
            # Clear current entry
            self.current_entry = None
            
            # Reset editor
            if 'title_var' in self._ui_components:
                self._ui_components['title_var'].set("New Entry")
            
            if 'date_label' in self._ui_components:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                self._ui_components['date_label'].configure(text=f"Created: {current_time}")
            
            if 'mood_var' in self._ui_components:
                self._ui_components['mood_var'].set("😐 Neutral")
            
            if 'tags_var' in self._ui_components:
                self._ui_components['tags_var'].set("")
            
            if 'content_text' in self._ui_components:
                self._ui_components['content_text'].delete("1.0", "end")
                placeholder = (
                    "Write about your day and how the weather affected your mood...\n\n"
                    "Tips:\n"
                    "• Describe the weather conditions you experienced\n"
                    "• Note how the weather made you feel\n"
                    "• Record any weather-related activities\n"
                    "• Add photos or observations"
                )
                self._ui_components['content_text'].insert("1.0", placeholder)
            
            if 'weather_label' in self._ui_components:
                self._ui_components['weather_label'].configure(text="Weather: Not loaded")
            
            self._update_status("New entry created")
            
        except Exception as e:
            logging.error(f"Error creating new entry: {e}")
            self._show_error("Failed to create new entry")
    
    def _safe_save_entry(self):
        """Safely save the current entry."""
        try:
            if not self.journal_service:
                self._show_error("Journal service not available")
                return
            
            # Get data from UI
            title = self._ui_components.get('title_var', ctk.StringVar()).get() or "Untitled Entry"
            mood = self._ui_components.get('mood_var', ctk.StringVar()).get() or "😐 Neutral"
            tags_str = self._ui_components.get('tags_var', ctk.StringVar()).get() or ""
            content = ""
            
            if 'content_text' in self._ui_components:
                content = self._ui_components['content_text'].get("1.0", "end-1c") or ""
            
            # Parse tags
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
            
            # Create or update entry
            if self.current_entry:
                # Update existing entry
                self.current_entry.title = title
                self.current_entry.content = content
                self.current_entry.mood = mood
                self.current_entry.tags = tags
                self.current_entry.updated_at = datetime.now()
                
                success = self.journal_service.update_entry(self.current_entry)
            else:
                # Create new entry
                entry_data = {
                    'title': title,
                    'content': content,
                    'mood': mood,
                    'tags': tags,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # Add current weather if available
                if self.weather_service:
                    try:
                        weather_data = self.weather_service.get_current_weather()
                        if weather_data:
                            entry_data['weather_data'] = weather_data
                    except Exception as e:
                        logging.warning(f"Could not add weather data: {e}")
                
                self.current_entry = self.journal_service.create_entry(entry_data)
                success = self.current_entry is not None
            
            if success:
                self._update_status("Entry saved successfully")
                self.load_entries()  # Refresh the list
            else:
                self._show_error("Failed to save entry")
                self._update_status("Save failed")
            
        except Exception as e:
            logging.error(f"Error saving entry: {e}")
            self._show_error("Failed to save entry")
            self._update_status("Save error")
    
    def _safe_delete_entry(self):
        """Safely delete the current entry."""
        try:
            if not self.current_entry:
                self._show_error("No entry selected to delete")
                return
            
            if not self.journal_service:
                self._show_error("Journal service not available")
                return
            
            # Confirm deletion
            title = getattr(self.current_entry, 'title', 'this entry') or 'this entry'
            if not messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete '{title}'?\n\nThis action cannot be undone.",
                parent=self
            ):
                return
            
            # Delete entry
            entry_id = getattr(self.current_entry, 'id', None)
            if entry_id and self.journal_service.delete_entry(entry_id):
                self._update_status("Entry deleted successfully")
                self.current_entry = None
                self._safe_new_entry()  # Reset editor
                self.load_entries()  # Refresh list
            else:
                self._show_error("Failed to delete entry")
                self._update_status("Delete failed")
            
        except Exception as e:
            logging.error(f"Error deleting entry: {e}")
            self._show_error("Failed to delete entry")
    
    def _safe_add_photo(self):
        """Safely add a photo to the current entry."""
        try:
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Photo",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                    ("All files", "*.*")
                ],
                parent=self
            )
            
            if not file_path:
                return
            
            # Add photo reference to content
            if 'content_text' in self._ui_components:
                current_content = self._ui_components['content_text'].get("1.0", "end-1c")
                photo_ref = f"\n\n[Photo: {file_path}]\n"
                self._ui_components['content_text'].insert("end", photo_ref)
            
            self._update_status(f"Photo added: {file_path.split('/')[-1]}")
            
        except Exception as e:
            logging.error(f"Error adding photo: {e}")
            self._show_error("Failed to add photo")
    
    def _safe_export_entry(self):
        """Safely export the current entry."""
        try:
            if not self.current_entry:
                self._show_error("No entry selected to export")
                return
            
            # Get export file path
            title = getattr(self.current_entry, 'title', 'entry') or 'entry'
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            default_name = f"{safe_title}.txt"
            
            file_path = filedialog.asksaveasfilename(
                title="Export Entry",
                defaultextension=".txt",
                initialvalue=default_name,
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                parent=self
            )
            
            if not file_path:
                return
            
            # Export entry
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {getattr(self.current_entry, 'title', 'Untitled')}\n")
                f.write(f"Date: {getattr(self.current_entry, 'created_at', 'Unknown')}\n")
                f.write(f"Mood: {getattr(self.current_entry, 'mood', 'Unknown')}\n")
                
                tags = getattr(self.current_entry, 'tags', [])
                if tags:
                    f.write(f"Tags: {', '.join(tags)}\n")
                
                f.write("\n" + "="*50 + "\n\n")
                f.write(getattr(self.current_entry, 'content', ''))
            
            self._update_status(f"Entry exported to {file_path}")
            
        except Exception as e:
            logging.error(f"Error exporting entry: {e}")
            self._show_error("Failed to export entry")
    
    def _safe_search(self, event=None):
        """Safely search entries."""
        try:
            if 'search_var' not in self._ui_components:
                return
            
            search_term = self._ui_components['search_var'].get().strip().lower()
            
            if not search_term:
                # Show all entries
                self._populate_entries_list(self.entries_cache)
                self._update_status(f"Showing all {len(self.entries_cache)} entries")
                return
            
            # Filter entries
            filtered_entries = []
            for entry in self.entries_cache:
                if not entry:
                    continue
                
                # Search in title, content, and tags
                title = getattr(entry, 'title', '') or ''
                content = getattr(entry, 'content', '') or ''
                tags = getattr(entry, 'tags', []) or []
                
                if (search_term in title.lower() or 
                    search_term in content.lower() or 
                    any(search_term in tag.lower() for tag in tags if isinstance(tag, str))):
                    filtered_entries.append(entry)
            
            self._populate_entries_list(filtered_entries)
            self._update_status(f"Found {len(filtered_entries)} entries matching '{search_term}'")
            
        except Exception as e:
            logging.error(f"Error searching entries: {e}")
            self._update_status("Search error")
    
    def _safe_refresh(self):
        """Safely refresh the entries list."""
        try:
            self.load_entries()
            
            # Clear search
            if 'search_var' in self._ui_components:
                self._ui_components['search_var'].set("")
            
        except Exception as e:
            logging.error(f"Error refreshing entries: {e}")
            self._show_error("Failed to refresh entries")
    
    def _update_status(self, message: str):
        """Safely update status bar."""
        try:
            if 'status_label' in self._ui_components and message:
                self._ui_components['status_label'].configure(text=str(message))
                
                # Auto-clear status after 5 seconds
                self.safe_after(5000, lambda: self._clear_status())
                
        except Exception as e:
            logging.error(f"Error updating status: {e}")
    
    def _clear_status(self):
        """Clear status message."""
        try:
            if 'status_label' in self._ui_components:
                self._ui_components['status_label'].configure(text="Ready")
        except Exception:
            pass
    
    def _show_error(self, message: str):
        """Show error message to user."""
        try:
            messagebox.showerror("Error", message, parent=self)
        except Exception as e:
            logging.error(f"Error showing error message: {e}")
    
    def _cleanup_callbacks(self, event=None):
        """Clean up callbacks and references."""
        try:
            # Clear UI components
            self._ui_components.clear()
            
            # Clear callbacks
            self._callbacks.clear()
            
            logging.debug("Journal tab cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
    
    def safe_after(self, delay: int, callback):
        """Safely schedule a callback with proper cleanup."""
        try:
            if not self.winfo_exists():
                return
            
            def safe_callback():
                try:
                    if self.winfo_exists() and callback:
                        callback()
                except Exception as e:
                    logging.error(f"Error in scheduled callback: {e}")
            
            after_id = self.after(delay, safe_callback)
            
            # Track for cleanup
            if hasattr(self, '_callbacks'):
                self._callbacks.add(after_id)
            
            return after_id
            
        except Exception as e:
            logging.error(f"Error scheduling callback: {e}")
            return None