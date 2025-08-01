"""Secure API Key Manager Component

Provides a secure interface for managing API keys with encryption,
validation, and proper security measures.
"""

import base64
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Tuple

import customtkinter as ctk
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..theme import DataTerminalTheme


class SecureAPIManager:
    """Secure API Key Manager with encryption and validation."""

    # API Key configurations with validation patterns and descriptions
    API_CONFIGS = {
        "openweather_api_key": {
            "name": "OpenWeatherMap API Key",
            "description": "Primary weather data provider",
            "pattern": r"^[a-f0-9]{32}$",
            "url": "https://openweathermap.org/api",
            "required": True,
            "test_endpoint": "https://api.openweathermap.org/data/2.5/weather?q=London&appid=",
        },
        "openweather_backup_api_key": {
            "name": "OpenWeatherMap Backup API Key",
            "description": "Backup weather data provider",
            "pattern": r"^[a-f0-9]{32}$",
            "url": "https://openweathermap.org/api",
            "required": False,
            "test_endpoint": None,
        },
        "weatherapi_api_key": {
            "name": "WeatherAPI.com Key",
            "description": "Alternative weather data provider",
            "pattern": r"^[a-zA-Z0-9]{32}$",
            "url": "https://www.weatherapi.com/signup.aspx",
            "required": False,
            "test_endpoint": None,
        },
        "gemini_api_key": {
            "name": "Google Gemini API Key",
            "description": "AI-powered activity suggestions and chat",
            "pattern": r"^AIza[0-9A-Za-z\-_]{35}$",
            "url": "https://ai.google.dev/",
            "required": False,
            "test_endpoint": None,
        },
        "openai_api_key": {
            "name": "OpenAI API Key",
            "description": "Advanced AI features and GPT models",
            "pattern": r"^sk-[a-zA-Z0-9\-_]{20,}$",
            "url": "https://platform.openai.com/api-keys",
            "required": False,
            "test_endpoint": None,
        },
        "google_maps_api_key": {
            "name": "Google Maps API Key",
            "description": "Interactive maps and location services",
            "pattern": r"^AIza[0-9A-Za-z\-_]{35}$",
            "url": "https://developers.google.com/maps/documentation/javascript/get-api-key",
            "required": False,
            "test_endpoint": None,
        },
        # Spotify API configuration removed
    }

    def __init__(self, parent, config_service):
        """Initialize the secure API manager.

        Args:
            parent: Parent widget
            config_service: Configuration service instance
        """
        self.parent = parent
        self.config_service = config_service
        self.secure_storage_path = Path("data/secure_keys.enc")
        self.secure_storage_path.parent.mkdir(exist_ok=True)

        # Initialize encryption
        self._init_encryption()

        # Storage for API key entries
        self.api_entries: Dict[str, ctk.CTkEntry] = {}
        self.show_buttons: Dict[str, ctk.CTkButton] = {}
        self.status_labels: Dict[str, ctk.CTkLabel] = {}

        # Load existing keys
        self.stored_keys = self._load_encrypted_keys()

    def _init_encryption(self):
        """Initialize encryption for secure key storage."""
        # Use a combination of machine-specific data for key derivation
        machine_id = hashlib.sha256(
            (
                os.environ.get("COMPUTERNAME", "default") + os.environ.get("USERNAME", "user")
            ).encode()
        ).digest()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"weather_dashboard_salt",
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id))
        self.cipher = Fernet(key)

    def _load_encrypted_keys(self) -> Dict[str, str]:
        """Load encrypted API keys from secure storage.

        Returns:
            Dictionary of decrypted API keys
        """
        try:
            if self.secure_storage_path.exists():
                with open(self.secure_storage_path, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Warning: Could not load encrypted keys: {e}")

        # Fallback to environment variables
        keys = {}
        for key_name in self.API_CONFIGS.keys():
            env_value = os.getenv(key_name.upper())
            if env_value:
                keys[key_name] = env_value
        return keys

    def _save_encrypted_keys(self, keys: Dict[str, str]):
        """Save API keys with encryption.

        Args:
            keys: Dictionary of API keys to save
        """
        try:
            json_data = json.dumps(keys).encode()
            encrypted_data = self.cipher.encrypt(json_data)
            with open(self.secure_storage_path, "wb") as f:
                f.write(encrypted_data)
        except Exception as e:
            raise Exception(f"Failed to save encrypted keys: {e}")

    def validate_api_key(self, key_name: str, key_value: str) -> Tuple[bool, str]:
        """Validate an API key format.

        Args:
            key_name: Name of the API key
            key_value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not key_value.strip():
            return True, ""  # Empty keys are allowed for optional APIs

        config = self.API_CONFIGS.get(key_name)
        if not config:
            return False, "Unknown API key type"

        pattern = config.get("pattern")
        if pattern and not re.match(pattern, key_value.strip()):
            return False, f"Invalid format for {config['name']}"

        return True, ""

    def create_api_section(self, parent_frame) -> ctk.CTkFrame:
        """Create the secure API keys section.

        Args:
            parent_frame: Parent frame to contain the API section

        Returns:
            The created API section frame
        """
        # Main API Keys Card
        api_card = ctk.CTkFrame(
            parent_frame,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        api_card.pack(fill="x", pady=10)

        # Title with security indicator
        title_frame = ctk.CTkFrame(api_card, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            title_frame,
            text="🔐 Secure API Key Management",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        ).pack(side="left")

        # Security info button
        info_btn = ctk.CTkButton(
            title_frame,
            text="ℹ️",
            width=30,
            height=30,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            fg_color="transparent",
            hover_color=DataTerminalTheme.BORDER,
            command=self._show_security_info,
        )
        info_btn.pack(side="right")

        # Create scrollable frame for API keys
        scrollable = ctk.CTkScrollableFrame(api_card, height=400, fg_color="transparent")
        scrollable.pack(fill="both", expand=True, padx=20, pady=10)

        # Create entries for each API key
        for key_name, config in self.API_CONFIGS.items():
            self._create_api_key_entry(scrollable, key_name, config)

        # Action buttons
        button_frame = ctk.CTkFrame(api_card, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 20))

        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save All Keys",
            height=40,
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            fg_color=DataTerminalTheme.SUCCESS,
            hover_color=DataTerminalTheme.PRIMARY,
            command=self._save_all_keys,
        )
        save_btn.pack(side="left", padx=(0, 10))

        # Validate button
        validate_btn = ctk.CTkButton(
            button_frame,
            text="✅ Validate Keys",
            height=40,
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            fg_color=DataTerminalTheme.WARNING,
            hover_color=DataTerminalTheme.PRIMARY,
            command=self._validate_all_keys,
        )
        validate_btn.pack(side="left", padx=(0, 10))

        # Clear button
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear All",
            height=40,
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            fg_color=DataTerminalTheme.ERROR,
            hover_color=DataTerminalTheme.PRIMARY,
            command=self._clear_all_keys,
        )
        clear_btn.pack(side="right")

        return api_card

    def _create_api_key_entry(self, parent, key_name: str, config: Dict):
        """Create an individual API key entry with security features.

        Args:
            parent: Parent widget
            key_name: Internal key name
            config: API configuration dictionary
        """
        # Main frame for this API key
        key_frame = ctk.CTkFrame(parent, fg_color="transparent")
        key_frame.pack(fill="x", pady=8)

        # Header with name and required indicator
        header_frame = ctk.CTkFrame(key_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))

        # API name and required indicator
        name_text = config["name"]
        if config.get("required", False):
            name_text += " *"

        name_label = ctk.CTkLabel(
            header_frame,
            text=name_text,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=(
                DataTerminalTheme.TEXT if not config.get("required") else DataTerminalTheme.ERROR
            ),
        )
        name_label.pack(side="left")

        # Get API key link
        if config.get("url"):
            link_btn = ctk.CTkButton(
                header_frame,
                text="🔗 Get Key",
                width=80,
                height=25,
                font=(DataTerminalTheme.FONT_FAMILY, 10),
                fg_color="transparent",
                hover_color=DataTerminalTheme.BORDER,
                command=lambda url=config["url"]: self._open_url(url),
            )
            link_btn.pack(side="right")

        # Description
        desc_label = ctk.CTkLabel(
            key_frame,
            text=config["description"],
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        desc_label.pack(anchor="w", pady=(0, 5))

        # Entry frame with show/hide functionality
        entry_frame = ctk.CTkFrame(key_frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        # API key entry (password field)
        entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text=f"Enter your {config['name']}",
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            width=400,
            height=35,
            fg_color=DataTerminalTheme.BACKGROUND,
            border_color=DataTerminalTheme.BORDER,
            show="*",  # Hide by default
        )
        entry.pack(side="left", padx=(0, 10))

        # Load existing value (masked)
        existing_value = self.stored_keys.get(key_name, "")
        if existing_value:
            entry.insert(0, existing_value)

        self.api_entries[key_name] = entry

        # Show/Hide button
        show_btn = ctk.CTkButton(
            entry_frame,
            text="👁️",
            width=35,
            height=35,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            fg_color=DataTerminalTheme.BORDER,
            hover_color=DataTerminalTheme.PRIMARY,
            command=lambda k=key_name: self._toggle_visibility(k),
        )
        show_btn.pack(side="left", padx=(0, 10))
        self.show_buttons[key_name] = show_btn

        # Status label
        status_label = ctk.CTkLabel(
            entry_frame, text="", font=(DataTerminalTheme.FONT_FAMILY, 10), width=100
        )
        status_label.pack(side="left")
        self.status_labels[key_name] = status_label

    def _toggle_visibility(self, key_name: str):
        """Toggle visibility of an API key entry.

        Args:
            key_name: Name of the API key to toggle
        """
        entry = self.api_entries[key_name]
        button = self.show_buttons[key_name]

        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(text="🙈")
        else:
            entry.configure(show="*")
            button.configure(text="👁️")

    def _save_all_keys(self):
        """Save all API keys securely."""
        try:
            keys_to_save = {}
            validation_errors = []

            # Validate and collect all keys
            for key_name, entry in self.api_entries.items():
                value = entry.get().strip()
                if value:  # Only save non-empty keys
                    is_valid, error = self.validate_api_key(key_name, value)
                    if not is_valid:
                        validation_errors.append(f"{self.API_CONFIGS[key_name]['name']}: {error}")
                    else:
                        keys_to_save[key_name] = value

            if validation_errors:
                self._show_notification(
                    "Validation Errors:\n" + "\n".join(validation_errors), "error"
                )
                return

            # Save encrypted keys
            self._save_encrypted_keys(keys_to_save)
            self.stored_keys = keys_to_save

            # Update environment variables for immediate use
            for key_name, value in keys_to_save.items():
                os.environ[key_name.upper()] = value

            # Update status labels
            for key_name in self.api_entries.keys():
                if key_name in keys_to_save:
                    self.status_labels[key_name].configure(
                        text="✅ Saved", text_color=DataTerminalTheme.SUCCESS
                    )
                else:
                    self.status_labels[key_name].configure(
                        text="⚪ Empty", text_color=DataTerminalTheme.TEXT_SECONDARY
                    )

            self._show_notification("API keys saved successfully!", "success")

        except Exception as e:
            self._show_notification(f"Error saving keys: {str(e)}", "error")

    def _validate_all_keys(self):
        """Validate all entered API keys."""
        validation_results = []

        for key_name, entry in self.api_entries.items():
            value = entry.get().strip()
            config = self.API_CONFIGS[key_name]

            if not value:
                if config.get("required", False):
                    validation_results.append(f"❌ {config['name']}: Required but missing")
                    self.status_labels[key_name].configure(
                        text="❌ Required", text_color=DataTerminalTheme.ERROR
                    )
                else:
                    validation_results.append(f"⚪ {config['name']}: Optional, not provided")
                    self.status_labels[key_name].configure(
                        text="⚪ Optional", text_color=DataTerminalTheme.TEXT_SECONDARY
                    )
            else:
                is_valid, error = self.validate_api_key(key_name, value)
                if is_valid:
                    validation_results.append(f"✅ {config['name']}: Valid format")
                    self.status_labels[key_name].configure(
                        text="✅ Valid", text_color=DataTerminalTheme.SUCCESS
                    )
                else:
                    validation_results.append(f"❌ {config['name']}: {error}")
                    self.status_labels[key_name].configure(
                        text="❌ Invalid", text_color=DataTerminalTheme.ERROR
                    )

        # Show validation results
        self._show_notification("Validation Results:\n" + "\n".join(validation_results), "info")

    def _clear_all_keys(self):
        """Clear all API key entries after confirmation."""
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Confirm Clear All")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        try:
            screen_width = dialog.winfo_screenwidth()
            screen_height = dialog.winfo_screenheight()
            logging.debug(
                f"Dialog screen dimensions: width={screen_width} ({type(screen_width)}), height={screen_height} ({type(screen_height)})"
            )

            if screen_width is None or screen_height is None:
                logging.error(
                    f"Dialog screen dimensions are None: width={screen_width}, height={screen_height}"
                )
                x, y = 100, 100
            else:
                x = (screen_width // 2) - (400 // 2)
                y = (screen_height // 2) - (200 // 2)
                logging.debug(f"Dialog calculated position: x={x}, y={y}")

            dialog.geometry(f"400x200+{x}+{y}")
        except Exception as e:
            logging.exception(f"Error positioning dialog: {e}")
            dialog.geometry("400x200+100+100")

        ctk.CTkLabel(
            dialog,
            text="⚠️ Clear All API Keys?",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.WARNING,
        ).pack(pady=20)

        ctk.CTkLabel(
            dialog,
            text="This will remove all stored API keys.\nYou will need to re-enter them.",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT,
        ).pack(pady=10)

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)

        def confirm_clear():
            for entry in self.api_entries.values():
                entry.delete(0, "end")
            for label in self.status_labels.values():
                label.configure(text="", text_color=DataTerminalTheme.TEXT)

            # Clear stored keys
            if self.secure_storage_path.exists():
                self.secure_storage_path.unlink()
            self.stored_keys = {}

            dialog.destroy()
            self._show_notification("All API keys cleared", "info")

        ctk.CTkButton(
            button_frame,
            text="Yes, Clear All",
            fg_color=DataTerminalTheme.ERROR,
            hover_color=DataTerminalTheme.PRIMARY,
            command=confirm_clear,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color=DataTerminalTheme.BORDER,
            hover_color=DataTerminalTheme.PRIMARY,
            command=dialog.destroy,
        ).pack(side="left", padx=10)

    def _show_security_info(self):
        """Show security information dialog."""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Security Information")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        try:
            screen_width = dialog.winfo_screenwidth()
            screen_height = dialog.winfo_screenheight()
            logging.debug(
                f"Security dialog screen dimensions: width={screen_width} ({type(screen_width)}), height={screen_height} ({type(screen_height)})"
            )

            if screen_width is None or screen_height is None:
                logging.error(
                    f"Security dialog screen dimensions are None: width={screen_width}, height={screen_height}"
                )
                x, y = 100, 100
            else:
                x = (screen_width // 2) - (500 // 2)
                y = (screen_height // 2) - (400 // 2)
                logging.debug(f"Security dialog calculated position: x={x}, y={y}")

            dialog.geometry(f"500x400+{x}+{y}")
        except Exception as e:
            logging.exception(f"Error positioning security dialog: {e}")
            dialog.geometry("500x400+100+100")

        ctk.CTkLabel(
            dialog,
            text="🔐 Security Features",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        ).pack(pady=20)

        info_text = (
            "• API keys are encrypted using machine-specific data\n"
            "• Keys are stored locally in encrypted format\n"
            "• Input fields are masked by default\n"
            "• Format validation prevents invalid keys\n"
            "• Required vs optional keys are clearly marked\n"
            "• Keys are never transmitted over the network\n"
            "• Secure deletion removes all traces\n\n"
            "Security Notes:\n"
            "• Keep your API keys confidential\n"
            "• Regularly rotate your keys\n"
            "• Monitor API usage for anomalies\n"
            "• Use environment variables for production"
        )

        text_widget = ctk.CTkTextbox(
            dialog,
            width=450,
            height=250,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            fg_color=DataTerminalTheme.BACKGROUND,
            text_color=DataTerminalTheme.TEXT,
        )
        text_widget.pack(pady=10, padx=25)
        text_widget.insert("1.0", info_text)
        text_widget.configure(state="disabled")

        ctk.CTkButton(dialog, text="Close", command=dialog.destroy).pack(pady=20)

    def _open_url(self, url: str):
        """Open URL in default browser.

        Args:
            url: URL to open
        """
        import webbrowser

        webbrowser.open(url)

    def _show_notification(self, message: str, notification_type: str = "info"):
        """Show a notification message.

        Args:
            message: Message to display
            notification_type: Type of notification (info, success, error, warning)
        """
        # Create notification window
        notification = ctk.CTkToplevel(self.parent)
        notification.title("Notification")
        notification.geometry("450x300")
        notification.resizable(False, False)
        notification.transient(self.parent)
        notification.grab_set()

        # Center the notification
        notification.update_idletasks()
        try:
            screen_width = notification.winfo_screenwidth()
            screen_height = notification.winfo_screenheight()
            logging.debug(
                f"Notification screen dimensions: width={screen_width} ({type(screen_width)}), height={screen_height} ({type(screen_height)})"
            )

            if screen_width is None or screen_height is None:
                logging.error(
                    f"Notification screen dimensions are None: width={screen_width}, height={screen_height}"
                )
                x, y = 100, 100
            else:
                x = (screen_width // 2) - (450 // 2)
                y = (screen_height // 2) - (300 // 2)
                logging.debug(f"Notification calculated position: x={x}, y={y}")

            notification.geometry(f"450x300+{x}+{y}")
        except Exception as e:
            logging.exception(f"Error positioning notification: {e}")
            notification.geometry("450x300+100+100")

        # Configure colors based on type
        colors = {
            "success": (DataTerminalTheme.SUCCESS, "✅"),
            "error": (DataTerminalTheme.ERROR, "❌"),
            "warning": (DataTerminalTheme.WARNING, "⚠️"),
            "info": (DataTerminalTheme.PRIMARY, "ℹ️"),
        }

        color, icon = colors.get(notification_type, colors["info"])

        ctk.CTkLabel(
            notification,
            text=f"{icon} {notification_type.title()}",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=color,
        ).pack(pady=20)

        # Message text
        text_widget = ctk.CTkTextbox(
            notification,
            width=400,
            height=180,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            fg_color=DataTerminalTheme.BACKGROUND,
            text_color=DataTerminalTheme.TEXT,
        )
        text_widget.pack(pady=10)
        text_widget.insert("1.0", message)
        text_widget.configure(state="disabled")

        ctk.CTkButton(notification, text="Close", command=notification.destroy).pack(pady=20)
