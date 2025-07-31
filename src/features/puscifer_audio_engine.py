# puscifer_audio_engine.py
"""
PUSCIFER-INSPIRED WEATHER AUDIO ENGINE
Maximum atmospheric intensity weather dashboard audio system
"""

import pygame
import numpy as np
import asyncio
import threading
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from enum import Enum
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import random

logger = logging.getLogger(__name__)

class WeatherMood(Enum):
    """Puscifer-inspired weather mood classifications"""
    MAYNARD_RAIN = "atmospheric_tension"        # Dark, brooding, layered
    DESERT_SUN = "electronic_drive"             # Pulsing, synthetic, hypnotic  
    STORM_CHAOS = "industrial_chaos"            # Aggressive, distorted, intense
    FOG_MYSTERY = "ambient_void"                # Spacious, ethereal, haunting
    SNOW_ISOLATION = "minimal_cold"             # Sparse, crystalline, isolated
    CLEAR_TRANSCENDENCE = "cosmic_elevation"    # Expansive, soaring, otherworldly

@dataclass
class AudioProfile:
    """Puscifer-style audio profile for weather conditions"""
    name: str
    spotify_search_terms: List[str]
    audio_characteristics: Dict[str, float]  # tempo, energy, valence, etc.
    ui_sound_pack: str
    background_ambience: str
    transition_style: str

