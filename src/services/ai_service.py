#!/usr/bin/env python3
"""
Enhanced AI Service with Multi-Model Fallback System

This service provides intelligent load distribution across multiple AI models
from both OpenAI and Google Gemini, with automatic fallback mechanisms.
"""

import json
import random
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Optional imports for AI services
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


class ModelProvider(Enum):
    """AI model providers."""
    OPENAI = "openai"
    GEMINI = "gemini"


class ModelTier(Enum):
    """Model performance tiers."""
    PREMIUM = "premium"  # High capability, higher cost
    STANDARD = "standard"  # Balanced performance/cost
    FAST = "fast"  # Fast response, lower cost
    FALLBACK = "fallback"  # Basic functionality


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    name: str
    provider: ModelProvider
    tier: ModelTier
    max_tokens: int
    temperature: float
    cost_per_token: float  # Relative cost (1.0 = baseline)
    avg_response_time: float  # Seconds
    rate_limit_rpm: int  # Requests per minute
    enabled: bool = True


class AIService:
    """Enhanced AI service with multi-model fallback system."""
    
    def __init__(self, config_service):
        self.config_service = config_service
        self.logger = logging.getLogger(__name__)
        
        # Model configurations
        self.models = self._initialize_model_configs()
        
        # Active clients
        self.openai_client = None
        self.gemini_models = {}
        
        # Usage tracking
        self.usage_stats = {
            'requests_by_model': {},
            'errors_by_model': {},
            'total_tokens': 0,
            'session_start': time.time()
        }
        
        # Load balancing state
        self.last_used_model = {}
        self.model_cooldowns = {}  # For rate limiting
        
        # Initialize AI clients
        self._initialize_clients()
    
    def _initialize_model_configs(self) -> List[ModelConfig]:
        """Initialize model configurations with fallback hierarchy."""
        return [
            # OpenAI Models (ordered by preference)
            ModelConfig(
                name="gpt-4o",
                provider=ModelProvider.OPENAI,
                tier=ModelTier.PREMIUM,
                max_tokens=4096,
                temperature=0.7,
                cost_per_token=3.0,
                avg_response_time=3.5,
                rate_limit_rpm=500
            ),
            ModelConfig(
                name="gpt-4o-mini",
                provider=ModelProvider.OPENAI,
                tier=ModelTier.STANDARD,
                max_tokens=4096,
                temperature=0.7,
                cost_per_token=1.5,
                avg_response_time=2.5,
                rate_limit_rpm=1000
            ),
            ModelConfig(
                name="gpt-3.5-turbo",
                provider=ModelProvider.OPENAI,
                tier=ModelTier.FAST,
                max_tokens=4096,
                temperature=0.7,
                cost_per_token=1.0,
                avg_response_time=1.5,
                rate_limit_rpm=3000
            ),
            
            # Gemini Models (ordered by preference)
            ModelConfig(
                name="gemini-1.5-pro",
                provider=ModelProvider.GEMINI,
                tier=ModelTier.PREMIUM,
                max_tokens=8192,
                temperature=0.7,
                cost_per_token=2.5,
                avg_response_time=4.0,
                rate_limit_rpm=300
            ),
            ModelConfig(
                name="gemini-1.5-flash",
                provider=ModelProvider.GEMINI,
                tier=ModelTier.STANDARD,
                max_tokens=8192,
                temperature=0.7,
                cost_per_token=1.2,
                avg_response_time=2.0,
                rate_limit_rpm=1000
            ),
            ModelConfig(
                name="gemini-1.0-pro",
                provider=ModelProvider.GEMINI,
                tier=ModelTier.FAST,
                max_tokens=4096,
                temperature=0.7,
                cost_per_token=0.8,
                avg_response_time=1.8,
                rate_limit_rpm=2000
            ),
        ]
    
    def _initialize_clients(self):
        """Initialize AI service clients."""
        # Initialize OpenAI
        if OPENAI_AVAILABLE:
            try:
                api_key = self.config_service.get('openai_api_key')
                if api_key and api_key.strip():
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.logger.info("✅ OpenAI client initialized")
                else:
                    self.logger.warning("⚠️ OpenAI API key not found")
            except Exception as e:
                self.logger.error(f"❌ OpenAI initialization error: {e}")
        
        # Initialize Gemini
        if GENAI_AVAILABLE:
            try:
                api_key = self.config_service.get('gemini_api_key')
                if api_key and api_key.strip():
                    genai.configure(api_key=api_key)
                    
                    # Initialize different Gemini models
                    gemini_model_names = [m.name for m in self.models if m.provider == ModelProvider.GEMINI]
                    for model_name in gemini_model_names:
                        try:
                            self.gemini_models[model_name] = genai.GenerativeModel(model_name)
                            self.logger.info(f"✅ Gemini model {model_name} initialized")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Failed to initialize {model_name}: {e}")
                else:
                    self.logger.warning("⚠️ Gemini API key not found")
            except Exception as e:
                self.logger.error(f"❌ Gemini initialization error: {e}")
    
    def get_available_models(self, tier: Optional[ModelTier] = None) -> List[ModelConfig]:
        """Get list of available models, optionally filtered by tier."""
        available = []
        
        for model in self.models:
            if not model.enabled:
                continue
                
            if tier and model.tier != tier:
                continue
            
            # Check if model is actually available
            if model.provider == ModelProvider.OPENAI and self.openai_client:
                available.append(model)
            elif model.provider == ModelProvider.GEMINI and model.name in self.gemini_models:
                available.append(model)
        
        return available
    
    def _select_optimal_model(self, 
                            preferred_tier: Optional[ModelTier] = None,
                            load_balance: bool = True) -> Optional[ModelConfig]:
        """Select the optimal model based on availability, performance, and load balancing."""
        available_models = self.get_available_models(preferred_tier)
        
        if not available_models:
            # Fallback to any available model
            available_models = self.get_available_models()
        
        if not available_models:
            return None
        
        # Filter out models in cooldown (rate limited)
        current_time = time.time()
        available_models = [
            m for m in available_models 
            if m.name not in self.model_cooldowns or 
               current_time > self.model_cooldowns[m.name]
        ]
        
        if not available_models:
            # All models are in cooldown, use the one with shortest remaining cooldown
            available_models = self.get_available_models(preferred_tier)
            if not available_models:
                available_models = self.get_available_models()
        
        if not available_models:
            return None
        
        if load_balance:
            # Implement weighted round-robin based on cost and performance
            weights = []
            for model in available_models:
                # Lower cost and faster response = higher weight
                try:
                    if model.cost_per_token and model.avg_response_time and model.cost_per_token > 0 and model.avg_response_time > 0:
                        weight = (1.0 / model.cost_per_token) * (1.0 / model.avg_response_time)
                    else:
                        weight = 1.0  # Default weight if values are invalid
                except (TypeError, ZeroDivisionError):
                    weight = 1.0  # Default weight on error
                
                # Reduce weight if model was used recently
                if model.name in self.last_used_model:
                    time_since_last = current_time - self.last_used_model[model.name]
                    if time_since_last < 60:  # Within last minute
                        weight *= 0.5
                
                weights.append(weight)
            
            # Weighted random selection
            selected_model = random.choices(available_models, weights=weights)[0]
        else:
            # Select highest tier available
            tier_order = [ModelTier.PREMIUM, ModelTier.STANDARD, ModelTier.FAST, ModelTier.FALLBACK]
            for tier in tier_order:
                tier_models = [m for m in available_models if m.tier == tier]
                if tier_models:
                    selected_model = tier_models[0]
                    break
            else:
                selected_model = available_models[0]
        
        # Update usage tracking
        self.last_used_model[selected_model.name] = current_time
        
        return selected_model
    
    def _generate_with_openai(self, model_config: ModelConfig, prompt: str, system_prompt: str) -> str:
        """Generate response using OpenAI model."""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        response = self.openai_client.chat.completions.create(
            model=model_config.name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature
        )
        
        # Update usage stats
        if hasattr(response, 'usage') and response.usage:
            self.usage_stats['total_tokens'] += response.usage.total_tokens
        
        return response.choices[0].message.content
    
    def _generate_with_gemini(self, model_config: ModelConfig, prompt: str, system_prompt: str) -> str:
        """Generate response using Gemini model."""
        if model_config.name not in self.gemini_models:
            raise Exception(f"Gemini model {model_config.name} not initialized")
        
        # Combine system prompt and user prompt for Gemini
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        model = self.gemini_models[model_config.name]
        response = model.generate_content(full_prompt)
        
        return response.text
    
    def _handle_rate_limit(self, model_config: ModelConfig, error: Exception):
        """Handle rate limiting by setting cooldown period."""
        cooldown_duration = 60  # 1 minute default
        
        # Adjust cooldown based on error type
        error_str = str(error).lower()
        if 'rate limit' in error_str or '429' in error_str:
            cooldown_duration = 120  # 2 minutes for rate limits
        elif 'quota' in error_str:
            cooldown_duration = 300  # 5 minutes for quota issues
        
        self.model_cooldowns[model_config.name] = time.time() + cooldown_duration
        self.logger.warning(f"⏰ Model {model_config.name} in cooldown for {cooldown_duration}s")
    
    def generate_suggestions(self, 
                           prompt: str, 
                           system_prompt: str = None,
                           preferred_tier: Optional[ModelTier] = None,
                           max_retries: int = 3) -> Tuple[str, str]:
        """
        Generate AI suggestions with intelligent model selection and fallback.
        
        Returns:
            Tuple of (response_text, model_used)
        """
        if system_prompt is None:
            system_prompt = (
                "You are an AI assistant that provides personalized activity suggestions "
                "based on weather conditions. Always respond with valid JSON in the exact format requested."
            )
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Select optimal model
                model_config = self._select_optimal_model(preferred_tier, load_balance=True)
                
                if not model_config:
                    raise Exception("No available AI models")
                
                self.logger.info(f"🤖 Using {model_config.name} (tier: {model_config.tier.value})")
                
                # Update usage stats
                if model_config.name not in self.usage_stats['requests_by_model']:
                    self.usage_stats['requests_by_model'][model_config.name] = 0
                self.usage_stats['requests_by_model'][model_config.name] += 1
                
                # Generate response
                start_time = time.time()
                
                if model_config.provider == ModelProvider.OPENAI:
                    response_text = self._generate_with_openai(model_config, prompt, system_prompt)
                elif model_config.provider == ModelProvider.GEMINI:
                    response_text = self._generate_with_gemini(model_config, prompt, system_prompt)
                else:
                    raise Exception(f"Unknown provider: {model_config.provider}")
                
                response_time = time.time() - start_time
                self.logger.info(f"✅ Generated response in {response_time:.2f}s using {model_config.name}")
                
                return response_text, model_config.name
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # Update error stats
                if model_config:
                    if model_config.name not in self.usage_stats['errors_by_model']:
                        self.usage_stats['errors_by_model'][model_config.name] = 0
                    self.usage_stats['errors_by_model'][model_config.name] += 1
                    
                    # Handle specific error types
                    if any(keyword in error_msg.lower() for keyword in ['rate limit', '429', 'quota']):
                        self._handle_rate_limit(model_config, e)
                    
                    self.logger.warning(f"⚠️ Error with {model_config.name}: {error_msg}")
                
                # If this was the last attempt, don't retry
                if attempt == max_retries - 1:
                    break
                
                # Wait before retry
                time.sleep(min(2 ** attempt, 10))  # Exponential backoff, max 10s
        
        # All attempts failed
        self.logger.error(f"❌ All AI models failed after {max_retries} attempts. Last error: {last_error}")
        raise Exception(f"AI generation failed: {last_error}")
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics."""
        session_duration = time.time() - self.usage_stats['session_start']
        
        return {
            **self.usage_stats,
            'session_duration_minutes': session_duration / 60 if session_duration else 0,
            'available_models': [m.name for m in self.get_available_models()],
            'models_in_cooldown': list(self.model_cooldowns.keys())
        }
    
    def reset_cooldowns(self):
        """Reset all model cooldowns (for testing/admin purposes)."""
        self.model_cooldowns.clear()
        self.logger.info("🔄 All model cooldowns reset")
    
    def generate_activity_suggestions(self, 
                                    weather_data: Dict, 
                                    user_preferences: Dict = None,
                                    prompt: str = None) -> Dict:
        """
        Generate activity suggestions based on weather data and user preferences.
        
        Args:
            weather_data: Current weather information
            user_preferences: User activity preferences
            prompt: Custom prompt (optional)
        
        Returns:
            Dictionary containing activity suggestions
        """
        if user_preferences is None:
            user_preferences = {}
        
        # Create comprehensive prompt if not provided
        if prompt is None:
            prompt = self._create_activity_prompt(weather_data, user_preferences)
        
        system_prompt = (
            "You are an AI assistant that provides personalized activity suggestions "
            "based on weather conditions and user preferences. Always respond with valid JSON "
            "in the exact format: {\"activities\": [{\"name\": \"Activity Name\", "
            "\"description\": \"Brief description\", \"category\": \"indoor/outdoor\", "
            "\"duration\": \"estimated time\", \"difficulty\": \"easy/medium/hard\"}]}"
        )
        
        try:
            # Determine optimal model tier based on request complexity
            preferred_tier = ModelTier.STANDARD
            if len(str(weather_data)) > 500 or len(str(user_preferences)) > 200:
                preferred_tier = ModelTier.PREMIUM  # Use premium for complex requests
            
            # Generate suggestions
            response_text, model_used = self.generate_suggestions(
                prompt=prompt,
                system_prompt=system_prompt,
                preferred_tier=preferred_tier
            )
            
            # Parse JSON response
            try:
                suggestions = json.loads(response_text)
                if 'activities' in suggestions and isinstance(suggestions['activities'], list):
                    self.logger.info(f"✅ Generated {len(suggestions['activities'])} activities using {model_used}")
                    return suggestions
                else:
                    raise ValueError("Invalid response format")
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"⚠️ Failed to parse AI response: {e}")
                # Try to extract activities from malformed JSON
                return self._extract_activities_from_text(response_text)
        
        except Exception as e:
            self.logger.error(f"❌ Activity suggestion generation failed: {e}")
            return self._get_default_activities(weather_data)
    
    def _create_activity_prompt(self, weather_data: Dict, user_preferences: Dict) -> str:
        """Create a comprehensive prompt for activity suggestions."""
        # Debug logging
        print(f"🔍 Debug - weather_data type: {type(weather_data)}, value: {weather_data}")
        print(f"🔍 Debug - user_preferences type: {type(user_preferences)}, value: {user_preferences}")
        
        # Extract weather information
        temp = weather_data.get('temperature', 'unknown')
        condition = weather_data.get('condition', 'unknown')
        humidity = weather_data.get('humidity', 'unknown')
        wind_speed = weather_data.get('wind_speed', 'unknown')
        
        # Ensure user_preferences is a dictionary
        if not isinstance(user_preferences, dict):
            print(f"⚠️ Warning: user_preferences is not a dict, got {type(user_preferences)}")
            user_preferences = {}
        
        # Extract user preferences
        preferred_activities = user_preferences.get('activities', [])
        fitness_level = user_preferences.get('fitness_level', 'moderate')
        time_available = user_preferences.get('time_available', '1-2 hours')
        
        prompt = f"""
