"""Spotify Web Player Component

Embeds a web browser with Spotify Web Playback SDK to create an active Spotify device
within the weather dashboard application.
"""

import customtkinter as ctk
import threading
import time
import logging
from typing import Optional, Callable
from pathlib import Path

# CEF Python doesn't support Python 3.13+, so we'll use pywebview only
CEF_AVAILABLE = False
    
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

from flask import Flask, render_template_string, request, jsonify
from services.logging_service import LoggingService


class SpotifyWebPlayer(ctk.CTkFrame):
    """Spotify Web Player with embedded browser for Web Playback SDK"""
    
    def __init__(self, parent, spotify_client_id: str, access_token: str, 
                 on_player_ready: Optional[Callable] = None,
                 on_player_state_changed: Optional[Callable] = None):
        super().__init__(parent)
        
        self.logger = LoggingService().get_logger("SpotifyWebPlayer")
        self.spotify_client_id = spotify_client_id
        self.access_token = access_token
        self.on_player_ready = on_player_ready
        self.on_player_state_changed = on_player_state_changed
        
        self.flask_app = None
        self.flask_thread = None
        self.web_server_port = 8001
        self.device_id = None
        self.player_state = {}
        
        self._setup_ui()
        self._start_web_server()
        
    def _setup_ui(self):
        """Setup the UI components"""
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="🎵 Spotify Player",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # Status
        self.status_label = ctk.CTkLabel(
            self, 
            text="Initializing Spotify Player...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Player controls frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(pady=10, padx=10, fill="x")
        
        # Control buttons
        self.prev_button = ctk.CTkButton(
            self.controls_frame,
            text="⏮",
            width=50,
            command=self.previous_track
        )
        self.prev_button.pack(side="left", padx=5)
        
        self.play_pause_button = ctk.CTkButton(
            self.controls_frame,
            text="⏸",
            width=50,
            command=self.toggle_play_pause
        )
        self.play_pause_button.pack(side="left", padx=5)
        
        self.next_button = ctk.CTkButton(
            self.controls_frame,
            text="⏭",
            width=50,
            command=self.next_track
        )
        self.next_button.pack(side="left", padx=5)
        
        # Volume control
        self.volume_label = ctk.CTkLabel(self.controls_frame, text="Volume:")
        self.volume_label.pack(side="left", padx=(20, 5))
        
        self.volume_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.set_volume
        )
        self.volume_slider.set(50)
        self.volume_slider.pack(side="left", padx=5, fill="x", expand=True)
        
        # Current track info
        self.track_info_frame = ctk.CTkFrame(self)
        self.track_info_frame.pack(pady=5, padx=10, fill="x")
        
        self.track_label = ctk.CTkLabel(
            self.track_info_frame,
            text="No track playing",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.track_label.pack(pady=5)
        
        self.artist_label = ctk.CTkLabel(
            self.track_info_frame,
            text="",
            font=ctk.CTkFont(size=10)
        )
        self.artist_label.pack()
        
        # Web player frame (will contain embedded browser)
        self.web_frame = ctk.CTkFrame(self, height=1)  # Minimal height, hidden
        self.web_frame.pack(pady=5, padx=10, fill="x")
        
        # Initialize web player
        self.after(1000, self._initialize_web_player)
        
    def _start_web_server(self):
        """Start Flask web server for Spotify Web Player"""
        self.flask_app = Flask(__name__)
        self.flask_app.logger.disabled = True  # Disable Flask logging
        
        @self.flask_app.route('/')
        def player():
            return render_template_string(self._get_player_html())
            
        @self.flask_app.route('/api/player-ready', methods=['POST'])
        def player_ready():
            data = request.get_json()
            self.device_id = data.get('device_id')
            self.logger.info(f"Spotify Web Player ready with device ID: {self.device_id}")
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.after_idle(lambda: self._safe_update_widget(self.status_label, 'text', "✅ Spotify Player Ready"))
            if self.on_player_ready:
                self.on_player_ready(self.device_id)
            return jsonify({'status': 'success'})
            
        @self.flask_app.route('/api/player-state', methods=['POST'])
        def player_state():
            data = request.get_json()
            self.player_state = data
            self._update_ui_from_state(data)
            if self.on_player_state_changed:
                self.on_player_state_changed(data)
            return jsonify({'status': 'success'})
            
        @self.flask_app.route('/api/control/<action>', methods=['POST'])
        def control(action):
            # Handle control commands from the web player
            return jsonify({'status': 'success'})
            
        def run_flask():
            self.flask_app.run(host='127.0.0.1', port=self.web_server_port, debug=False, use_reloader=False)
            
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        self.logger.info(f"Spotify Web Player server started on port {self.web_server_port}")
        
    def _get_player_html(self):
        """Generate HTML for Spotify Web Player"""
        return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Spotify Web Player</title>
    <script src="https://sdk.scdn.co/spotify-player.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #121212;
            color: #ffffff;
            font-family: Arial, sans-serif;
        }}
        .player-container {{
            text-align: center;
            max-width: 400px;
            margin: 0 auto;
        }}
        .status {{
            margin: 10px 0;
            padding: 10px;
            background: #1db954;
            border-radius: 5px;
            font-size: 12px;
        }}
        .track-info {{
            margin: 15px 0;
            padding: 10px;
            background: #282828;
            border-radius: 5px;
            display: none;
        }}
        .track-name {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .track-artist {{
            color: #b3b3b3;
            font-size: 14px;
        }}
        .controls {{
            margin: 15px 0;
            display: none;
        }}
        .control-btn {{
            background: #1db954;
            border: none;
            color: white;
            padding: 10px 15px;
            margin: 0 5px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
        }}
        .control-btn:hover {{
            background: #1ed760;
        }}
        .control-btn:disabled {{
            background: #535353;
            cursor: not-allowed;
        }}
        .volume-control {{
            margin: 10px 0;
            display: none;
        }}
        .volume-slider {{
            width: 100%;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="player-container">
        <div id="status" class="status">Initializing Spotify Player...</div>
        
        <div id="track-info" class="track-info">
            <div id="track-name" class="track-name">No track selected</div>
            <div id="track-artist" class="track-artist">Select a track from Spotify</div>
        </div>
        
        <div id="controls" class="controls">
            <button id="prev-btn" class="control-btn">⏮️</button>
            <button id="play-btn" class="control-btn">▶️</button>
            <button id="next-btn" class="control-btn">⏭️</button>
        </div>
        
        <div id="volume-control" class="volume-control">
            <label for="volume-slider">Volume:</label>
            <input type="range" id="volume-slider" class="volume-slider" min="0" max="1" step="0.1" value="0.5">
        </div>
    </div>
    
    <script>
        window.onSpotifyWebPlaybackSDKReady = () => {{
            const token = '{self.access_token}';
            const player = new Spotify.Player({{
                name: 'Weather Dashboard Player',
                getOAuthToken: cb => {{ cb(token); }},
                volume: 0.5
            }});
            
            // Error handling
            player.addListener('initialization_error', ({{ message }}) => {{
                console.error('Failed to initialize:', message);
                let errorMsg = 'Failed to initialize: ' + message;
                if (message.includes('premium') || message.includes('Premium')) {{
                    errorMsg = '⚠️ Spotify Premium required for Web Player';
                }} else if (message.includes('authentication') || message.includes('token')) {{
                    errorMsg = '⚠️ Authentication failed - please reconnect Spotify';
                }}
                document.getElementById('status').textContent = errorMsg;
            }});
            
            player.addListener('authentication_error', ({{ message }}) => {{
                console.error('Failed to authenticate:', message);
                document.getElementById('status').textContent = '⚠️ Authentication failed: ' + message;
            }});
            
            player.addListener('account_error', ({{ message }}) => {{
                console.error('Failed to validate account:', message);
                let errorMsg = 'Account validation failed: ' + message;
                if (message.includes('premium') || message.includes('Premium')) {{
                    errorMsg = '⚠️ Spotify Premium account required';
                }}
                document.getElementById('status').textContent = errorMsg;
            }});
            
            player.addListener('playback_error', ({{ message }}) => {{
                console.error('Failed to perform playback:', message);
            }});
            
            // Playback status updates
            player.addListener('player_state_changed', state => {{
                if (state) {{
                    // Update UI with current track info
                    const track = state.track_window.current_track;
                    if (track) {{
                        document.getElementById('track-name').textContent = track.name;
                        document.getElementById('track-artist').textContent = track.artists.map(artist => artist.name).join(', ');
                    }}
                    
                    // Update play/pause button
                    const playBtn = document.getElementById('play-btn');
                    if (state.paused) {{
                        playBtn.textContent = '▶️';
                        playBtn.title = 'Play';
                    }} else {{
                        playBtn.textContent = '⏸️';
                        playBtn.title = 'Pause';
                    }}
                    
                    fetch('/api/player-state', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify(state)
                    }});
                }}
            }});
            
            // Ready
            player.addListener('ready', ({{ device_id }}) => {{
                console.log('Ready with Device ID', device_id);
                document.getElementById('status').textContent = 'Player Ready!';
                
                // Show controls when player is ready
                document.getElementById('controls').style.display = 'block';
                document.getElementById('volume-control').style.display = 'block';
                document.getElementById('track-info').style.display = 'block';
                
                fetch('/api/player-ready', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ device_id: device_id }})
                }});
            }});
            
            // Not Ready
            player.addListener('not_ready', ({{ device_id }}) => {{
                console.log('Device ID has gone offline', device_id);
                document.getElementById('status').textContent = 'Device offline: ' + device_id;
            }});
            
            // Connect to the player!
            player.connect().then(success => {{
                if (success) {{
                    console.log('Successfully connected to Spotify!');
                }} else {{
                    console.log('Failed to connect to Spotify');
                    document.getElementById('status').textContent = 'Failed to connect to Spotify';
                }}
            }});
            
            // Add control button event listeners
            document.getElementById('play-btn').addEventListener('click', () => {{
                player.togglePlay().then(() => {{
                    console.log('Toggled playback');
                }}).catch(err => {{
                    console.error('Error toggling playback:', err);
                }});
            }});
            
            document.getElementById('prev-btn').addEventListener('click', () => {{
                player.previousTrack().then(() => {{
                    console.log('Previous track');
                }}).catch(err => {{
                    console.error('Error going to previous track:', err);
                }});
            }});
            
            document.getElementById('next-btn').addEventListener('click', () => {{
                player.nextTrack().then(() => {{
                    console.log('Next track');
                }}).catch(err => {{
                    console.error('Error going to next track:', err);
                }});
            }});
            
            document.getElementById('volume-slider').addEventListener('input', (e) => {{
                const volume = parseFloat(e.target.value);
                player.setVolume(volume).then(() => {{
                    console.log('Volume set to', volume);
                }}).catch(err => {{
                    console.error('Error setting volume:', err);
                }});
            }});
            
            // Store player reference globally
            window.spotifyPlayer = player;
        }};
    </script>
