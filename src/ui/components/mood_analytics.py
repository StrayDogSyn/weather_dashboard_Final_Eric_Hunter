import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from collections import defaultdict, Counter

from services.journal_service import JournalService
from models.journal_entry import JournalEntry


class MoodAnalyticsComponent:
    """Component for mood analytics and weather correlation visualization."""
    
    def __init__(self, parent: tk.Widget, journal_service: JournalService):
        """Initialize the mood analytics component.
        
        Args:
            parent: Parent widget
            journal_service: Journal service instance
        """
        self.parent = parent
        self.journal_service = journal_service
        self.current_data = []
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Setup UI
        self._setup_ui()
        
        # Load initial data
        self._load_data()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Title
        title_label = ttk.Label(self.frame, text="Mood Analytics & Weather Correlation", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Control panel
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Date range selection
        date_frame = ttk.LabelFrame(control_frame, text="Date Range", padding=10)
        date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Label(date_frame, text="From:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.start_date_entry = ttk.Entry(date_frame, textvariable=self.start_date_var, width=12)
        self.start_date_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(date_frame, text="To:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.end_date_entry = ttk.Entry(date_frame, textvariable=self.end_date_var, width=12)
        self.end_date_entry.grid(row=0, column=3)
        
        # Analysis type selection
        analysis_frame = ttk.LabelFrame(control_frame, text="Analysis Type", padding=10)
        analysis_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.analysis_type_var = tk.StringVar(value="mood_trend")
        analysis_types = [
            ("Mood Trend", "mood_trend"),
            ("Weather Correlation", "weather_correlation"),
            ("Mood Distribution", "mood_distribution"),
            ("Weather Impact", "weather_impact")
        ]
        
        for i, (text, value) in enumerate(analysis_types):
            ttk.Radiobutton(analysis_frame, text=text, variable=self.analysis_type_var, 
                           value=value, command=self._update_analysis).grid(row=i//2, column=i%2, 
                                                                           sticky=tk.W, padx=5, pady=2)
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="Refresh Data", command=self._load_data)
        refresh_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Chart tab
        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text="Charts")
        
        # Statistics tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        
        # Insights tab
        self.insights_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.insights_frame, text="Insights")
        
        # Setup chart area
        self._setup_chart_area()
        
        # Setup statistics area
        self._setup_statistics_area()
        
        # Setup insights area
        self._setup_insights_area()
    
    def _setup_chart_area(self):
        """Setup the chart visualization area."""
        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(self.chart_frame)
        toolbar_frame.pack(fill=tk.X)
        
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
    
    def _setup_statistics_area(self):
        """Setup the statistics display area."""
        # Create scrollable text widget for statistics
        stats_container = ttk.Frame(self.stats_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Statistics text widget with scrollbar
        self.stats_text = tk.Text(stats_container, wrap=tk.WORD, font=('Consolas', 10))
        stats_scrollbar = ttk.Scrollbar(stats_container, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_insights_area(self):
        """Setup the insights display area."""
        # Create scrollable text widget for insights
        insights_container = ttk.Frame(self.insights_frame)
        insights_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Insights text widget with scrollbar
        self.insights_text = tk.Text(insights_container, wrap=tk.WORD, font=('Arial', 11))
        insights_scrollbar = ttk.Scrollbar(insights_container, orient=tk.VERTICAL, command=self.insights_text.yview)
        self.insights_text.configure(yscrollcommand=insights_scrollbar.set)
        
        self.insights_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        insights_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _load_data(self):
        """Load journal data for analysis."""
        try:
            # Parse date range
            start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d')
            
            # Load entries from journal service
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                entries = loop.run_until_complete(
                    self.journal_service.get_entries_by_date_range(start_date, end_date)
                )
                self.current_data = entries
                
                # Update analysis
                self._update_analysis()
                
            finally:
                loop.close()
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date format. Please use YYYY-MM-DD format.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def _update_analysis(self):
        """Update the analysis based on current data and selected type."""
        if not self.current_data:
            self._show_no_data_message()
            return
        
        analysis_type = self.analysis_type_var.get()
        
        if analysis_type == "mood_trend":
            self._show_mood_trend()
        elif analysis_type == "weather_correlation":
            self._show_weather_correlation()
        elif analysis_type == "mood_distribution":
            self._show_mood_distribution()
        elif analysis_type == "weather_impact":
            self._show_weather_impact()
        
        # Update statistics and insights
        self._update_statistics()
        self._update_insights()
    
    def _show_no_data_message(self):
        """Show message when no data is available."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No data available for the selected date range', 
                horizontalalignment='center', verticalalignment='center', 
                transform=ax.transAxes, fontsize=16)
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def _show_mood_trend(self):
        """Show mood trend over time."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Extract dates and moods
        dates = [entry.date_created for entry in self.current_data]
        moods = [entry.mood_rating for entry in self.current_data]
        
        # Sort by date
        sorted_data = sorted(zip(dates, moods))
        dates, moods = zip(*sorted_data) if sorted_data else ([], [])
        
        if dates and moods:
            # Plot mood trend
            ax.plot(dates, moods, marker='o', linewidth=2, markersize=6, alpha=0.7)
            
            # Add trend line
            if len(dates) > 1:
                z = np.polyfit(range(len(dates)), moods, 1)
                p = np.poly1d(z)
                ax.plot(dates, p(range(len(dates))), "--", alpha=0.8, color='red', 
                       label=f'Trend (slope: {z[0]:.3f})')
                ax.legend()
            
            # Add average line
            avg_mood = np.mean(moods)
            ax.axhline(y=avg_mood, color='green', linestyle=':', alpha=0.7, 
                      label=f'Average: {avg_mood:.1f}')
            ax.legend()
            
            ax.set_xlabel('Date')
            ax.set_ylabel('Mood Rating')
            ax.set_title('Mood Trend Over Time')
            ax.set_ylim(0, 11)
            ax.grid(True, alpha=0.3)
            
            # Format x-axis dates
            self.figure.autofmt_xdate()
        
        self.canvas.draw()
    
    def _show_weather_correlation(self):
        """Show correlation between mood and weather conditions."""
        self.figure.clear()
        
        # Extract weather data and moods
        weather_moods = defaultdict(list)
        
        for entry in self.current_data:
            if entry.weather_data:
                condition = entry.get_weather_condition()
                if condition and condition != 'Unknown':
                    weather_moods[condition].append(entry.mood_rating)
        
        if weather_moods:
            # Create subplots
            ax1 = self.figure.add_subplot(211)
            ax2 = self.figure.add_subplot(212)
            
            # Box plot of moods by weather condition
            conditions = list(weather_moods.keys())
            mood_data = [weather_moods[condition] for condition in conditions]
            
            ax1.boxplot(mood_data, labels=conditions)
            ax1.set_title('Mood Distribution by Weather Condition')
            ax1.set_ylabel('Mood Rating')
            ax1.set_ylim(0, 11)
            ax1.grid(True, alpha=0.3)
            
            # Average mood by weather condition
            avg_moods = [np.mean(moods) for moods in mood_data]
            bars = ax2.bar(conditions, avg_moods, alpha=0.7)
            
            # Color bars based on mood level
            for bar, avg_mood in zip(bars, avg_moods):
                if avg_mood >= 7:
                    bar.set_color('green')
                elif avg_mood >= 5:
                    bar.set_color('orange')
                else:
                    bar.set_color('red')
            
            ax2.set_title('Average Mood by Weather Condition')
            ax2.set_ylabel('Average Mood Rating')
            ax2.set_ylim(0, 10)
            ax2.grid(True, alpha=0.3)
            
            # Rotate x-axis labels
            plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
            plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _show_mood_distribution(self):
        """Show distribution of mood ratings."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        moods = [entry.mood_rating for entry in self.current_data]
        
        if moods:
            # Create histogram
            bins = np.arange(0.5, 11.5, 1)
            counts, _, patches = ax.hist(moods, bins=bins, alpha=0.7, edgecolor='black')
            
            # Color bars based on mood level
            for i, patch in enumerate(patches):
                mood_level = i + 1
                if mood_level >= 8:
                    patch.set_facecolor('green')
                elif mood_level >= 6:
                    patch.set_facecolor('lightgreen')
                elif mood_level >= 4:
                    patch.set_facecolor('orange')
                else:
                    patch.set_facecolor('red')
            
            ax.set_xlabel('Mood Rating')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Mood Ratings')
            ax.set_xticks(range(1, 11))
            ax.grid(True, alpha=0.3)
            
            # Add statistics text
            mean_mood = np.mean(moods)
            median_mood = np.median(moods)
            mode_mood = Counter(moods).most_common(1)[0][0]
            
            stats_text = f'Mean: {mean_mood:.1f}\nMedian: {median_mood:.1f}\nMode: {mode_mood}'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        self.canvas.draw()
    
    def _show_weather_impact(self):
        """Show how different weather factors impact mood."""
        self.figure.clear()
        
        # Extract temperature and mood data
        temps = []
        moods = []
        
        for entry in self.current_data:
            temp = entry.get_temperature()
            if temp is not None:
                temps.append(temp)
                moods.append(entry.mood_rating)
        
        if temps and moods:
            # Create scatter plot
            ax = self.figure.add_subplot(111)
            scatter = ax.scatter(temps, moods, alpha=0.6, s=50)
            
            # Add trend line
            if len(temps) > 1:
                z = np.polyfit(temps, moods, 1)
                p = np.poly1d(z)
                temp_range = np.linspace(min(temps), max(temps), 100)
                ax.plot(temp_range, p(temp_range), "--", alpha=0.8, color='red',
                       label=f'Trend (correlation: {np.corrcoef(temps, moods)[0,1]:.3f})')
                ax.legend()
            
            ax.set_xlabel('Temperature (°F)')
            ax.set_ylabel('Mood Rating')
            ax.set_title('Mood vs Temperature')
            ax.set_ylim(0, 11)
            ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def _update_statistics(self):
        """Update the statistics display."""
        self.stats_text.delete(1.0, tk.END)
        
        if not self.current_data:
            self.stats_text.insert(tk.END, "No data available for analysis.")
            return
        
        # Basic statistics
        moods = [entry.mood_rating for entry in self.current_data]
        
        stats = f"""MOOD STATISTICS
{'='*50}

Total Entries: {len(self.current_data)}
Date Range: {self.start_date_var.get()} to {self.end_date_var.get()}

MOOD ANALYSIS:
Mean Mood: {np.mean(moods):.2f}
Median Mood: {np.median(moods):.2f}
Standard Deviation: {np.std(moods):.2f}
Minimum Mood: {min(moods)}
Maximum Mood: {max(moods)}

MOOD DISTRIBUTION:
"""
        
        # Mood distribution
        mood_counts = Counter(moods)
        for mood in range(1, 11):
            count = mood_counts.get(mood, 0)
            percentage = (count / len(moods)) * 100 if moods else 0
            stats += f"Mood {mood}: {count} entries ({percentage:.1f}%)\n"
        
        # Weather correlation
        weather_moods = defaultdict(list)
        for entry in self.current_data:
            condition = entry.get_weather_condition()
            if condition and condition != 'Unknown':
                weather_moods[condition].append(entry.mood_rating)
        
        if weather_moods:
            stats += f"\nWEATHER CORRELATION:\n"
            for condition, condition_moods in weather_moods.items():
                avg_mood = np.mean(condition_moods)
                stats += f"{condition}: {avg_mood:.2f} avg mood ({len(condition_moods)} entries)\n"
        
        # Temperature correlation
        temps = []
        temp_moods = []
        for entry in self.current_data:
            temp = entry.get_temperature()
            if temp is not None:
                temps.append(temp)
                temp_moods.append(entry.mood_rating)
        
        if len(temps) > 1:
            correlation = np.corrcoef(temps, temp_moods)[0, 1]
            stats += f"\nTEMPERATURE CORRELATION:\n"
            stats += f"Correlation coefficient: {correlation:.3f}\n"
            if abs(correlation) > 0.3:
                direction = "positive" if correlation > 0 else "negative"
                strength = "strong" if abs(correlation) > 0.7 else "moderate"
                stats += f"There is a {strength} {direction} correlation between temperature and mood.\n"
            else:
                stats += f"There is little to no correlation between temperature and mood.\n"
        
        self.stats_text.insert(tk.END, stats)
    
    def _update_insights(self):
        """Update the insights display with AI-like analysis."""
        self.insights_text.delete(1.0, tk.END)
        
        if not self.current_data:
            self.insights_text.insert(tk.END, "No data available for insights.")
            return
        
        insights = "MOOD & WEATHER INSIGHTS\n" + "="*50 + "\n\n"
        
        moods = [entry.mood_rating for entry in self.current_data]
        avg_mood = np.mean(moods)
        
        # Overall mood assessment
        if avg_mood >= 7:
            insights += "🌟 POSITIVE OUTLOOK: Your overall mood has been quite positive during this period! "
        elif avg_mood >= 5:
            insights += "😊 BALANCED MOOD: Your mood has been generally stable with room for improvement. "
        else:
            insights += "💙 CHALLENGING PERIOD: This seems to have been a more difficult time emotionally. "
        
        insights += f"Your average mood rating is {avg_mood:.1f}/10.\n\n"
        
        # Mood variability
        mood_std = np.std(moods)
        if mood_std > 2:
            insights += "📊 HIGH VARIABILITY: Your mood shows significant fluctuation. Consider identifying triggers for both high and low periods.\n\n"
        elif mood_std < 1:
            insights += "📊 STABLE MOOD: Your mood has been quite consistent during this period.\n\n"
        else:
            insights += "📊 MODERATE VARIABILITY: Your mood shows normal day-to-day variation.\n\n"
        
        # Weather insights
        weather_moods = defaultdict(list)
        for entry in self.current_data:
            condition = entry.get_weather_condition()
            if condition and condition != 'Unknown':
                weather_moods[condition].append(entry.mood_rating)
        
        if weather_moods:
            # Find best and worst weather for mood
            weather_avgs = {condition: np.mean(moods) for condition, moods in weather_moods.items()}
            best_weather = max(weather_avgs, key=weather_avgs.get)
            worst_weather = min(weather_avgs, key=weather_avgs.get)
            
            insights += f"☀️ WEATHER IMPACT:\n"
            insights += f"• Your mood tends to be highest during {best_weather.lower()} weather ({weather_avgs[best_weather]:.1f}/10)\n"
            insights += f"• Your mood tends to be lowest during {worst_weather.lower()} weather ({weather_avgs[worst_weather]:.1f}/10)\n\n"
            
            # Weather recommendations
            if weather_avgs[best_weather] - weather_avgs[worst_weather] > 1:
                insights += f"💡 RECOMMENDATION: There's a notable difference in your mood based on weather. "
                insights += f"Consider planning mood-boosting activities during {worst_weather.lower()} weather.\n\n"
        
        # Temperature insights
        temps = []
        temp_moods = []
        for entry in self.current_data:
            temp = entry.get_temperature()
            if temp is not None:
                temps.append(temp)
                temp_moods.append(entry.mood_rating)
        
        if len(temps) > 1:
            correlation = np.corrcoef(temps, temp_moods)[0, 1]
            if correlation > 0.3:
                insights += "🌡️ TEMPERATURE SENSITIVITY: You tend to feel better in warmer weather. Consider light therapy or warm indoor activities during colder periods.\n\n"
            elif correlation < -0.3:
                insights += "🌡️ HEAT SENSITIVITY: You tend to feel better in cooler weather. Consider staying cool and hydrated during hot periods.\n\n"
        
        # Trend insights
        if len(moods) > 5:
            recent_moods = moods[-5:]
            earlier_moods = moods[:-5] if len(moods) > 5 else moods[:len(moods)//2]
            
            if np.mean(recent_moods) > np.mean(earlier_moods) + 0.5:
                insights += "📈 IMPROVING TREND: Your mood has been improving recently! Keep up whatever you're doing.\n\n"
            elif np.mean(recent_moods) < np.mean(earlier_moods) - 0.5:
                insights += "📉 DECLINING TREND: Your mood has been declining recently. Consider reaching out for support or trying new mood-boosting activities.\n\n"
        
        # Actionable suggestions
        insights += "🎯 ACTIONABLE INSIGHTS:\n"
        insights += "• Continue journaling to track patterns and triggers\n"
        insights += "• Pay attention to how different weather conditions affect you\n"
        insights += "• Consider planning activities based on weather forecasts\n"
        insights += "• Use this data to inform conversations with healthcare providers\n"
        insights += "• Celebrate the positive patterns you've identified!\n"
        
        self.insights_text.insert(tk.END, insights)
    
    def get_frame(self) -> ttk.Frame:
        """Get the main frame widget."""
        return self.frame
    
    # Add geometry management methods that delegate to the frame
    def pack(self, **kwargs):
        """Allow this component to be packed"""
        return self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Allow this component to be gridded"""
        return self.frame.grid(**kwargs)
    
    def place(self, **kwargs):
        """Allow this component to be placed"""
        return self.frame.place(**kwargs)
    
    def refresh_data(self):
        """Refresh the analytics data."""
        self._load_data()
    
    def set_date_range(self, start_date: datetime, end_date: datetime):
        """Set the date range for analysis."""
        self.start_date_var.set(start_date.strftime('%Y-%m-%d'))
        self.end_date_var.set(end_date.strftime('%Y-%m-%d'))
        self._load_data()
    
    def export_chart(self, filename: str):
        """Export the current chart to a file."""
        try:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Chart exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export chart: {str(e)}")