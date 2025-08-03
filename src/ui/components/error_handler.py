#!/usr/bin/env python3
"""
Main Error Handler Integration for Weather Dashboard
Integrates all error handling components and provides a unified interface.
"""

import tkinter as tk
import traceback
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from .diagnostics import DiagnosticsManager, ErrorReport, UserFriendlyLogger
from .error_states import APIErrorDisplay, InputValidationError, LoadingState, OfflineIndicator
from .help_system import FeatureDiscovery, KeyboardShortcutOverlay, OnboardingOverlay, ToolTip

# Import our error handling components
from .toast_notification import ToastManager, ToastType


class ErrorHandler:
    """Main error handler that integrates all error handling components."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.logger = UserFriendlyLogger(__name__)

        # Initialize components with error handling
        try:
            self.toast_manager = ToastManager(parent)
        except Exception:
            self.toast_manager = None

        try:
            self.diagnostics_manager = DiagnosticsManager(parent)
        except Exception:
            self.diagnostics_manager = None

        # Error state components
        self.offline_indicator = None
        self.loading_states = {}
        self.validation_errors = {}

        # Help system components
        self.tooltips = {}
        self.onboarding = None
        self.shortcuts_overlay = None
        self.feature_discovery = None

        # Error tracking
        self.error_count = 0
        self.last_errors = []
        self.max_error_history = 10

        # Setup error handling
        self._setup_error_handling()

    def _setup_error_handling(self):
        """Setup comprehensive error handling."""
        try:
            # Check if parent has tk attribute and report_callback_exception method
            if (
                hasattr(self.parent, "tk")
                and self.parent.tk is not None
                and hasattr(self.parent.tk, "report_callback_exception")
            ):
                # Override tkinter's report_callback_exception
                original_report = self.parent.tk.report_callback_exception

                def custom_report(exc_type, exc_value, exc_traceback):
                    try:
                        self._handle_tkinter_error(exc_type, exc_value, exc_traceback)
                    except Exception:
                        # Fallback to original handler if our handler fails
                        original_report(exc_type, exc_value, exc_traceback)

                self.parent.tk.report_callback_exception = custom_report
            else:
                # For CustomTkinter or other cases, try alternative approach
                import tkinter as tk

                root = tk._default_root
                if root and hasattr(root, "report_callback_exception"):
                    original_report = root.report_callback_exception

                    def custom_report(exc_type, exc_value, exc_traceback):
                        try:
                            self._handle_tkinter_error(exc_type, exc_value, exc_traceback)
                        except Exception:
                            # Fallback to original handler if our handler fails
                            original_report(exc_type, exc_value, exc_traceback)

                    root.report_callback_exception = custom_report
        except Exception:
            # If error handling setup fails, log it but don't crash the app
            pass

    def _handle_tkinter_error(self, exc_type, exc_value, exc_traceback):
        """Handle tkinter callback exceptions."""
        # Log the error
        error_msg = self.logger.log_user_error(exc_value, "Tkinter callback")

        # Track error
        self._track_error(exc_type, exc_value, exc_traceback)

        # Show appropriate user feedback
        if self._is_critical_error(exc_type, exc_value):
            self._show_critical_error(error_msg)
        else:
            self.show_error_toast(error_msg)

    def _track_error(self, exc_type, exc_value, exc_traceback):
        """Track error for analysis and reporting."""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": exc_type.__name__,
            "message": str(exc_value),
            "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback),
        }

        self.last_errors.append(error_info)
        if len(self.last_errors) > self.max_error_history:
            self.last_errors.pop(0)

        self.error_count += 1

        # Store in diagnostics manager if available
        if self.diagnostics_manager:
            try:
                error_report = ErrorReport(
                    timestamp=error_info["timestamp"],
                    error_type=error_info["type"],
                    error_message=error_info["message"],
                    user_message="",
                    technical_details="".join(error_info["traceback"]),
                    system_info={},
                )
                self.diagnostics_manager.add_error_report(error_report)
            except Exception as e:
                print(f"Warning: Could not store error report: {e}")

    def _is_critical_error(self, exc_type, exc_value) -> bool:
        """Determine if error is critical and requires immediate attention."""
        critical_errors = [MemoryError, SystemError, OSError]

        if exc_type in critical_errors:
            return True

        # Check error message for critical patterns
        error_str = str(exc_value).lower()
        critical_patterns = [
            "out of memory",
            "system error",
            "cannot allocate",
            "disk full",
            "permission denied",
        ]

        return any(pattern in error_str for pattern in critical_patterns)

    def _show_critical_error(self, message: str):
        """Show critical error dialog."""
        try:
            from tkinter import messagebox

            messagebox.showerror(
                "Critical Error", f"{message}\n\nThe application may need to be restarted."
            )
        except Exception:
            # Last resort - print to console
            print(f"CRITICAL ERROR: {message}")

    @contextmanager
    def error_context(
        self, context: str, show_loading: bool = False, loading_parent: tk.Widget = None
    ):
        """Context manager for handling errors in specific operations."""
        loading_state = None

        try:
            # Show loading state if requested
            if show_loading and loading_parent:
                loading_state = self.show_loading(loading_parent, f"Loading {context}...")

            yield

            # Success - show success toast for important operations
            if context in ["weather data", "location update", "settings save"]:
                self.show_success_toast(f"{context.title()} updated successfully")

        except Exception as e:
            # Handle the error
            user_message = self.logger.log_user_error(e, context)

            # Show appropriate error feedback
            if "network" in str(e).lower() or "connection" in str(e).lower():
                self.show_network_error(user_message, context)
            elif "api" in str(e).lower() or "http" in str(e).lower():
                self.show_api_error(user_message, context, retry_callback=None)
            else:
                self.show_error_toast(user_message)

            # Re-raise for caller to handle if needed
            raise

        finally:
            # Hide loading state
            if loading_state:
                self.hide_loading(loading_state)

    # Toast notification methods
    def show_success_toast(self, message: str, duration: int = 3000):
        """Show success toast notification."""
        if self.toast_manager:
            self.toast_manager.show_toast(
                message=message, toast_type=ToastType.SUCCESS, duration=duration
            )

    def show_error_toast(self, message: str, persistent: bool = False):
        """Show error toast notification."""
        if self.toast_manager:
            duration = None if persistent else 5000
            self.toast_manager.show_toast(
                message=message,
                toast_type=ToastType.ERROR,
                duration=duration,
                action_text="Report" if persistent else None,
                action_callback=self._show_bug_report if persistent else None,
            )

    def show_warning_toast(self, message: str, duration: int = 5000):
        """Show warning toast notification."""
        if self.toast_manager:
            self.toast_manager.show_toast(
                message=message, toast_type=ToastType.WARNING, duration=duration
            )

    def show_info_toast(self, message: str, duration: int = 5000):
        """Show info toast notification."""
        if self.toast_manager:
            self.toast_manager.show_toast(
                message=message, toast_type=ToastType.INFO, duration=duration
            )

    def show_toast(self, message: str, level: str = "info", duration: int = 5000):
        """Show toast notification with specified level."""
        level_map = {
            "error": self.show_error_toast,
            "warning": self.show_warning_toast,
            "success": self.show_success_toast,
            "info": self.show_info_toast,
        }

        toast_method = level_map.get(level.lower(), self.show_info_toast)
        toast_method(message, duration)

    # Error state methods
    def show_offline_indicator(self, parent: tk.Widget, has_cached_data: bool = False):
        """Show offline indicator."""
        if self.offline_indicator:
            self.offline_indicator.destroy()

        self.offline_indicator = OfflineIndicator(parent, has_cached_data=has_cached_data)
        self.offline_indicator.show()
        return self.offline_indicator

    def hide_offline_indicator(self):
        """Hide offline indicator."""
        if self.offline_indicator:
            self.offline_indicator.hide()
            self.offline_indicator = None

    def show_loading(
        self, parent: tk.Widget, message: str = "Loading...", show_progress: bool = False
    ) -> LoadingState:
        """Show loading state."""
        loading_state = LoadingState(parent, message=message, show_progress=show_progress)
        loading_state.show()

        # Track loading state
        loading_id = id(loading_state)
        self.loading_states[loading_id] = loading_state

        return loading_state

    def hide_loading(self, loading_state: LoadingState):
        """Hide loading state."""
        if loading_state:
            loading_state.hide()
            loading_id = id(loading_state)
            self.loading_states.pop(loading_id, None)

    def show_api_error(self, message: str, context: str, retry_callback: Optional[Callable] = None):
        """Show API error with retry option."""
        # Create API error display
        error_dialog = tk.Toplevel(self.parent)
        error_dialog.title("Service Error")
        error_dialog.geometry("400x200")
        error_dialog.resizable(False, False)
        error_dialog.transient(self.parent)
        error_dialog.grab_set()

        api_error = APIErrorDisplay(error_dialog, message=message, retry_callback=retry_callback)
        api_error.show()

        # Center dialog
        self._center_dialog(error_dialog)

    def show_network_error(self, message: str, context: str):
        """Show network error with diagnostics option."""
        self.show_error_toast(f"{message} Check your internet connection.", persistent=True)

        # Show offline indicator if not already shown
        if not self.offline_indicator:
            self.show_offline_indicator(self.parent, has_cached_data=True)

    def show_validation_error(self, widget: tk.Widget, message: str, hint: str = ""):
        """Show input validation error."""
        validation_error = InputValidationError(widget, message=message, hint=hint)
        validation_error.show()

        # Track validation error
        widget_id = str(widget)
        self.validation_errors[widget_id] = validation_error

        return validation_error

    def clear_validation_error(self, widget: tk.Widget):
        """Clear validation error for widget."""
        widget_id = str(widget)
        if widget_id in self.validation_errors:
            self.validation_errors[widget_id].hide()
            del self.validation_errors[widget_id]

    # Help system methods
    def add_tooltip(self, widget: tk.Widget, text: str, delay: int = 500):
        """Add tooltip to widget."""
        tooltip = ToolTip(widget, text, delay)
        widget_id = str(widget)
        self.tooltips[widget_id] = tooltip
        return tooltip

    def show_onboarding(self, steps: list):
        """Show onboarding overlay."""
        if not self.onboarding:
            self.onboarding = OnboardingOverlay(self.parent)

        self.onboarding.start_onboarding(steps)

    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts overlay."""
        if not self.shortcuts_overlay:
            shortcuts = {
                "?": "Show this help",
                "Ctrl+R": "Refresh weather data",
                "Ctrl+S": "Open settings",
                "Ctrl+L": "Change location",
                "Ctrl+H": "Show hourly forecast",
                "Ctrl+Q": "Quit application",
                "F5": "Refresh all data",
                "Esc": "Close dialogs",
            }

            self.shortcuts_overlay = KeyboardShortcutOverlay(self.parent, shortcuts)

        self.shortcuts_overlay.show()

    def show_feature_discovery(self, widget: tk.Widget, title: str, description: str):
        """Show feature discovery animation."""
        if not self.feature_discovery:
            self.feature_discovery = FeatureDiscovery(self.parent)

        self.feature_discovery.highlight_feature(widget, title, description)

    # Utility methods
    def _center_dialog(self, dialog: tk.Toplevel):
        """Center dialog on parent window."""
        dialog.update_idletasks()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        dialog.geometry(f"+{x}+{y}")

    def _show_bug_report(self):
        """Show bug report dialog for the last error."""
        if self.last_errors:
            last_error = self.last_errors[-1]

            # Create error report
            error_report = ErrorReport(
                timestamp=last_error["timestamp"],
                error_type=last_error["type"],
                error_message=last_error["message"],
                user_message=self.logger.get_user_friendly_message(
                    Exception(last_error["message"])
                ),
                technical_details="".join(last_error["traceback"]),
                system_info={},
            )

            # Show bug report dialog
            from .diagnostics import BugReportDialog

            bug_dialog = BugReportDialog(self.parent, error_report)
            bug_dialog.show()

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": self.error_count,
            "recent_errors": len(self.last_errors),
            "error_types": list(set(error["type"] for error in self.last_errors)),
            "last_error_time": self.last_errors[-1]["timestamp"] if self.last_errors else None,
        }

    def cleanup(self):
        """Cleanup error handler resources."""
        # Hide all loading states
        for loading_state in list(self.loading_states.values()):
            self.hide_loading(loading_state)

        # Clear validation errors
        for validation_error in list(self.validation_errors.values()):
            validation_error.hide()
        self.validation_errors.clear()

        # Hide offline indicator
        self.hide_offline_indicator()

        # Cleanup toast manager
        if hasattr(self.toast_manager, "cleanup"):
            self.toast_manager.cleanup()

        # Clear tooltips
        self.tooltips.clear()


# Decorator for automatic error handling
def handle_errors(
    error_handler: ErrorHandler,
    context: str = "",
    show_loading: bool = False,
    show_success: bool = False,
):
    """Decorator for automatic error handling."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            loading_state = None
            try:
                # Show loading if requested
                if show_loading and hasattr(args[0], "master"):
                    loading_state = error_handler.show_loading(
                        args[0].master, f"Loading {context or func.__name__}..."
                    )

                # Execute function
                result = func(*args, **kwargs)

                # Show success if requested
                if show_success:
                    error_handler.show_success_toast(
                        f"{context or func.__name__} completed successfully"
                    )

                return result

            except Exception as e:
                # Handle error
                user_message = error_handler.logger.log_user_error(e, context or func.__name__)
                error_handler.show_error_toast(user_message)
                raise

            finally:
                # Hide loading
                if loading_state:
                    error_handler.hide_loading(loading_state)

        return wrapper

    return decorator
