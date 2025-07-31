"""Weather Journal List Component

This module provides a list view for weather journal entries with
glassmorphic styling, search functionality, and entry management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Callable

from services.journal_service import JournalService
from models.journal_entry import JournalEntry
from ui.theme import WeatherTheme


class JournalList(tk.Frame):
    """List view for weather journal entries with glassmorphic styling."""
    
    def __init__(self, parent, journal_service: JournalService, theme: WeatherTheme, **kwargs):
        """Initialize the journal list.
        
        Args:
            parent: Parent widget
            journal_service: Journal service for data operations
            theme: Theme configuration
        """
        super().__init__(parent, **kwargs)
        
        self.journal_service = journal_service
        self.theme = theme
        self.entries: List[JournalEntry] = []
        self.filtered_entries: List[JournalEntry] = []
        self.selected_entry: Optional[JournalEntry] = None
        self.on_entry_selected: Optional[Callable] = None
        self.on_entry_deleted: Optional[Callable] = None
        
        # Configure glassmorphic styling
        self.configure(
            bg=theme.colors['glass_bg'],
            relief='flat',
            bd=0
        )
        
        self._setup_ui()
        self._load_entries()
    
    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        # Main container
        main_frame = tk.Frame(
            self,
            bg=self.theme.colors['glass_bg'],
            relief='flat',
            bd=0
        )
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header with search
        self._create_header(main_frame)
        
        # Entry list
        self._create_entry_list(main_frame)
        
        # Footer with statistics
        self._create_footer(main_frame)
    
    def _create_header(self, parent: tk.Widget) -> None:
        """Create the header with search functionality."""
        header_frame = tk.Frame(
            parent,
            bg=self.theme.colors['glass_bg'],
            height=80
        )
        header_frame.pack(fill='x', pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="Journal Entries",
            font=self.theme.fonts['heading'],
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['glass_bg']
        )
        title_label.pack(side='left', pady=10)
        
        # Search frame
        search_frame = tk.Frame(header_frame, bg=self.theme.colors['glass_bg'])
        search_frame.pack(side='right', pady=10, padx=10)
        
        search_label = tk.Label(
            search_frame,
            text="Search:",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        search_label.pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=self.theme.fonts['small'],
            bg=self.theme.colors['input_bg'],
            fg=self.theme.colors['text_primary'],
            relief='flat',
            bd=5,
            width=20
        )
        self.search_entry.pack(side='left')
        
        # Refresh button
        self.refresh_btn = self._create_glass_button(
            search_frame, "↻", self._refresh_entries,
            width=30
        )
        self.refresh_btn.pack(side='left', padx=(5, 0))
    
    def _create_entry_list(self, parent: tk.Widget) -> None:
        """Create the scrollable entry list."""
        # List container with glassmorphic effect
        list_frame = tk.Frame(
            parent,
            bg=self.theme.colors['glass_bg'],
            relief='flat',
            bd=1,
            highlightbackground=self.theme.colors['border'],
            highlightthickness=1
        )
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Scrollable frame setup
        canvas = tk.Canvas(
            list_frame,
            bg=self.theme.colors['glass_bg'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.theme.colors['glass_bg'])
        
        self.scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        
        canvas.bind('<MouseWheel>', _on_mousewheel)
        self.scrollable_frame.bind('<MouseWheel>', _on_mousewheel)
    
    def _create_footer(self, parent: tk.Widget) -> None:
        """Create the footer with statistics."""
        footer_frame = tk.Frame(
            parent,
            bg=self.theme.colors['glass_bg'],
            height=40
        )
        footer_frame.pack(fill='x')
        footer_frame.pack_propagate(False)
        
        # Statistics label
        self.stats_label = tk.Label(
            footer_frame,
            text="Loading...",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        self.stats_label.pack(side='left', pady=10, padx=10)
        
        # Mood statistics
        self.mood_label = tk.Label(
            footer_frame,
            text="",
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['glass_bg']
        )
        self.mood_label.pack(side='right', pady=10, padx=10)
    
    def _create_glass_button(self, parent: tk.Widget, text: str, command: Callable,
                           width: int = 40, bg_color: str = None) -> tk.Button:
        """Create a glassmorphic styled button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            width: Button width
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
            width=width//8,
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
    
    def _create_entry_card(self, entry: JournalEntry) -> tk.Frame:
        """Create a glassmorphic card for a journal entry.
        
        Args:
            entry: Journal entry to display
            
        Returns:
            Entry card frame
        """
        # Card frame with glassmorphic styling
        card = tk.Frame(
            self.scrollable_frame,
            bg=self.theme.colors['card_bg'],
            relief='flat',
            bd=1,
            highlightbackground=self.theme.colors['border'],
            highlightthickness=1
        )
        card.pack(fill='x', padx=5, pady=3)
        
        # Card content
        content_frame = tk.Frame(card, bg=self.theme.colors['card_bg'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=8)
        
        # Header row
        header_frame = tk.Frame(content_frame, bg=self.theme.colors['card_bg'])
        header_frame.pack(fill='x', pady=(0, 5))
        
        # Date and time
        date_label = tk.Label(
            header_frame,
            text=entry.date_created.strftime('%Y-%m-%d %H:%M'),
            font=self.theme.fonts['small_bold'],
            fg=self.theme.colors['text_primary'],
            bg=self.theme.colors['card_bg']
        )
        date_label.pack(side='left')
        
        # Mood indicator
        if entry.mood_rating:
            mood_text = f"😊 {entry.mood_rating}/10"
            mood_label = tk.Label(
                header_frame,
                text=mood_text,
                font=self.theme.fonts['small'],
                fg=self.theme.colors['accent'],
                bg=self.theme.colors['card_bg']
            )
            mood_label.pack(side='right')
        
        # Content preview
        preview_text = entry.get_preview(80)
        preview_label = tk.Label(
            content_frame,
            text=preview_text,
            font=self.theme.fonts['small'],
            fg=self.theme.colors['text_secondary'],
            bg=self.theme.colors['card_bg'],
            wraplength=400,
            justify='left',
            anchor='w'
        )
        preview_label.pack(fill='x', pady=(0, 5))
        
        # Footer row
        footer_frame = tk.Frame(content_frame, bg=self.theme.colors['card_bg'])
        footer_frame.pack(fill='x')
        
        # Tags
        if entry.tags:
            tags_text = ' '.join([f'#{tag}' for tag in entry.tags[:3]])
            if len(entry.tags) > 3:
                tags_text += f' +{len(entry.tags) - 3} more'
            
            tags_label = tk.Label(
                footer_frame,
                text=tags_text,
                font=self.theme.fonts['small'],
                fg=self.theme.colors['accent_light'],
                bg=self.theme.colors['card_bg']
            )
            tags_label.pack(side='left')
        
        # Weather indicator
        if entry.has_weather_data():
            weather_text = "🌤️ " + entry.get_weather_summary()[:20] + "..."
            weather_label = tk.Label(
                footer_frame,
                text=weather_text,
                font=self.theme.fonts['small'],
                fg=self.theme.colors['text_secondary'],
                bg=self.theme.colors['card_bg']
            )
            weather_label.pack(side='left', padx=(10, 0))
        
        # Action buttons
        action_frame = tk.Frame(footer_frame, bg=self.theme.colors['card_bg'])
        action_frame.pack(side='right')
        
        # Edit button
        edit_btn = self._create_glass_button(
            action_frame, "Edit", lambda: self._select_entry(entry),
            width=40, bg_color=self.theme.colors['accent']
        )
        edit_btn.pack(side='left', padx=2)
        
        # Delete button
        delete_btn = self._create_glass_button(
            action_frame, "Delete", lambda: self._delete_entry(entry),
            width=50, bg_color=self.theme.colors['error']
        )
        delete_btn.pack(side='left', padx=2)
        
        # Click to select
        def on_card_click(event):
            self._select_entry(entry)
        
        # Bind click events to all card components
        for widget in [card, content_frame, header_frame, footer_frame, 
                      date_label, preview_label]:
            widget.bind('<Button-1>', on_card_click)
        
        # Hover effects
        def on_enter(event):
            card.configure(bg=self.theme.colors['card_hover'])
            content_frame.configure(bg=self.theme.colors['card_hover'])
            header_frame.configure(bg=self.theme.colors['card_hover'])
            footer_frame.configure(bg=self.theme.colors['card_hover'])
            action_frame.configure(bg=self.theme.colors['card_hover'])
        
        def on_leave(event):
            card.configure(bg=self.theme.colors['card_bg'])
            content_frame.configure(bg=self.theme.colors['card_bg'])
            header_frame.configure(bg=self.theme.colors['card_bg'])
            footer_frame.configure(bg=self.theme.colors['card_bg'])
            action_frame.configure(bg=self.theme.colors['card_bg'])
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        return card
    
    def _load_entries(self) -> None:
        """Load journal entries from the service."""
        def load_data():
            try:
                entries = self.journal_service.get_entries(limit=100)
                # Check if widget is still valid before scheduling UI update
                try:
                    self.after(0, lambda: self._update_entries(entries))
                except RuntimeError:
                    # Widget may have been destroyed or main loop not running
                    pass
            except Exception as e:
                error_msg = str(e)
                try:
                    self.after(0, lambda: self._show_error(f"Failed to load entries: {error_msg}"))
                except RuntimeError:
                    # Widget may have been destroyed or main loop not running
                    print(f"Failed to load journal entries: {error_msg}")
        
        # Only start the thread if the widget is properly initialized
        try:
            threading.Thread(target=load_data, daemon=True).start()
        except Exception:
            # Fallback: load entries directly if threading fails
            try:
                entries = self.journal_service.get_entries(limit=100)
                self._update_entries(entries)
            except Exception as e:
                self._show_error(f"Failed to load entries: {e}")
    
    def _update_entries(self, entries: List[JournalEntry]) -> None:
        """Update the entry list display.
        
        Args:
            entries: List of journal entries
        """
        self.entries = entries
        self.filtered_entries = entries.copy()
        self._refresh_display()
        self._update_statistics()
    
    def _refresh_display(self) -> None:
        """Refresh the entry list display."""
        # Clear existing cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Create cards for filtered entries
        if not self.filtered_entries:
            # Show empty state
            empty_label = tk.Label(
                self.scrollable_frame,
                text="No journal entries found.\nCreate your first entry to get started!",
                font=self.theme.fonts['body'],
                fg=self.theme.colors['text_secondary'],
                bg=self.theme.colors['glass_bg'],
                justify='center'
            )
            empty_label.pack(expand=True, pady=50)
        else:
            for entry in self.filtered_entries:
                self._create_entry_card(entry)
    
    def _update_statistics(self) -> None:
        """Update the statistics display."""
        total_entries = len(self.entries)
        filtered_count = len(self.filtered_entries)
        
        if total_entries == 0:
            self.stats_label.configure(text="No entries")
            self.mood_label.configure(text="")
            return
        
        # Basic statistics
        if filtered_count != total_entries:
            stats_text = f"Showing {filtered_count} of {total_entries} entries"
        else:
            stats_text = f"{total_entries} entries"
        
        self.stats_label.configure(text=stats_text)
        
        # Mood statistics
        def load_mood_stats():
            try:
                mood_stats = self.journal_service.get_mood_statistics()
                if mood_stats.get('average_mood'):
                    mood_text = f"Avg mood: {mood_stats['average_mood']}/10"
                    self.after(0, lambda: self.mood_label.configure(text=mood_text))
                else:
                    self.after(0, lambda: self.mood_label.configure(text=""))
            except Exception:
                self.after(0, lambda: self.mood_label.configure(text=""))
        
        threading.Thread(target=load_mood_stats, daemon=True).start()
    
    def _on_search_changed(self, *args) -> None:
        """Handle search text changes."""
        search_term = self.search_var.get().strip().lower()
        
        if not search_term:
            self.filtered_entries = self.entries.copy()
        else:
            # Filter entries by content, tags, and location
            self.filtered_entries = [
                entry for entry in self.entries
                if (search_term in entry.entry_content.lower() or
                    any(search_term in tag.lower() for tag in entry.tags) or
                    (entry.location and search_term in entry.location.lower()))
            ]
        
        self._refresh_display()
        self._update_statistics()
    
    def _select_entry(self, entry: JournalEntry) -> None:
        """Select an entry for editing.
        
        Args:
            entry: Entry to select
        """
        self.selected_entry = entry
        if self.on_entry_selected:
            self.on_entry_selected(entry)
    
    def _delete_entry(self, entry: JournalEntry) -> None:
        """Delete a journal entry.
        
        Args:
            entry: Entry to delete
        """
        result = messagebox.askyesno(
            "Delete Entry",
            f"Are you sure you want to delete the entry from {entry.date_created.strftime('%Y-%m-%d %H:%M')}?\n\nThis action cannot be undone."
        )
        
        if result:
            def delete_entry():
                try:
                    success = self.journal_service.delete_entry(entry.id)
                    if success:
                        self.after(0, lambda: self._on_entry_deleted(entry))
                    else:
                        self.after(0, lambda: self._show_error("Failed to delete entry"))
                except Exception as e:
                    self.after(0, lambda: self._show_error(f"Delete error: {e}"))
            
            threading.Thread(target=delete_entry, daemon=True).start()
    
    def _on_entry_deleted(self, entry: JournalEntry) -> None:
        """Handle successful entry deletion.
        
        Args:
            entry: Deleted entry
        """
        # Remove from local lists
        if entry in self.entries:
            self.entries.remove(entry)
        if entry in self.filtered_entries:
            self.filtered_entries.remove(entry)
        
        # Refresh display
        self._refresh_display()
        self._update_statistics()
        
        # Notify callback
        if self.on_entry_deleted:
            self.on_entry_deleted(entry)
    
    def _refresh_entries(self) -> None:
        """Refresh entries from the database."""
        self._load_entries()
    
    def _show_error(self, message: str) -> None:
        """Show error message.
        
        Args:
            message: Error message
        """
        messagebox.showerror("Error", message)
    
    def refresh(self) -> None:
        """Public method to refresh the entry list."""
        self._refresh_entries()
    
    def set_on_entry_selected_callback(self, callback: Callable) -> None:
        """Set callback for when entry is selected.
        
        Args:
            callback: Callback function
        """
        self.on_entry_selected = callback
    
    def set_on_entry_deleted_callback(self, callback: Callable) -> None:
        """Set callback for when entry is deleted.
        
        Args:
            callback: Callback function
        """
        self.on_entry_deleted = callback