</body>
</html>
        '''
        
    def _initialize_web_player(self):
        """Initialize the embedded web player"""
        if WEBVIEW_AVAILABLE:
            try:
                self._initialize_webview()
            except Exception as e:
                self.logger.warning(f"WebView initialization failed, using fallback: {e}")
                self._initialize_fallback_player()
        else:
            self.logger.warning("No web browser library available. Install pywebview.")
            self._initialize_fallback_player()
            
    def _initialize_fallback_player(self):
        """Initialize fallback player with direct URL access"""
        try:
            import webbrowser
            self.status_label.configure(text="🎵 Web Player Available")
            
            # Add info label about requirements
            info_label = ctk.CTkLabel(
                self,
                text="Note: Spotify Premium required",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            info_label.grid(row=3, column=0, columnspan=3, pady=(5, 0), sticky="ew")
            
            # Add a button to open the web player in default browser
            open_button = ctk.CTkButton(
                self,
                text="Open Web Player",
                command=lambda: webbrowser.open(f"http://127.0.0.1:{self.web_server_port}"),
                width=120,
                height=28
            )
            open_button.grid(row=4, column=0, columnspan=3, pady=5, sticky="ew")
            
            self.logger.info("Fallback web player initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize fallback player: {e}")
            self.status_label.configure(text="⚠️ Web player unavailable")
            

            
    def _initialize_webview(self):
        """Initialize webview for Spotify player"""
        try:
            # Skip webview initialization if already started globally
            if getattr(self.__class__, '_webview_started', False):
                self.logger.info("WebView already started globally, skipping initialization")
                self.status_label.configure(text="🎵 Web Player Ready")
                return
                
            # Create webview window but don't start it yet
            self.webview_window = webview.create_window(
                'Spotify Player',
                f"http://127.0.0.1:{self.web_server_port}",
                width=400,
                height=100,
                resizable=False,
                shadow=False
            )
            
            # Schedule webview start on main thread using tkinter's after method
            if hasattr(self, 'parent') and hasattr(self.parent, 'after'):
                self.parent.after(100, self._start_webview)
            else:
                # Fallback: try to start immediately (may fail if not on main thread)
                self._start_webview()
            
            self.logger.info("WebView initialized for Spotify Web Player")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebView: {e}")
            self.status_label.configure(text="⚠️ WebView initialization failed")
    
    def _start_webview(self):
        """Start the webview on the main thread with non-blocking approach"""
        try:
            # Only start if we have a window and webview hasn't been started yet
            if hasattr(self, 'webview_window') and not getattr(self, 'webview_started', False):
                self.webview_started = True
                # Use after_idle to start webview without blocking the UI
                if hasattr(self, 'parent') and hasattr(self.parent, 'after_idle'):
                    self.parent.after_idle(lambda: self._actually_start_webview())
                else:
                    self._actually_start_webview()
                self.logger.info("WebView scheduled to start")
        except Exception as e:
            self.logger.error(f"Failed to start WebView: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="⚠️ WebView start failed")
                
    def _actually_start_webview(self):
        """Actually start the webview - must be called on main thread"""
        try:
            # Check if webview was already started globally
            if getattr(self.__class__, '_webview_started', False):
                self.logger.info("WebView already started globally")
                self.status_label.configure(text="🎵 Web Player Ready")
                return
                
            # Start webview without the invalid 'block' parameter
            webview.start(debug=False)
            # Mark as started globally for this class
            self.__class__._webview_started = True
            self.logger.info("WebView started successfully")
            self.status_label.configure(text="🎵 Web Player Ready")
        except Exception as e:
            self.logger.error(f"Failed to actually start WebView: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="⚠️ WebView start failed")
            
    def _update_ui_from_state(self, state):
        """Update UI based on player state"""
        try:
            if state.get('track_window', {}).get('current_track'):
                track = state['track_window']['current_track']
                track_name = track.get('name', 'Unknown Track')
                artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                
                # Check if widgets still exist before updating
                if hasattr(self, 'track_label') and self.track_label.winfo_exists():
                    self.after_idle(lambda: self._safe_update_widget(self.track_label, 'text', track_name))
                if hasattr(self, 'artist_label') and self.artist_label.winfo_exists():
                    self.after_idle(lambda: self._safe_update_widget(self.artist_label, 'text', artists))
                
            # Update play/pause button
            is_paused = state.get('paused', True)
            button_text = "▶" if is_paused else "⏸"
            if hasattr(self, 'play_pause_button') and self.play_pause_button.winfo_exists():
                self.after_idle(lambda: self._safe_update_widget(self.play_pause_button, 'text', button_text))
            
        except Exception as e:
            self.logger.error(f"Error updating UI from player state: {e}")
    
    def _safe_update_widget(self, widget, attribute, value):
        """Safely update widget attribute, checking if widget still exists"""
        try:
            if widget and widget.winfo_exists():
                widget.configure(**{attribute: value})
        except Exception as e:
            self.logger.debug(f"Widget update failed (widget may be destroyed): {e}")
            
    def toggle_play_pause(self):
        """Toggle play/pause"""
        # This would be handled by the Web Playback SDK
        pass
        
    def next_track(self):
        """Skip to next track"""
        # This would be handled by the Web Playback SDK
        pass
        
    def previous_track(self):
        """Skip to previous track"""
        # This would be handled by the Web Playback SDK
        pass
        
    def set_volume(self, value):
        """Set volume"""
        # This would be handled by the Web Playback SDK
        pass
        
    def get_device_id(self) -> Optional[str]:
        """Get the Spotify device ID for this player"""
        return self.device_id
        
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop Flask server if running
            if hasattr(self, 'flask_thread') and self.flask_thread and self.flask_thread.is_alive():
                self.logger.info("Stopping Flask server...")
                # Flask server will stop when the thread ends
                
            # Clean up webview if available
            if WEBVIEW_AVAILABLE and getattr(self, 'webview_started', False):
                try:
                    if hasattr(webview, 'destroy_window'):
                        webview.destroy_window()
                except Exception as webview_error:
                    self.logger.debug(f"WebView cleanup error (non-critical): {webview_error}")
                    
            self.logger.info("Spotify Web Player cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Non-critical error during cleanup: {e}")