class PusciferAudioEngine:
    """Main audio engine inspired by Puscifer's atmospheric mastery"""
    
    def __init__(self, spotify_client_id: str, spotify_client_secret: str, redirect_uri: str = "http://127.0.0.1:8000/callback"):
        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret
        self.redirect_uri = redirect_uri
        self.spotify = None
        self.current_mood = None
        self.audio_profiles = self._create_puscifer_profiles()
        self.ambient_player = None
        self.ui_sounds = {}
        self.is_playing = False
        
        # Initialize pygame for audio
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        logger.info("🎵 Puscifer Audio Engine initialized")
    
    def _create_puscifer_profiles(self) -> Dict[WeatherMood, AudioProfile]:
        """Create Maynard-approved weather audio profiles"""
        return {
            WeatherMood.MAYNARD_RAIN: AudioProfile(
                name="Maynard's Rain Ritual",
                spotify_search_terms=[
                    "puscifer", "tool atmospheric", "a perfect circle rain",
                    "dark ambient rain", "industrial ambient", "maynard james keenan",
                    "atmospheric metal", "progressive dark", "nine inch nails ambient"
                ],
                audio_characteristics={
                    "tempo": 0.3,      # Slow, methodical
                    "energy": 0.6,     # Controlled intensity
                    "valence": 0.2,    # Dark, brooding
                    "instrumentalness": 0.8,  # Mostly instrumental
                    "acousticness": 0.1,      # Electronic/processed
                },
                ui_sound_pack="industrial_wet",
                background_ambience="rain_layers_distorted",
                transition_style="fade_crossfilter"
            ),
            
            WeatherMood.DESERT_SUN: AudioProfile(
                name="Desert Drive Hypnosis",
                spotify_search_terms=[
                    "puscifer conditions of my parole", "queens of the stone age",
                    "desert rock", "stoner rock instrumental", "kyuss ambient",
                    "electronic desert", "synthwave dark", "outrun atmospheric"
                ],
                audio_characteristics={
                    "tempo": 0.7,      # Driving, pulsing
                    "energy": 0.8,     # High energy
                    "valence": 0.6,    # Neutral to positive
                    "instrumentalness": 0.6,
                    "acousticness": 0.2,
                },
                ui_sound_pack="synth_desert",
                background_ambience="desert_wind_electronic",
                transition_style="beat_match_crossfade"
            ),
            
            WeatherMood.STORM_CHAOS: AudioProfile(
                name="Chaos Theory Weather",
                spotify_search_terms=[
                    "tool lateralus", "puscifer remix", "industrial metal",
                    "nine inch nails storm", "ministry atmospheric",
                    "aggressive electronic", "dark techno", "harsh ambient"
                ],
                audio_characteristics={
                    "tempo": 0.9,      # Intense, chaotic
                    "energy": 0.95,    # Maximum intensity
                    "valence": 0.1,    # Dark, aggressive
                    "instrumentalness": 0.5,
                    "acousticness": 0.0,
                },
                ui_sound_pack="industrial_storm",
                background_ambience="thunder_processed",
                transition_style="impact_cut"
            ),
            
            WeatherMood.FOG_MYSTERY: AudioProfile(
                name="Ethereal Void Navigation",
                spotify_search_terms=[
                    "a perfect circle thirteenth step", "puscifer ambient",
                    "dark ambient fog", "ethereal wave", "atmospheric black metal",
                    "space ambient", "void ambient", "cosmic horror ambient"
                ],
                audio_characteristics={
                    "tempo": 0.2,      # Very slow, floating
                    "energy": 0.3,     # Low energy, mysterious
                    "valence": 0.3,    # Melancholic, mysterious
                    "instrumentalness": 0.9,
                    "acousticness": 0.3,
                },
                ui_sound_pack="ethereal_mystery",
                background_ambience="fog_whispers",
                transition_style="ghostly_morph"
            ),
            
            WeatherMood.SNOW_ISOLATION: AudioProfile(
                name="Winter Meditation",
                spotify_search_terms=[
                    "puscifer conditions", "minimal techno cold",
                    "winter ambient", "isolationist ambient", "arctic ambient",
                    "minimal electronic", "cold wave", "post-rock ambient"
                ],
                audio_characteristics={
                    "tempo": 0.4,      # Slow, contemplative
                    "energy": 0.4,     # Subdued energy
                    "valence": 0.4,    # Neutral, introspective
                    "instrumentalness": 0.8,
                    "acousticness": 0.4,
                },
                ui_sound_pack="crystalline_minimal",
                background_ambience="snow_silence",
                transition_style="crystalline_fade"
            ),
            
            WeatherMood.CLEAR_TRANSCENDENCE: AudioProfile(
                name="Cosmic Elevation",
                spotify_search_terms=[
                    "tool fear inoculum", "puscifer money shot",
                    "progressive transcendent", "cosmic ambient",
                    "space rock", "psychedelic ambient", "transcendental music"
                ],
                audio_characteristics={
                    "tempo": 0.6,      # Moderate, flowing
                    "energy": 0.7,     # Uplifting energy
                    "valence": 0.8,    # Positive, transcendent
                    "instrumentalness": 0.7,
                    "acousticness": 0.3,
                },
                ui_sound_pack="cosmic_uplifting",
                background_ambience="clear_sky_harmony",
                transition_style="ascending_crossfade"
            )
        }
    
    async def initialize_spotify(self):
        """Initialize Spotify with Puscifer-approved scopes"""
        try:
            scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-modify-public playlist-modify-private"
            
            auth_manager = SpotifyOAuth(
                client_id=self.spotify_client_id,
                client_secret=self.spotify_client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope
            )
            
            self.spotify = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test connection
            user = self.spotify.current_user()
            logger.info(f"🎵 Spotify connected for user: {user['display_name']}")
            
            # Create/find weather playlists
            await self._setup_weather_playlists()
            
            return True
            
        except Exception as e:
            logger.error(f"Spotify initialization failed: {e}")
            return False
    
    async def _setup_weather_playlists(self):
        """Create Puscifer-inspired weather playlists"""
        try:
            user_id = self.spotify.current_user()['id']
            
            for mood, profile in self.audio_profiles.items():
                playlist_name = f"Weather Dashboard: {profile.name}"
                
                # Check if playlist exists
                playlists = self.spotify.current_user_playlists()
                existing = None
                
                for playlist in playlists['items']:
                    if playlist['name'] == playlist_name:
                        existing = playlist
                        break
                
                if not existing:
                    # Create new playlist
                    playlist = self.spotify.user_playlist_create(
                        user_id,
                        playlist_name,
                        description=f"Puscifer-inspired weather mood: {mood.value}"
                    )
                    
                    # Populate with tracks
                    await self._populate_playlist(playlist['id'], profile)
                    
                    logger.info(f"✅ Created playlist: {playlist_name}")
                
        except Exception as e:
            logger.error(f"Playlist setup failed: {e}")
    
    async def _populate_playlist(self, playlist_id: str, profile: AudioProfile):
        """Populate playlist with Puscifer-approved tracks"""
        try:
            track_uris = []
            
            for search_term in profile.spotify_search_terms:
                results = self.spotify.search(
                    q=search_term,
                    type='track',
                    limit=10
                )
                
                for track in results['tracks']['items']:
                    # Get audio features
                    features = self.spotify.audio_features([track['id']])[0]
                    if features:
                        # Check if track matches profile characteristics
                        score = self._calculate_track_match_score(features, profile)
                        if score > 0.7:  # Good match
                            track_uris.append(track['uri'])
                
                if len(track_uris) >= 50:  # Enough tracks
                    break
            
            # Add tracks to playlist in batches
            if track_uris:
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i+100]
                    self.spotify.playlist_add_items(playlist_id, batch)
                
                logger.info(f"✅ Added {len(track_uris)} tracks to playlist")
            
        except Exception as e:
            logger.error(f"Playlist population failed: {e}")
    
    def _calculate_track_match_score(self, features: Dict, profile: AudioProfile) -> float:
        """Calculate how well a track matches the Puscifer profile"""
        if not features:
            return 0.0
        
        score = 0.0
        characteristics = profile.audio_characteristics
        
        # Weight different characteristics
        weights = {
            'tempo': 0.2,
            'energy': 0.3,
            'valence': 0.2,
            'instrumentalness': 0.15,
            'acousticness': 0.15
        }
        
        for char, target_value in characteristics.items():
            if char in features and char in weights:
                # Normalize tempo (typically 0-200 BPM)
                if char == 'tempo':
                    feature_value = min(features[char] / 200.0, 1.0)
                else:
                    feature_value = features[char]
                
                # Calculate similarity (closer = higher score)
                similarity = 1.0 - abs(feature_value - target_value)
                score += similarity * weights[char]
        
        return score
    
    def set_weather_mood(self, weather_condition: str, temperature: float = None):
        """Set audio mood based on weather with Puscifer intensity"""
        try:
            # Map weather to Puscifer mood
            mood_mapping = {
                'rain': WeatherMood.MAYNARD_RAIN,
                'drizzle': WeatherMood.MAYNARD_RAIN,
                'thunderstorm': WeatherMood.STORM_CHAOS,
                'storm': WeatherMood.STORM_CHAOS,
                'snow': WeatherMood.SNOW_ISOLATION,
                'clear': WeatherMood.CLEAR_TRANSCENDENCE,
                'sunny': WeatherMood.DESERT_SUN,
                'fog': WeatherMood.FOG_MYSTERY,
                'mist': WeatherMood.FOG_MYSTERY,
                'clouds': WeatherMood.FOG_MYSTERY,
            }
            
            # Temperature adjustments (Maynard would approve)
            new_mood = mood_mapping.get(weather_condition.lower(), WeatherMood.CLEAR_TRANSCENDENCE)
            
            if temperature:
                if temperature > 30:  # Hot - desert vibes
                    new_mood = WeatherMood.DESERT_SUN
                elif temperature < 0:  # Freezing - isolation
                    new_mood = WeatherMood.SNOW_ISOLATION
            
            if new_mood != self.current_mood:
                self.current_mood = new_mood
                asyncio.create_task(self._transition_to_mood(new_mood))
                
                logger.info(f"🎵 Weather mood set to: {new_mood.value}")
            
        except Exception as e:
            logger.error(f"Failed to set weather mood: {e}")
    
    async def _transition_to_mood(self, mood: WeatherMood):
        """Transition to new mood with Puscifer-style effects"""
        try:
            profile = self.audio_profiles[mood]
            
            # Start ambient background
            self._start_ambient_background(profile.background_ambience)
            
            # Switch Spotify playlist
            if self.spotify:
                await self._switch_spotify_playlist(profile.name)
            
            # Update UI sounds
            self._load_ui_sound_pack(profile.ui_sound_pack)
            
            logger.info(f"✅ Transitioned to mood: {profile.name}")
            
        except Exception as e:
            logger.error(f"Mood transition failed: {e}")
    
    def _start_ambient_background(self, ambience_type: str):
        """Start Puscifer-style ambient background"""
        try:
            # Load ambient sound file
            ambient_file = f"assets/audio/ambient/{ambience_type}.wav"
            
            if pygame.mixer.get_init():
                # Stop current ambient
                pygame.mixer.stop()
                
                # Load and play new ambient
                ambient_sound = pygame.mixer.Sound(ambient_file)
                ambient_sound.set_volume(0.3)  # Subtle background
                pygame.mixer.Channel(0).play(ambient_sound, loops=-1)
                
                logger.info(f"🌊 Started ambient: {ambience_type}")
            
        except Exception as e:
            logger.warning(f"Ambient background failed: {e}")
    
    async def _switch_spotify_playlist(self, playlist_name: str):
        """Switch to weather-appropriate Spotify playlist"""
        try:
            if not self.spotify:
                return
            
            full_name = f"Weather Dashboard: {playlist_name}"
            
            # Find playlist
            playlists = self.spotify.current_user_playlists()
            target_playlist = None
            
            for playlist in playlists['items']:
                if playlist['name'] == full_name:
                    target_playlist = playlist
                    break
            
            if target_playlist:
                # Get user's active device
                devices = self.spotify.devices()
                if devices['devices']:
                    device_id = devices['devices'][0]['id']
                    
                    # Start playback
                    self.spotify.start_playback(
                        device_id=device_id,
                        context_uri=target_playlist['uri']
                    )
                    
                    logger.info(f"🎵 Started playlist: {playlist_name}")
            
        except Exception as e:
            logger.warning(f"Spotify playlist switch failed: {e}")
    
    def _load_ui_sound_pack(self, sound_pack: str):
        """Load Puscifer-inspired UI sound effects"""
        try:
            sound_pack_path = f"assets/audio/ui/{sound_pack}/"
            
            ui_sound_files = {
                'click': f"{sound_pack_path}click.wav",
                'hover': f"{sound_pack_path}hover.wav",
                'tab_switch': f"{sound_pack_path}tab_switch.wav",
                'weather_update': f"{sound_pack_path}weather_update.wav",
                'error': f"{sound_pack_path}error.wav",
                'success': f"{sound_pack_path}success.wav",
            }
            
            # Load sounds
            for sound_name, file_path in ui_sound_files.items():
                try:
                    sound = pygame.mixer.Sound(file_path)
                    sound.set_volume(0.5)
                    self.ui_sounds[sound_name] = sound
                except:
                    pass  # Sound file not found, use default
            
            logger.info(f"🔊 Loaded UI sound pack: {sound_pack}")
            
        except Exception as e:
            logger.warning(f"UI sound pack loading failed: {e}")
    
    def play_ui_sound(self, sound_name: str):
        """Play Puscifer-style UI sound effect"""
        try:
            if sound_name in self.ui_sounds:
                pygame.mixer.Channel(1).play(self.ui_sounds[sound_name])
        except Exception as e:
            logger.debug(f"UI sound play failed: {e}")
    
    def create_weather_audio_visualizer(self, parent_widget):
        """Create real-time audio visualizer for weather mood"""
        try:
            import tkinter as tk
            from tkinter import Canvas
            import customtkinter as ctk
            
            # Create visualizer frame
            viz_frame = ctk.CTkFrame(parent_widget, height=100)
            viz_frame.pack(fill='x', padx=10, pady=5)
            
            # Canvas for audio visualization
            canvas = Canvas(
                viz_frame,
                height=80,
                bg='#1a1a1a',
                highlightthickness=0
            )
            canvas.pack(fill='x', padx=10, pady=10)
            
            # Start visualizer animation
            self._start_audio_visualizer(canvas)
            
            return viz_frame
            
        except Exception as e:
            logger.error(f"Audio visualizer creation failed: {e}")
            return None
    
    def _start_audio_visualizer(self, canvas):
        """Start Puscifer-style audio visualizer animation"""
        def update_visualizer():
            try:
                canvas.delete("all")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                
                if width > 1 and height > 1:
                    # Generate audio-reactive bars
                    num_bars = 20
                    bar_width = width // num_bars
                    
                    for i in range(num_bars):
                        # Simulate audio levels (replace with real audio analysis)
                        level = random.uniform(0.1, 1.0) if self.is_playing else 0.1
                        
                        bar_height = int(height * level * 0.8)
                        x1 = i * bar_width
                        x2 = x1 + bar_width - 2
                        y1 = height - bar_height
                        y2 = height
                        
                        # Puscifer-inspired color scheme
                        colors = ['#00FFB3', '#FF6B35', '#7209b7', '#f72585']
                        color = random.choice(colors)
                        
                        canvas.create_rectangle(
                            x1, y1, x2, y2,
                            fill=color,
                            outline=color
                        )
                
                # Schedule next update
                canvas.after(50, update_visualizer)
                
            except Exception as e:
                logger.debug(f"Visualizer update failed: {e}")
        
        # Start the animation
        canvas.after(100, update_visualizer)

