"""Common utilities for Weather Dashboard scripts."""

__version__ = "1.0.0"
__author__ = "Weather Dashboard Team"

# Import commonly used classes for convenience
from .base_script import BaseScript
from .logger import setup_logger
from .config_manager import ConfigManager
from .cli_utils import CLIUtils
from .file_utils import FileUtils
from .process_utils import ProcessUtils

__all__ = [
    "BaseScript",
    "setup_logger",
    "ConfigManager",
    "CLIUtils",
    "FileUtils",
    "ProcessUtils",
]