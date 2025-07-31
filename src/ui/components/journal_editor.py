"""Weather Journal Editor Component

This module provides a rich text editor with glassmorphic styling for
creating and editing weather journal entries with Markdown support.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import asyncio
from datetime import datetime
from typing import Optional, Callable, Dict, Any
import re
from pathlib import Path

from services.journal_service import JournalService
from models.journal_entry import JournalEntry
from ..theme import WeatherTheme


class JournalEditor(tk.Frame):
    """Rich text editor for weather journal entries with glassmorphic styling."""
    
    def __init__(self, parent, journal_service: JournalService, theme: WeatherTheme, **kwargs):
        """Initialize the journal editor.
        
        Args:
            parent: Parent widget
            journal_service: Journal service for data operations
            theme: Theme configuration
        """
        super().__init__(parent, **kwargs)
        
        self.journal_service = journal_service
        self.theme = theme
        self.current_entry: Optional[JournalEntry] = None
        self.auto_save_timer: Optional[threading.Timer] = None
        self.is_modified = False
        self.on_entry_saved: Optional[Callable] = None
        
        # Configure glassmorphic styling
        self.configure(
            bg=theme.colors['glass_bg'],
            relief='flat',
            bd=0
        )
        
        self._setup_ui()
        self._setup_auto_save()
        self._setup_markdown_highlighting()
    
    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        # Main container with glassmorphic effect
        main_frame = tk.Frame(
            self,
            bg=self.theme.colors['glass_bg'],
            relief='flat',
            bd=0
        )
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header section
        self._create_header(main_frame)
        
        # Toolbar
        self._create_toolbar(main_frame)
        
        # Editor section
        self._create_editor(main_frame)
        
        # Footer with metadata
        self._create_footer(main_frame)
    
    def _create_header(self, parent: tk.Widget) -> None:
        """Create the header section with title and weather info."""
        header_frame = tk.Frame(
            parent,
            bg=self.theme.colors['glass_bg'],
            height=80
        )
        header_frame.pack(fill='x', pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title label
        self.title_label = tk.Label(
            header_frame,
            text="New Journal Entry",
            font=self.theme.fonts['heading'],
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['glass_bg']
        )
        self.title_label.pack(side='left', pady=10)
        
        # Weather info display
        self.weather_frame = tk.Frame(
            header_frame,
            bg=self.theme.colors['glass_bg']
        )
        self.weather_frame.pack(side='right', pady=10, padx=10)
        
        self.weather_label = tk.Label(
            self.weather_frame,
            text="Loading weather...",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        self.weather_label.pack()
    
    def _create_toolbar(self, parent: tk.Widget) -> None:
        """Create the toolbar with formatting and action buttons."""
        toolbar_frame = tk.Frame(
            parent,
            bg=self.theme.colors['glass_bg'],
            height=50
        )
        toolbar_frame.pack(fill='x', pady=(0, 10))
        toolbar_frame.pack_propagate(False)
        
        # Formatting buttons
        format_frame = tk.Frame(toolbar_frame, bg=self.theme.colors['glass_bg'])
        format_frame.pack(side='left', pady=5)
        
        # Bold button
        self.bold_btn = self._create_glass_button(
            format_frame, "B", self._toggle_bold,
            font=(self.theme.fonts['body'][0], 12, 'bold')
        )
        self.bold_btn.pack(side='left', padx=2)
        
        # Italic button
        self.italic_btn = self._create_glass_button(
            format_frame, "I", self._toggle_italic,
            font=(self.theme.fonts['body'][0], 12, 'italic')
        )
        self.italic_btn.pack(side='left', padx=2)
        
        # Header button
        self.header_btn = self._create_glass_button(
            format_frame, "H", self._insert_header
        )
        self.header_btn.pack(side='left', padx=2)
        
        # List button
        self.list_btn = self._create_glass_button(
            format_frame, "•", self._insert_list
        )
        self.list_btn.pack(side='left', padx=2)
        
        # Action buttons
        action_frame = tk.Frame(toolbar_frame, bg=self.theme.colors['glass_bg'])
        action_frame.pack(side='right', pady=5)
        
        # Save button
        self.save_btn = self._create_glass_button(
            action_frame, "Save", self._save_entry,
            width=80, bg_color=self.theme.colors['accent']
        )
        self.save_btn.pack(side='right', padx=5)
        
        # New button
        self.new_btn = self._create_glass_button(
            action_frame, "New", self._new_entry,
            width=60
        )
        self.new_btn.pack(side='right', padx=5)
    
    def _create_editor(self, parent: tk.Widget) -> None:
        """Create the main text editor with glassmorphic styling."""
        editor_frame = tk.Frame(
            parent,
            bg=self.theme.colors['glass_bg'],
            relief='flat',
            bd=1,
            highlightbackground=self.theme.colors['border'],
            highlightthickness=1
        )
        editor_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Text editor with scrollbar
        text_frame = tk.Frame(editor_frame, bg=self.theme.colors['glass_bg'])
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Text widget
        self.text_editor = tk.Text(
            text_frame,
            font=self.theme.fonts['body'],
            bg=self.theme.colors['input_bg'],
            fg=self.theme.colors['text_primary'],
            insertbackground=self.theme.colors['accent'],
            selectbackground=self.theme.colors['accent_light'],
            selectforeground=self.theme.colors['text_primary'],
            relief='flat',
            bd=0,
            wrap='word',
            yscrollcommand=scrollbar.set,
            padx=15,
            pady=15
        )
        self.text_editor.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=self.text_editor.yview)
        
        # Bind events
        self.text_editor.bind('<KeyRelease>', self._on_text_changed)
        self.text_editor.bind('<Button-1>', self._on_text_changed)
        self.text_editor.bind('<Control-s>', lambda e: self._save_entry())
        self.text_editor.bind('<Control-b>', lambda e: self._toggle_bold())
        self.text_editor.bind('<Control-i>', lambda e: self._toggle_italic())
    
    def _create_footer(self, parent: tk.Widget) -> None:
        """Create the footer with metadata inputs."""
        footer_frame = tk.Frame(
            parent,
            bg=self.theme.colors['glass_bg'],
            height=100
        )
        footer_frame.pack(fill='x')
        footer_frame.pack_propagate(False)
        
        # Left side - mood and location
        left_frame = tk.Frame(footer_frame, bg=self.theme.colors['glass_bg'])
        left_frame.pack(side='left', fill='y', padx=10, pady=10)
        
        # Mood rating
        mood_label = tk.Label(
            left_frame,
            text="Mood (1-10):",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        mood_label.pack(anchor='w')
        
        self.mood_var = tk.StringVar()
        self.mood_entry = tk.Entry(
            left_frame,
            textvariable=self.mood_var,
            font=self.theme.fonts['small'],
            bg=self.theme.colors['input_bg'],
            fg=self.theme.colors['text_primary'],
            relief='flat',
            bd=5,
            width=10
        )
        self.mood_entry.pack(anchor='w', pady=(2, 5))
        
        # Location
        location_label = tk.Label(
            left_frame,
            text="Location:",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        location_label.pack(anchor='w')
        
        self.location_var = tk.StringVar()
        self.location_entry = tk.Entry(
            left_frame,
            textvariable=self.location_var,
            font=self.theme.fonts['small'],
            bg=self.theme.colors['input_bg'],
            fg=self.theme.colors['text_primary'],
            relief='flat',
            bd=5,
            width=20
        )
        self.location_entry.pack(anchor='w', pady=(2, 0))
        
        # Right side - tags
        right_frame = tk.Frame(footer_frame, bg=self.theme.colors['glass_bg'])
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        tags_label = tk.Label(
            right_frame,
            text="Tags (comma-separated):",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        tags_label.pack(anchor='w')
        
        self.tags_var = tk.StringVar()
        self.tags_entry = tk.Entry(
            right_frame,
            textvariable=self.tags_var,
            font=self.theme.fonts['small'],
            bg=self.theme.colors['input_bg'],
            fg=self.theme.colors['text_primary'],
            relief='flat',
            bd=5
        )
        self.tags_entry.pack(fill='x', pady=(2, 0))
        
        # Status label
        self.status_label = tk.Label(
            footer_frame,
            text="Ready",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        self.status_label.pack(side='bottom', anchor='w', padx=10)
    
    def _create_glass_button(self, parent: tk.Widget, text: str, command: Callable,
                           width: int = 40, font: tuple = None, bg_color: str = None) -> tk.Button:
        """Create a glassmorphic styled button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            width: Button width
            font: Button font
            bg_color: Background color override
            
        Returns:
            Configured button widget
        """
        bg = bg_color or self.theme.colors['button_bg']
        
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=font or self.theme.fonts['small'],
            bg=bg,
            fg=self.theme.colors['text_primary'],
            activebackground=self.theme.colors['button_hover'],
            activeforeground=self.theme.colors['text_primary'],
            relief='flat',
            bd=0,
            width=width//8,  # Approximate character width
            cursor='hand2'
        )
        
        # Hover effects
        def on_enter(e):
            button.configure(bg=self.theme.colors['button_hover'])
        
        def on_leave(e):
            button.configure(bg=bg)
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
        
        return button
    
    def _setup_auto_save(self) -> None:
        """Setup auto-save functionality."""
        self.auto_save_interval = 30  # seconds
    
    def _setup_markdown_highlighting(self) -> None:
        """Setup basic Markdown syntax highlighting."""
        # Configure text tags for Markdown highlighting
        self.text_editor.tag_configure('bold', font=self.theme.fonts['body'] + ('bold',))
        self.text_editor.tag_configure('italic', font=self.theme.fonts['body'] + ('italic',))
        self.text_editor.tag_configure('header', 
                                     font=(self.theme.fonts['body'][0], 16, 'bold'),
                                     foreground=self.theme.colors['accent'])
        self.text_editor.tag_configure('code', 
                                     font=('Consolas', 10),
                                     background=self.theme.colors['code_bg'])
    
    def _on_text_changed(self, event=None) -> None:
        """Handle text change events."""
        self.is_modified = True
        self._update_status("Modified")
        self._schedule_auto_save()
        self._apply_markdown_highlighting()
    
    def _apply_markdown_highlighting(self) -> None:
        """Apply basic Markdown syntax highlighting."""
        content = self.text_editor.get('1.0', 'end-1c')
        
        # Clear existing tags
        for tag in ['bold', 'italic', 'header', 'code']:
            self.text_editor.tag_remove(tag, '1.0', 'end')
        
        # Apply highlighting patterns
        patterns = [
            (r'\*\*(.*?)\*\*', 'bold'),  # **bold**
            (r'\*(.*?)\*', 'italic'),     # *italic*
            (r'^#{1,6}\s+(.*?)$', 'header'),  # # headers
            (r'`(.*?)`', 'code'),         # `code`
        ]
        
        for pattern, tag in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.text_editor.tag_add(tag, start_idx, end_idx)
    
    def _schedule_auto_save(self) -> None:
        """Schedule auto-save after delay."""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        self.auto_save_timer = threading.Timer(
            self.auto_save_interval,
            self._auto_save
        )
        self.auto_save_timer.start()
    
    def _auto_save(self) -> None:
        """Perform auto-save operation."""
        if self.is_modified and self.current_entry:
            self._save_entry(auto_save=True)
    
    def _toggle_bold(self) -> None:
        """Toggle bold formatting for selected text."""
        try:
            selection = self.text_editor.get('sel.first', 'sel.last')
            if selection:
                # Wrap selection with bold markdown
                self.text_editor.delete('sel.first', 'sel.last')
                self.text_editor.insert('insert', f'**{selection}**')
        except tk.TclError:
            # No selection, insert bold markers
            self.text_editor.insert('insert', '****')
            # Move cursor between markers
            current = self.text_editor.index('insert')
            self.text_editor.mark_set('insert', f'{current}-2c')
    
    def _toggle_italic(self) -> None:
        """Toggle italic formatting for selected text."""
        try:
            selection = self.text_editor.get('sel.first', 'sel.last')
            if selection:
                # Wrap selection with italic markdown
                self.text_editor.delete('sel.first', 'sel.last')
                self.text_editor.insert('insert', f'*{selection}*')
        except tk.TclError:
            # No selection, insert italic markers
            self.text_editor.insert('insert', '**')
            # Move cursor between markers
            current = self.text_editor.index('insert')
            self.text_editor.mark_set('insert', f'{current}-1c')
    
    def _insert_header(self) -> None:
        """Insert header markdown."""
        self.text_editor.insert('insert', '# ')
    
    def _insert_list(self) -> None:
        """Insert list item markdown."""
        self.text_editor.insert('insert', '- ')
    
    def _new_entry(self) -> None:
        """Create a new journal entry."""
        if self.is_modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Save before creating new entry?"
            )
            if result is True:
                self._save_entry()
            elif result is None:
                return
        
        self._clear_editor()
        self._load_current_weather()
    
    def _save_entry(self, auto_save: bool = False) -> None:
        """Save the current journal entry.
        
        Args:
            auto_save: Whether this is an auto-save operation
        """
        try:
            content = self.text_editor.get('1.0', 'end-1c').strip()
            if not content:
                if not auto_save:
                    messagebox.showwarning("Empty Entry", "Cannot save empty journal entry.")
                return
            
            # Get metadata
            mood_rating = None
            if self.mood_var.get().strip():
                try:
                    mood_rating = int(self.mood_var.get())
                    if not 1 <= mood_rating <= 10:
                        raise ValueError("Mood rating must be between 1 and 10")
                except ValueError as e:
                    if not auto_save:
                        messagebox.showerror("Invalid Mood", str(e))
                    return
            
            location = self.location_var.get().strip() or None
            tags = [tag.strip().lower() for tag in self.tags_var.get().split(',') if tag.strip()]
            
            # Create or update entry
            if self.current_entry is None:
                # Create new entry
                def create_entry():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        entry = loop.run_until_complete(
                            self.journal_service.create_entry(
                                content=content,
                                mood_rating=mood_rating,
                                tags=tags,
                                location=location
                            )
                        )
                        self.current_entry = entry
                        self.is_modified = False
                        
                        # Update UI on main thread
                        def on_saved_callback():
                            self._on_entry_saved(auto_save)
                        self.after(0, on_saved_callback)
                    except Exception as e:
                        def on_error_callback():
                            self._on_save_error(str(e), auto_save)
                        self.after(0, on_error_callback)
                    finally:
                        loop.close()
                
                threading.Thread(target=create_entry, daemon=True).start()
            else:
                # Update existing entry
                self.current_entry.entry_content = content
                self.current_entry.mood_rating = mood_rating
                self.current_entry.tags = tags
                self.current_entry.location = location
                
                def update_entry():
                    try:
                        success = self.journal_service.update_entry(self.current_entry)
                        if success:
                            self.is_modified = False
                            def on_saved_callback():
                                self._on_entry_saved(auto_save)
                            self.after(0, on_saved_callback)
                        else:
                            def on_error_callback():
                                self._on_save_error("Failed to update entry", auto_save)
                            self.after(0, on_error_callback)
                    except Exception as e:
                        def on_error_callback():
                            self._on_save_error(str(e), auto_save)
                        self.after(0, on_error_callback)
                
                threading.Thread(target=update_entry, daemon=True).start()
                
        except Exception as e:
            if not auto_save:
                messagebox.showerror("Save Error", f"Failed to save entry: {e}")
    
    def _on_entry_saved(self, auto_save: bool) -> None:
        """Handle successful entry save.
        
        Args:
            auto_save: Whether this was an auto-save operation
        """
        status = "Auto-saved" if auto_save else "Saved"
        self._update_status(status)
        
        if self.current_entry:
            self.title_label.configure(text=f"Entry - {self.current_entry.date_created.strftime('%Y-%m-%d %H:%M')}")
        
        if self.on_entry_saved:
            self.on_entry_saved(self.current_entry)
    
    def _on_save_error(self, error: str, auto_save: bool) -> None:
        """Handle save error.
        
        Args:
            error: Error message
            auto_save: Whether this was an auto-save operation
        """
        self._update_status(f"Save failed: {error}")
        if not auto_save:
            messagebox.showerror("Save Error", f"Failed to save entry: {error}")
    
    def _clear_editor(self) -> None:
        """Clear the editor and reset state."""
        self.text_editor.delete('1.0', 'end')
        self.mood_var.set('')
        self.location_var.set('')
        self.tags_var.set('')
        self.current_entry = None
        self.is_modified = False
        self.title_label.configure(text="New Journal Entry")
        self._update_status("Ready")
    
    def _load_current_weather(self) -> None:
        """Load current weather information."""
        def get_weather():
            try:
                if self.journal_service.weather_service:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        weather = loop.run_until_complete(
                            self.journal_service.weather_service.get_current_weather()
                        )
                        if weather:
                            weather_text = f"{weather.get('condition', 'Unknown')}, {weather.get('temperature', 'N/A')}°F"
                            def update_weather_text():
                                self.weather_label.configure(text=weather_text)
                            self.after(0, update_weather_text)
                        else:
                            def update_weather_unavailable():
                                self.weather_label.configure(text="Weather unavailable")
                            self.after(0, update_weather_unavailable)
                    finally:
                        loop.close()
                else:
                    def update_weather_service_unavailable():
                        self.weather_label.configure(text="Weather service unavailable")
                    self.after(0, update_weather_service_unavailable)
            except Exception as e:
                def update_weather_error():
                    self.weather_label.configure(text="Weather error")
                self.after(0, update_weather_error)
        
        threading.Thread(target=get_weather, daemon=True).start()
    
    def _update_status(self, status: str) -> None:
        """Update status label.
        
        Args:
            status: Status message
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_label.configure(text=f"{status} - {timestamp}")
    
    def load_entry(self, entry: JournalEntry) -> None:
        """Load an existing journal entry for editing.
        
        Args:
            entry: Journal entry to load
        """
        self.current_entry = entry
        
        # Load content
        self.text_editor.delete('1.0', 'end')
        self.text_editor.insert('1.0', entry.entry_content)
        
        # Load metadata
        self.mood_var.set(str(entry.mood_rating) if entry.mood_rating else '')
        self.location_var.set(entry.location or '')
        self.tags_var.set(', '.join(entry.tags))
        
        # Update UI
        self.title_label.configure(text=f"Entry - {entry.date_created.strftime('%Y-%m-%d %H:%M')}")
        
        # Load weather info
        if entry.has_weather_data():
            weather_summary = entry.get_weather_summary()
            self.weather_label.configure(text=weather_summary)
        else:
            self.weather_label.configure(text="No weather data")
        
        self.is_modified = False
        self._update_status("Loaded")
        self._apply_markdown_highlighting()
    
    def set_on_entry_saved_callback(self, callback: Callable) -> None:
        """Set callback for when entry is saved.
        
        Args:
            callback: Callback function
        """
        self.on_entry_saved = callback
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the editor interface.
        
        Args:
            enabled: Whether to enable the editor
        """
        state = 'normal' if enabled else 'disabled'
        
        # Enable/disable text widget
        if hasattr(self, 'text_widget'):
            self.text_widget.configure(state=state)
        
        # Enable/disable buttons
        for widget in self.winfo_children():
            if isinstance(widget, (tk.Button, ttk.Button)):
                widget.configure(state=state)
            elif hasattr(widget, 'winfo_children'):
                # Recursively enable/disable child widgets
                for child in widget.winfo_children():
                    if isinstance(child, (tk.Button, ttk.Button)):
                        child.configure(state=state)
    
    def clear_entry(self) -> None:
        """Clear the editor and reset state."""
        self._clear_editor()
    
    def focus_content(self) -> None:
        """Focus on the content text editor."""
        if hasattr(self, 'text_editor'):
            self.text_editor.focus_set()
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes.
        
        Returns:
            True if there are unsaved changes, False otherwise
        """
        return self.is_modified
    
    def get_entry_data(self) -> Dict[str, Any]:
        """Get current entry data from the editor.
        
        Returns:
            Dictionary containing entry data
        """
        content = self.text_editor.get('1.0', 'end-1c').strip()
        mood_rating = None
        try:
            mood_str = self.mood_var.get().strip()
            if mood_str:
                mood_rating = int(mood_str)
        except (ValueError, AttributeError):
            pass
        
        tags = []
        try:
            tags_str = self.tags_var.get().strip()
            if tags_str:
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        except AttributeError:
            pass
        
        location = ''
        try:
            location = self.location_var.get().strip()
        except AttributeError:
            pass
        
        return {
            'entry_content': content,
            'mood_rating': mood_rating,
            'tags': tags,
            'location': location,
            'date_created': datetime.now()
        }
    
    def auto_populate_weather(self) -> None:
        """Auto-populate weather information for new entries."""
        self._load_current_weather()