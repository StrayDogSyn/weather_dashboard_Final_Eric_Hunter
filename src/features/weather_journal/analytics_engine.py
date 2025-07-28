#!/usr/bin/env python3
"""
Weather Journal Analytics Engine - Advanced data analysis and visualization

This module provides comprehensive analytics for journal entries including:
- Mood vs weather correlation analysis
- Data visualization with glassmorphic charts
- Statistical insights and trends
- Word cloud generation
- Calendar view analytics
"""

import os
import re
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# Data analysis libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False

from ...utils.logger import LoggerMixin
from ...ui.components.glass import (
    GlassFrame, GlassButton, GlassLabel, 
    ComponentSize, create_glass_card
)
from .database import JournalDatabase
from .models import JournalEntry


class AnalyticsEngine(LoggerMixin):
    """
    Core analytics engine for processing journal data.
    
    Provides statistical analysis, correlation detection,
    and data preparation for visualization.
    """
    
    def __init__(self, database: JournalDatabase):
        self.database = database
        
        # Mood scoring system
        self.mood_scores = {
            'very_sad': 1,
            'sad': 2,
            'neutral': 3,
            'happy': 4,
            'very_happy': 5
        }
        
        # Weather scoring system
        self.weather_scores = {
            'stormy': 1,
            'rainy': 2,
            'cloudy': 3,
            'partly_cloudy': 4,
            'sunny': 5,
            'clear': 5
        }
        
        self.logger.info("Analytics Engine initialized")
    
    def calculate_mood_weather_correlation(self) -> Dict[str, Any]:
        """
        Calculate correlation between mood and weather conditions.
        
        Returns:
            Dictionary with correlation data and statistics
        """
        entries = self.database.get_all_entries()
        
        if len(entries) < 2:
            return {
                'correlation': 0.0,
                'sample_size': len(entries),
                'significance': 'insufficient_data',
                'mood_weather_pairs': [],
                'weather_mood_averages': {}
            }
        
        # Extract mood and weather scores
        mood_scores = []
        weather_scores = []
        mood_weather_pairs = []
        
        for entry in entries:
            mood_score = self.mood_scores.get(entry.mood, 3)
            weather_score = self.weather_scores.get(entry.weather_condition.lower(), 3)
            
            mood_scores.append(mood_score)
            weather_scores.append(weather_score)
            mood_weather_pairs.append({
                'date': entry.created_at[:10],
                'mood': entry.mood,
                'mood_score': mood_score,
                'weather': entry.weather_condition,
                'weather_score': weather_score,
                'title': entry.title
            })
        
        # Calculate Pearson correlation coefficient
        correlation = self._calculate_correlation(mood_scores, weather_scores)
        
        # Calculate weather-mood averages
        weather_moods = defaultdict(list)
        for pair in mood_weather_pairs:
            weather_moods[pair['weather']].append(pair['mood_score'])
        
        weather_mood_averages = {
            weather: sum(scores) / len(scores)
            for weather, scores in weather_moods.items()
        }
        
        # Determine significance
        significance = self._determine_significance(correlation, len(entries))
        
        return {
            'correlation': correlation,
            'sample_size': len(entries),
            'significance': significance,
            'mood_weather_pairs': mood_weather_pairs,
            'weather_mood_averages': weather_mood_averages
        }
    
    def analyze_mood_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze mood trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        entries = [e for e in self.database.get_all_entries() 
                  if e.created_at >= cutoff_date]
        
        if not entries:
            return {
                'trend': 'no_data',
                'average_mood': 3.0,
                'mood_distribution': {},
                'daily_averages': [],
                'trend_direction': 'stable'
            }
        
        # Calculate daily mood averages
        daily_moods = defaultdict(list)
        for entry in entries:
            date = entry.created_at[:10]
            mood_score = self.mood_scores.get(entry.mood, 3)
            daily_moods[date].append(mood_score)
        
        daily_averages = [
            {
                'date': date,
                'average_mood': sum(scores) / len(scores),
                'entry_count': len(scores)
            }
            for date, scores in sorted(daily_moods.items())
        ]
        
        # Calculate overall statistics
        all_mood_scores = [self.mood_scores.get(e.mood, 3) for e in entries]
        average_mood = sum(all_mood_scores) / len(all_mood_scores)
        
        mood_distribution = Counter(e.mood for e in entries)
        
        # Determine trend direction
        if len(daily_averages) >= 2:
            recent_avg = sum(day['average_mood'] for day in daily_averages[-7:]) / min(7, len(daily_averages))
            earlier_avg = sum(day['average_mood'] for day in daily_averages[:7]) / min(7, len(daily_averages))
            
            if recent_avg > earlier_avg + 0.2:
                trend_direction = 'improving'
            elif recent_avg < earlier_avg - 0.2:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'trend': 'analyzed',
            'average_mood': average_mood,
            'mood_distribution': dict(mood_distribution),
            'daily_averages': daily_averages,
            'trend_direction': trend_direction
        }
    
    def generate_word_frequency(self, limit: int = 50) -> List[Tuple[str, int]]:
        """
        Generate word frequency analysis from journal content.
        
        Args:
            limit: Maximum number of words to return
            
        Returns:
            List of (word, frequency) tuples
        """
        entries = self.database.get_all_entries()
        
        # Combine all content
        all_text = ' '.join(entry.content for entry in entries)
        
        # Clean and tokenize text
        words = self._extract_words(all_text)
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        filtered_words = [word for word in words if word.lower() not in stop_words and len(word) > 2]
        
        # Count frequencies
        word_counts = Counter(filtered_words)
        
        return word_counts.most_common(limit)
    
    def analyze_entry_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in journal entry creation.
        
        Returns:
            Dictionary with pattern analysis
        """
        entries = self.database.get_all_entries()
        
        if not entries:
            return {
                'total_entries': 0,
                'entries_per_day': {},
                'entries_per_month': {},
                'average_length': 0,
                'longest_streak': 0,
                'current_streak': 0
            }
        
        # Analyze by day of week
        day_counts = defaultdict(int)
        month_counts = defaultdict(int)
        lengths = []
        
        for entry in entries:
            date_obj = datetime.fromisoformat(entry.created_at.replace('Z', '+00:00'))
            day_name = date_obj.strftime('%A')
            month_name = date_obj.strftime('%B')
            
            day_counts[day_name] += 1
            month_counts[month_name] += 1
            lengths.append(len(entry.content))
        
        # Calculate streaks
        entry_dates = sorted(set(entry.created_at[:10] for entry in entries))
        longest_streak, current_streak = self._calculate_streaks(entry_dates)
        
        return {
            'total_entries': len(entries),
            'entries_per_day': dict(day_counts),
            'entries_per_month': dict(month_counts),
            'average_length': sum(lengths) / len(lengths) if lengths else 0,
            'longest_streak': longest_streak,
            'current_streak': current_streak
        }
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient.
        
        Args:
            x: First variable values
            y: Second variable values
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _determine_significance(self, correlation: float, sample_size: int) -> str:
        """
        Determine statistical significance of correlation.
        
        Args:
            correlation: Correlation coefficient
            sample_size: Number of data points
            
        Returns:
            Significance level string
        """
        abs_corr = abs(correlation)
        
        if sample_size < 10:
            return 'insufficient_data'
        elif abs_corr > 0.7:
            return 'strong'
        elif abs_corr > 0.5:
            return 'moderate'
        elif abs_corr > 0.3:
            return 'weak'
        else:
            return 'negligible'
    
    def _extract_words(self, text: str) -> List[str]:
        """
        Extract words from text, removing punctuation and normalizing.
        
        Args:
            text: Input text
            
        Returns:
            List of cleaned words
        """
        # Remove punctuation and split
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def _calculate_streaks(self, dates: List[str]) -> Tuple[int, int]:
        """
        Calculate longest and current writing streaks.
        
        Args:
            dates: List of entry dates (YYYY-MM-DD format)
            
        Returns:
            Tuple of (longest_streak, current_streak)
        """
        if not dates:
            return 0, 0
        
        # Convert to date objects
        date_objects = [datetime.strptime(date, '%Y-%m-%d').date() for date in dates]
        date_objects.sort()
        
        longest_streak = 1
        current_streak = 1
        temp_streak = 1
        
        for i in range(1, len(date_objects)):
            if (date_objects[i] - date_objects[i-1]).days == 1:
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        # Calculate current streak
        today = datetime.now().date()
        if date_objects and (today - date_objects[-1]).days <= 1:
            current_streak = 1
            for i in range(len(date_objects) - 2, -1, -1):
                if (date_objects[i+1] - date_objects[i]).days == 1:
                    current_streak += 1
                else:
                    break
        else:
            current_streak = 0
        
        return longest_streak, current_streak


class AnalyticsVisualization(GlassFrame, LoggerMixin):
    """
    Glassmorphic analytics visualization widget.
    
    Provides interactive charts and graphs with glassmorphic styling.
    """
    
    def __init__(self, parent, analytics_engine: AnalyticsEngine, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.analytics_engine = analytics_engine
        self.current_chart = None
        
        self._setup_ui()
        self._setup_matplotlib_style()
        
        self.logger.info("Analytics Visualization initialized")
    
    def _setup_ui(self):
        """Setup the visualization interface."""
        # Header
        header_frame = GlassFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = GlassLabel(
            header_frame,
            text="📊 Analytics Dashboard",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        # Chart selection buttons
        button_frame = GlassFrame(header_frame)
        button_frame.pack(side="right", padx=10, pady=10)
        
        chart_buttons = [
            ("📈 Mood Trends", self._show_mood_trends),
            ("🌤️ Mood vs Weather", self._show_mood_weather_correlation),
            ("☁️ Word Cloud", self._show_word_cloud),
            ("📅 Calendar View", self._show_calendar_view)
        ]
        
        for text, command in chart_buttons:
            btn = GlassButton(
                button_frame,
                text=text,
                command=command,
                size=ComponentSize.SMALL,
                width=120
            )
            btn.pack(side="left", padx=2)
        
        # Chart area
        self.chart_frame = GlassFrame(self)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Statistics panel
        self.stats_frame = GlassFrame(self)
        self.stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Show default chart
        self._show_mood_trends()
    
    def _setup_matplotlib_style(self):
        """Configure matplotlib for glassmorphic styling."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        plt.style.use('dark_background')
        plt.rcParams.update({
            'figure.facecolor': '#2b2b2b',
            'axes.facecolor': '#2b2b2b',
            'axes.edgecolor': '#4d4d4d',
            'axes.labelcolor': '#ffffff',
            'text.color': '#ffffff',
            'xtick.color': '#ffffff',
            'ytick.color': '#ffffff',
            'grid.color': '#4d4d4d',
            'grid.alpha': 0.3
        })
    
    def _show_mood_trends(self):
        """Display mood trends chart."""
        self._clear_chart_area()
        
        if not MATPLOTLIB_AVAILABLE:
            self._show_no_matplotlib_message()
            return
        
        # Get mood trend data
        trend_data = self.analytics_engine.analyze_mood_trends(30)
        
        if trend_data['trend'] == 'no_data':
            self._show_no_data_message("No mood data available for the last 30 days.")
            return
        
        # Create figure
        fig = Figure(figsize=(10, 6), facecolor='#2b2b2b')
        ax = fig.add_subplot(111)
        
        # Plot daily mood averages
        daily_data = trend_data['daily_averages']
        if daily_data:
            dates = [datetime.strptime(day['date'], '%Y-%m-%d') for day in daily_data]
            moods = [day['average_mood'] for day in daily_data]
            
            ax.plot(dates, moods, color='#4a9eff', linewidth=2, marker='o', markersize=4)
            ax.fill_between(dates, moods, alpha=0.3, color='#4a9eff')
            
            # Formatting
            ax.set_title('Mood Trends (Last 30 Days)', fontsize=14, fontweight='bold', color='#ffffff')
            ax.set_xlabel('Date', fontsize=12, color='#ffffff')
            ax.set_ylabel('Average Mood Score', fontsize=12, color='#ffffff')
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            fig.autofmt_xdate()
            
            # Set y-axis limits
            ax.set_ylim(1, 5)
            ax.set_yticks([1, 2, 3, 4, 5])
            ax.set_yticklabels(['Very Sad', 'Sad', 'Neutral', 'Happy', 'Very Happy'])
        
        # Embed chart
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Update statistics
        self._update_mood_stats(trend_data)
    
    def _show_mood_weather_correlation(self):
        """Display mood vs weather correlation chart."""
        self._clear_chart_area()
        
        if not MATPLOTLIB_AVAILABLE:
            self._show_no_matplotlib_message()
            return
        
        # Get correlation data
        corr_data = self.analytics_engine.calculate_mood_weather_correlation()
        
        if corr_data['sample_size'] < 2:
            self._show_no_data_message("Insufficient data for correlation analysis.")
            return
        
        # Create figure with subplots
        fig = Figure(figsize=(12, 8), facecolor='#2b2b2b')
        
        # Scatter plot
        ax1 = fig.add_subplot(221)
        pairs = corr_data['mood_weather_pairs']
        
        if pairs:
            weather_scores = [p['weather_score'] for p in pairs]
            mood_scores = [p['mood_score'] for p in pairs]
            
            ax1.scatter(weather_scores, mood_scores, alpha=0.6, color='#4a9eff', s=50)
            ax1.set_xlabel('Weather Score', color='#ffffff')
            ax1.set_ylabel('Mood Score', color='#ffffff')
            ax1.set_title('Mood vs Weather Scatter Plot', fontweight='bold', color='#ffffff')
            ax1.grid(True, alpha=0.3)
        
        # Weather-mood averages bar chart
        ax2 = fig.add_subplot(222)
        weather_avgs = corr_data['weather_mood_averages']
        
        if weather_avgs:
            weathers = list(weather_avgs.keys())
            avg_moods = list(weather_avgs.values())
            
            bars = ax2.bar(weathers, avg_moods, color='#4aff9e', alpha=0.7)
            ax2.set_xlabel('Weather Condition', color='#ffffff')
            ax2.set_ylabel('Average Mood Score', color='#ffffff')
            ax2.set_title('Average Mood by Weather', fontweight='bold', color='#ffffff')
            ax2.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, avg_moods):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                        f'{value:.1f}', ha='center', va='bottom', color='#ffffff')
        
        # Correlation info
        ax3 = fig.add_subplot(212)
        ax3.axis('off')
        
        correlation = corr_data['correlation']
        significance = corr_data['significance']
        sample_size = corr_data['sample_size']
        
        info_text = f"""Correlation Analysis Results:
        
Correlation Coefficient: {correlation:.3f}
Significance Level: {significance.title()}
Sample Size: {sample_size} entries
        
Interpretation:
        • Correlation ranges from -1 (perfect negative) to +1 (perfect positive)
        • Values near 0 indicate little to no linear relationship
        • Current correlation is {self._interpret_correlation(correlation)}"""
        
        ax3.text(0.05, 0.95, info_text, transform=ax3.transAxes, fontsize=11,
                verticalalignment='top', color='#ffffff', family='monospace')
        
        plt.tight_layout()
        
        # Embed chart
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Update statistics
        self._update_correlation_stats(corr_data)
    
    def _show_word_cloud(self):
        """Display word cloud visualization."""
        self._clear_chart_area()
        
        if not WORDCLOUD_AVAILABLE:
            self._show_missing_library_message("WordCloud library not available. Install with: pip install wordcloud")
            return
        
        # Get word frequency data
        word_freq = self.analytics_engine.generate_word_frequency(100)
        
        if not word_freq:
            self._show_no_data_message("No text data available for word cloud generation.")
            return
        
        # Create word cloud
        try:
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='#2b2b2b',
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                random_state=42
            ).generate_from_frequencies(dict(word_freq))
            
            # Create matplotlib figure
            if MATPLOTLIB_AVAILABLE:
                fig = Figure(figsize=(10, 6), facecolor='#2b2b2b')
                ax = fig.add_subplot(111)
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                ax.set_title('Word Cloud - Most Frequent Words', fontsize=14, fontweight='bold', color='#ffffff')
                
                # Embed chart
                canvas = FigureCanvasTkAgg(fig, self.chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
            else:
                # Fallback to text display
                self._show_word_frequency_text(word_freq)
                
        except Exception as e:
            self.logger.error(f"Error generating word cloud: {e}")
            self._show_word_frequency_text(word_freq)
    
    def _show_calendar_view(self):
        """Display calendar view of entries."""
        self._clear_chart_area()
        
        # Get entry patterns
        patterns = self.analytics_engine.analyze_entry_patterns()
        
        if patterns['total_entries'] == 0:
            self._show_no_data_message("No entries available for calendar view.")
            return
        
        # Create calendar-style visualization
        calendar_frame = GlassFrame(self.chart_frame)
        calendar_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = GlassLabel(
            calendar_frame,
            text="📅 Entry Patterns",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Day of week analysis
        dow_frame = create_glass_card(calendar_frame)
        dow_frame.pack(fill="x", padx=10, pady=10)
        
        dow_title = GlassLabel(
            dow_frame,
            text="Entries by Day of Week",
            font=("Segoe UI", 12, "bold")
        )
        dow_title.pack(pady=5)
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = patterns['entries_per_day']
        max_count = max(day_counts.values()) if day_counts else 1
        
        for day in days_order:
            count = day_counts.get(day, 0)
            percentage = (count / max_count) * 100 if max_count > 0 else 0
            
            day_row = GlassFrame(dow_frame)
            day_row.pack(fill="x", padx=10, pady=2)
            
            day_label = GlassLabel(
                day_row,
                text=f"{day}:",
                font=("Segoe UI", 10),
                width=80
            )
            day_label.pack(side="left")
            
            # Progress bar
            progress_frame = tk.Frame(day_row, bg="#3d3d3d", height=20)
            progress_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            if percentage > 0:
                progress_fill = tk.Frame(
                    progress_frame,
                    bg="#4a9eff",
                    width=int(percentage * 2),
                    height=20
                )
                progress_fill.pack(side="left")
            
            count_label = GlassLabel(
                day_row,
                text=f"{count}",
                font=("Segoe UI", 10, "bold"),
                width=30
            )
            count_label.pack(side="right")
        
        # Statistics summary
        stats_frame = create_glass_card(calendar_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_title = GlassLabel(
            stats_frame,
            text="Writing Statistics",
            font=("Segoe UI", 12, "bold")
        )
        stats_title.pack(pady=5)
        
        stats_text = f"""Total Entries: {patterns['total_entries']}
Average Length: {patterns['average_length']:.0f} characters
Longest Streak: {patterns['longest_streak']} days
Current Streak: {patterns['current_streak']} days"""
        
        stats_label = GlassLabel(
            stats_frame,
            text=stats_text,
            font=("Segoe UI", 10),
            justify="left"
        )
        stats_label.pack(pady=10)
    
    def _clear_chart_area(self):
        """Clear the current chart area."""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
    
    def _show_no_data_message(self, message: str):
        """Show a no data message."""
        no_data_label = GlassLabel(
            self.chart_frame,
            text=f"📊 {message}",
            font=("Segoe UI", 14)
        )
        no_data_label.pack(expand=True)
    
    def _show_no_matplotlib_message(self):
        """Show message when matplotlib is not available."""
        message = "📊 Matplotlib not available.\nInstall with: pip install matplotlib"
        self._show_no_data_message(message)
    
    def _show_missing_library_message(self, message: str):
        """Show message for missing libraries."""
        missing_label = GlassLabel(
            self.chart_frame,
            text=message,
            font=("Segoe UI", 12)
        )
        missing_label.pack(expand=True)
    
    def _show_word_frequency_text(self, word_freq: List[Tuple[str, int]]):
        """Show word frequency as text when word cloud is not available."""
        freq_frame = create_glass_card(self.chart_frame)
        freq_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = GlassLabel(
            freq_frame,
            text="📝 Most Frequent Words",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # Create scrollable text area
        text_frame = ctk.CTkScrollableFrame(freq_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for i, (word, count) in enumerate(word_freq[:20]):
            word_label = GlassLabel(
                text_frame,
                text=f"{i+1:2d}. {word:<15} ({count} times)",
                font=("Consolas", 10)
            )
            word_label.pack(anchor="w", pady=1)
    
    def _update_mood_stats(self, trend_data: Dict[str, Any]):
        """Update mood statistics display."""
        stats_card = create_glass_card(self.stats_frame)
        stats_card.pack(fill="x", padx=10, pady=5)
        
        stats_title = GlassLabel(
            stats_card,
            text="📈 Mood Statistics",
            font=("Segoe UI", 12, "bold")
        )
        stats_title.pack(pady=5)
        
        avg_mood = trend_data['average_mood']
        trend_direction = trend_data['trend_direction']
        
        mood_names = {1: 'Very Sad', 2: 'Sad', 3: 'Neutral', 4: 'Happy', 5: 'Very Happy'}
        avg_mood_name = mood_names.get(round(avg_mood), 'Unknown')
        
        stats_text = f"Average Mood: {avg_mood:.1f} ({avg_mood_name})\nTrend: {trend_direction.title()}"
        
        stats_label = GlassLabel(
            stats_card,
            text=stats_text,
            font=("Segoe UI", 10)
        )
        stats_label.pack(pady=5)
    
    def _update_correlation_stats(self, corr_data: Dict[str, Any]):
        """Update correlation statistics display."""
        stats_card = create_glass_card(self.stats_frame)
        stats_card.pack(fill="x", padx=10, pady=5)
        
        stats_title = GlassLabel(
            stats_card,
            text="🌤️ Correlation Statistics",
            font=("Segoe UI", 12, "bold")
        )
        stats_title.pack(pady=5)
        
        correlation = corr_data['correlation']
        significance = corr_data['significance']
        interpretation = self._interpret_correlation(correlation)
        
        stats_text = f"Correlation: {correlation:.3f}\nSignificance: {significance.title()}\nInterpretation: {interpretation}"
        
        stats_label = GlassLabel(
            stats_card,
            text=stats_text,
            font=("Segoe UI", 10)
        )
        stats_label.pack(pady=5)
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient."""
        abs_corr = abs(correlation)
        
        if abs_corr < 0.1:
            return "No meaningful relationship"
        elif abs_corr < 0.3:
            return "Weak relationship"
        elif abs_corr < 0.5:
            return "Moderate relationship"
        elif abs_corr < 0.7:
            return "Strong relationship"
        else:
            return "Very strong relationship"