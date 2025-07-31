# spotify_callback_server.py
"""
Spotify Callback Server

This module implements a simple Flask server to handle Spotify OAuth callbacks.
It listens on http://127.0.0.1:8000/callback and processes the authorization code
returned by Spotify after user authentication.
"""

import logging
import threading
from flask import Flask, request

logger = logging.getLogger(__name__)

class SpotifyCallbackServer:
    """Simple Flask server to handle Spotify OAuth callbacks"""
    
    def __init__(self, port=8000):
        self.port = port
        self.app = Flask(__name__)
        self.server_thread = None
        self.is_running = False
        self.auth_code = None
        
        # Define routes
        self.app.route('/callback')(self.callback_handler)
    
    def callback_handler(self):
        """Handle the Spotify callback with authorization code"""
        try:
            # Get the authorization code from the request
            self.auth_code = request.args.get('code')
            logger.info("✅ Received Spotify authorization code")
            return "<h1>Authentication successful!</h1><p>You can close this window and return to the application.</p>"
        except Exception as e:
            logger.error(f"Error processing Spotify callback: {e}")
            return "<h1>Authentication error</h1><p>There was an error processing your Spotify authentication. Please try again.</p>"
    
    def start(self):
        """Start the Flask server in a separate thread"""
        if self.is_running:
            logger.warning("Spotify callback server is already running")
            return
        
        def run_server():
            try:
                logger.info(f"Starting Spotify callback server on port {self.port}")
                self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"Error starting Spotify callback server: {e}")
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True  # Thread will exit when main program exits
        self.server_thread.start()
        self.is_running = True
        logger.info("Spotify callback server thread started")
    
    def stop(self):
        """Stop the Flask server"""
        if not self.is_running:
            return
        
        # Flask doesn't have a clean shutdown mechanism when run in a thread
        # We'll rely on the daemon thread property to terminate when the main app exits
        self.is_running = False
        logger.info("Spotify callback server marked for shutdown")
    
    def get_auth_code(self):
        """Return the received authorization code"""
        return self.auth_code