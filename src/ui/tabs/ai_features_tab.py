import customtkinter as ctk
from ..components.glassmorphic import GlassPanel
from ..components.common.loading_spinner import LoadingSpinner
from ...services.ai.ai_manager import AIManager
from ...services.weather.ml_weather_service import MLWeatherService
import threading
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIFeaturesTab(ctk.CTkFrame):
    """Enhanced consolidated AI Features tab with all AI functionality."""
    
    def __init__(self, parent, weather_service, gemini_service):
        super().__init__(parent, fg_color="transparent")
        self.weather_service = weather_service
        self.gemini_service = gemini_service
        self.ai_manager = None
        self.ml_weather_service = MLWeatherService()
        self.current_feature = "analysis"
        self.font_size = 14  # Default larger font size
        self.text_widgets = []  # Track text widgets for font changes
        self.setup_ui()
        self.initialize_ai_manager()

    def setup_ui(self):
        """Create unified AI features interface"""
        # Main container
        self.main_container = GlassPanel(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header()
        
        # Feature selector (tabs within tab)
        self.create_feature_selector()
        
        # Content area
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Load default feature
        self.show_weather_analysis()

    def create_header(self):
        """Create unified header with font controls"""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🤖 AI Weather Features",
            font=("Arial", 24, "bold"),
            text_color="#00D4FF"
        )
        title_label.pack(side="left")
        
        # Font controls in the middle
        self.create_font_controls(header_frame)
        
        # Status indicator
        self.ai_status = ctk.CTkLabel(
            header_frame,
            text="✅ AI Ready",
            font=("Arial", 12),
            text_color="#4ECDC4"
        )
        self.ai_status.pack(side="right", padx=20)

    def create_feature_selector(self):
        """Create feature selection buttons"""
        selector_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        selector_frame.pack(fill="x", padx=20, pady=10)
        
        # Feature buttons
        self.feature_buttons = {}
        features = [
            ("🔍 Weather Analysis", "analysis", self.show_weather_analysis),
            ("🤖 ML Predictions", "ml_predictions", self.show_ml_predictions),
            ("🎯 Activity Suggestions", "activities", self.show_activity_suggestions),
            ("🎭 Weather Poetry", "poetry", self.show_weather_poetry),
            ("📊 Weather Insights", "insights", self.show_weather_insights),
            ("🎵 Weather Stories", "stories", self.show_weather_stories)
        ]
        
        for text, key, command in features:
            btn = ctk.CTkButton(
                selector_frame,
                text=text,
                command=command,
                fg_color="#2B2B2B",
                hover_color="#00D4FF",
                height=40,
                font=("Arial", 12)
            )
            btn.pack(side="left", padx=5, fill="x", expand=True)
            self.feature_buttons[key] = btn
        
        # Highlight active feature
        self.set_active_feature("analysis")

    def set_active_feature(self, feature_key):
        """Highlight active feature button"""
        self.current_feature = feature_key
        for key, btn in self.feature_buttons.items():
            if key == feature_key:
                btn.configure(fg_color="#00D4FF", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="#2B2B2B", text_color="#FFFFFF")

    def clear_content(self):
        """Clear content area"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def initialize_ai_manager(self):
        """Initialize AI manager for enhanced features"""
        try:
            # Get API key from gemini service instead of passing the service object
            api_key = getattr(self.gemini_service, 'api_key', None) if self.gemini_service else None
            self.ai_manager = AIManager(api_key)
            self.ai_status.configure(text="✅ AI Ready", text_color="#4ECDC4")
        except Exception as e:
            logger.error(f"Failed to initialize AI manager: {e}")
            self.ai_status.configure(text="❌ AI Unavailable", text_color="#FF6B6B")

    def show_weather_analysis(self):
        """Show weather analysis feature"""
        self.set_active_feature("analysis")
        self.clear_content()
        
        # Create analysis interface
        analysis_frame = ctk.CTkFrame(self.content_frame, fg_color="#1E1E1E")
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            analysis_frame,
            text="🔍 AI Weather Analysis",
            font=("Arial", 18, "bold"),
            text_color="#00D4FF"
        )
        title.pack(pady=20)
        
        # Analysis content
        self.create_analysis_content(analysis_frame)

    def show_activity_suggestions(self):
        """Show activity suggestions feature"""
        self.set_active_feature("activities")
        self.clear_content()
        
        # Create activities interface
        activities_frame = ctk.CTkFrame(self.content_frame, fg_color="#1E1E1E")
        activities_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            activities_frame,
            text="🎯 AI Activity Suggestions",
            font=("Arial", 18, "bold"),
            text_color="#00D4FF"
        )
        title.pack(pady=20)
        
        # Activities content
        self.create_activities_content(activities_frame)

    def show_weather_poetry(self):
        """Show weather poetry feature"""
        self.set_active_feature("poetry")
        self.clear_content()
        
        # Create poetry interface
        poetry_frame = ctk.CTkFrame(self.content_frame, fg_color="#1E1E1E")
        poetry_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            poetry_frame,
            text="🎭 AI Weather Poetry",
            font=("Arial", 18, "bold"),
            text_color="#00D4FF"
        )
        title.pack(pady=20)
        
        # Poetry content
        self.create_poetry_content(poetry_frame)

    def show_ml_predictions(self):
        """Show ML predictions feature"""
        self.set_active_feature("ml_predictions")
        self.clear_content()
        
        # Create ML predictions interface
        ml_frame = ctk.CTkFrame(self.content_frame, fg_color="#1E1E1E")
        ml_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            ml_frame,
            text="🤖 ML Weather Predictions",
            font=("Arial", 18, "bold"),
            text_color="#00D4FF"
        )
        title.pack(pady=20)
        
        # ML predictions content
        self.create_ml_predictions_content(ml_frame)

    def show_weather_insights(self):
        """Show weather insights feature"""
        self.set_active_feature("insights")
        self.clear_content()
        
        # Create insights interface
        insights_frame = ctk.CTkFrame(self.content_frame, fg_color="#1E1E1E")
        insights_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            insights_frame,
            text="📊 AI Weather Insights",
            font=("Arial", 18, "bold"),
            text_color="#00D4FF"
        )
        title.pack(pady=20)
        
        # Insights content
        self.create_insights_content(insights_frame)

    def show_weather_stories(self):
        """Show weather stories feature"""
        self.set_active_feature("stories")
        self.clear_content()
        
        # Create stories interface
        stories_frame = ctk.CTkFrame(self.content_frame, fg_color="#1E1E1E")
        stories_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            stories_frame,
            text="🎵 AI Weather Stories",
            font=("Arial", 18, "bold"),
            text_color="#00D4FF"
        )
        title.pack(pady=20)
        
        # Stories content
        self.create_stories_content(stories_frame)

    def create_analysis_content(self, parent):
        """Create weather analysis content"""
        # Analysis input
        input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)
        
        analysis_label = ctk.CTkLabel(
            input_frame,
            text="Ask AI to analyze current weather conditions:",
            font=("Arial", 12)
        )
        analysis_label.pack(anchor="w", pady=(0, 5))
        
        self.analysis_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="e.g., What should I wear today?",
            height=40,
            font=("Arial", 12)
        )
        self.analysis_entry.pack(fill="x", pady=(0, 10))
        
        analyze_btn = ctk.CTkButton(
            input_frame,
            text="🔍 Analyze Weather",
            command=self.perform_weather_analysis,
            fg_color="#00D4FF",
            hover_color="#0099CC",
            height=40
        )
        analyze_btn.pack(pady=5)
        
        # Results area
        self.analysis_results = ctk.CTkTextbox(
            parent,
            height=300,
            font=("Arial", self.font_size),
            wrap="word"
        )
        self.analysis_results.pack(fill="both", expand=True, padx=20, pady=10)
        self.analysis_results.insert("1.0", "AI weather analysis results will appear here...")
        self.text_widgets.append(self.analysis_results)

    def create_activities_content(self, parent):
        """Create activity suggestions content"""
        # Activity preferences
        prefs_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prefs_frame.pack(fill="x", padx=20, pady=10)
        
        prefs_label = ctk.CTkLabel(
            prefs_frame,
            text="Activity Preferences:",
            font=("Arial", 12, "bold")
        )
        prefs_label.pack(anchor="w", pady=(0, 5))
        
        # Activity type selector
        self.activity_type = ctk.CTkComboBox(
            prefs_frame,
            values=["Outdoor", "Indoor", "Sports", "Relaxation", "Adventure", "Cultural"],
            height=35
        )
        self.activity_type.pack(fill="x", pady=(0, 10))
        self.activity_type.set("Outdoor")
        
        suggest_btn = ctk.CTkButton(
            prefs_frame,
            text="🎯 Get AI Suggestions",
            command=self.generate_activity_suggestions,
            fg_color="#4ECDC4",
            hover_color="#3BA99C",
            height=40
        )
        suggest_btn.pack(pady=5)
        
        # Suggestions area
        self.activities_results = ctk.CTkTextbox(
            parent,
            height=300,
            font=("Arial", self.font_size),
            wrap="word"
        )
        self.activities_results.pack(fill="both", expand=True, padx=20, pady=10)
        self.activities_results.insert("1.0", "AI activity suggestions will appear here...")
        self.text_widgets.append(self.activities_results)

    def create_poetry_content(self, parent):
        """Create weather poetry content"""
        # Poetry style selector
        style_frame = ctk.CTkFrame(parent, fg_color="transparent")
        style_frame.pack(fill="x", padx=20, pady=10)
        
        style_label = ctk.CTkLabel(
            style_frame,
            text="Poetry Style:",
            font=("Arial", 12, "bold")
        )
        style_label.pack(anchor="w", pady=(0, 5))
        
        self.poetry_style = ctk.CTkComboBox(
            style_frame,
            values=["Haiku", "Sonnet", "Free Verse", "Limerick", "Acrostic"],
            height=35
        )
        self.poetry_style.pack(fill="x", pady=(0, 10))
        self.poetry_style.set("Haiku")
        
        generate_btn = ctk.CTkButton(
            style_frame,
            text="🎭 Generate Poetry",
            command=self.generate_weather_poetry,
            fg_color="#9B59B6",
            hover_color="#8E44AD",
            height=40
        )
        generate_btn.pack(pady=5)
        
        # Poetry display
        self.poetry_results = ctk.CTkTextbox(
            parent,
            height=300,
            font=("Arial", self.font_size),
            wrap="word"
        )
        self.poetry_results.pack(fill="both", expand=True, padx=20, pady=10)
        self.poetry_results.insert("1.0", "AI-generated weather poetry will appear here...")
        self.text_widgets.append(self.poetry_results)

    def create_insights_content(self, parent):
        """Create weather insights content"""
        # Insights controls
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        insights_btn = ctk.CTkButton(
            controls_frame,
            text="📊 Generate Weather Insights",
            command=self.generate_weather_insights,
            fg_color="#E67E22",
            hover_color="#D35400",
            height=40
        )
        insights_btn.pack(pady=5)
        
        # Insights display
        self.insights_results = ctk.CTkTextbox(
            parent,
            height=300,
            font=("Arial", self.font_size),
            wrap="word"
        )
        self.insights_results.pack(fill="both", expand=True, padx=20, pady=10)
        self.insights_results.insert("1.0", "AI weather insights will appear here...")
        self.text_widgets.append(self.insights_results)

    def create_stories_content(self, parent):
        """Create weather stories content"""
        # Story controls
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        story_label = ctk.CTkLabel(
            controls_frame,
            text="Story Theme:",
            font=("Arial", 12, "bold")
        )
        story_label.pack(anchor="w", pady=(0, 5))
        
        self.story_theme = ctk.CTkComboBox(
            controls_frame,
            values=["Adventure", "Mystery", "Romance", "Fantasy", "Sci-Fi"],
            height=35
        )
        self.story_theme.pack(fill="x", pady=(0, 10))
        self.story_theme.set("Adventure")
        
        story_btn = ctk.CTkButton(
            controls_frame,
            text="🎵 Create Weather Story",
            command=self.generate_weather_story,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            height=40
        )
        story_btn.pack(pady=5)
        
        # Story display
        self.stories_results = ctk.CTkTextbox(
            parent,
            height=300,
            font=("Arial", self.font_size),
            wrap="word"
        )
        self.stories_results.pack(fill="both", expand=True, padx=20, pady=10)
        self.stories_results.insert("1.0", "AI-generated weather stories will appear here...")
        self.text_widgets.append(self.stories_results)

    def create_ml_predictions_content(self, parent):
        """Create ML predictions interface"""
        # Control panel
        control_frame = ctk.CTkFrame(parent, fg_color="#2B2B2B")
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # Prediction horizon selector
        horizon_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        horizon_frame.pack(fill="x", padx=10, pady=10)
        
        horizon_label = ctk.CTkLabel(
            horizon_frame,
            text="Prediction Horizon:",
            font=("Arial", 12, "bold")
        )
        horizon_label.pack(side="left", padx=(0, 10))
        
        self.prediction_horizon = ctk.CTkOptionMenu(
            horizon_frame,
            values=["6 hours", "12 hours", "24 hours", "48 hours"],
            width=120
        )
        self.prediction_horizon.pack(side="left", padx=5)
        self.prediction_horizon.set("24 hours")
        
        # Model type selector
        model_label = ctk.CTkLabel(
            horizon_frame,
            text="Model Type:",
            font=("Arial", 12, "bold")
        )
        model_label.pack(side="left", padx=(20, 10))
        
        self.model_type = ctk.CTkOptionMenu(
            horizon_frame,
            values=["Gradient Boosting", "Random Forest", "Ensemble"],
            width=140
        )
        self.model_type.pack(side="left", padx=5)
        self.model_type.set("Ensemble")
        
        # Generate button
        predict_btn = ctk.CTkButton(
            horizon_frame,
            text="🔮 Generate Predictions",
            command=self.generate_ml_predictions,
            fg_color="#00D4FF",
            hover_color="#0099CC",
            height=35,
            width=180
        )
        predict_btn.pack(side="right", padx=10)
        
        # Results area with tabs
        results_frame = ctk.CTkFrame(parent, fg_color="#2B2B2B")
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create tabview for different result types
        self.ml_tabview = ctk.CTkTabview(results_frame)
        self.ml_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Predictions tab
        predictions_tab = self.ml_tabview.add("📈 Predictions")
        self.ml_predictions_results = ctk.CTkTextbox(
            predictions_tab,
            height=250,
            font=("Consolas", 11),
            wrap="word"
        )
        self.ml_predictions_results.pack(fill="both", expand=True, padx=10, pady=10)
        self.ml_predictions_results.insert("1.0", "🤖 ML weather predictions will appear here...\n\nClick 'Generate Predictions' to start!")
        
        # Model Info tab
        model_info_tab = self.ml_tabview.add("🔧 Model Info")
        self.model_info_results = ctk.CTkTextbox(
            model_info_tab,
            height=250,
            font=("Consolas", 11),
            wrap="word"
        )
        self.model_info_results.pack(fill="both", expand=True, padx=10, pady=10)
        self.model_info_results.insert("1.0", "📊 Model information and accuracy metrics will appear here...")
        
        # Uncertainty tab
        uncertainty_tab = self.ml_tabview.add("📊 Uncertainty")
        self.uncertainty_results = ctk.CTkTextbox(
            uncertainty_tab,
            height=250,
            font=("Consolas", 11),
            wrap="word"
        )
        self.uncertainty_results.pack(fill="both", expand=True, padx=10, pady=10)
        self.uncertainty_results.insert("1.0", "🎯 Prediction confidence and uncertainty bounds will appear here...")

    def generate_ml_predictions(self):
        """Generate ML weather predictions"""
        # Clear previous results
        self.ml_predictions_results.delete("1.0", "end")
        self.model_info_results.delete("1.0", "end")
        self.uncertainty_results.delete("1.0", "end")
        
        # Show loading state
        self.ml_predictions_results.insert("1.0", "🔄 Generating ML predictions...\n\nThis may take a moment for model training...")
        self.model_info_results.insert("1.0", "🔄 Preparing model information...")
        self.uncertainty_results.insert("1.0", "🔄 Calculating uncertainty bounds...")
        
        def predict():
            try:
                # Get current weather data
                current_weather = self.weather_service.get_current_weather()
                if not current_weather:
                    self.after(0, lambda: self.display_ml_error("❌ No current weather data available for predictions."))
                    return
                
                # Convert weather data to format expected by ML service
                weather_dict = {
                    'temp': getattr(current_weather, 'temperature', 20),
                    'humidity': getattr(current_weather, 'humidity', 50),
                    'pressure': getattr(current_weather, 'pressure', 1013),
                    'wind_speed': getattr(current_weather, 'wind_speed', 5),
                    'clouds': getattr(current_weather, 'cloud_cover', 50),
                    'visibility': getattr(current_weather, 'visibility', 10000),
                    'dt': datetime.now().timestamp()
                }
                
                # Get prediction horizon
                horizon_text = self.prediction_horizon.get()
                hours_map = {"6 hours": 6, "12 hours": 12, "24 hours": 24, "48 hours": 48}
                hours_ahead = hours_map.get(horizon_text, 24)
                
                # Generate predictions
                predictions = self.ml_weather_service.predict_weather(weather_dict, hours_ahead)
                
                # Format and display results
                self.after(0, lambda: self.display_ml_predictions(predictions, hours_ahead))
                self.after(0, lambda: self.display_model_info())
                self.after(0, lambda: self.display_uncertainty_info(predictions))
                
            except Exception as e:
                logger.error(f"ML prediction error: {e}")
                self.after(0, lambda: self.display_ml_error(f"❌ Prediction failed: {str(e)}"))
        
        threading.Thread(target=predict, daemon=True).start()
    
    def display_ml_predictions(self, predictions, hours_ahead):
        """Display ML prediction results"""
        self.ml_predictions_results.delete("1.0", "end")
        
        if not predictions:
            self.ml_predictions_results.insert("1.0", "❌ No predictions generated. Model may need training data.")
            return
        
        # Format predictions display
        result_text = f"🤖 **ML Weather Predictions ({hours_ahead} hours)**\n"
        result_text += f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Show first few predictions in detail
        result_text += "📊 **Detailed Predictions:**\n\n"
        for i, pred in enumerate(predictions[:12]):  # Show first 12 hours in detail
            hour = pred.get('hour', i+1)
            temp = pred.get('temperature', 0)
            temp_min = pred.get('temperature_min', temp-2)
            temp_max = pred.get('temperature_max', temp+2)
            humidity = pred.get('humidity', 50)
            confidence = pred.get('confidence', 0.5)
            
            result_text += f"Hour {hour:2d}: {temp:5.1f}°C ({temp_min:4.1f}-{temp_max:4.1f}) | "
            result_text += f"Humidity: {humidity:3.0f}% | Confidence: {confidence:.1%}\n"
        
        # Summary statistics
        if len(predictions) > 12:
            result_text += f"\n📈 **Summary ({len(predictions)} total predictions):**\n\n"
            temps = [p.get('temperature', 0) for p in predictions]
            humidities = [p.get('humidity', 50) for p in predictions]
            confidences = [p.get('confidence', 0.5) for p in predictions]
            
            result_text += f"Temperature Range: {min(temps):.1f}°C to {max(temps):.1f}°C\n"
            result_text += f"Average Temperature: {sum(temps)/len(temps):.1f}°C\n"
            result_text += f"Humidity Range: {min(humidities):.0f}% to {max(humidities):.0f}%\n"
            result_text += f"Average Confidence: {sum(confidences)/len(confidences):.1%}\n"
        
        self.ml_predictions_results.insert("1.0", result_text)
    
    def display_model_info(self):
        """Display model information"""
        self.model_info_results.delete("1.0", "end")
        
        info_text = "🔧 **ML Model Information**\n\n"
        info_text += "**Models Used:**\n"
        info_text += "• Temperature: Gradient Boosting Regressor\n"
        info_text += "• Humidity: Random Forest Regressor\n\n"
        
        info_text += "**Model Features:**\n"
        info_text += "• Temperature, Humidity, Pressure\n"
        info_text += "• Wind Speed, Cloud Cover, Visibility\n"
        info_text += "• Time features (hour, day, month)\n\n"
        
        info_text += "**Training Status:**\n"
        if hasattr(self.ml_weather_service, 'models') and self.ml_weather_service.models:
            info_text += "✅ Models loaded and ready\n"
            info_text += f"• Available models: {list(self.ml_weather_service.models.keys())}\n"
        else:
            info_text += "⚠️ Models training on-demand\n"
            info_text += "• First prediction may take longer\n"
        
        info_text += "\n**Model Configuration:**\n"
        info_text += "• Gradient Boosting: 100 estimators, depth=5\n"
        info_text += "• Random Forest: 100 estimators, depth=10\n"
        info_text += "• Feature scaling: StandardScaler\n"
        
        self.model_info_results.insert("1.0", info_text)
    
    def display_uncertainty_info(self, predictions):
        """Display uncertainty and confidence information"""
        self.uncertainty_results.delete("1.0", "end")
        
        if not predictions:
            self.uncertainty_results.insert("1.0", "❌ No uncertainty data available.")
            return
        
        uncertainty_text = "🎯 **Prediction Uncertainty Analysis**\n\n"
        
        # Calculate uncertainty metrics
        confidences = [p.get('confidence', 0.5) for p in predictions]
        temp_ranges = [p.get('temperature_max', 0) - p.get('temperature_min', 0) for p in predictions]
        
        uncertainty_text += "**Confidence Metrics:**\n"
        uncertainty_text += f"• Average Confidence: {sum(confidences)/len(confidences):.1%}\n"
        uncertainty_text += f"• Confidence Range: {min(confidences):.1%} - {max(confidences):.1%}\n"
        uncertainty_text += f"• High Confidence Hours: {sum(1 for c in confidences if c > 0.8)}\n\n"
        
        uncertainty_text += "**Temperature Uncertainty:**\n"
        uncertainty_text += f"• Average Uncertainty: ±{sum(temp_ranges)/len(temp_ranges)/2:.1f}°C\n"
        uncertainty_text += f"• Max Uncertainty: ±{max(temp_ranges)/2:.1f}°C\n"
        uncertainty_text += f"• Min Uncertainty: ±{min(temp_ranges)/2:.1f}°C\n\n"
        
        uncertainty_text += "**Prediction Quality:**\n"
        high_conf = sum(1 for c in confidences if c > 0.8)
        med_conf = sum(1 for c in confidences if 0.6 <= c <= 0.8)
        low_conf = sum(1 for c in confidences if c < 0.6)
        
        uncertainty_text += f"• High Confidence: {high_conf} hours ({high_conf/len(confidences):.1%})\n"
        uncertainty_text += f"• Medium Confidence: {med_conf} hours ({med_conf/len(confidences):.1%})\n"
        uncertainty_text += f"• Low Confidence: {low_conf} hours ({low_conf/len(confidences):.1%})\n\n"
        
        uncertainty_text += "**Notes:**\n"
        uncertainty_text += "• Confidence decreases with prediction horizon\n"
        uncertainty_text += "• Uncertainty bounds represent model variance\n"
        uncertainty_text += "• Higher uncertainty indicates less reliable predictions\n"
        
        self.uncertainty_results.insert("1.0", uncertainty_text)
    
    def display_ml_error(self, error_message):
        """Display ML prediction error"""
        self.ml_predictions_results.delete("1.0", "end")
        self.ml_predictions_results.insert("1.0", error_message)
        
        self.model_info_results.delete("1.0", "end")
        self.model_info_results.insert("1.0", "❌ Model information unavailable due to error.")
        
        self.uncertainty_results.delete("1.0", "end")
        self.uncertainty_results.insert("1.0", "❌ Uncertainty analysis unavailable due to error.")

    def generate_activity_suggestions(self):
        """Generate AI activity suggestions"""
        if not self.ai_manager:
            self.activities_results.delete("1.0", "end")
            self.activities_results.insert("1.0", "❌ AI service unavailable. Please check your configuration.")
            return
        
        activity_type = self.activity_type.get()
        self.activities_results.delete("1.0", "end")
        self.activities_results.insert("1.0", "🔄 Generating activity suggestions...")
        
        def generate():
            try:
                weather_data = self.weather_service.get_current_weather()
                if weather_data:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    suggestions = loop.run_until_complete(self.ai_manager.get_activity_suggestions(weather_data))
                    
                    # Format the result for display
                    if isinstance(suggestions, dict) and 'suggestions' in suggestions:
                        formatted_result = "🎯 **Activity Suggestions:**\n\n"
                        for activity in suggestions['suggestions'][:5]:  # Show top 5
                            formatted_result += f"• **{activity.get('name', 'Activity')}**\n"
                            formatted_result += f"  {activity.get('description', 'No description')}\n\n"
                    else:
                        formatted_result = str(suggestions)
                    
                    self.after(0, lambda: self.display_activities_result(formatted_result))
                else:
                    self.after(0, lambda: self.display_activities_result("❌ No weather data available for suggestions."))
            except Exception as activity_error:
                logger.error(f"Activity suggestion error: {activity_error}")
                self.after(0, lambda: self.display_activities_result(f"❌ Suggestion failed: {str(activity_error)}"))
        
        threading.Thread(target=generate, daemon=True).start()

    def perform_weather_analysis(self):
        """Perform AI weather analysis"""
        if not self.ai_manager:
            self.analysis_results.delete("1.0", "end")
            self.analysis_results.insert("1.0", "❌ AI service unavailable. Please check your configuration.")
            return
        
        query = self.analysis_entry.get().strip()
        if not query:
            query = "Analyze the current weather conditions"
        
        self.analysis_results.delete("1.0", "end")
        self.analysis_results.insert("1.0", "🔄 Analyzing weather conditions...")
        
        def analyze():
            try:
                # Get current weather data
                weather_data = self.weather_service.get_current_weather()
                if weather_data:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    analysis = loop.run_until_complete(self.ai_manager.get_weather_insights(weather_data))
                    self.after(0, lambda: self.display_analysis_result(analysis))
                else:
                    self.after(0, lambda: self.display_analysis_result("❌ No weather data available for analysis."))
            except Exception as analysis_error:
                logger.error(f"Weather analysis error: {analysis_error}")
                self.after(0, lambda: self.display_analysis_result(f"❌ Analysis failed: {str(analysis_error)}"))
        
        threading.Thread(target=analyze, daemon=True).start()

    def display_analysis_result(self, result):
        """Display analysis result"""
        self.analysis_results.delete("1.0", "end")
        self.analysis_results.insert("1.0", result)

    def display_activities_result(self, result):
        """Display activities result"""
        self.activities_results.delete("1.0", "end")
        self.activities_results.insert("1.0", result)

    def generate_weather_poetry(self):
        """Generate AI weather poetry"""
        if not self.ai_manager:
            self.poetry_results.delete("1.0", "end")
            self.poetry_results.insert("1.0", "❌ AI service unavailable. Please check your configuration.")
            return
        
        style = self.poetry_style.get()
        self.poetry_results.delete("1.0", "end")
        self.poetry_results.insert("1.0", "🔄 Composing weather poetry...")
        
        def generate():
            try:
                weather_data = self.weather_service.get_current_weather()
                if weather_data:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    poetry = loop.run_until_complete(self.ai_manager.generate_weather_poetry(style.lower(), weather_data))
                    
                    # Format the result for display
                    if isinstance(poetry, dict) and 'poem' in poetry:
                        formatted_result = f"🎭 **{poetry.get('style', 'Poetry').title()}**\n\n{poetry['poem']}"
                    else:
                        formatted_result = str(poetry)
                    
                    self.after(0, lambda: self.display_poetry_result(formatted_result))
                else:
                    self.after(0, lambda: self.display_poetry_result("❌ No weather data available for poetry."))
            except Exception as poetry_error:
                logger.error(f"Poetry generation error: {poetry_error}")
                self.after(0, lambda: self.display_poetry_result(f"❌ Poetry generation failed: {str(poetry_error)}"))
        
        threading.Thread(target=generate, daemon=True).start()

    def display_poetry_result(self, result):
        """Display poetry result"""
        self.poetry_results.delete("1.0", "end")
        self.poetry_results.insert("1.0", result)

    def generate_weather_insights(self):
        """Generate AI weather insights"""
        if not self.ai_manager:
            self.insights_results.delete("1.0", "end")
            self.insights_results.insert("1.0", "❌ AI service unavailable. Please check your configuration.")
            return
        
        self.insights_results.delete("1.0", "end")
        self.insights_results.insert("1.0", "🔄 Generating weather insights...")
        
        def generate():
            try:
                weather_data = self.weather_service.get_current_weather()
                if weather_data:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    insights = loop.run_until_complete(self.ai_manager.get_weather_insights(weather_data))
                    self.after(0, lambda: self.display_insights_result(insights))
                else:
                    self.after(0, lambda: self.display_insights_result("❌ No weather data available for insights."))
            except Exception as insights_error:
                logger.error(f"Insights generation error: {insights_error}")
                self.after(0, lambda: self.display_insights_result(f"❌ Insights generation failed: {str(insights_error)}"))
        
        threading.Thread(target=generate, daemon=True).start()

    def display_insights_result(self, result):
        """Display insights result"""
        self.insights_results.delete("1.0", "end")
        self.insights_results.insert("1.0", result)

    def generate_weather_story(self):
        """Generate AI weather story"""
        if not self.ai_manager:
            self.stories_results.delete("1.0", "end")
            self.stories_results.insert("1.0", "❌ AI service unavailable. Please check your configuration.")
            return
        
        theme = self.story_theme.get()
        self.stories_results.delete("1.0", "end")
        self.stories_results.insert("1.0", "🔄 Creating weather story...")
        
        def generate():
            try:
                weather_data = self.weather_service.get_current_weather()
                if weather_data:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    story = loop.run_until_complete(self.ai_manager.generate_weather_story(weather_data, "short"))
                    
                    # Format the result for display
                    if isinstance(story, dict) and 'story' in story:
                        formatted_result = f"📖 **Weather Story**\n\n{story['story']}"
                    else:
                        formatted_result = str(story)
                    
                    self.after(0, lambda: self.display_stories_result(formatted_result))
                else:
                    self.after(0, lambda: self.display_stories_result("❌ No weather data available for story."))
            except Exception as story_error:
                logger.error(f"Story generation error: {story_error}")
                self.after(0, lambda: self.display_stories_result(f"❌ Story generation failed: {str(story_error)}"))
        
        threading.Thread(target=generate, daemon=True).start()

    def display_stories_result(self, result):
        """Display stories result"""
        self.stories_results.delete("1.0", "end")
        self.stories_results.insert("1.0", result)

    def create_font_controls(self, parent):
        """Create font size control buttons."""
        font_frame = ctk.CTkFrame(parent, fg_color="transparent")
        font_frame.pack(side="left", padx=(50, 0))

        # Font size label
        font_label = ctk.CTkLabel(
            font_frame,
            text="Font:",
            font=("Arial", 12, "bold"),
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
            font=("Arial", 10, "bold"),
        )
        decrease_btn.pack(side="left", padx=2)

        # Current font size display
        self.font_size_label = ctk.CTkLabel(
            font_frame,
            text=str(self.font_size),
            font=("Arial", 12, "bold"),
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
            font=("Arial", 10, "bold"),
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