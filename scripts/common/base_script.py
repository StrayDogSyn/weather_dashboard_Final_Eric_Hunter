#!/usr/bin/env python3
"""
Base Script Class for Weather Dashboard Scripts

Provides common functionality for all scripts including:
- Standardized logging
- Configuration management
- Error handling
- CLI argument parsing
- Progress tracking
"""

import sys
import time
import argparse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .logger import setup_logger
from .config_manager import ConfigManager
from .cli_utils import CLIUtils


class BaseScript(ABC):
    """Abstract base class for all Weather Dashboard scripts."""
    
    def __init__(self, script_name: str, description: str, version: str = "1.0.0"):
        self.script_name = script_name
        self.description = description
        self.version = version
        self.start_time = time.time()
        
        # Initialize components
        self.project_root = self._find_project_root()
        self.logger = setup_logger(script_name)
        self.config = ConfigManager(self.project_root)
        self.cli = CLIUtils(script_name, description, version)
        
        # Script state
        self.dry_run = False
        self.verbose = False
        self.args: Optional[argparse.Namespace] = None
        
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "main.py").exists() or (current / "requirements.txt").exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def setup_common_args(self) -> None:
        """Setup common command line arguments."""
        self.cli.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without executing them"
        )
        self.cli.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        self.cli.add_argument(
            "--config",
            type=str,
            help="Path to custom configuration file"
        )
        self.cli.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging level"
        )
    
    @abstractmethod
    def setup_args(self) -> None:
        """Setup script-specific command line arguments."""
        pass
    
    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Execute the main script logic."""
        pass
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command line arguments. Override in subclasses."""
        return True
    
    def pre_run_setup(self) -> None:
        """Setup tasks before running main logic. Override in subclasses."""
        pass
    
    def post_run_cleanup(self) -> None:
        """Cleanup tasks after running main logic. Override in subclasses."""
        pass
    
    def handle_error(self, error: Exception) -> None:
        """Handle errors consistently across scripts."""
        self.logger.error(f"Error in {self.script_name}: {error}")
        if self.verbose:
            self.logger.exception("Full traceback:")
    
    def log_execution_summary(self, result: Dict[str, Any]) -> None:
        """Log execution summary."""
        execution_time = time.time() - self.start_time
        self.logger.info(f"Script execution completed in {execution_time:.2f} seconds")
        
        if result:
            self.logger.info("Execution results:")
            for key, value in result.items():
                self.logger.info(f"  {key}: {value}")
    
    def execute(self, argv: Optional[List[str]] = None) -> int:
        """Main execution method."""
        try:
            # Setup arguments
            self.setup_common_args()
            self.setup_args()
            
            # Parse arguments
            self.args = self.cli.parse_args(argv)
            
            # Configure based on arguments
            if self.args.config:
                self.config.load_custom_config(self.args.config)
            
            self.dry_run = self.args.dry_run
            self.verbose = self.args.verbose
            
            # Setup logging level
            self.logger.setLevel(self.args.log_level)
            
            # Validate arguments
            if not self.validate_args(self.args):
                self.logger.error("Argument validation failed")
                return 1
            
            # Log startup
            self.logger.info(f"Starting {self.script_name} v{self.version}")
            self.logger.info(f"Project root: {self.project_root}")
            self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
            
            # Pre-run setup
            self.pre_run_setup()
            
            # Execute main logic
            result = self.run()
            
            # Post-run cleanup
            self.post_run_cleanup()
            
            # Log summary
            self.log_execution_summary(result)
            
            self.logger.info(f"{self.script_name} completed successfully")
            return 0
            
        except KeyboardInterrupt:
            self.logger.warning("Script interrupted by user")
            return 130
        except Exception as error:
            self.handle_error(error)
            return 1
    
    def main(self) -> None:
        """Entry point for script execution."""
        sys.exit(self.execute())