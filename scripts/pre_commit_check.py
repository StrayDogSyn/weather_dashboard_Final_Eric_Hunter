#!/usr/bin/env python3
"""
Pre-commit Code Quality Check Script for Weather Dashboard

Ensures all code passes quality checks before committing:
- Black formatting
- isort import organization
- flake8 style checking
- mypy type checking
- Custom project-specific checks

Usage:
    python pre_commit_check.py [options]
    python pre_commit_check.py --fix
    python pre_commit_check.py --tools black,isort
    python pre_commit_check.py --parallel
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# Import common utilities
from common.base_script import BaseScript
from common.cli_utils import CLIUtils
from common.process_utils import ProcessUtils, ProcessResult


@dataclass
class CheckResult:
    """Result of a code quality check."""
    name: str
    description: str
    command: str
    success: bool
    output: str = ""
    error: str = ""
    duration: float = 0.0
    skipped: bool = False
    skip_reason: str = ""


class PreCommitChecker(BaseScript):
    """Pre-commit code quality checker."""
    
    def __init__(self):
        super().__init__(
            name="pre_commit_check",
            description="Run pre-commit code quality checks",
            version="2.0.0"
        )
        
        # Get configuration
        self.check_config = self.config.get('scripts.pre_commit', {})
        self.tools_config = self.check_config.get('tools', {})
        self.paths_config = self.check_config.get('paths', {})
        self.parallel_config = self.check_config.get('parallel', {})
        
        # Initialize process utilities
        self.process_utils = ProcessUtils(
            timeout=self.check_config.get('timeout', 300),
            logger=self.logger
        )
        
        # Define default paths to check
        self.default_paths = self.paths_config.get('default', [
            'src/', 'tests/', 'scripts/', 'main.py'
        ])
        
        # Define available tools and their configurations
        self.available_tools = {
            'black': {
                'name': 'Black',
                'description': 'Code formatting',
                'check_command': 'python -m black --check --diff {paths}',
                'fix_command': 'python -m black {paths}',
                'config_file': None,
                'enabled': True
            },
            'isort': {
                'name': 'isort',
                'description': 'Import organization',
                'check_command': 'python -m isort --check-only --diff {paths}',
                'fix_command': 'python -m isort {paths}',
                'config_file': None,
                'enabled': True
            },
            'flake8': {
                'name': 'flake8',
                'description': 'Style checking',
                'check_command': 'python -m flake8 {paths} --config=setup.cfg',
                'fix_command': None,  # flake8 doesn't auto-fix
                'config_file': 'setup.cfg',
                'enabled': True
            },
            'mypy': {
                'name': 'mypy',
                'description': 'Type checking',
                'check_command': 'python -m mypy {paths} --config-file=setup.cfg',
                'fix_command': None,  # mypy doesn't auto-fix
                'config_file': 'setup.cfg',
                'enabled': True
            },
            'pylint': {
                'name': 'pylint',
                'description': 'Code analysis',
                'check_command': 'python -m pylint {paths}',
                'fix_command': None,
                'config_file': '.pylintrc',
                'enabled': False  # Disabled by default
            },
            'bandit': {
                'name': 'bandit',
                'description': 'Security analysis',
                'check_command': 'python -m bandit -r {paths}',
                'fix_command': None,
                'config_file': None,
                'enabled': False  # Disabled by default
            }
        }
        
        # Update tool configurations from config file
        for tool_name, tool_config in self.tools_config.items():
            if tool_name in self.available_tools:
                self.available_tools[tool_name].update(tool_config)
    
    def setup_cli(self) -> CLIUtils:
        """Setup command line interface."""
        cli = CLIUtils(
            script_name=self.name,
            description=self.description,
            version=self.version
        )
        
        # Add arguments
        cli.add_argument(
            '--tools', '-t',
            type=str,
            help='Comma-separated list of tools to run (default: all enabled)'
        )
        
        cli.add_argument(
            '--paths', '-p',
            type=str,
            help='Comma-separated list of paths to check (default: configured paths)'
        )
        
        cli.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to auto-fix issues where possible'
        )
        
        cli.add_argument(
            '--parallel',
            action='store_true',
            help='Run checks in parallel for faster execution'
        )
        
        cli.add_argument(
            '--max-workers',
            type=int,
            default=self.parallel_config.get('max_workers', 4),
            help='Maximum number of parallel workers'
        )
        
        cli.add_argument(
            '--fail-fast',
            action='store_true',
            help='Stop on first failure'
        )
        
        cli.add_argument(
            '--list-tools',
            action='store_true',
            help='List available tools and exit'
        )
        
        cli.add_argument(
            '--config-check',
            action='store_true',
            help='Check if required tools are installed'
        )
        
        cli.add_common_arguments()
        
        return cli
    
    def get_enabled_tools(self, requested_tools: Optional[List[str]] = None) -> Dict[str, dict]:
        """Get list of enabled tools to run."""
        if requested_tools:
            # Filter to requested tools
            tools = {}
            for tool_name in requested_tools:
                if tool_name in self.available_tools:
                    tools[tool_name] = self.available_tools[tool_name]
                else:
                    self.logger.warning(f"Unknown tool: {tool_name}")
            return tools
        else:
            # Return all enabled tools
            return {
                name: config for name, config in self.available_tools.items()
                if config.get('enabled', True)
            }
    
    def check_tool_availability(self, tools: Dict[str, dict]) -> Dict[str, bool]:
        """Check if required tools are available."""
        availability = {}
        
        for tool_name, tool_config in tools.items():
            # Extract the tool command (first part of check_command)
            command_parts = tool_config['check_command'].split()
            if len(command_parts) >= 3 and command_parts[0] == 'python' and command_parts[1] == '-m':
                tool_module = command_parts[2]
                available = self.process_utils.check_package_installed(tool_module)
            else:
                # For other commands, check if the command is available
                tool_cmd = command_parts[0] if command_parts else tool_name
                available = self.process_utils.check_command_available(tool_cmd)
            
            availability[tool_name] = available
            
            if not available:
                self.logger.warning(f"Tool {tool_name} is not available")
        
        return availability
    
    def run_single_check(self, tool_name: str, tool_config: dict, paths: List[str], fix_mode: bool = False) -> CheckResult:
        """Run a single code quality check."""
        # Prepare paths string
        paths_str = ' '.join(paths)
        
        # Choose command based on mode
        if fix_mode and tool_config.get('fix_command'):
            command = tool_config['fix_command'].format(paths=paths_str)
            description = f"{tool_config['description']} (fixing)"
        else:
            command = tool_config['check_command'].format(paths=paths_str)
            description = tool_config['description']
        
        self.logger.info(f"Running {tool_name}: {command}")
        
        try:
            # Run the command
            result = self.process_utils.run_command(
                command,
                cwd=self.project_root,
                capture_output=True
            )
            
            return CheckResult(
                name=tool_name,
                description=description,
                command=command,
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                duration=result.duration
            )
        
        except Exception as e:
            self.logger.error(f"Error running {tool_name}: {e}")
            return CheckResult(
                name=tool_name,
                description=description,
                command=command,
                success=False,
                error=str(e)
            )
    
    def run_checks_sequential(self, tools: Dict[str, dict], paths: List[str], fix_mode: bool = False, fail_fast: bool = False) -> List[CheckResult]:
        """Run checks sequentially."""
        results = []
        
        for tool_name, tool_config in tools.items():
            result = self.run_single_check(tool_name, tool_config, paths, fix_mode)
            results.append(result)
            
            # Log immediate result
            if result.success:
                self.logger.info(f"✅ {result.description} passed ({result.duration:.2f}s)")
            else:
                self.logger.error(f"❌ {result.description} failed ({result.duration:.2f}s)")
                if result.error:
                    self.logger.error(f"Error: {result.error}")
            
            # Stop on first failure if fail_fast is enabled
            if fail_fast and not result.success:
                self.logger.info("Stopping due to --fail-fast")
                break
        
        return results
    
    def run_checks_parallel(self, tools: Dict[str, dict], paths: List[str], max_workers: int = 4, fix_mode: bool = False) -> List[CheckResult]:
        """Run checks in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_tool = {
                executor.submit(self.run_single_check, tool_name, tool_config, paths, fix_mode): tool_name
                for tool_name, tool_config in tools.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Log immediate result
                    if result.success:
                        self.logger.info(f"✅ {result.description} passed ({result.duration:.2f}s)")
                    else:
                        self.logger.error(f"❌ {result.description} failed ({result.duration:.2f}s)")
                
                except Exception as e:
                    self.logger.error(f"Error running {tool_name}: {e}")
                    results.append(CheckResult(
                        name=tool_name,
                        description=tools[tool_name]['description'],
                        command="",
                        success=False,
                        error=str(e)
                    ))
        
        # Sort results by tool name for consistent output
        results.sort(key=lambda r: r.name)
        return results
    
    def display_results(self, results: List[CheckResult], fix_mode: bool = False) -> None:
        """Display check results."""
        cli = CLIUtils(self.name, self.description, self.version)
        
        # Display header
        mode_text = "Code Quality Fixes" if fix_mode else "Code Quality Checks"
        cli.print_header("Pre-commit Checker", f"Weather Dashboard {mode_text}")
        
        # Display individual results
        cli.print_section("Check Results")
        
        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            if result.skipped:
                status = "⏭️ SKIP"
            
            duration_text = f"({result.duration:.2f}s)" if result.duration > 0 else ""
            print(f"{status} {result.description} {duration_text}")
            
            # Show error details for failed checks
            if not result.success and not result.skipped:
                if result.output:
                    print(f"  Output: {result.output[:200]}{'...' if len(result.output) > 200 else ''}")
                if result.error:
                    print(f"  Error: {result.error[:200]}{'...' if len(result.error) > 200 else ''}")
        
        # Summary
        passed = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)
        total = len(results)
        
        cli.print_summary("Summary", {
            'Total Checks': total,
            'Passed': passed,
            'Failed': failed,
            'Skipped': skipped,
            'Success Rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%"
        })
        
        # Recommendations
        if failed > 0 and not fix_mode:
            cli.print_section("Recommendations")
            print("💡 To auto-fix formatting issues, run:")
            print("   python pre_commit_check.py --fix")
            print("")
            print("💡 To run specific tools only:")
            print("   python pre_commit_check.py --tools black,isort")
            print("")
            print("💡 To run checks in parallel:")
            print("   python pre_commit_check.py --parallel")
    
    def list_available_tools(self) -> None:
        """List all available tools and their status."""
        cli = CLIUtils(self.name, self.description, self.version)
        
        cli.print_header("Available Tools", "Pre-commit Code Quality Tools")
        
        # Check tool availability
        availability = self.check_tool_availability(self.available_tools)
        
        table_data = []
        for tool_name, tool_config in self.available_tools.items():
            enabled = "✅" if tool_config.get('enabled', True) else "❌"
            available = "✅" if availability.get(tool_name, False) else "❌"
            can_fix = "✅" if tool_config.get('fix_command') else "❌"
            
            table_data.append([
                tool_name,
                tool_config['description'],
                enabled,
                available,
                can_fix
            ])
        
        print(cli.format_table(
            ['Tool', 'Description', 'Enabled', 'Available', 'Can Fix'],
            table_data
        ))
    
    def run_config_check(self) -> bool:
        """Check configuration and tool availability."""
        cli = CLIUtils(self.name, self.description, self.version)
        
        cli.print_header("Configuration Check", "Pre-commit Setup Validation")
        
        # Check enabled tools
        enabled_tools = self.get_enabled_tools()
        availability = self.check_tool_availability(enabled_tools)
        
        cli.print_section("Tool Availability")
        
        all_available = True
        for tool_name, available in availability.items():
            status = "✅" if available else "❌"
            print(f"{status} {tool_name}")
            if not available:
                all_available = False
                print(f"   Install with: pip install {tool_name}")
        
        # Check configuration files
        cli.print_section("Configuration Files")
        
        config_files = set()
        for tool_config in enabled_tools.values():
            if tool_config.get('config_file'):
                config_files.add(tool_config['config_file'])
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            exists = config_path.exists()
            status = "✅" if exists else "❌"
            print(f"{status} {config_file}")
            if not exists:
                all_available = False
        
        # Check paths
        cli.print_section("Target Paths")
        
        for path_str in self.default_paths:
            path = self.project_root / path_str
            exists = path.exists()
            status = "✅" if exists else "⚠️"
            print(f"{status} {path_str}")
        
        return all_available
    
    def run(self) -> int:
        """Main execution method."""
        try:
            # Setup CLI and parse arguments
            cli = self.setup_cli()
            args = cli.parse_args()
            
            # Configure logging based on arguments
            self.configure_logging(args)
            
            # Handle special modes
            if args.list_tools:
                self.list_available_tools()
                return 0
            
            if args.config_check:
                success = self.run_config_check()
                return 0 if success else 1
            
            self.logger.info("Starting pre-commit checks")
            
            # Parse tools and paths
            requested_tools = args.tools.split(',') if args.tools else None
            paths = args.paths.split(',') if args.paths else self.default_paths
            
            # Get enabled tools
            tools = self.get_enabled_tools(requested_tools)
            
            if not tools:
                cli.print_status("No tools enabled or available", "error")
                return 1
            
            # Check tool availability
            availability = self.check_tool_availability(tools)
            unavailable_tools = [name for name, available in availability.items() if not available]
            
            if unavailable_tools:
                cli.print_status(f"Some tools are not available: {', '.join(unavailable_tools)}", "warning")
                # Remove unavailable tools
                tools = {name: config for name, config in tools.items() if availability.get(name, False)}
            
            if not tools:
                cli.print_status("No available tools to run", "error")
                return 1
            
            # Run checks
            if args.parallel and len(tools) > 1:
                results = self.run_checks_parallel(
                    tools, paths, args.max_workers, args.fix
                )
            else:
                results = self.run_checks_sequential(
                    tools, paths, args.fix, args.fail_fast
                )
            
            # Display results
            if not args.quiet:
                self.display_results(results, args.fix)
            
            # Determine exit code
            failed_count = sum(1 for r in results if not r.success and not r.skipped)
            
            if failed_count == 0:
                if args.fix:
                    cli.print_status("All fixes applied successfully!", "success")
                else:
                    cli.print_status("All checks passed! Code is ready to commit.", "success")
                return 0
            else:
                if args.fix:
                    cli.print_status(f"{failed_count} tools could not fix all issues", "error")
                else:
                    cli.print_status(f"{failed_count} checks failed", "error")
                return 1
        
        except KeyboardInterrupt:
            self.logger.info("Pre-commit checks cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1


def main():
    """Main entry point."""
    checker = PreCommitChecker()
    return checker.run()


if __name__ == "__main__":
    exit(main())
