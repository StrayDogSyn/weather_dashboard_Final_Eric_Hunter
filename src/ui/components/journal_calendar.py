from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, date, timedelta
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from dataclasses import dataclass
from collections import defaultdict

from services.journal_service import JournalService
from models.journal_entry import JournalEntry


class JournalCalendarComponent(ttk.Frame):
    """Calendar view for date-based journal entry navigation."""
    
    def __init__(self, parent: tk.Widget, journal_service: JournalService,
                 on_date_selected: Optional[Callable[[datetime], None]] = None,
                 on_entry_selected: Optional[Callable[[JournalEntry], None]] = None):
        """Initialize the calendar component.
        
        Args:
            parent: Parent widget
            journal_service: Journal service instance
            on_date_selected: Callback when a date is selected
            on_entry_selected: Callback when an entry is selected
        """
        super().__init__(parent)
        self.journal_service = journal_service
        self.on_date_selected = on_date_selected
        self.on_entry_selected = on_entry_selected
        
        # Calendar state
        self.current_date = datetime.now()
        self.selected_date: Optional[datetime] = None
        self.entry_counts: Dict[str, int] = {}  # date_str -> count
        self.entries_by_date: Dict[str, List[JournalEntry]] = defaultdict(list)
        
        # Create the calendar interface
        self._create_calendar_interface()
        
        # Load initial data
        self._load_month_data()
    
    def _create_calendar_interface(self):
        """Create the calendar interface components."""
        # Main calendar frame
        self.calendar_frame = ttk.LabelFrame(self, text="Journal Calendar", padding=10)
        self.calendar_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Navigation frame
        nav_frame = ttk.Frame(self.calendar_frame)
        nav_frame.pack(fill="x", pady=(0, 10))
        
        # Previous month button
        ttk.Button(nav_frame, text="◀", command=self._previous_month, width=3).pack(side="left")
        
        # Month/Year label
        self.month_year_label = ttk.Label(nav_frame, font=('TkDefaultFont', 12, 'bold'))
        self.month_year_label.pack(side="left", expand=True)
        
        # Next month button
        ttk.Button(nav_frame, text="▶", command=self._next_month, width=3).pack(side="right")
        
        # Today button
        ttk.Button(nav_frame, text="Today", command=self._go_to_today).pack(side="right", padx=(0, 5))
        
        # Calendar grid frame
        self.grid_frame = ttk.Frame(self.calendar_frame)
        self.grid_frame.pack(fill="both", expand=True)
        
        # Day headers
        self.day_headers = []
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day_name in enumerate(day_names):
            header = ttk.Label(self.grid_frame, text=day_name, font=('TkDefaultFont', 9, 'bold'),
                              anchor='center', relief='solid', borderwidth=1)
            header.grid(row=0, column=i, sticky='nsew', padx=1, pady=1)
            self.day_headers.append(header)
        
        # Calendar day buttons
        self.day_buttons: List[List[tk.Button]] = []
        for week in range(6):  # 6 weeks max in a month view
            week_buttons = []
            for day in range(7):
                btn = tk.Button(self.grid_frame, text="", width=4, height=3,
                              command=lambda w=week, d=day: self._on_day_clicked(w, d),
                              relief='solid', borderwidth=1)
                btn.grid(row=week+1, column=day, sticky='nsew', padx=1, pady=1)
                week_buttons.append(btn)
            self.day_buttons.append(week_buttons)
        
        # Configure grid weights
        for i in range(7):
            self.grid_frame.columnconfigure(i, weight=1)
        for i in range(7):  # 6 weeks + 1 header
            self.grid_frame.rowconfigure(i, weight=1)
        
        # Selected date info frame
        info_frame = ttk.LabelFrame(self.calendar_frame, text="Selected Date", padding=5)
        info_frame.pack(fill="x", pady=(10, 0))
        
        self.date_info_label = ttk.Label(info_frame, text="No date selected")
        self.date_info_label.pack()
        
        # Entries list for selected date
        entries_frame = ttk.LabelFrame(self.calendar_frame, text="Entries", padding=5)
        entries_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        # Entries listbox with scrollbar
        listbox_frame = ttk.Frame(entries_frame)
        listbox_frame.pack(fill="both", expand=True)
        
        self.entries_listbox = tk.Listbox(listbox_frame, height=4)
        entries_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.entries_listbox.yview)
        self.entries_listbox.configure(yscrollcommand=entries_scrollbar.set)
        
        self.entries_listbox.pack(side="left", fill="both", expand=True)
        entries_scrollbar.pack(side="right", fill="y")
        
        # Bind double-click to select entry
        self.entries_listbox.bind('<Double-1>', self._on_entry_double_clicked)
        
        # Action buttons
        action_frame = ttk.Frame(entries_frame)
        action_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(action_frame, text="View Entry", command=self._view_selected_entry).pack(side="left")
        ttk.Button(action_frame, text="New Entry", command=self._create_new_entry).pack(side="left", padx=(5, 0))
    
    def _update_calendar_display(self):
        """Update the calendar display for the current month."""
        # Update month/year label
        month_name = calendar.month_name[self.current_date.month]
        year = self.current_date.year
        self.month_year_label.config(text=f"{month_name} {year}")
        
        # Get calendar data
        cal = calendar.monthcalendar(year, self.current_date.month)
        
        # Clear all buttons
        for week_buttons in self.day_buttons:
            for btn in week_buttons:
                btn.config(text="", state="disabled", bg="SystemButtonFace", fg="black")
        
        # Fill in the days
        today = datetime.now().date()
        selected_date = self.selected_date.date() if self.selected_date else None
        
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                btn = self.day_buttons[week_idx][day_idx]
                
                if day == 0:  # Empty day
                    btn.config(text="", state="disabled", bg="SystemButtonFace")
                else:
                    btn.config(text=str(day), state="normal")
                    
                    # Create date for this day
                    day_date = datetime(year, self.current_date.month, day).date()
                    date_str = day_date.strftime('%Y-%m-%d')
                    
                    # Color coding
                    bg_color = "SystemButtonFace"
                    fg_color = "black"
                    
                    # Highlight today
                    if day_date == today:
                        bg_color = "lightblue"
                        fg_color = "darkblue"
                    
                    # Highlight selected date
                    if day_date == selected_date:
                        bg_color = "lightgreen"
                        fg_color = "darkgreen"
                    
                    # Show entry indicator
                    entry_count = self.entry_counts.get(date_str, 0)
                    if entry_count > 0:
                        if bg_color == "SystemButtonFace":
                            bg_color = "lightyellow"
                        # Add entry count to button text
                        btn.config(text=f"{day}\n({entry_count})")
                    
                    btn.config(bg=bg_color, fg=fg_color)
    
    def _load_month_data(self):
        """Load journal entries for the current month."""
        try:
            # Calculate month range
            year = self.current_date.year
            month = self.current_date.month
            
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Get entries for the month
            entries = self.journal_service.search_entries(
                date_range=(start_date, end_date),
                limit=1000  # Should be enough for a month
            )
            
            # Group entries by date
            self.entry_counts.clear()
            self.entries_by_date.clear()
            
            for entry in entries:
                date_str = entry.date_created.strftime('%Y-%m-%d')
                self.entries_by_date[date_str].append(entry)
                self.entry_counts[date_str] = len(self.entries_by_date[date_str])
            
            # Update display
            self._update_calendar_display()
            
        except Exception as e:
            print(f"Failed to load month data: {e}")
    
    def _on_day_clicked(self, week: int, day: int):
        """Handle day button click."""
        btn = self.day_buttons[week][day]
        day_text = btn.cget('text')
        
        if not day_text or btn.cget('state') == 'disabled':
            return
        
        # Extract day number
        day_num = int(day_text.split('\n')[0])
        
        # Create selected date
        self.selected_date = datetime(self.current_date.year, self.current_date.month, day_num)
        
        # Update display
        self._update_calendar_display()
        self._update_selected_date_info()
        
        # Call callback
        if self.on_date_selected:
            self.on_date_selected(self.selected_date)
    
    def _update_selected_date_info(self):
        """Update the selected date information display."""
        if not self.selected_date:
            self.date_info_label.config(text="No date selected")
            self.entries_listbox.delete(0, tk.END)
            return
        
        # Update date label
        date_str = self.selected_date.strftime('%A, %B %d, %Y')
        self.date_info_label.config(text=date_str)
        
        # Update entries list
        self.entries_listbox.delete(0, tk.END)
        
        date_key = self.selected_date.strftime('%Y-%m-%d')
        entries = self.entries_by_date.get(date_key, [])
        
        for entry in entries:
            # Format entry for display
            time_str = entry.date_created.strftime('%H:%M')
            mood_str = f"Mood: {entry.mood_rating}/10" if entry.mood_rating else "No mood"
            preview = entry.get_preview(50)
            
            display_text = f"{time_str} - {mood_str} - {preview}"
            self.entries_listbox.insert(tk.END, display_text)
    
    def _on_entry_double_clicked(self, event=None):
        """Handle entry double-click."""
        self._view_selected_entry()
    
    def _view_selected_entry(self):
        """View the selected entry."""
        selection = self.entries_listbox.curselection()
        if not selection or not self.selected_date:
            return
        
        # Get the selected entry
        date_key = self.selected_date.strftime('%Y-%m-%d')
        entries = self.entries_by_date.get(date_key, [])
        
        if selection[0] < len(entries):
            entry = entries[selection[0]]
            if self.on_entry_selected:
                self.on_entry_selected(entry)
    
    def _create_new_entry(self):
        """Create a new entry for the selected date."""
        if not self.selected_date:
            return
        
        # This would typically open the entry creation dialog
        # For now, just call the date selected callback
        if self.on_date_selected:
            self.on_date_selected(self.selected_date)
    
    def _previous_month(self):
        """Navigate to previous month."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        
        self._load_month_data()
    
    def _next_month(self):
        """Navigate to next month."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        
        self._load_month_data()
    
    def _go_to_today(self):
        """Navigate to current month and select today."""
        today = datetime.now()
        self.current_date = today
        self.selected_date = today
        
        self._load_month_data()
        self._update_selected_date_info()
    
    def refresh_data(self):
        """Refresh the calendar data."""
        self._load_month_data()
        if self.selected_date:
            self._update_selected_date_info()
    
    def select_date(self, date: datetime):
        """Programmatically select a date."""
        # Navigate to the month if necessary
        if date.year != self.current_date.year or date.month != self.current_date.month:
            self.current_date = date
            self._load_month_data()
        
        # Select the date
        self.selected_date = date
        self._update_calendar_display()
        self._update_selected_date_info()
    
    def get_selected_date(self) -> Optional[datetime]:
        """Get the currently selected date."""
        return self.selected_date
    
    def get_entries_for_date(self, date: datetime) -> List[JournalEntry]:
        """Get entries for a specific date."""
        date_key = date.strftime('%Y-%m-%d')
        return self.entries_by_date.get(date_key, []).copy()