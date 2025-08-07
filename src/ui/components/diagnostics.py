#!/usr/bin/env python3
"""
Diagnostics and Logging System for Weather Dashboard
Provides user-friendly error handling, bug reporting, and network diagnostics.
"""

import json
import logging
import os
import platform
import socket
import sys
import threading
import time
import tkinter as tk
import traceback
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any, Callable, Dict, List

class LogLevel(Enum):
    """Log levels for user-friendly display."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ErrorReport:
    """Structure for error reports."""

    timestamp: str
    error_type: str
    error_message: str
    user_message: str
    technical_details: str
    system_info: Dict[str, Any]
    steps_to_reproduce: str = ""
    user_email: str = ""
    logs: List[str] = None

class UserFriendlyLogger:
    """Logger that provides user-friendly error messages."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.user_messages = {
            # Network errors
            "ConnectionError": "Unable to connect to the internet. Please check your connection.",
            "TimeoutError": "The request took too long. Please try again.",
            "URLError": "Unable to reach the weather service. Please check your internet connection.",
            # API errors
            "HTTPError": "The weather service is temporarily unavailable. Please try again later.",
            "JSONDecodeError": "Received invalid data from the weather service. Please try again.",
            "KeyError": "The weather data format has changed. Please update the application.",
            # File errors
            "FileNotFoundError": "A required file is missing. Please reinstall the application.",
            "PermissionError": "Unable to access a required file. Please check file permissions.",
            "OSError": "A system error occurred. Please restart the application.",
            # General errors
            "ValueError": "Invalid input provided. Please check your entries.",
            "TypeError": "An internal error occurred. Please report this bug.",
            "AttributeError": "An internal error occurred. Please report this bug.",
        }

    def get_user_friendly_message(self, exception: Exception) -> str:
        """Convert exception to user-friendly message."""
        exception_type = type(exception).__name__

        # Check for specific error patterns
        error_str = str(exception).lower()

        if "api key" in error_str or "unauthorized" in error_str:
            return (
                "There's an issue with the weather service authentication. Please contact support."
            )
        elif "rate limit" in error_str or "too many requests" in error_str:
            return "Too many requests to the weather service. Please wait a moment and try again."
        elif "location not found" in error_str or "invalid location" in error_str:
            return "The location you entered could not be found. Please try a different location."
        elif "network" in error_str or "connection" in error_str:
            return "Network connection issue. Please check your internet connection."

        # Use predefined messages
        return self.user_messages.get(
            exception_type,
            "An unexpected error occurred. Please try again or contact support if the problem persists.",
        )

    def log_user_error(self, exception: Exception, context: str = "") -> str:
        """Log error and return user-friendly message."""
        user_message = self.get_user_friendly_message(exception)

        # Log technical details
        self.logger.error(
            f"Error in {context}: {type(exception).__name__}: {exception}", exc_info=True
        )

        return user_message

