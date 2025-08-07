import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ...services.ai.ai_manager import AIManager
from ...services.weather.weather_service import WeatherService
from ..components.common.loading_spinner import LoadingSpinner
from ..theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class AITab(ctk.CTkFrame):
    """AI Features tab with poetry generation and activity suggestions"""
    
    def __init__(self, parent, weather_service: WeatherService, theme_manager: ThemeManager):
        super().__init__(parent)
        
        self.weather_service = weather_service
        self.theme_manager = theme_manager
        self.ai_manager = None
        
        # Current data
        self.current_weather = None
        self.current_poems = {}
        self.current_activities = []
        
        # UI state
        self.is_loading = False
        
        # Font size control
        self.font_size = 16
        self.text_widgets = []
        
        # Initialize AI manager in background
        self.init_ai_manager()
        
        # Create UI
        self.create_widgets()
        
        # Apply theme
        self.apply_theme()
    
    def init_ai_manager(self):
        """Initialize AI manager"""
        try:
            self.ai_manager = AIManager()
            self.after(100, self.on_ai_manager_ready)
        except Exception as e:
            logger.error(f"Failed to initialize AI manager: {e}")
            self.after(100, self.on_ai_manager_error)
    
    def on_ai_manager_ready(self):
        """Called when AI manager is ready"""
        self.status_label.configure(text="AI Features Ready")
        self.refresh_button.configure(state="normal")
        
        # Load initial data if weather is available
        if self.current_weather:
            self.refresh_ai_content()
    
    def on_ai_manager_error(self):
        """Called when AI manager fails to initialize"""
        self.status_label.configure(text="AI Features Unavailable (Fallback Mode)")
        self.refresh_button.configure(state="normal")
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.create_header()
        
        # Main content area with notebook
        self.create_main_content()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create header with title and controls"""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🤖 AI Weather Features",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Font controls
        self.create_font_controls(header_frame)
        
        # Controls frame
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=2, padx=20, pady=15, sticky="e")
        
        # Refresh button
        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh AI Content",
            command=self.refresh_ai_content,
            state="disabled"
        )
        self.refresh_button.grid(row=0, column=0, padx=5)
        
        # Settings button
        settings_button = ctk.CTkButton(
            controls_frame,
            text="⚙️ AI Settings",
            command=self.show_ai_settings,
            width=120
        )
        settings_button.grid(row=0, column=1, padx=5)
    
    def create_main_content(self):
        """Create main content area with tabbed interface"""
        # Create notebook for different AI features
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Poetry tab
        self.create_poetry_tab()
        
        # Activities tab
        self.create_activities_tab()
        
        # Insights tab
        self.create_insights_tab()
        
        # Stories tab
        self.create_stories_tab()
    
    def create_poetry_tab(self):
        """Create poetry generation tab"""
        poetry_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(poetry_frame, text="📝 Weather Poetry")
        
        poetry_frame.grid_columnconfigure(1, weight=1)
        poetry_frame.grid_rowconfigure(1, weight=1)
        
        # Poetry style selection
        style_frame = ctk.CTkFrame(poetry_frame)
        style_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(style_frame, text="Poetry Style:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.poetry_style_var = ctk.StringVar(value="haiku")
        style_options = ["haiku", "limerick", "free_verse", "sonnet"]
        
        for i, style in enumerate(style_options):
            radio = ctk.CTkRadioButton(
                style_frame,
                text=style.replace('_', ' ').title(),
                variable=self.poetry_style_var,
                value=style,
                command=self.on_poetry_style_changed
            )
            radio.grid(row=0, column=i+1, padx=10, pady=10)
        
        # Generate button
        generate_poetry_btn = ctk.CTkButton(
            style_frame,
            text="✨ Generate Poem",
            command=self.generate_poetry
        )
        generate_poetry_btn.grid(row=0, column=len(style_options)+1, padx=10, pady=10)
        
        # Poetry display area
        self.poetry_text = ctk.CTkTextbox(
            poetry_frame,
            font=ctk.CTkFont(size=self.font_size, family="Georgia"),
            wrap="word"
        )
        self.poetry_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.text_widgets.append(self.poetry_text)
        
        # Poetry metadata frame
        metadata_frame = ctk.CTkFrame(poetry_frame)
        metadata_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        self.poetry_metadata_label = ctk.CTkLabel(
            metadata_frame,
            text="Select a style and generate your first weather poem!",
            font=ctk.CTkFont(size=12)
        )
        self.poetry_metadata_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Save poem button
        save_poetry_btn = ctk.CTkButton(
            metadata_frame,
            text="💾 Save Poem",
            command=self.save_current_poem,
            width=100
        )
        save_poetry_btn.grid(row=0, column=1, padx=10, pady=10, sticky="e")
    
    def create_activities_tab(self):
        """Create activity suggestions tab"""
        activities_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(activities_frame, text="🎯 Activity Suggestions")
        
        activities_frame.grid_columnconfigure(0, weight=1)
        activities_frame.grid_rowconfigure(1, weight=1)
        
        # Controls frame
        controls_frame = ctk.CTkFrame(activities_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        controls_frame.grid_columnconfigure(2, weight=1)
        
        # Category filter
        ctk.CTkLabel(controls_frame, text="Category:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.activity_category_var = ctk.StringVar(value="all")
        self.activity_category_menu = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.activity_category_var,
            values=["all", "outdoor", "indoor", "exercise", "creative", "social", "relaxation"],
            command=self.filter_activities
        )
        self.activity_category_menu.grid(row=0, column=1, padx=10, pady=10)
        
        # Generate activities button
        generate_activities_btn = ctk.CTkButton(
            controls_frame,
            text="🎲 Generate Activities",
            command=self.generate_activities
        )
        generate_activities_btn.grid(row=0, column=3, padx=10, pady=10)
        
        # Activities display
        self.activities_scrollable = ctk.CTkScrollableFrame(activities_frame)
        self.activities_scrollable.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.activities_scrollable.grid_columnconfigure(0, weight=1)
        
        # Initial message
        initial_label = ctk.CTkLabel(
            self.activities_scrollable,
            text="🌤️ Generate weather-appropriate activities to get started!",
            font=ctk.CTkFont(size=16)
        )
        initial_label.grid(row=0, column=0, pady=50)
    
    def create_insights_tab(self):
        """Create weather insights tab"""
        insights_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(insights_frame, text="🧠 Weather Insights")
        
        insights_frame.grid_columnconfigure(0, weight=1)
        insights_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(insights_frame)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            header,
            text="🔍 AI Weather Analysis",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        generate_insights_btn = ctk.CTkButton(
            header,
            text="🧠 Generate Insights",
            command=self.generate_insights
        )
        generate_insights_btn.grid(row=0, column=2, padx=20, pady=15)
        
        # Insights display
        self.insights_text = ctk.CTkTextbox(
            insights_frame,
            font=ctk.CTkFont(size=self.font_size),
            wrap="word"
        )
        self.insights_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.text_widgets.append(self.insights_text)
        
        # Facts section
        facts_frame = ctk.CTkFrame(insights_frame)
        facts_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        facts_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            facts_frame,
            text="📚 Weather Facts",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.facts_frame = ctk.CTkFrame(facts_frame, fg_color="transparent")
        self.facts_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.facts_frame.grid_columnconfigure(0, weight=1)
    
    def create_stories_tab(self):
        """Create weather stories tab"""
        stories_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(stories_frame, text="📖 Weather Stories")
        
        stories_frame.grid_columnconfigure(0, weight=1)
        stories_frame.grid_rowconfigure(1, weight=1)
        
        # Story controls
        controls_frame = ctk.CTkFrame(stories_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(controls_frame, text="Story Type:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.story_type_var = ctk.StringVar(value="short")
        story_type_menu = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.story_type_var,
            values=["short", "adventure", "mystery", "romance", "fantasy"]
        )
        story_type_menu.grid(row=0, column=1, padx=10, pady=10)
        
        generate_story_btn = ctk.CTkButton(
            controls_frame,
            text="📝 Generate Story",
            command=self.generate_story
        )
        generate_story_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Story display
        self.story_text = ctk.CTkTextbox(
            stories_frame,
            font=ctk.CTkFont(size=self.font_size, family="Georgia"),
            wrap="word"
        )
        self.story_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.text_widgets.append(self.story_text)
    
    def create_status_bar(self):
        """Create status bar"""
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Initializing AI Features...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Loading spinner placeholder
        self.loading_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        self.loading_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")
    
    def update_weather_data(self, weather_data: Dict[str, Any]):
        """Update with new weather data"""
        self.current_weather = weather_data
        
        if self.ai_manager and not self.is_loading:
            self.refresh_ai_content()
    
    def refresh_ai_content(self):
        """Refresh all AI content"""
        if not self.current_weather or self.is_loading:
            return
        
        self.is_loading = True
        self.status_label.configure(text="Refreshing AI content...")
        
        # Run in background thread
        threading.Thread(target=self._refresh_ai_content_async, daemon=True).start()
    
    def _refresh_ai_content_async(self):
        """Refresh AI content in background thread"""
        try:
            # Generate initial content
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Generate a haiku as default
            poem_task = self.ai_manager.generate_weather_poetry('haiku', self.current_weather)
            activities_task = self.ai_manager.get_activity_suggestions(self.current_weather)
            
            poem = loop.run_until_complete(poem_task)
            activities = loop.run_until_complete(activities_task)
            
            loop.close()
            
            # Update UI in main thread
            self.after(100, lambda: self._update_ui_with_content(poem, activities))
            
        except Exception as e:
            logger.error(f"Failed to refresh AI content: {e}")
            self.after(100, lambda: self._on_refresh_error(str(e)))
    
    def _update_ui_with_content(self, poem, activities):
        """Update UI with generated content"""
        # Update poetry
        if poem:
            self.current_poems['haiku'] = poem
            self.display_poem(poem)
        
        # Update activities
        if activities and 'suggestions' in activities:
            self.current_activities = activities['suggestions']
            self.display_activities(self.current_activities)
        
        self.is_loading = False
        self.status_label.configure(text="AI content updated successfully")
    
    def _on_refresh_error(self, error_msg):
        """Handle refresh error"""
        self.is_loading = False
        self.status_label.configure(text=f"Error: {error_msg}")
    
    def generate_poetry(self):
        """Generate poetry in selected style"""
        if not self.current_weather or not self.ai_manager:
            messagebox.showwarning("No Data", "Please wait for weather data to load.")
            return
        
        style = self.poetry_style_var.get()
        
        def _generate():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                poem = loop.run_until_complete(
                    self.ai_manager.generate_weather_poetry(style, self.current_weather)
                )
                
                loop.close()
                
                self.after(100, lambda: self._on_poetry_generated(poem, style))
                
            except Exception as e:
                logger.error(f"Poetry generation failed: {e}")
                self.after(100, lambda: self._on_poetry_error(str(e)))
        
        self.status_label.configure(text=f"Generating {style} poem...")
        threading.Thread(target=_generate, daemon=True).start()
    
    def _on_poetry_generated(self, poem, style):
        """Handle generated poetry"""
        self.current_poems[style] = poem
        self.display_poem(poem)
        self.status_label.configure(text=f"{style.title()} poem generated successfully")
    
    def _on_poetry_error(self, error_msg):
        """Handle poetry generation error"""
        self.status_label.configure(text=f"Poetry generation failed: {error_msg}")
    
    def display_poem(self, poem_data):
        """Display poem in the text widget"""
        self.poetry_text.delete("1.0", "end")
        
        if poem_data:
            poem_text = poem_data.get('poem', '')
            style = poem_data.get('style', 'unknown')
            timestamp = poem_data.get('timestamp', '')
            
            self.poetry_text.insert("1.0", poem_text)
            
            # Update metadata
            metadata = f"Style: {style.title()} | Generated: {timestamp[:19] if timestamp else 'Unknown'}"
            if poem_data.get('fallback'):
                metadata += " | Fallback Mode"
            
            self.poetry_metadata_label.configure(text=metadata)
    
    def generate_activities(self):
        """Generate activity suggestions"""
        if not self.current_weather or not self.ai_manager:
            messagebox.showwarning("No Data", "Please wait for weather data to load.")
            return
        
        def _generate():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                activities = loop.run_until_complete(
                    self.ai_manager.get_activity_suggestions(self.current_weather)
                )
                
                loop.close()
                
                self.after(100, lambda: self._on_activities_generated(activities))
                
            except Exception as e:
                logger.error(f"Activity generation failed: {e}")
                self.after(100, lambda: self._on_activities_error(str(e)))
        
        self.status_label.configure(text="Generating activity suggestions...")
        threading.Thread(target=_generate, daemon=True).start()
    
    def _on_activities_generated(self, activities_data):
        """Handle generated activities"""
        if activities_data and 'suggestions' in activities_data:
            self.current_activities = activities_data['suggestions']
            self.display_activities(self.current_activities)
            self.status_label.configure(text="Activity suggestions generated successfully")
    
    def _on_activities_error(self, error_msg):
        """Handle activity generation error"""
        self.status_label.configure(text=f"Activity generation failed: {error_msg}")
    
    def display_activities(self, activities):
        """Display activities in the scrollable frame"""
        # Clear existing activities
        for widget in self.activities_scrollable.winfo_children():
            widget.destroy()
        
        if not activities:
            no_activities_label = ctk.CTkLabel(
                self.activities_scrollable,
                text="No activities available. Try generating new suggestions!",
                font=ctk.CTkFont(size=14)
            )
            no_activities_label.grid(row=0, column=0, pady=20)
            return
        
        # Display each activity
        for i, activity in enumerate(activities):
            self.create_activity_card(activity, i)
    
    def create_activity_card(self, activity, row):
        """Create a card for displaying an activity"""
        card = ctk.CTkFrame(self.activities_scrollable)
        card.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        card.grid_columnconfigure(1, weight=1)
        
        # Activity name
        name_label = ctk.CTkLabel(
            card,
            text=activity.get('name', 'Unknown Activity'),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")
        
        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=activity.get('description', ''),
            font=ctk.CTkFont(size=12),
            wraplength=400,
            justify="left"
        )
        desc_label.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")
        
        # Metadata
        metadata_frame = ctk.CTkFrame(card, fg_color="transparent")
        metadata_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 15))
        
        # Category and duration
        category = activity.get('category', 'general')
        duration = activity.get('duration', 'Unknown')
        
        meta_text = f"Category: {category.title()}"
        if duration != 'Unknown':
            meta_text += f" | Duration: {duration}"
        
        meta_label = ctk.CTkLabel(
            metadata_frame,
            text=meta_text,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        meta_label.grid(row=0, column=0, sticky="w")
    
    def generate_insights(self):
        """Generate weather insights"""
        if not self.current_weather or not self.ai_manager:
            messagebox.showwarning("No Data", "Please wait for weather data to load.")
            return
        
        def _generate():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                insights = loop.run_until_complete(
                    self.ai_manager.get_weather_insights(self.current_weather)
                )
                
                facts = loop.run_until_complete(
                    self.ai_manager.generate_weather_facts(self.current_weather)
                )
                
                loop.close()
                
                self.after(100, lambda: self._on_insights_generated(insights, facts))
                
            except Exception as e:
                logger.error(f"Insights generation failed: {e}")
                self.after(100, lambda: self._on_insights_error(str(e)))
        
        self.status_label.configure(text="Generating weather insights...")
        threading.Thread(target=_generate, daemon=True).start()
    
    def _on_insights_generated(self, insights, facts):
        """Handle generated insights"""
        # Display insights
        self.insights_text.delete("1.0", "end")
        self.insights_text.insert("1.0", insights)
        
        # Display facts
        for widget in self.facts_frame.winfo_children():
            widget.destroy()
        
        for i, fact in enumerate(facts[:5]):
            fact_label = ctk.CTkLabel(
                self.facts_frame,
                text=f"• {fact}",
                font=ctk.CTkFont(size=12),
                wraplength=600,
                justify="left"
            )
            fact_label.grid(row=i, column=0, sticky="w", padx=10, pady=2)
        
        self.status_label.configure(text="Weather insights generated successfully")
    
    def _on_insights_error(self, error_msg):
        """Handle insights generation error"""
        self.status_label.configure(text=f"Insights generation failed: {error_msg}")
    
    def generate_story(self):
        """Generate weather story"""
        if not self.current_weather or not self.ai_manager:
            messagebox.showwarning("No Data", "Please wait for weather data to load.")
            return
        
        story_type = self.story_type_var.get()
        
        def _generate():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                story = loop.run_until_complete(
                    self.ai_manager.generate_weather_story(self.current_weather, story_type)
                )
                
                loop.close()
                
                self.after(100, lambda: self._on_story_generated(story))
                
            except Exception as e:
                logger.error(f"Story generation failed: {e}")
                self.after(100, lambda: self._on_story_error(str(e)))
        
        self.status_label.configure(text=f"Generating {story_type} story...")
        threading.Thread(target=_generate, daemon=True).start()
    
    def _on_story_generated(self, story_data):
        """Handle generated story"""
        self.story_text.delete("1.0", "end")
        
        if story_data:
            story_text = story_data.get('story', '')
            self.story_text.insert("1.0", story_text)
        
        self.status_label.configure(text="Weather story generated successfully")
    
    def _on_story_error(self, error_msg):
        """Handle story generation error"""
        self.status_label.configure(text=f"Story generation failed: {error_msg}")
    
    def on_poetry_style_changed(self):
        """Handle poetry style change"""
        style = self.poetry_style_var.get()
        if style in self.current_poems:
            self.display_poem(self.current_poems[style])
    
    def filter_activities(self, category):
        """Filter activities by category"""
        if category == "all":
            self.display_activities(self.current_activities)
        else:
            filtered = [a for a in self.current_activities if a.get('category') == category]
            self.display_activities(filtered)
    
    def save_current_poem(self):
        """Save current poem to file"""
        style = self.poetry_style_var.get()
        if style not in self.current_poems:
            messagebox.showwarning("No Poem", "No poem to save. Generate a poem first.")
            return
        
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Poem"
            )
            
            if filename:
                poem_data = self.current_poems[style]
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Weather Poem - {style.title()}\n")
                    f.write("=" * 40 + "\n\n")
                    f.write(poem_data.get('poem', ''))
                    f.write("\n\n" + "=" * 40 + "\n")
                    f.write(f"Generated: {poem_data.get('timestamp', '')}\n")
                    f.write(f"Weather: {poem_data.get('weather', {})}\n")
                
                messagebox.showinfo("Saved", f"Poem saved to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save poem: {e}")
    
    def show_ai_settings(self):
        """Show AI settings dialog"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("AI Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self)
        
        # AI Status
        status_frame = ctk.CTkFrame(settings_window)
        status_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            status_frame,
            text="AI Service Status",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        if self.ai_manager:
            status = self.ai_manager.get_service_status()
            
            for feature, available in status.get('features', {}).items():
                status_text = "✅ Available" if available else "❌ Unavailable"
                ctk.CTkLabel(
                    status_frame,
                    text=f"{feature.replace('_', ' ').title()}: {status_text}"
                ).pack(anchor="w", padx=20, pady=2)
        
        # Close button
        ctk.CTkButton(
            settings_window,
            text="Close",
            command=settings_window.destroy
        ).pack(pady=20)
    
    def create_font_controls(self, parent):
        """Create font size control buttons."""
        font_frame = ctk.CTkFrame(parent, fg_color="transparent")
        font_frame.grid(row=0, column=1, padx=(50, 0), pady=15)

        # Font size label
        font_label = ctk.CTkLabel(
            font_frame,
            text="Font:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
        )
        font_label.pack(side="left", padx=(0, 5))

        # Decrease font button
        decrease_btn = ctk.CTkButton(
            font_frame,
            text="A-",
            width=35,
            height=30,
            command=self._decrease_font_size,
            fg_color="#2B2B2B",
            hover_color="#00D4FF",
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        decrease_btn.pack(side="left", padx=2)

        # Current font size display
        self.font_size_label = ctk.CTkLabel(
            font_frame,
            text=str(self.font_size),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
            width=25,
        )
        self.font_size_label.pack(side="left", padx=2)

        # Increase font button
        increase_btn = ctk.CTkButton(
            font_frame,
            text="A+",
            width=35,
            height=30,
            command=self._increase_font_size,
            fg_color="#2B2B2B",
            hover_color="#00D4FF",
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        increase_btn.pack(side="left", padx=2)

    def _increase_font_size(self):
        """Increase font size for all AI text widgets."""
        if self.font_size < 24:
            self.font_size += 1
            self._update_font_sizes()

    def _decrease_font_size(self):
        """Decrease font size for all AI text widgets."""
        if self.font_size > 10:
            self.font_size -= 1
            self._update_font_sizes()

    def _update_font_sizes(self):
        """Update font sizes for all tracked text widgets."""
        self.font_size_label.configure(text=str(self.font_size))
        
        for widget in self.text_widgets:
            try:
                current_font = widget.cget("font")
                if isinstance(current_font, tuple):
                    family, size, *style = current_font
                    new_font = (family, self.font_size, *style)
                    widget.configure(font=new_font)
                elif isinstance(current_font, str):
                    # Handle string font specifications
                    parts = current_font.split()
                    if len(parts) >= 2:
                        family = parts[0]
                        style = parts[2:] if len(parts) > 2 else []
                        new_font = (family, self.font_size, *style)
                        widget.configure(font=new_font)
            except Exception as e:
                logger.debug(f"Could not update font for widget: {e}")
                pass  # Skip widgets that can't be updated

    def apply_theme(self):
        """Apply current theme"""
        if self.theme_manager:
            # Theme will be applied automatically by CustomTkinter
            pass