import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, List, Optional

from models.journal_entry import JournalEntry
from services.journal_service import JournalService


class JournalSearchComponent(ttk.Frame):
    """Advanced search interface for weather journal entries."""

    def __init__(
        self,
        parent: tk.Widget,
        journal_service: JournalService,
        on_entry_selected: Optional[Callable[[JournalEntry], None]] = None,
    ):
        """Initialize the search component.

        Args:
            parent: Parent widget
            journal_service: Journal service instance
            on_entry_selected: Callback when an entry is selected
        """
        super().__init__(parent)
        self.journal_service = journal_service
        self.on_entry_selected = on_entry_selected

        # Search state
        self.search_results: List[JournalEntry] = []
        self.current_suggestions: Dict[str, List[str]] = {
            "tags": [],
            "categories": [],
            "locations": [],
        }
        self.search_debounce_timer: Optional[threading.Timer] = None

        # Create the search interface
        self._create_search_interface()

        # Load initial suggestions
        self._load_suggestions()

    def _create_search_interface(self):
        """Create the search interface components."""
        # Main search frame
        self.search_frame = ttk.LabelFrame(self, text="Advanced Search", padding=10)
        self.search_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Search query section
        query_frame = ttk.Frame(self.search_frame)
        query_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(query_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(query_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Clear search button
        ttk.Button(query_frame, text="Clear", command=self._clear_search).pack(
            side="right", padx=(5, 0)
        )

        # Filters section
        filters_frame = ttk.LabelFrame(self.search_frame, text="Filters", padding=5)
        filters_frame.pack(fill="x", pady=(0, 10))

        # First row of filters
        filter_row1 = ttk.Frame(filters_frame)
        filter_row1.pack(fill="x", pady=(0, 5))

        # Mood range filter
        mood_frame = ttk.Frame(filter_row1)
        mood_frame.pack(side="left", padx=(0, 10))
        ttk.Label(mood_frame, text="Mood:").pack(side="left")
        self.mood_min_var = tk.StringVar(value="1")
        self.mood_max_var = tk.StringVar(value="10")
        ttk.Spinbox(mood_frame, from_=1, to=10, width=5, textvariable=self.mood_min_var).pack(
            side="left", padx=(5, 2)
        )
        ttk.Label(mood_frame, text="to").pack(side="left")
        ttk.Spinbox(mood_frame, from_=1, to=10, width=5, textvariable=self.mood_max_var).pack(
            side="left", padx=(2, 0)
        )

        # Date range filter
        date_frame = ttk.Frame(filter_row1)
        date_frame.pack(side="left", padx=(0, 10))
        ttk.Label(date_frame, text="Date Range:").pack(side="left")
        self.date_range_var = tk.StringVar(value="All")
        date_combo = ttk.Combobox(
            date_frame,
            textvariable=self.date_range_var,
            width=12,
            values=["All", "Today", "Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
        )
        date_combo.pack(side="left", padx=(5, 0))
        date_combo.bind("<<ComboboxSelected>>", self._on_date_range_changed)

        # Second row of filters
        filter_row2 = ttk.Frame(filters_frame)
        filter_row2.pack(fill="x", pady=(0, 5))

        # Category filter
        category_frame = ttk.Frame(filter_row2)
        category_frame.pack(side="left", padx=(0, 10))
        ttk.Label(category_frame, text="Category:").pack(side="left")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, width=15)
        self.category_combo.pack(side="left", padx=(5, 0))

        # Weather condition filter
        weather_frame = ttk.Frame(filter_row2)
        weather_frame.pack(side="left", padx=(0, 10))
        ttk.Label(weather_frame, text="Weather:").pack(side="left")
        self.weather_var = tk.StringVar()
        weather_combo = ttk.Combobox(
            weather_frame,
            textvariable=self.weather_var,
            width=15,
            values=["All", "Sunny", "Cloudy", "Rainy", "Snowy", "Stormy", "Foggy"],
        )
        weather_combo.pack(side="left", padx=(5, 0))

        # Third row - Tags
        filter_row3 = ttk.Frame(filters_frame)
        filter_row3.pack(fill="x")

        ttk.Label(filter_row3, text="Tags:").pack(side="left")
        self.tags_var = tk.StringVar()
        self.tags_entry = ttk.Entry(filter_row3, textvariable=self.tags_var, width=30)
        self.tags_entry.pack(side="left", padx=(5, 0))
        self.tags_entry.bind("<KeyRelease>", self._on_tags_changed)

        # Search button
        ttk.Button(filter_row3, text="Search", command=self._perform_search).pack(
            side="right", padx=(10, 0)
        )

        # Results section
        results_frame = ttk.LabelFrame(self.search_frame, text="Search Results", padding=5)
        results_frame.pack(fill="both", expand=True)

        # Results tree
        columns = ("Date", "Mood", "Category", "Preview", "Tags")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)

        # Configure columns
        self.results_tree.heading("Date", text="Date")
        self.results_tree.heading("Mood", text="Mood")
        self.results_tree.heading("Category", text="Category")
        self.results_tree.heading("Preview", text="Preview")
        self.results_tree.heading("Tags", text="Tags")

        self.results_tree.column("Date", width=120)
        self.results_tree.column("Mood", width=60)
        self.results_tree.column("Category", width=100)
        self.results_tree.column("Preview", width=300)
        self.results_tree.column("Tags", width=150)

        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_tree.yview
        )
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)

        self.results_tree.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")

        # Bind double-click to select entry
        self.results_tree.bind("<Double-1>", self._on_result_selected)

        # Export and analysis buttons
        action_frame = ttk.Frame(self.search_frame)
        action_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(action_frame, text="Export Results", command=self._export_results).pack(
            side="left"
        )
        ttk.Button(action_frame, text="Mood Analysis", command=self._show_mood_analysis).pack(
            side="left", padx=(10, 0)
        )

        # Results count label
        self.results_count_label = ttk.Label(action_frame, text="No results")
        self.results_count_label.pack(side="right")

    def _load_suggestions(self):
        """Load autocomplete suggestions."""
        try:
            # Load categories
            categories = self.journal_service.get_entry_suggestions("", limit=20)["categories"]
            self.category_combo["values"] = ["All"] + categories
        except Exception as e:
            print(f"Failed to load suggestions: {e}")

    def _on_search_changed(self, event=None):
        """Handle search query changes with debouncing."""
        if self.search_debounce_timer:
            self.search_debounce_timer.cancel()

        self.search_debounce_timer = threading.Timer(0.5, self._perform_search)
        self.search_debounce_timer.start()

    def _on_tags_changed(self, event=None):
        """Handle tags input changes for autocomplete."""
        query = self.tags_var.get().strip()
        if len(query) >= 2:
            try:
                suggestions = self.journal_service.get_entry_suggestions(query, limit=5)
                # Could implement dropdown suggestions here
            except Exception as e:
                print(f"Failed to get tag suggestions: {e}")

    def _on_date_range_changed(self, event=None):
        """Handle date range selection changes."""
        if self.date_range_var.get() == "Custom":
            # Could implement custom date picker here
            pass

    def _clear_search(self):
        """Clear all search filters."""
        self.search_var.set("")
        self.mood_min_var.set("1")
        self.mood_max_var.set("10")
        self.date_range_var.set("All")
        self.category_var.set("")
        self.weather_var.set("")
        self.tags_var.set("")
        self._perform_search()

    def _perform_search(self):
        """Perform the search with current filters."""
        try:
            # Build search parameters
            query = self.search_var.get().strip()

            # Mood range
            mood_range = None
            try:
                min_mood = int(self.mood_min_var.get())
                max_mood = int(self.mood_max_var.get())
                if min_mood <= max_mood:
                    mood_range = (min_mood, max_mood)
            except ValueError:
                pass

            # Date range
            date_range = None
            date_selection = self.date_range_var.get()
            if date_selection != "All":
                end_date = datetime.now()
                if date_selection == "Today":
                    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                elif date_selection == "Last 7 days":
                    start_date = end_date - timedelta(days=7)
                elif date_selection == "Last 30 days":
                    start_date = end_date - timedelta(days=30)
                elif date_selection == "Last 90 days":
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = None

                if start_date:
                    date_range = (start_date, end_date)

            # Categories
            categories = None
            if self.category_var.get() and self.category_var.get() != "All":
                categories = [self.category_var.get()]

            # Weather conditions
            weather_conditions = None
            if self.weather_var.get() and self.weather_var.get() != "All":
                weather_conditions = [self.weather_var.get()]

            # Tags
            tags = None
            if self.tags_var.get().strip():
                tags = [tag.strip() for tag in self.tags_var.get().split(",") if tag.strip()]

            # Perform search
            self.search_results = self.journal_service.search_entries(
                query=query,
                mood_range=mood_range,
                date_range=date_range,
                weather_conditions=weather_conditions,
                categories=categories,
                tags=tags,
                limit=100,
            )

            # Update results display
            self._update_results_display()

        except Exception as e:
            messagebox.showerror("Search Error", f"Failed to perform search: {str(e)}")

    def _update_results_display(self):
        """Update the results tree with search results."""
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add new results
        for entry in self.search_results:
            # Format data for display
            date_str = entry.date_created.strftime("%Y-%m-%d %H:%M")
            mood_str = f"{entry.mood_rating}/10" if entry.mood_rating else "N/A"
            category_str = entry.category or "N/A"
            preview = entry.get_preview(100)  # Get first 100 chars
            tags_str = ", ".join(entry.tags[:3]) if entry.tags else "N/A"  # Show first 3 tags

            # Insert into tree
            item_id = self.results_tree.insert(
                "", "end", values=(date_str, mood_str, category_str, preview, tags_str)
            )

            # Store entry reference
            self.results_tree.set(item_id, "entry_id", entry.id)

        # Update count label
        count = len(self.search_results)
        self.results_count_label.config(text=f"{count} result{'s' if count != 1 else ''}")

    def _on_result_selected(self, event=None):
        """Handle result selection."""
        selection = self.results_tree.selection()
        if selection and self.on_entry_selected:
            item = selection[0]
            entry_id = self.results_tree.set(item, "entry_id")

            # Find the entry
            for entry in self.search_results:
                if str(entry.id) == str(entry_id):
                    self.on_entry_selected(entry)
                    break

    def _export_results(self):
        """Export search results to file."""
        if not self.search_results:
            messagebox.showwarning("No Results", "No search results to export.")
            return

        # Ask for export format
        format_dialog = tk.Toplevel(self.parent)
        format_dialog.title("Export Format")
        format_dialog.geometry("300x150")
        format_dialog.transient(self.parent)
        format_dialog.grab_set()

        ttk.Label(format_dialog, text="Select export format:").pack(pady=10)

        format_var = tk.StringVar(value="json")
        ttk.Radiobutton(format_dialog, text="JSON", variable=format_var, value="json").pack()
        ttk.Radiobutton(format_dialog, text="HTML", variable=format_var, value="html").pack()
        ttk.Radiobutton(format_dialog, text="Plain Text", variable=format_var, value="txt").pack()

        def do_export():
            format_type = format_var.get()
            extensions = {"json": ".json", "html": ".html", "txt": ".txt"}

            filename = filedialog.asksaveasfilename(
                defaultextension=extensions[format_type],
                filetypes=[(f"{format_type.upper()} files", f"*{extensions[format_type]}")],
            )

            if filename:
                try:
                    export_data = self.journal_service.export_entries(
                        format_type=format_type, entries=self.search_results
                    )

                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(export_data)

                    messagebox.showinfo("Export Complete", f"Results exported to {filename}")
                    format_dialog.destroy()

                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

        ttk.Button(format_dialog, text="Export", command=do_export).pack(pady=10)
        ttk.Button(format_dialog, text="Cancel", command=format_dialog.destroy).pack()

    def _show_mood_analysis(self):
        """Show mood correlation analysis."""
        try:
            analysis = self.journal_service.get_mood_weather_correlation(days=30)

            # Create analysis window
            analysis_window = tk.Toplevel(self.parent)
            analysis_window.title("Mood Analysis")
            analysis_window.geometry("600x400")
            analysis_window.transient(self.parent)

            # Create text widget with scrollbar
            text_frame = ttk.Frame(analysis_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)

            text_widget = tk.Text(text_frame, wrap="word")
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Format analysis results
            if "error" in analysis:
                text_widget.insert("end", f"Error: {analysis['error']}")
            else:
                text_widget.insert("end", "MOOD-WEATHER CORRELATION ANALYSIS\n")
                text_widget.insert("end", "=" * 40 + "\n\n")

                text_widget.insert(
                    "end", f"Analysis Period: {analysis.get('analysis_period_days', 30)} days\n"
                )
                text_widget.insert(
                    "end", f"Total Entries: {analysis.get('total_entries_analyzed', 0)}\n\n"
                )

                if analysis.get("temperature_mood_correlation") is not None:
                    corr = analysis["temperature_mood_correlation"]
                    text_widget.insert("end", f"Temperature-Mood Correlation: {corr}\n")
                    if corr > 0.3:
                        text_widget.insert(
                            "end",
                            "→ Positive correlation: Higher temperatures tend to improve mood\n",
                        )
                    elif corr < -0.3:
                        text_widget.insert(
                            "end",
                            "→ Negative correlation: Higher temperatures tend to worsen mood\n",
                        )
                    else:
                        text_widget.insert(
                            "end", "→ Weak correlation: Temperature has little effect on mood\n"
                        )
                    text_widget.insert("end", "\n")

                weather_moods = analysis.get("weather_condition_moods", {})
                if weather_moods:
                    text_widget.insert("end", "MOOD BY WEATHER CONDITION:\n")
                    text_widget.insert("end", "-" * 30 + "\n")

                    for condition, data in sorted(
                        weather_moods.items(), key=lambda x: x[1]["average_mood"], reverse=True
                    ):
                        text_widget.insert("end", f"{condition}:\n")
                        text_widget.insert("end", f"  Average Mood: {data['average_mood']}/10\n")
                        text_widget.insert("end", f"  Entries: {data['count']}\n")
                        text_widget.insert(
                            "end", f"  Range: {data['min_mood']}-{data['max_mood']}\n\n"
                        )

            text_widget.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to generate analysis: {str(e)}")

    def refresh_suggestions(self):
        """Refresh autocomplete suggestions."""
        self._load_suggestions()

    def get_search_results(self) -> List[JournalEntry]:
        """Get current search results."""
        return self.search_results.copy()