# Integration class for the main weather dashboard
class PusciferWeatherIntegration:
    """Integration layer for Puscifer audio in weather dashboard"""
    
    def __init__(self, dashboard, spotify_client_id: str, spotify_client_secret: str, redirect_uri: str = "http://127.0.0.1:8000/callback"):
        self.dashboard = dashboard
        self.audio_engine = PusciferAudioEngine(spotify_client_id, spotify_client_secret, redirect_uri)
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the Puscifer audio system"""
        try:
            success = await self.audio_engine.initialize_spotify()
            if success:
                self.is_initialized = True
                logger.info("🎵 Puscifer weather integration ready!")
                
                # Add audio controls to dashboard
                self._add_audio_controls()
                
                # Add visualizer
                self._add_audio_visualizer()
                
            return success
            
        except Exception as e:
            logger.error(f"Puscifer integration failed: {e}")
            return False
    
    def on_weather_update(self, weather_data: Dict):
        """Handle weather updates with Puscifer intensity"""
        try:
            if self.is_initialized:
                condition = weather_data.get('condition', 'clear')
                temperature = weather_data.get('temperature')
                
                self.audio_engine.set_weather_mood(condition, temperature)
                
        except Exception as e:
            logger.error(f"Weather audio update failed: {e}")
    
    def _add_audio_controls(self):
        """Add Puscifer-style audio controls to dashboard"""
        try:
            import customtkinter as ctk
            
            # Find appropriate parent (could be settings tab or main frame)
            parent = getattr(self.dashboard, 'settings_frame', self.dashboard)
            
            # Audio control frame
            audio_frame = ctk.CTkFrame(parent)
            audio_frame.pack(fill='x', padx=10, pady=5)
            
            # Title
            title = ctk.CTkLabel(
                audio_frame,
                text="🎵 PUSCIFER WEATHER AUDIO",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title.pack(pady=5)
            
            # Controls
            controls_frame = ctk.CTkFrame(audio_frame, fg_color="transparent")
            controls_frame.pack(fill='x', padx=10, pady=5)
            
            # Enable/disable toggle
            self.audio_enabled = ctk.CTkSwitch(
                controls_frame,
                text="Enable Weather Audio",
                command=self._toggle_audio
            )
            self.audio_enabled.pack(side='left', padx=10)
            
            # Volume control
            volume_label = ctk.CTkLabel(controls_frame, text="Volume:")
            volume_label.pack(side='left', padx=(20, 5))
            
            self.volume_slider = ctk.CTkSlider(
                controls_frame,
                from_=0,
                to=100,
                command=self._set_volume
            )
            self.volume_slider.set(70)
            self.volume_slider.pack(side='left', padx=5)
            
            # Current mood display
            self.mood_label = ctk.CTkLabel(
                audio_frame,
                text="Current Mood: Initializing...",
                font=ctk.CTkFont(size=12)
            )
            self.mood_label.pack(pady=5)
            
        except Exception as e:
            logger.error(f"Audio controls creation failed: {e}")
    
    def _add_audio_visualizer(self):
        """Add audio visualizer to dashboard"""
        try:
            # Find main content area
            parent = getattr(self.dashboard, 'main_frame', self.dashboard)
            
            visualizer = self.audio_engine.create_weather_audio_visualizer(parent)
            if visualizer:
                logger.info("✅ Audio visualizer added to dashboard")
                
        except Exception as e:
            logger.error(f"Audio visualizer integration failed: {e}")
    
    def _toggle_audio(self):
        """Toggle Puscifer audio system"""
        try:
            enabled = self.audio_enabled.get()
            self.audio_engine.is_playing = enabled
            
            if enabled:
                logger.info("🎵 Puscifer audio enabled")
            else:
                logger.info("🔇 Puscifer audio disabled")
                pygame.mixer.stop()
                
        except Exception as e:
            logger.error(f"Audio toggle failed: {e}")
    
    def _set_volume(self, value):
        """Set audio volume"""
        try:
            volume = float(value) / 100.0
            pygame.mixer.set_volume(volume)
            
        except Exception as e:
            logger.error(f"Volume set failed: {e}")

# Usage example for integration:
"""
# In your main dashboard initialization:
async def initialize_puscifer_audio(self):
    puscifer_integration = PusciferWeatherIntegration(
        self,
        spotify_client_id="your_spotify_client_id",
        spotify_client_secret="your_spotify_client_secret"
    )
    
    success = await puscifer_integration.initialize()
    if success:
        # Connect weather updates
        self.weather_service.add_callback(puscifer_integration.on_weather_update)
        self.puscifer_audio = puscifer_integration
        
        logger.info("🎵 PUSCIFER WEATHER AUDIO SYSTEM ACTIVATED!")
"""