#!/usr/bin/env python3
"""
Weather Journal Tabbed Interface - Glassmorphic tabbed container

This module provides a sophisticated tabbed interface with:
- Glassmorphic tab styling
- Smooth animations
- Write, Browse, Analytics, and Search tabs
- Professional layout and navigation
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, List, Optional, Callable
from datetime import datetime

from ...utils.logger import LoggerMixin
from ...ui.components.glass import (
    GlassFrame, GlassButton, GlassLabel, 
    ComponentSize, create_glass_card
)
from .rich_text_editor import MarkdownEditor
from .photo_manager import PhotoGalleryWidget, PhotoManager
from .database import JournalDatabase
from .models import JournalEntry


class GlassmorphicTab:
    """
    Represents a single tab in the glassmorphic interface.
    """
    
    def __init__(self, name: str, icon: str, content_widget: tk.Widget, tooltip: str = None):
        self.name = name
        self.icon = icon
        self.content_widget = content_widget
        self.tooltip = tooltip or name
        self.is_active = False
        self.button = None


class TabbedJournalInterface(GlassFrame, LoggerMixin):
    """
    Main tabbed interface for the weather journal.
    
    Features:
    - Write tab with rich text editor
    - Browse tab with entry cards
    - Analytics tab with data visualization
    - Search tab with advanced filtering
    """
    
    def __init__(self, parent, database: JournalDatabase, photo_manager: PhotoManager, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.database = database
        self.photo_manager = photo_manager
        self.current_tab = None
        self.tabs = {}
        self.tab_buttons = {}
        
        # Current entry state
        self.current_entry = None
        self.is_editing = False
        
        self._setup_ui()
        self._create_tabs()
        self._switch_to_tab('write')
        
        self.logger.info("Tabbed Journal Interface initialized")
    
    def _setup_ui(self):
        """Setup the main interface structure."""
        # Tab bar
        self.tab_bar = self._create_tab_bar()
        self.tab_bar.pack(fill="x", padx=10, pady=(10, 5))
        
        # Content area
        self.content_area = GlassFrame(self)
        self.content_area.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _create_tab_bar(self) -> GlassFrame:
        """Create the glassmorphic tab bar."""
        tab_bar = GlassFrame(self)
        
        # Tab definitions
        tab_definitions = [
            ('write', '✏️', 'Write', 'Create new journal entries'),
            ('browse', '📖', 'Browse', 'Browse existing entries'),
            ('analytics', '📊', 'Analytics', 'View analytics and insights'),
            ('search', '🔍', 'Search', 'Search and filter entries')
        ]
        
        for tab_id, icon, name, tooltip in tab_definitions:
            button = GlassButton(
                tab_bar,
                text=f"{icon} {name}",
                command=lambda t=tab_id: self._switch_to_tab(t),
                size=ComponentSize.MEDIUM,
                width=120,
                height=40
            )
            button.pack(side="left", padx=5, pady=5)
            
            self.tab_buttons[tab_id] = button
            self._add_tooltip(button, tooltip)
        
        # Spacer
        spacer = tk.Frame(tab_bar, bg="transparent")
        spacer.pack(side="left", fill="x", expand=True)
        
        # Action buttons
        self.action_buttons = self._create_action_buttons(tab_bar)
        
        return tab_bar
    
    def _create_action_buttons(self, parent) -> Dict[str, GlassButton]:
        """Create action buttons for the tab bar."""
        buttons = {}
        
        # Save button
        buttons['save'] = GlassButton(
            parent,
            text="💾 Save",
            command=self._save_current_entry,
            size=ComponentSize.SMALL,
            width=80
        )
        buttons['save'].pack(side="right", padx=5, pady=5)
        
        # New entry button
        buttons['new'] = GlassButton(
            parent,
            text="➕ New",
            command=self._create_new_entry,
            size=ComponentSize.SMALL,
            width=80
        )
        buttons['new'].pack(side="right", padx=5, pady=5)
        
        return buttons
    
    def _create_tabs(self):
        """Create all tab content widgets."""
        # Write tab
        self.tabs['write'] = GlassmorphicTab(
            name="Write",
            icon="✏️",
            content_widget=self._create_write_tab(),
            tooltip="Create and edit journal entries"
        )
        
        # Browse tab
        self.tabs['browse'] = GlassmorphicTab(
            name="Browse",
            icon="📖",
            content_widget=self._create_browse_tab(),
            tooltip="Browse and manage existing entries"
        )
        
        # Analytics tab
        self.tabs['analytics'] = GlassmorphicTab(
            name="Analytics",
            icon="📊",
            content_widget=self._create_analytics_tab(),
            tooltip="View analytics and insights"
        )
        
        # Search tab
        self.tabs['search'] = GlassmorphicTab(
            name="Search",
            icon="🔍",
            content_widget=self._create_search_tab(),
            tooltip="Search and filter entries"
        )
    
    def _create_write_tab(self) -> GlassFrame:
        """Create the write tab content."""
        write_frame = GlassFrame(self.content_area)
        
        # Entry metadata section
        metadata_frame = self._create_metadata_section(write_frame)
        metadata_frame.pack(fill="x", padx=10, pady=5)
        
        # Main editor area
        editor_frame = GlassFrame(write_frame)
        editor_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Rich text editor
        self.markdown_editor = MarkdownEditor(
            editor_frame,
            on_content_change=self._on_content_change
        )
        self.markdown_editor.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Photo gallery
        self.photo_gallery = PhotoGalleryWidget(
            write_frame,
            self.photo_manager
        )
        self.photo_gallery.pack(fill="x", padx=10, pady=5)
        
        return write_frame
    
    def _create_metadata_section(self, parent) -> GlassFrame:
        """Create the entry metadata section."""
        metadata_frame = create_glass_card(parent)
        
        # Title section
        title_frame = GlassFrame(metadata_frame)
        title_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = GlassLabel(
            title_frame,
            text="📝 Title:",
            font=("Segoe UI", 12, "bold")
        )
        title_label.pack(side="left", padx=(0, 10))
        
        self.title_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="Enter journal entry title...",
            font=("Segoe UI", 12),
            height=35
        )
        self.title_entry.pack(side="left", fill="x", expand=True)
        
        # Metadata row
        meta_row = GlassFrame(metadata_frame)
        meta_row.pack(fill="x", padx=10, pady=5)
        
        # Mood selection
        mood_frame = GlassFrame(meta_row)
        mood_frame.pack(side="left", padx=(0, 20))
        
        mood_label = GlassLabel(
            mood_frame,
            text="😊 Mood:",
            font=("Segoe UI", 10, "bold")
        )
        mood_label.pack(side="top", anchor="w")
        
        self.mood_var = tk.StringVar(value="neutral")
        self.mood_combo = ctk.CTkComboBox(
            mood_frame,
            values=["very_happy", "happy", "neutral", "sad", "very_sad"],
            variable=self.mood_var,
            width=120
        )
        self.mood_combo.pack(side="top")
        
        # Category selection
        category_frame = GlassFrame(meta_row)
        category_frame.pack(side="left", padx=(0, 20))
        
        category_label = GlassLabel(
            category_frame,
            text="📁 Category:",
            font=("Segoe UI", 10, "bold")
        )
        category_label.pack(side="top", anchor="w")
        
        self.category_var = tk.StringVar()
        self.category_combo = ctk.CTkComboBox(
            category_frame,
            values=self._get_categories(),
            variable=self.category_var,
            width=120
        )
        self.category_combo.pack(side="top")
        
        # Weather info (auto-populated)
        weather_frame = GlassFrame(meta_row)
        weather_frame.pack(side="left", padx=(0, 20))
        
        weather_label = GlassLabel(
            weather_frame,
            text="🌤️ Weather:",
            font=("Segoe UI", 10, "bold")
        )
        weather_label.pack(side="top", anchor="w")
        
        self.weather_label = GlassLabel(
            weather_frame,
            text="Loading...",
            font=("Segoe UI", 9)
        )
        self.weather_label.pack(side="top")
        
        # Auto-populate weather
        self._load_current_weather()
        
        return metadata_frame
    
    def _create_browse_tab(self) -> GlassFrame:
        """Create the browse tab content."""
        browse_frame = GlassFrame(self.content_area)
        
        # Header with filters
        header_frame = create_glass_card(browse_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        header_label = GlassLabel(
            header_frame,
            text="📖 Browse Journal Entries",
            font=("Segoe UI", 16, "bold")
        )
        header_label.pack(side="left", padx=10, pady=10)
        
        # Filter controls
        filter_frame = GlassFrame(header_frame)
        filter_frame.pack(side="right", padx=10, pady=10)
        
        # Date filter
        date_label = GlassLabel(filter_frame, text="📅 Filter:")
        date_label.pack(side="left", padx=(0, 5))
        
        self.date_filter = ctk.CTkComboBox(
            filter_frame,
            values=["All Time", "Today", "This Week", "This Month", "This Year"],
            command=self._filter_entries
        )
        self.date_filter.pack(side="left", padx=5)
        
        # Entries list
        self.entries_frame = ctk.CTkScrollableFrame(
            browse_frame,
            fg_color="transparent"
        )
        self.entries_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Load entries
        self._load_entries_list()
        
        return browse_frame
    
    def _create_analytics_tab(self) -> GlassFrame:
        """Create the analytics tab content."""
        analytics_frame = GlassFrame(self.content_area)
        
        # Header
        header = GlassLabel(
            analytics_frame,
            text="📊 Journal Analytics & Insights",
            font=("Segoe UI", 16, "bold")
        )
        header.pack(pady=20)
        
        # Analytics cards grid
        cards_frame = GlassFrame(analytics_frame)
        cards_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create analytics cards
        self._create_analytics_cards(cards_frame)
        
        return analytics_frame
    
    def _create_search_tab(self) -> GlassFrame:
        """Create the search tab content."""
        search_frame = GlassFrame(self.content_area)
        
        # Search header
        search_header = create_glass_card(search_frame)
        search_header.pack(fill="x", padx=10, pady=5)
        
        search_label = GlassLabel(
            search_header,
            text="🔍 Advanced Search",
            font=("Segoe UI", 16, "bold")
        )
        search_label.pack(side="left", padx=10, pady=10)
        
        # Search controls
        search_controls = GlassFrame(search_frame)
        search_controls.pack(fill="x", padx=10, pady=5)
        
        # Search input
        self.search_entry = ctk.CTkEntry(
            search_controls,
            placeholder_text="Search entries, tags, content...",
            font=("Segoe UI", 12),
            height=40
        )
        self.search_entry.pack(fill="x", padx=10, pady=5)
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Advanced filters
        filters_frame = GlassFrame(search_controls)
        filters_frame.pack(fill="x", padx=10, pady=5)
        
        # Mood filter
        mood_filter_label = GlassLabel(filters_frame, text="Mood:")
        mood_filter_label.pack(side="left", padx=(0, 5))
        
        self.search_mood_filter = ctk.CTkComboBox(
            filters_frame,
            values=["All", "very_happy", "happy", "neutral", "sad", "very_sad"],
            command=self._perform_search
        )
        self.search_mood_filter.pack(side="left", padx=5)
        
        # Category filter
        category_filter_label = GlassLabel(filters_frame, text="Category:")
        category_filter_label.pack(side="left", padx=(10, 5))
        
        self.search_category_filter = ctk.CTkComboBox(
            filters_frame,
            values=["All"] + self._get_categories(),
            command=self._perform_search
        )
        self.search_category_filter.pack(side="left", padx=5)
        
        # Search results
        self.search_results_frame = ctk.CTkScrollableFrame(
            search_frame,
            fg_color="transparent"
        )
        self.search_results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        return search_frame
    
    def _create_analytics_cards(self, parent):
        """Create analytics visualization cards."""
        # Entry count card
        count_card = create_glass_card(parent)
        count_card.pack(fill="x", padx=10, pady=5)
        
        count_label = GlassLabel(
            count_card,
            text="📝 Total Entries",
            font=("Segoe UI", 12, "bold")
        )
        count_label.pack(pady=5)
        
        entry_count = len(self.database.get_all_entries())
        count_value = GlassLabel(
            count_card,
            text=str(entry_count),
            font=("Segoe UI", 24, "bold")
        )
        count_value.pack(pady=5)
        
        # Mood distribution card
        mood_card = create_glass_card(parent)
        mood_card.pack(fill="x", padx=10, pady=5)
        
        mood_label = GlassLabel(
            mood_card,
            text="😊 Mood Distribution",
            font=("Segoe UI", 12, "bold")
        )
        mood_label.pack(pady=5)
        
        # Simple mood stats
        mood_stats = self._calculate_mood_stats()
        for mood, count in mood_stats.items():
            mood_row = GlassLabel(
                mood_card,
                text=f"{mood.title()}: {count}",
                font=("Segoe UI", 10)
            )
            mood_row.pack(pady=2)
        
        # Recent activity card
        activity_card = create_glass_card(parent)
        activity_card.pack(fill="x", padx=10, pady=5)
        
        activity_label = GlassLabel(
            activity_card,
            text="📈 Recent Activity",
            font=("Segoe UI", 12, "bold")
        )
        activity_label.pack(pady=5)
        
        recent_entries = self.database.get_recent_entries(limit=5)
        for entry in recent_entries:
            entry_row = GlassLabel(
                activity_card,
                text=f"{entry.created_at[:10]}: {entry.title[:30]}...",
                font=("Segoe UI", 9)
            )
            entry_row.pack(pady=1, anchor="w", padx=10)
    
    def _switch_to_tab(self, tab_id: str):
        """Switch to the specified tab."""
        if self.current_tab == tab_id:
            return
        
        # Hide current tab content
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab].content_widget.pack_forget()
        
        # Show new tab content
        if tab_id in self.tabs:
            self.tabs[tab_id].content_widget.pack(fill="both", expand=True)
            self.current_tab = tab_id
            
            # Update button states
            self._update_tab_buttons(tab_id)
            
            # Refresh tab content if needed
            self._refresh_tab_content(tab_id)
            
            self.logger.info(f"Switched to tab: {tab_id}")
    
    def _update_tab_buttons(self, active_tab: str):
        """Update tab button visual states."""
        for tab_id, button in self.tab_buttons.items():
            if tab_id == active_tab:
                button.configure(fg_color="#4a9eff")
            else:
                button.configure(fg_color="transparent")
    
    def _refresh_tab_content(self, tab_id: str):
        """Refresh content for the specified tab."""
        if tab_id == 'browse':
            self._load_entries_list()
        elif tab_id == 'analytics':
            # Refresh analytics data
            pass
        elif tab_id == 'search':
            # Clear search results
            self._clear_search_results()
    
    # Event handlers
    def _on_content_change(self, content: str):
        """Handle content changes in the editor."""
        self.is_editing = True
        # Auto-save could be implemented here
    
    def _on_search_change(self, event=None):
        """Handle search input changes."""
        # Debounced search
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)
        
        self._search_timer = self.after(300, self._perform_search)
    
    # Data operations
    def _save_current_entry(self):
        """Save the current journal entry."""
        try:
            title = self.title_entry.get().strip()
            content = self.markdown_editor.get_content()
            content_markdown = self.markdown_editor.get_markdown_content()
            mood = self.mood_var.get()
            category = self.category_var.get()
            
            if not title:
                tk.messagebox.showwarning("Missing Title", "Please enter a title for your entry.")
                return
            
            if not content.strip():
                tk.messagebox.showwarning("Empty Content", "Please write some content for your entry.")
                return
            
            # Create or update entry
            if self.current_entry:
                # Update existing entry
                self.current_entry.title = title
                self.current_entry.content = content
                self.current_entry.content_markdown = content_markdown
                self.current_entry.mood = mood
                self.current_entry.updated_at = datetime.now().isoformat()
                
                success = self.database.update_entry(self.current_entry)
            else:
                # Create new entry
                entry = JournalEntry(
                    title=title,
                    content=content,
                    content_markdown=content_markdown,
                    mood=mood,
                    weather_condition="sunny",  # This should come from weather service
                    temperature=22.0,  # This should come from weather service
                    location="Current Location",  # This should come from location service
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                entry_id = self.database.save_entry(entry)
                if entry_id:
                    entry.id = entry_id
                    self.current_entry = entry
                    success = True
                else:
                    success = False
            
            if success:
                self.is_editing = False
                tk.messagebox.showinfo("Success", "Entry saved successfully!")
                
                # Update photo gallery with entry ID
                if self.current_entry and self.current_entry.id:
                    self.photo_gallery.load_photos(self.current_entry.id)
                
                # Refresh browse tab if visible
                if self.current_tab == 'browse':
                    self._load_entries_list()
            else:
                tk.messagebox.showerror("Error", "Failed to save entry.")
                
        except Exception as e:
            self.logger.error(f"Error saving entry: {e}")
            tk.messagebox.showerror("Error", f"Failed to save entry: {e}")
    
    def _create_new_entry(self):
        """Create a new journal entry."""
        if self.is_editing:
            if tk.messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to continue?"):
                self._clear_editor()
            else:
                return
        else:
            self._clear_editor()
        
        # Switch to write tab
        self._switch_to_tab('write')
    
    def _clear_editor(self):
        """Clear the editor for a new entry."""
        self.current_entry = None
        self.is_editing = False
        
        self.title_entry.delete(0, 'end')
        self.markdown_editor.clear_content()
        self.mood_var.set("neutral")
        self.category_var.set("")
        
        # Clear photo gallery
        self.photo_gallery.load_photos(None)
        
        # Focus on title
        self.title_entry.focus_set()
    
    def _load_entries_list(self):
        """Load and display the entries list."""
        # Clear existing entries
        for widget in self.entries_frame.winfo_children():
            widget.destroy()
        
        entries = self.database.get_all_entries()
        
        if not entries:
            empty_label = GlassLabel(
                self.entries_frame,
                text="No journal entries yet. Click 'New' to create your first entry!",
                font=("Segoe UI", 12)
            )
            empty_label.pack(pady=50)
            return
        
        for entry in entries:
            entry_card = self._create_entry_card(entry)
            entry_card.pack(fill="x", padx=5, pady=5)
    
    def _create_entry_card(self, entry: JournalEntry) -> GlassFrame:
        """Create a card widget for a journal entry."""
        card = create_glass_card(self.entries_frame)
        
        # Header with title and date
        header_frame = GlassFrame(card)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = GlassLabel(
            header_frame,
            text=entry.title,
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(side="left")
        
        date_label = GlassLabel(
            header_frame,
            text=entry.created_at[:10],
            font=("Segoe UI", 10)
        )
        date_label.pack(side="right")
        
        # Content preview
        content_preview = entry.content[:100] + "..." if len(entry.content) > 100 else entry.content
        content_label = GlassLabel(
            card,
            text=content_preview,
            font=("Segoe UI", 10),
            wraplength=400
        )
        content_label.pack(fill="x", padx=10, pady=5)
        
        # Metadata row
        meta_frame = GlassFrame(card)
        meta_frame.pack(fill="x", padx=10, pady=5)
        
        mood_label = GlassLabel(
            meta_frame,
            text=f"😊 {entry.mood}",
            font=("Segoe UI", 9)
        )
        mood_label.pack(side="left")
        
        weather_label = GlassLabel(
            meta_frame,
            text=f"🌤️ {entry.weather_condition} {entry.temperature}°C",
            font=("Segoe UI", 9)
        )
        weather_label.pack(side="left", padx=(20, 0))
        
        # Action buttons
        actions_frame = GlassFrame(card)
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        edit_button = GlassButton(
            actions_frame,
            text="✏️ Edit",
            command=lambda: self._edit_entry(entry),
            size=ComponentSize.SMALL
        )
        edit_button.pack(side="left", padx=(0, 5))
        
        delete_button = GlassButton(
            actions_frame,
            text="🗑️ Delete",
            command=lambda: self._delete_entry(entry),
            size=ComponentSize.SMALL
        )
        delete_button.pack(side="left")
        
        return card
    
    def _edit_entry(self, entry: JournalEntry):
        """Load an entry for editing."""
        self.current_entry = entry
        self.is_editing = False
        
        # Populate editor
        self.title_entry.delete(0, 'end')
        self.title_entry.insert(0, entry.title)
        
        self.markdown_editor.set_content(entry.content)
        self.mood_var.set(entry.mood)
        
        # Load photos
        if entry.id:
            self.photo_gallery.load_photos(entry.id)
        
        # Switch to write tab
        self._switch_to_tab('write')
    
    def _delete_entry(self, entry: JournalEntry):
        """Delete a journal entry after confirmation."""
        if tk.messagebox.askyesno("Delete Entry", f"Are you sure you want to delete '{entry.title}'?"):
            if self.database.delete_entry(entry.id):
                tk.messagebox.showinfo("Success", "Entry deleted successfully!")
                self._load_entries_list()
            else:
                tk.messagebox.showerror("Error", "Failed to delete entry.")
    
    def _filter_entries(self, filter_value: str):
        """Filter entries based on date range."""
        # Implement date filtering logic
        self._load_entries_list()
    
    def _perform_search(self):
        """Perform search with current filters."""
        query = self.search_entry.get().strip()
        mood_filter = self.search_mood_filter.get()
        category_filter = self.search_category_filter.get()
        
        # Clear previous results
        self._clear_search_results()
        
        if not query and mood_filter == "All" and category_filter == "All":
            return
        
        # Perform search (simplified)
        results = self.database.search_entries(query)
        
        # Apply additional filters
        if mood_filter != "All":
            results = [r for r in results if r.mood == mood_filter]
        
        # Display results
        for entry in results:
            result_card = self._create_entry_card(entry)
            result_card.pack(fill="x", padx=5, pady=5)
    
    def _clear_search_results(self):
        """Clear search results display."""
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
    
    # Helper methods
    def _get_categories(self) -> List[str]:
        """Get available categories."""
        categories = self.database.get_categories()
        return [cat['name'] for cat in categories]
    
    def _load_current_weather(self):
        """Load current weather information."""
        # This should integrate with the weather service
        self.weather_label.configure(text="Sunny, 22°C")
    
    def _calculate_mood_stats(self) -> Dict[str, int]:
        """Calculate mood distribution statistics."""
        entries = self.database.get_all_entries()
        mood_counts = {}
        
        for entry in entries:
            mood = entry.mood
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        return mood_counts
    
    def _add_tooltip(self, widget, text: str):
        """Add a simple tooltip to a widget."""
        # Simplified tooltip implementation
        pass