class NetworkDiagnostics:
    """Network diagnostics and testing tools."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_hosts = [
            ("google.com", 80),
            ("8.8.8.8", 53),
            ("api.openweathermap.org", 443),
            ("cloudflare.com", 80),
        ]

    def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive network diagnostics."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "connectivity": self._test_connectivity(),
            "dns": self._test_dns(),
            "api_endpoints": self._test_api_endpoints(),
            "speed": self._test_speed(),
            "system_info": self._get_network_info(),
        }

        return results

    def _test_connectivity(self) -> Dict[str, Any]:
        """Test basic internet connectivity."""
        results = {}

        for host, port in self.test_hosts:
            try:
                start_time = time.time()
                socket.create_connection((host, port), timeout=5)
                response_time = (time.time() - start_time) * 1000

                results[host] = {"status": "success", "response_time_ms": round(response_time, 2)}
            except Exception as e:
                results[host] = {"status": "failed", "error": str(e)}

        return results

    def _test_dns(self) -> Dict[str, Any]:
        """Test DNS resolution."""
        test_domains = ["google.com", "api.openweathermap.org", "github.com"]
        results = {}

        for domain in test_domains:
            try:
                start_time = time.time()
                socket.gethostbyname(domain)
                response_time = (time.time() - start_time) * 1000

                results[domain] = {"status": "success", "response_time_ms": round(response_time, 2)}
            except Exception as e:
                results[domain] = {"status": "failed", "error": str(e)}

        return results

    def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test weather API endpoints."""
        endpoints = {
            "OpenWeatherMap": "https://api.openweathermap.org/data/2.5/weather?q=London&appid=test",
            "WeatherAPI": "https://api.weatherapi.com/v1/current.json?key=test&q=London",
        }

        results = {}

        for name, url in endpoints.items():
            try:
                start_time = time.time()
                response = urllib.request.urlopen(url, timeout=10)
                response_time = (time.time() - start_time) * 1000

                results[name] = {
                    "status": "reachable",
                    "response_time_ms": round(response_time, 2),
                    "http_status": response.getcode(),
                }
            except Exception as e:
                results[name] = {"status": "unreachable", "error": str(e)}

        return results

    def _test_speed(self) -> Dict[str, Any]:
        """Test basic connection speed."""
        try:
            # Simple speed test using a small file download
            test_url = "https://httpbin.org/bytes/1024"  # 1KB test file

            start_time = time.time()
            response = urllib.request.urlopen(test_url, timeout=10)
            data = response.read()
            end_time = time.time()

            duration = end_time - start_time
            speed_kbps = (len(data) / 1024) / duration if duration > 0 else 0

            return {
                "status": "success",
                "speed_kbps": round(speed_kbps, 2),
                "test_size_kb": len(data) / 1024,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _get_network_info(self) -> Dict[str, Any]:
        """Get system network information."""
        info = {"platform": platform.system(), "hostname": socket.gethostname()}

        try:
            # Get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                info["local_ip"] = s.getsockname()[0]
        except Exception:
            info["local_ip"] = "unknown"

        return info

class BugReportDialog:
    """Dialog for collecting bug reports from users."""

    def __init__(self, parent: tk.Widget, error_report: ErrorReport):
        self.parent = parent
        self.error_report = error_report
        self.dialog = None
        self.logger = logging.getLogger(__name__)

    def show(self):
        """Show the bug report dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Report Bug")
        self.dialog.geometry("600x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._center_dialog()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Help us fix this issue", font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Error summary
        error_frame = ttk.LabelFrame(main_frame, text="Error Summary", padding="10")
        error_frame.pack(fill="x", pady=(0, 10))

        error_label = ttk.Label(
            error_frame, text=self.error_report.user_message, wraplength=500, justify="left"
        )
        error_label.pack(anchor="w")

        # User information
        user_frame = ttk.LabelFrame(main_frame, text="Contact Information (Optional)", padding="10")
        user_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(user_frame, text="Email:").pack(anchor="w")
        self.email_entry = ttk.Entry(user_frame, width=50)
        self.email_entry.pack(fill="x", pady=(0, 5))

        # Steps to reproduce
        steps_frame = ttk.LabelFrame(main_frame, text="Steps to Reproduce (Optional)", padding="10")
        steps_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.steps_text = scrolledtext.ScrolledText(
            steps_frame, height=6, wrap="word", font=("Arial", 9)
        )
        self.steps_text.pack(fill="both", expand=True)
        self.steps_text.insert(
            "1.0", "Please describe what you were doing when the error occurred..."
        )

        # Technical details (collapsible)
        self.details_frame = ttk.LabelFrame(main_frame, text="Technical Details", padding="10")
        self.details_frame.pack(fill="x", pady=(0, 10))

        self.show_details_var = tk.BooleanVar()
        details_check = ttk.Checkbutton(
            self.details_frame,
            text="Show technical details",
            variable=self.show_details_var,
            command=self._toggle_details,
        )
        details_check.pack(anchor="w")

        self.details_text = scrolledtext.ScrolledText(
            self.details_frame, height=8, wrap="word", font=("Courier", 8), state="disabled"
        )

        # Populate technical details
        details = f"""Error Type: {self.error_report.error_type}
Timestamp: {self.error_report.timestamp}

Technical Details:
{self.error_report.technical_details}

System Information:
{json.dumps(self.error_report.system_info, indent=2)}"""

        self.details_text.config(state="normal")
        self.details_text.insert("1.0", details)
        self.details_text.config(state="disabled")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(
            side="right", padx=(5, 0)
        )

        ttk.Button(button_frame, text="Send Report", command=self._send_report).pack(side="right")

        ttk.Button(button_frame, text="Save to File", command=self._save_to_file).pack(side="left")

    def _toggle_details(self):
        """Toggle technical details visibility."""
        if self.show_details_var.get():
            self.details_text.pack(fill="both", expand=True, pady=(5, 0))
        else:
            self.details_text.pack_forget()

    def _send_report(self):
        """Send the bug report."""
        # Update report with user input
        self.error_report.user_email = self.email_entry.get()
        self.error_report.steps_to_reproduce = self.steps_text.get("1.0", "end-1c")

        # In a real application, this would send to a bug tracking system
        # For now, we'll save to a local file
        try:
            report_file = f"logs/bug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)

            with open(report_file, "w") as f:
                json.dump(asdict(self.error_report), f, indent=2)

            messagebox.showinfo(
                "Report Sent",
                f"Bug report saved to {report_file}\n\nThank you for helping us improve the application!",
            )

            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save bug report: {e}")

    def _save_to_file(self):
        """Save report to user-specified file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Bug Report",
        )

        if filename:
            try:
                # Update report with user input
                self.error_report.user_email = self.email_entry.get()
                self.error_report.steps_to_reproduce = self.steps_text.get("1.0", "end-1c")

                with open(filename, "w") as f:
                    json.dump(asdict(self.error_report), f, indent=2)

                messagebox.showinfo("Saved", f"Bug report saved to {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()

    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

class DiagnosticsManager:
    """Main diagnostics and error handling manager."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.logger = UserFriendlyLogger(__name__)
        self.network_diagnostics = NetworkDiagnostics()
        self.error_handlers = {}

        # Setup exception handling
        self._setup_exception_handling()

    def _setup_exception_handling(self):
        """Setup global exception handling."""

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            # Create error report
            error_report = self._create_error_report(exc_type, exc_value, exc_traceback)

            # Show user-friendly error
            self._show_user_error(error_report)

        sys.excepthook = handle_exception

    def _create_error_report(self, exc_type, exc_value, exc_traceback) -> ErrorReport:
        """Create comprehensive error report."""
        technical_details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        user_message = self.logger.get_user_friendly_message(exc_value)

        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "timestamp": datetime.now().isoformat(),
        }

        return ErrorReport(
            timestamp=datetime.now().isoformat(),
            error_type=exc_type.__name__,
            error_message=str(exc_value),
            user_message=user_message,
            technical_details=technical_details,
            system_info=system_info,
        )

    def _show_user_error(self, error_report: ErrorReport):
        """Show user-friendly error dialog."""
        try:
            # Create error dialog
            dialog = tk.Toplevel(self.parent)
            dialog.title("Error Occurred")
            dialog.geometry("500x300")
            dialog.resizable(False, False)
            dialog.transient(self.parent)
            dialog.grab_set()

            # Error icon and message
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill="both", expand=True)

            # Icon
            icon_label = ttk.Label(main_frame, text="⚠️", font=("Arial", 24))
            icon_label.pack(pady=(0, 10))

            # User message
            message_label = ttk.Label(
                main_frame,
                text=error_report.user_message,
                wraplength=450,
                justify="center",
                font=("Arial", 11),
            )
            message_label.pack(pady=(0, 20))

            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack()

            ttk.Button(
                button_frame,
                text="Report Bug",
                command=lambda: self._show_bug_report(error_report, dialog),
            ).pack(side="left", padx=(0, 10))

            ttk.Button(
                button_frame, text="Run Diagnostics", command=lambda: self._show_diagnostics(dialog)
            ).pack(side="left", padx=(0, 10))

            ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side="left")

        except Exception as e:
            # Fallback to simple message box
            messagebox.showerror(
                "Error",
                f"An error occurred: {error_report.user_message}\n\nPlease restart the application.",
            )

    def _show_bug_report(self, error_report: ErrorReport, parent_dialog: tk.Toplevel):
        """Show bug report dialog."""
        parent_dialog.destroy()
        bug_dialog = BugReportDialog(self.parent, error_report)
        bug_dialog.show()

    def _show_diagnostics(self, parent_dialog: tk.Toplevel):
        """Show network diagnostics."""
        parent_dialog.destroy()

        def run_diagnostics():
            # Show progress dialog
            progress_dialog = tk.Toplevel(self.parent)
            progress_dialog.title("Running Diagnostics")
            progress_dialog.geometry("300x100")
            progress_dialog.resizable(False, False)
            progress_dialog.transient(self.parent)
            progress_dialog.grab_set()

            ttk.Label(
                progress_dialog, text="Running network diagnostics...", font=("Arial", 10)
            ).pack(pady=20)

            progress_bar = ttk.Progressbar(progress_dialog, mode="indeterminate")
            progress_bar.pack(pady=10, padx=20, fill="x")
            progress_bar.start()

            # Run diagnostics in background
            def run_tests():
                try:
                    results = self.network_diagnostics.run_diagnostics()
                    self.parent.after(
                        0, lambda: self._show_diagnostics_results(results, progress_dialog)
                    )
                except Exception as e:
                    error_msg = str(e)
                    self.parent.after(
                        0, lambda: self._show_diagnostics_error(error_msg, progress_dialog)
                    )

            threading.Thread(target=run_tests, daemon=True).start()

        run_diagnostics()

    def _show_diagnostics_results(self, results: Dict[str, Any], progress_dialog: tk.Toplevel):
        """Show diagnostics results."""
        progress_dialog.destroy()

        # Create results dialog
        results_dialog = tk.Toplevel(self.parent)
        results_dialog.title("Network Diagnostics Results")
        results_dialog.geometry("600x500")
        results_dialog.resizable(True, True)
        results_dialog.transient(self.parent)

        # Results text
        text_widget = scrolledtext.ScrolledText(
            results_dialog, wrap="word", font=("Courier", 9), padx=10, pady=10
        )
        text_widget.pack(fill="both", expand=True)

        # Format results
        formatted_results = json.dumps(results, indent=2)
        text_widget.insert("1.0", formatted_results)
        text_widget.config(state="disabled")

        # Close button
        ttk.Button(results_dialog, text="Close", command=results_dialog.destroy).pack(pady=10)

    def _show_diagnostics_error(self, error: str, progress_dialog: tk.Toplevel):
        """Show diagnostics error."""
        progress_dialog.destroy()
        messagebox.showerror("Diagnostics Error", f"Failed to run diagnostics: {error}")

    def handle_error(self, exception: Exception, context: str = "") -> str:
        """Handle an error and return user-friendly message."""
        return self.logger.log_user_error(exception, context)

    def register_error_handler(self, error_type: type, handler: Callable):
        """Register custom error handler."""
        self.error_handlers[error_type] = handler

    def add_error_report(self, error_info: Dict[str, Any]):
        """Add error report to diagnostics manager."""
        try:
            # Log the error for diagnostics
            self.logger.log_user_error(
                Exception(error_info.get("message", "Unknown error")),
                error_info.get("type", "Unknown"),
            )
        except Exception:
            # Silently ignore if logging fails

            pass
