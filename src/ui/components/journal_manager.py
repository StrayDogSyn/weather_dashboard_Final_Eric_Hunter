"""Weather Journal Manager Component

This module provides a comprehensive journal management interface that combines
the journal editor and list views with glassmorphic styling.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional

from services.journal_service import JournalService
from services.enhanced_weather_service import EnhancedWeatherService
from models.journal_entry import JournalEntry
from ui.theme import WeatherTheme
from ui.components.journal_editor import JournalEditor
from ui.components.journal_list import JournalList


class JournalManager(tk.Frame):
    """Comprehensive journal management interface with glassmorphic styling."""
    
    def __init__(self, parent, weather_service: EnhancedWeatherService, theme: WeatherTheme, **kwargs):
        """Initialize the journal manager.
        
        Args:
            parent: Parent widget
            weather_service: Weather service for data integration
            theme: Theme configuration
        """
        super().__init__(parent, **kwargs)
        
        self.weather_service = weather_service
        self.theme = theme
        
        # Initialize services
        self.journal_service = JournalService(weather_service=weather_service)
        
        # Current state
        self.current_entry: Optional[JournalEntry] = None
        self.is_editing = False
        
        # Configure glassmorphic styling
        self.configure(
            bg=theme.colors['glass_bg'],
            relief='flat',
            bd=0
        )
        
        self._setup_ui()
        self._setup_callbacks()
    
    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        # Configure main grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - Journal List
        self._create_list_panel()
        
        # Right panel - Journal Editor
        self._create_editor_panel()
        
        # Separator
        self._create_separator()
    
    def _create_list_panel(self) -> None:
        """Create the journal list panel."""
        # List container with glassmorphic effect
        list_container = tk.Frame(
            self,
            bg=self.theme.colors['glass_bg'],
            relief='flat',
            bd=1,
            highlightbackground=self.theme.colors['border'],
            highlightthickness=1
        )
        list_container.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(1, weight=1)
        
        # List header
        list_header = tk.Frame(
            list_container,
            bg=self.theme.colors['glass_bg'],
            height=50
        )
        list_header.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 0))
        list_header.grid_propagate(False)
        
        header_label = tk.Label(
            list_header,
            text="📖 Journal Entries",
            font=self.theme.fonts['heading'],
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['glass_bg']
        )
        header_label.pack(side='left', pady=10)
        
        # New entry button
        self.new_entry_btn = self._create_glass_button(
            list_header, "+ New Entry", self._create_new_entry,
            bg_color=self.theme.colors['accent']
        )
        self.new_entry_btn.pack(side='right', pady=10)
        
        # Journal list
        self.journal_list = JournalList(
            list_container,
            journal_service=self.journal_service,
            theme=self.theme
        )
        self.journal_list.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
    
    def _create_editor_panel(self) -> None:
        """Create the journal editor panel."""
        # Editor container with glassmorphic effect
        editor_container = tk.Frame(
            self,
            bg=self.theme.colors['glass_bg'],
            relief='flat',
            bd=1,
            highlightbackground=self.theme.colors['border'],
            highlightthickness=1
        )
        editor_container.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        editor_container.grid_columnconfigure(0, weight=1)
        editor_container.grid_rowconfigure(1, weight=1)
        
        # Editor header
        editor_header = tk.Frame(
            editor_container,
            bg=self.theme.colors['glass_bg'],
            height=50
        )
        editor_header.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 0))
        editor_header.grid_propagate(False)
        
        self.editor_title = tk.Label(
            editor_header,
            text="✏️ Create New Entry",
            font=self.theme.fonts['heading'],
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['glass_bg']
        )
        self.editor_title.pack(side='left', pady=10)
        
        # Editor action buttons
        action_frame = tk.Frame(editor_header, bg=self.theme.colors['glass_bg'])
        action_frame.pack(side='right', pady=10)
        
        self.save_btn = self._create_glass_button(
            action_frame, "💾 Save", self._save_entry,
            bg_color=self.theme.colors['success']
        )
        self.save_btn.pack(side='left', padx=2)
        
        self.cancel_btn = self._create_glass_button(
            action_frame, "❌ Cancel", self._cancel_editing,
            bg_color=self.theme.colors['error']
        )
        self.cancel_btn.pack(side='left', padx=2)
        
        # Journal editor
        self.journal_editor = JournalEditor(
            editor_container,
            journal_service=self.journal_service,
            theme=self.theme
        )
        self.journal_editor.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        
        # Initially disable editor
        self._set_editor_state(False)
    
    def _create_separator(self) -> None:
        """Create a visual separator between panels."""
        separator = tk.Frame(
            self,
            bg=self.theme.colors['border'],
            width=1
        )
        separator.grid(row=0, column=0, sticky='ns', padx=(0, 5))
    
    def _create_glass_button(self, parent: tk.Widget, text: str, command,
                           bg_color: str = None) -> tk.Button:
        """Create a glassmorphic styled button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            bg_color: Background color override
            
        Returns:
            Configured button widget
        """
        bg = bg_color or self.theme.colors['button_bg']
        
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=self.theme.fonts['small'],
            bg=bg,
            fg=self.theme.colors['text_primary'],
            activebackground=self.theme.colors['button_hover'],
            activeforeground=self.theme.colors['text_primary'],
            relief='flat',
            bd=0,
            padx=10,
            pady=5,
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
    
    def _setup_callbacks(self) -> None:
        """Setup callbacks between components."""
        # Journal list callbacks
        self.journal_list.set_on_entry_selected_callback(self._on_entry_selected)
        self.journal_list.set_on_entry_deleted_callback(self._on_entry_deleted)
        
        # Journal editor callbacks
        self.journal_editor.set_on_entry_saved_callback(self._on_entry_saved)
    
    def _create_new_entry(self) -> None:
        """Create a new journal entry."""
        self.current_entry = None
        self.is_editing = True
        
        # Update UI
        self.editor_title.configure(text="✏️ Create New Entry")
        self._set_editor_state(True)
        
        # Clear and setup editor for new entry
        self.journal_editor.clear_entry()
        self.journal_editor.auto_populate_weather()
        
        # Focus on editor
        self.journal_editor.focus_content()
    
    def _on_entry_selected(self, entry: JournalEntry) -> None:
        """Handle entry selection from the list.
        
        Args:
            entry: Selected journal entry
        """
        self.current_entry = entry
        self.is_editing = True
        
        # Update UI
        self.editor_title.configure(text=f"✏️ Edit Entry - {entry.date_created.strftime('%Y-%m-%d %H:%M')}")
        self._set_editor_state(True)
        
        # Load entry into editor
        self.journal_editor.load_entry(entry)
        
        # Focus on editor
        self.journal_editor.focus_content()
    
    def _on_entry_deleted(self, entry: JournalEntry) -> None:
        """Handle entry deletion.
        
        Args:
            entry: Deleted journal entry
        """
        # If the deleted entry was being edited, clear the editor
        if self.current_entry and self.current_entry.id == entry.id:
            self._cancel_editing()
    
    def _save_entry(self) -> None:
        """Save the current entry."""
        if not self.is_editing:
            return
        
        def save_operation():
            try:
                # Get entry data from editor
                entry_data = self.journal_editor.get_entry_data()
                
                if self.current_entry:
                    # Update existing entry
                    entry_data['id'] = self.current_entry.id
                    updated_entry = JournalEntry.from_dict(entry_data)
                    success = self.journal_service.update_entry(updated_entry)
                    
                    if success:
                        self.after(0, lambda: self._on_entry_saved(updated_entry, is_new=False))
                    else:
                        self.after(0, lambda: self._show_error("Failed to update entry"))
                else:
                    # Create new entry
                    new_entry = JournalEntry.from_dict(entry_data)
                    entry_id = self.journal_service.create_entry(new_entry)
                    
                    if entry_id:
                        new_entry.id = entry_id
                        self.after(0, lambda: self._on_entry_saved(new_entry, is_new=True))
                    else:
                        self.after(0, lambda: self._show_error("Failed to create entry"))
                        
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: self._show_error(f"Save error: {error_msg}"))
        
        # Show saving indicator
        original_text = self.save_btn.cget('text')
        self.save_btn.configure(text="💾 Saving...")
        self.save_btn.configure(state='disabled')
        
        # Perform save operation
        threading.Thread(target=save_operation, daemon=True).start()
    
    def _on_entry_saved(self, entry: JournalEntry, is_new: bool = True) -> None:
        """Handle successful entry save.
        
        Args:
            entry: Saved journal entry
            is_new: Whether this is a new entry
        """
        # Reset save button
        self.save_btn.configure(text="💾 Save")
        self.save_btn.configure(state='normal')
        
        # Update current entry reference
        self.current_entry = entry
        
        # Refresh the journal list
        self.journal_list.refresh()
        
        # Show success message
        action = "created" if is_new else "updated"
        messagebox.showinfo("Success", f"Journal entry {action} successfully!")
        
        # Keep editor open for further editing
        if is_new:
            self.editor_title.configure(text=f"✏️ Edit Entry - {entry.date_created.strftime('%Y-%m-%d %H:%M')}")
    
    def _cancel_editing(self) -> None:
        """Cancel current editing session."""
        if self.is_editing and self.journal_editor.has_unsaved_changes():
            result = messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to cancel?"
            )
            if not result:
                return
        
        # Reset state
        self.current_entry = None
        self.is_editing = False
        
        # Update UI
        self.editor_title.configure(text="✏️ Select an entry to edit")
        self._set_editor_state(False)
        
        # Clear editor
        self.journal_editor.clear_entry()
    
    def _set_editor_state(self, enabled: bool) -> None:
        """Enable or disable the editor interface.
        
        Args:
            enabled: Whether to enable the editor
        """
        state = 'normal' if enabled else 'disabled'
        
        # Update button states
        self.save_btn.configure(state=state)
        self.cancel_btn.configure(state=state)
        
        # Update editor state
        self.journal_editor.set_enabled(enabled)
    
    def _show_error(self, message: str) -> None:
        """Show error message.
        
        Args:
            message: Error message
        """
        # Reset save button if it was in saving state
        self.save_btn.configure(text="💾 Save")
        self.save_btn.configure(state='normal')
        
        messagebox.showerror("Error", message)
    
    def refresh(self) -> None:
        """Refresh the journal interface."""
        self.journal_list.refresh()
        
        # If not currently editing, clear the editor
        if not self.is_editing:
            self.journal_editor.clear_entry()
    
    def get_current_entry(self) -> Optional[JournalEntry]:
        """Get the currently selected/edited entry.
        
        Returns:
            Current journal entry or None
        """
        return self.current_entry
    
    def create_entry_with_weather(self, location: str = None) -> None:
        """Create a new entry with current weather data.
        
        Args:
            location: Location for weather data (optional)
        """
        self._create_new_entry()
        
        if location:
            self.journal_editor.set_location(location)
            self.journal_editor.auto_populate_weather()