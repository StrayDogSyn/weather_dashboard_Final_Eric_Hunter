"""Main Activity Suggester Class

Combines all mixins to create the complete ActivitySuggester component.
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Dict, Optional
from datetime import datetime
import json
import sqlite3
from pathlib import Path
import threading
import traceback

from ...theme import DataTerminalTheme
from ..base_component import BaseComponent
from services.ai_service import AIService, ModelTier

# Import mixins
from .ai_providers import AIProvidersMixin
from .database_manager import DatabaseManagerMixin
from .ui_components import UIComponentsMixin
from .suggestion_engine import SuggestionEngineMixin

# Optional imports for legacy AI services
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False


class ActivitySuggester(AIProvidersMixin, DatabaseManagerMixin, UIComponentsMixin, SuggestionEngineMixin, BaseComponent):
    """Activity Suggester component that provides AI-powered activity recommendations based on weather."""
    
    def __init__(self, parent, weather_service, config_service, **kwargs):
        """Initialize the Activity Suggester.
        
        Args:
            parent: Parent widget
            weather_service: Weather service instance
            config_service: Configuration service instance
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, **kwargs)
        
        # Store services
        self.weather_service = weather_service
        self.config_service = config_service
        
        # Initialize enhanced AI service
        self.ai_service = AIService(config_service)
        
        # Initialize legacy AI services
        self._initialize_gemini()
        self._initialize_openai()
        
        # Initialize data storage
        self.suggestions = []
        self.current_weather = None
        self.selected_category = "All"
        
        # Setup database
        self._setup_database()
        
        # Create UI
        self._create_ui()
        
        # Load initial suggestions
        self._refresh_suggestions()
    
    def __del__(self):
        """Clean up database connection."""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass