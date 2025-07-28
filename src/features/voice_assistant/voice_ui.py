#!/usr/bin/env python3
"""
Voice Assistant UI - User Interface for Cortana Integration

This module provides the UI components for the voice assistant feature,
integrating with the main dashboard interface.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import threading

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from .cortana_service import CortanaService
from .models import VoiceCommand, VoiceResponse, VoiceState, CommandType, ResponseType
from ...utils.logger import LoggerMixin
from ...ui.components.hunter_glass import HunterGlassButton, HunterGlassFrame, HunterGlassLabel


class VoiceAssistantUI(HunterGlassFrame, LoggerMixin):
    """Voice Assistant UI component for the main dashboard."""
    
    def __init__(
        self,
        parent,
        cortana_service: Optional[CortanaService] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.cortana_service = cortana_service
        self.is_listening = False
        self.command_history = []
        
        # UI Components
        self.status_label = None
        self.listen_button = None
        self.text_input = None
        self.send_button = None
        self.conversation_area = None
        self.settings_frame = None
        
        # Setup UI
        self._setup_ui()
        self._setup_cortana_callbacks()
        
        # Initial status update
        self._update_status()
    
    def _setup_ui(self):
        """Setup the voice assistant user interface."""
        # Main container with glassmorphic effect
        self.configure(corner_radius=15)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="🎤 Cortana Voice Assistant",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#2B2B2B", "#FFFFFF")
        )
        title_label.pack(pady=(20, 10))
        
        # Status section
        self._create_status_section()
        
        # Voice controls section
        self._create_voice_controls()
        
        # Text input section
        self._create_text_input_section()
        
        # Conversation history
        self._create_conversation_section()
        
        # Settings section
        self._create_settings_section()
    
    def _create_status_section(self):
        """Create the status display section."""
        status_frame = ctk.CTkFrame(self, corner_radius=10)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="🔴 Idle",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_label.pack(pady=10)
        
        # Service availability
        if self.cortana_service:
            status = self.cortana_service.get_status()
            availability_text = "✅ Voice Assistant Ready" if status['speech_available'] else "⚠️ Speech Recognition Unavailable"
        else:
            availability_text = "❌ Voice Service Not Connected"
        
        availability_label = ctk.CTkLabel(
            status_frame,
            text=availability_text,
            font=ctk.CTkFont(size=12)
        )
        availability_label.pack(pady=(0, 10))
    
    def _create_voice_controls(self):
        """Create voice control buttons."""
        controls_frame = ctk.CTkFrame(self, corner_radius=10)
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        # Listen button
        self.listen_button = ctk.CTkButton(
            controls_frame,
            text="🎤 Start Listening",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._toggle_listening
        )
        self.listen_button.pack(pady=15)
        
        # Quick commands
        quick_commands_label = ctk.CTkLabel(
            controls_frame,
            text="Quick Commands:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        quick_commands_label.pack(pady=(10, 5))
        
        quick_commands = [
            ("Weather", "What's the weather like?"),
            ("Forecast", "Weather forecast for tomorrow"),
            ("Journal", "Create a journal entry"),
            ("Activity", "Suggest an activity")
        ]
        
        quick_frame = ctk.CTkFrame(controls_frame)
        quick_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        for i, (label, command) in enumerate(quick_commands):
            btn = ctk.CTkButton(
                quick_frame,
                text=label,
                width=80,
                height=30,
                font=ctk.CTkFont(size=10),
                command=lambda cmd=command: self._send_text_command(cmd)
            )
            btn.grid(row=i//2, column=i%2, padx=5, pady=2, sticky="ew")
        
        quick_frame.grid_columnconfigure(0, weight=1)
        quick_frame.grid_columnconfigure(1, weight=1)
    
    def _create_text_input_section(self):
        """Create text input for manual commands."""
        input_frame = ctk.CTkFrame(self, corner_radius=10)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="Type a command:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        input_label.pack(pady=(15, 5))
        
        # Text input with send button
        text_frame = ctk.CTkFrame(input_frame)
        text_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.text_input = ctk.CTkEntry(
            text_frame,
            placeholder_text="Ask about weather, create journal entry, etc.",
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.text_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.send_button = ctk.CTkButton(
            text_frame,
            text="Send",
            width=60,
            height=35,
            command=self._send_text_command
        )
        self.send_button.pack(side="right")
        
        # Bind Enter key
        self.text_input.bind("<Return>", lambda e: self._send_text_command())
    
    def _create_conversation_section(self):
        """Create conversation history display."""
        conv_frame = ctk.CTkFrame(self, corner_radius=10)
        conv_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        conv_label = ctk.CTkLabel(
            conv_frame,
            text="Conversation History:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        conv_label.pack(pady=(15, 5))
        
        # Scrollable text area
        self.conversation_area = ctk.CTkTextbox(
            conv_frame,
            height=200,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.conversation_area.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Clear button
        clear_button = ctk.CTkButton(
            conv_frame,
            text="Clear History",
            width=100,
            height=30,
            command=self._clear_conversation
        )
        clear_button.pack(pady=(0, 15))
        
        # Add welcome message
        self._add_to_conversation(
            "Cortana",
            "Hello! I'm Cortana, your voice assistant. You can ask me about weather, create journal entries, or get activity suggestions. Try saying 'Hello' or 'What's the weather like?'",
            "assistant"
        )
    
    def _create_settings_section(self):
        """Create settings controls."""
        self.settings_frame = ctk.CTkFrame(self, corner_radius=10)
        self.settings_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        settings_label = ctk.CTkLabel(
            self.settings_frame,
            text="Settings:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        settings_label.pack(pady=(15, 10))
        
        # Settings grid
        settings_grid = ctk.CTkFrame(self.settings_frame)
        settings_grid.pack(fill="x", padx=15, pady=(0, 15))
        
        # Voice enabled toggle
        self.voice_enabled_var = tk.BooleanVar(value=True)
        voice_enabled_cb = ctk.CTkCheckBox(
            settings_grid,
            text="Voice Recognition Enabled",
            variable=self.voice_enabled_var,
            command=self._update_voice_settings
        )
        voice_enabled_cb.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        
        # Auto-listen toggle
        self.auto_listen_var = tk.BooleanVar(value=False)
        auto_listen_cb = ctk.CTkCheckBox(
            settings_grid,
            text="Auto-listen Mode",
            variable=self.auto_listen_var,
            command=self._update_voice_settings
        )
        auto_listen_cb.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Speech rate slider
        rate_label = ctk.CTkLabel(settings_grid, text="Speech Rate:")
        rate_label.grid(row=2, column=0, sticky="w", pady=5)
        
        self.speech_rate_var = tk.DoubleVar(value=200)
        rate_slider = ctk.CTkSlider(
            settings_grid,
            from_=100,
            to=300,
            variable=self.speech_rate_var,
            command=self._update_speech_rate
        )
        rate_slider.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        # Volume slider
        volume_label = ctk.CTkLabel(settings_grid, text="Volume:")
        volume_label.grid(row=3, column=0, sticky="w", pady=5)
        
        self.volume_var = tk.DoubleVar(value=0.8)
        volume_slider = ctk.CTkSlider(
            settings_grid,
            from_=0.0,
            to=1.0,
            variable=self.volume_var,
            command=self._update_volume
        )
        volume_slider.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        settings_grid.grid_columnconfigure(1, weight=1)
    
    def _setup_cortana_callbacks(self):
        """Setup callbacks for Cortana service events."""
        if not self.cortana_service:
            return
        
        self.cortana_service.on_command_received = self._on_command_received
        self.cortana_service.on_response_generated = self._on_response_generated
        self.cortana_service.on_state_changed = self._on_state_changed
        self.cortana_service.on_error = self._on_error
    
    def _toggle_listening(self):
        """Toggle voice listening on/off."""
        if not self.cortana_service:
            self._show_error("Voice service not available")
            return
        
        if self.is_listening:
            self.cortana_service.stop_listening()
        else:
            success = self.cortana_service.start_listening()
            if not success:
                self._show_error("Failed to start voice listening")
    
    def _send_text_command(self, command_text: Optional[str] = None):
        """Send a text command to Cortana."""
        if not self.cortana_service:
            self._show_error("Voice service not available")
            return
        
        if command_text is None:
            command_text = self.text_input.get().strip()
            self.text_input.delete(0, "end")
        
        if not command_text:
            return
        
        # Add user message to conversation
        self._add_to_conversation("You", command_text, "user")
        
        # Process command in background thread
        def process_command():
            try:
                response = self.cortana_service.process_text_command(command_text)
                # Response will be handled by callback
            except Exception as e:
                self.after(0, lambda: self._show_error(f"Error processing command: {e}"))
        
        threading.Thread(target=process_command, daemon=True).start()
    
    def _on_command_received(self, command: VoiceCommand):
        """Handle command received from Cortana."""
        def update_ui():
            if command.raw_text not in [msg[1] for msg in self.command_history if msg[2] == "user"]:
                self._add_to_conversation("You", command.raw_text, "user")
        
        self.after(0, update_ui)
    
    def _on_response_generated(self, response: VoiceResponse):
        """Handle response generated by Cortana."""
        def update_ui():
            self._add_to_conversation("Cortana", response.text, "assistant")
        
        self.after(0, update_ui)
    
    def _on_state_changed(self, state: VoiceState):
        """Handle Cortana state changes."""
        def update_ui():
            self.is_listening = (state == VoiceState.LISTENING)
            self._update_status()
        
        self.after(0, update_ui)
    
    def _on_error(self, error: Exception):
        """Handle Cortana errors."""
        def update_ui():
            self._show_error(f"Voice assistant error: {error}")
        
        self.after(0, update_ui)
    
    def _update_status(self):
        """Update the status display."""
        if not self.status_label:
            return
        
        if self.is_listening:
            status_text = "🟢 Listening..."
            button_text = "🛑 Stop Listening"
        else:
            status_text = "🔴 Idle"
            button_text = "🎤 Start Listening"
        
        self.status_label.configure(text=status_text)
        if self.listen_button:
            self.listen_button.configure(text=button_text)
    
    def _add_to_conversation(self, speaker: str, message: str, msg_type: str):
        """Add a message to the conversation history."""
        timestamp = datetime.now().strftime("%H:%M")
        
        # Format message
        if msg_type == "user":
            formatted_msg = f"[{timestamp}] 👤 {speaker}: {message}\n\n"
        else:
            formatted_msg = f"[{timestamp}] 🤖 {speaker}: {message}\n\n"
        
        # Add to conversation area
        self.conversation_area.insert("end", formatted_msg)
        self.conversation_area.see("end")
        
        # Add to history
        self.command_history.append((timestamp, message, msg_type))
        
        # Limit history size
        if len(self.command_history) > 50:
            self.command_history = self.command_history[-50:]
    
    def _clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_area.delete("1.0", "end")
        self.command_history.clear()
        
        # Add welcome message back
        self._add_to_conversation(
            "Cortana",
            "Conversation cleared. How can I help you?",
            "assistant"
        )
    
    def _update_voice_settings(self):
        """Update voice assistant settings."""
        if not self.cortana_service:
            return
        
        try:
            self.cortana_service.update_settings(
                enabled=self.voice_enabled_var.get(),
                auto_listen=self.auto_listen_var.get()
            )
        except Exception as e:
            self._show_error(f"Failed to update settings: {e}")
    
    def _update_speech_rate(self, value):
        """Update speech rate setting."""
        if not self.cortana_service:
            return
        
        try:
            self.cortana_service.update_settings(speech_rate=int(value))
        except Exception as e:
            self._show_error(f"Failed to update speech rate: {e}")
    
    def _update_volume(self, value):
        """Update volume setting."""
        if not self.cortana_service:
            return
        
        try:
            self.cortana_service.update_settings(volume=float(value))
        except Exception as e:
            self._show_error(f"Failed to update volume: {e}")
    
    def _show_error(self, message: str):
        """Show error message in conversation."""
        self._add_to_conversation("System", f"Error: {message}", "error")
        self.logger.error(message)
    
    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return self.command_history.copy()
    
    def set_cortana_service(self, service: CortanaService):
        """Set or update the Cortana service."""
        self.cortana_service = service
        self._setup_cortana_callbacks()
        self._update_status()
    
    def cleanup(self):
        """Clean up resources."""
        if self.cortana_service:
            self.cortana_service.cleanup()
        
        self.command_history.clear()
        self.logger.info("Voice Assistant UI cleanup completed")


class VoiceAssistantWidget(ctk.CTkFrame):
    """Simplified voice assistant widget for embedding in other UIs."""
    
    def __init__(self, parent, cortana_service: Optional[CortanaService] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.cortana_service = cortana_service
        
        # Quick voice controls
        self.listen_button = ctk.CTkButton(
            self,
            text="🎤 Voice Command",
            command=self._quick_listen
        )
        self.listen_button.pack(pady=10)
        
        # Status
        self.status_label = ctk.CTkLabel(
            self,
            text="Voice Assistant Ready",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.pack()
    
    def _quick_listen(self):
        """Quick voice listening for embedded use."""
        if not self.cortana_service:
            return
        
        # Simple one-shot listening
        self.listen_button.configure(text="🔴 Listening...", state="disabled")
        
        def listen_and_respond():
            try:
                # This would need to be implemented for one-shot listening
                # For now, just toggle the main listening mode
                if self.cortana_service.state == VoiceState.LISTENING:
                    self.cortana_service.stop_listening()
                else:
                    self.cortana_service.start_listening()
            finally:
                self.after(0, lambda: self.listen_button.configure(
                    text="🎤 Voice Command", 
                    state="normal"
                ))
        
        threading.Thread(target=listen_and_respond, daemon=True).start()