Current Weather Conditions:
- Temperature: {temp}°F
- Condition: {condition}
- Humidity: {humidity}%
- Wind Speed: {wind_speed} mph

User Preferences:
- Preferred Activities: {', '.join(preferred_activities) if preferred_activities else 'No specific preferences'}
- Fitness Level: {fitness_level}
- Available Time: {time_available}

Please suggest 5-8 personalized activities that are appropriate for these weather conditions and user preferences. 
Include both indoor and outdoor options when possible. Consider safety, comfort, and enjoyment.

Respond with valid JSON only."""
        
        return prompt
    
    def _extract_activities_from_text(self, text: str) -> Dict:
        """Extract activities from malformed AI response text."""
        try:
            # Try to find JSON-like content
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback: create basic structure
        return {
            "activities": [
                {
                    "name": "Weather-Appropriate Activity",
                    "description": "AI suggested activity based on current conditions",
                    "category": "mixed",
                    "duration": "30-60 minutes",
                    "difficulty": "easy"
                }
            ]
        }
    
    def _get_default_activities(self, weather_data: Dict) -> Dict:
        """Get default activities when AI generation fails."""
        temp = weather_data.get('temperature', 70)
        condition = weather_data.get('condition', '').lower()
        
        if temp > 75 and 'rain' not in condition:
            activities = [
                {
                    "name": "Outdoor Walk",
                    "description": "Enjoy a pleasant walk in nice weather",
                    "category": "outdoor",
                    "duration": "30-45 minutes",
                    "difficulty": "easy"
                },
                {
                    "name": "Picnic in the Park",
                    "description": "Perfect weather for outdoor dining",
                    "category": "outdoor",
                    "duration": "1-2 hours",
                    "difficulty": "easy"
                }
            ]
        elif temp < 40 or 'rain' in condition or 'snow' in condition:
            activities = [
                {
                    "name": "Indoor Reading",
                    "description": "Cozy up with a good book",
                    "category": "indoor",
                    "duration": "1-2 hours",
                    "difficulty": "easy"
                },
                {
                    "name": "Home Workout",
                    "description": "Stay active indoors",
                    "category": "indoor",
                    "duration": "30-60 minutes",
                    "difficulty": "medium"
                }
            ]
        else:
            activities = [
                {
                    "name": "Light Exercise",
                    "description": "Moderate activity suitable for current weather",
                    "category": "mixed",
                    "duration": "30-45 minutes",
                    "difficulty": "easy"
                }
            ]
        
        return {"activities": activities}