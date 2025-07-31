#!/usr/bin/env python3
"""
CLI Utilities for Weather Dashboard Scripts

Provides consistent command line interface functionality:
- Argument parsing with common options
- Help formatting
- Progress indicators
- User prompts and confirmations
- Output formatting
"""

import sys
import argparse
import time
from typing import List, Optional, Any, Dict
from pathlib import Path
from datetime import datetime


class ProgressIndicator:
    """Simple progress indicator for long-running operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, increment: int = 1, message: str = None) -> None:
        """Update progress indicator."""
        self.current += increment
        
        # Throttle updates to avoid excessive output
        now = time.time()
        if now - self.last_update < 0.1 and self.current < self.total:
            return
        
        self.last_update = now
        
        # Calculate progress
        percentage = min(100, (self.current / self.total) * 100)
        elapsed = now - self.start_time
        
        # Estimate remaining time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f" ETA: {eta:.1f}s" if eta > 1 else ""
        else:
            eta_str = ""
        
        # Create progress bar
        bar_width = 30
        filled = int(bar_width * percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Format output
        status = f"\r{self.description}: [{bar}] {percentage:5.1f}% ({self.current}/{self.total}){eta_str}"
        if message:
            status += f" - {message}"
        
        print(status, end="", flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete
    
    def finish(self, message: str = "Complete") -> None:
        """Mark progress as finished."""
        self.current = self.total
        self.update(0, message)


class CLIUtils:
    """Utilities for command line interface operations."""
    
    def __init__(self, script_name: str, description: str, version: str = "1.0.0"):
        self.script_name = script_name
        self.description = description
        self.version = version
        self.parser = argparse.ArgumentParser(
            prog=script_name,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add version argument
        self.parser.add_argument(
            "--version",
            action="version",
            version=f"{script_name} v{version}"
        )
    
    def add_argument(self, *args, **kwargs) -> None:
        """Add argument to parser."""
        self.parser.add_argument(*args, **kwargs)
    
    def add_argument_group(self, title: str, description: str = None) -> argparse._ArgumentGroup:
        """Add argument group to parser."""
        return self.parser.add_argument_group(title, description)
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        return self.parser.parse_args(args)
    
    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Ask user for confirmation."""
        suffix = " [Y/n]" if default else " [y/N]"
        while True:
            response = input(f"{message}{suffix}: ").strip().lower()
            if not response:
                return default
            if response in ('y', 'yes'):
                return True
            if response in ('n', 'no'):
                return False
            print("Please enter 'y' or 'n'")
    
    @staticmethod
    def select_option(message: str, options: List[str], default: int = 0) -> int:
        """Let user select from a list of options."""
        print(f"\n{message}")
        for i, option in enumerate(options):
            marker = "*" if i == default else " "
            print(f"{marker} {i + 1}. {option}")
        
        while True:
            try:
                response = input(f"\nSelect option (1-{len(options)}) [default: {default + 1}]: ").strip()
                if not response:
                    return default
                
                choice = int(response) - 1
                if 0 <= choice < len(options):
                    return choice
                else:
                    print(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                print("Please enter a valid number")
    
    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]], title: str = None) -> str:
        """Format data as a table."""
        if not rows:
            return "No data to display"
        
        # Calculate column widths
        widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # Create format string
        format_str = " | ".join(f"{{:<{width}}}" for width in widths)
        
        # Build table
        lines = []
        
        if title:
            lines.append(title)
            lines.append("=" * len(title))
            lines.append("")
        
        # Header
        lines.append(format_str.format(*headers))
        lines.append("-" * (sum(widths) + 3 * (len(headers) - 1)))
        
        # Rows
        for row in rows:
            formatted_row = [str(cell) for cell in row]
            lines.append(format_str.format(*formatted_row))
        
        return "\n".join(lines)
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def print_header(title: str, subtitle: str = None, width: int = 60) -> None:
        """Print formatted header."""
        print("=" * width)
        print(f"{title:^{width}}")
        if subtitle:
            print(f"{subtitle:^{width}}")
        print("=" * width)
    
    @staticmethod
    def print_section(title: str, width: int = 60) -> None:
        """Print formatted section header."""
        print(f"\n{title}")
        print("-" * len(title))
    
    @staticmethod
    def print_status(message: str, status: str, color: bool = True) -> None:
        """Print status message with optional color."""
        if color:
            colors = {
                'success': '\033[32m✅\033[0m',  # Green checkmark
                'error': '\033[31m❌\033[0m',    # Red X
                'warning': '\033[33m⚠️\033[0m',  # Yellow warning
                'info': '\033[34mℹ️\033[0m',     # Blue info
                'processing': '\033[36m🔄\033[0m'  # Cyan processing
            }
            icon = colors.get(status.lower(), '•')
        else:
            icons = {
                'success': '[OK]',
                'error': '[ERROR]',
                'warning': '[WARNING]',
                'info': '[INFO]',
                'processing': '[PROCESSING]'
            }
            icon = icons.get(status.lower(), '[STATUS]')
        
        print(f"{icon} {message}")
    
    @staticmethod
    def print_summary(title: str, items: Dict[str, Any], width: int = 60) -> None:
        """Print formatted summary."""
        print(f"\n{title}")
        print("=" * len(title))
        
        for key, value in items.items():
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    value_str = f"{value:.2f}"
                else:
                    value_str = f"{value:,}"
            else:
                value_str = str(value)
            
            print(f"{key:.<{width-len(value_str)-2}} {value_str}")
    
    def create_progress_indicator(self, total: int, description: str = "Processing") -> ProgressIndicator:
        """Create a progress indicator."""
        return ProgressIndicator(total, description)
    
    def add_common_arguments(self) -> None:
        """Add commonly used arguments."""
        self.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without executing them"
        )
        self.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        self.add_argument(
            "--quiet", "-q",
            action="store_true",
            help="Suppress non-essential output"
        )
        self.add_argument(
            "--force", "-f",
            action="store_true",
            help="Force operation without confirmation"
        )
    
    def validate_file_path(self, path: str, must_exist: bool = True) -> Path:
        """Validate and return Path object."""
        file_path = Path(path)
        
        if must_exist and not file_path.exists():
            self.parser.error(f"File does not exist: {path}")
        
        return file_path
    
    def validate_directory_path(self, path: str, must_exist: bool = True, create: bool = False) -> Path:
        """Validate and return directory Path object."""
        dir_path = Path(path)
        
        if must_exist and not dir_path.exists():
            if create:
                dir_path.mkdir(parents=True, exist_ok=True)
            else:
                self.parser.error(f"Directory does not exist: {path}")
        
        if dir_path.exists() and not dir_path.is_dir():
            self.parser.error(f"Path is not a directory: {path}")
        
        return dir_path