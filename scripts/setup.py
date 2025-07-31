#!/usr/bin/env python3
"""
Development Environment Setup Script for Weather Dashboard

This script sets up the development environment for new contributors:
- Python version validation
- Virtual environment creation
- Dependency installation
- Configuration file setup
- Database initialization
- Development tools setup
- Environment validation

Usage:
    python setup.py [options]
    python setup.py --env development
    python setup.py --skip-tests
    python setup.py --force-reinstall
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import common utilities
from common.base_script import BaseScript
from common.cli_utils import CLIUtils
from common.file_utils import FileUtils
from common.process_utils import ProcessUtils, ProcessResult


@dataclass
class SetupStep:
    """Represents a setup step with its result."""
    name: str
    description: str
    success: bool = False
    message: str = ""
    required: bool = True
    duration: float = 0.0
    skipped: bool = False
    skip_reason: str = ""


class EnvironmentSetup(BaseScript):
    """Development environment setup manager."""
    
    def __init__(self):
        super().__init__(
            name="setup",
            description="Setup Weather Dashboard development environment",
            version="2.0.0"
        )
        
        # Get configuration
        self.setup_config = self.config.get('scripts.setup', {})
        self.env_config = self.setup_config.get('environments', {})
        self.deps_config = self.setup_config.get('dependencies', {})
        self.tools_config = self.setup_config.get('tools', {})
        
        # Initialize utilities
        self.file_utils = FileUtils(logger=self.logger)
        self.process_utils = ProcessUtils(
            timeout=self.setup_config.get('timeout', 600),
            logger=self.logger
        )
        
        # Setup tracking
        self.setup_steps: List[SetupStep] = []
        self.environment_type = 'development'
        
        # Define minimum requirements
        self.min_python_version = tuple(self.setup_config.get('min_python_version', [3, 8]))
        self.required_files = self.setup_config.get('required_files', [
            'requirements.txt', 'main.py', 'src/'
        ])
        
        # Define environment-specific configurations
        self.env_configs = {
            'development': {
                'requirements_files': [
                    'requirements.txt',
                    'docs/development/requirements-dev.txt'
                ],
                'install_dev_tools': True,
                'run_tests': True,
                'create_sample_data': True
            },
            'production': {
                'requirements_files': ['requirements.txt'],
                'install_dev_tools': False,
                'run_tests': False,
                'create_sample_data': False
            },
            'testing': {
                'requirements_files': [
                    'requirements.txt',
                    'docs/development/requirements-test.txt'
                ],
                'install_dev_tools': False,
                'run_tests': True,
                'create_sample_data': True
            }
        }
    
    def setup_cli(self) -> CLIUtils:
        """Setup command line interface."""
        cli = CLIUtils(
            script_name=self.name,
            description=self.description,
            version=self.version
        )
        
        # Add arguments
        cli.add_argument(
            '--env', '--environment',
            type=str,
            choices=['development', 'production', 'testing'],
            default='development',
            help='Environment type to setup (default: development)'
        )
        
        cli.add_argument(
            '--skip-venv',
            action='store_true',
            help='Skip virtual environment creation'
        )
        
        cli.add_argument(
            '--skip-deps',
            action='store_true',
            help='Skip dependency installation'
        )
        
        cli.add_argument(
            '--skip-tests',
            action='store_true',
            help='Skip running tests'
        )
        
        cli.add_argument(
            '--skip-config',
            action='store_true',
            help='Skip configuration file setup'
        )
        
        cli.add_argument(
            '--force-reinstall',
            action='store_true',
            help='Force reinstall all dependencies'
        )
        
        cli.add_argument(
            '--python-path',
            type=str,
            help='Path to Python executable to use'
        )
        
        cli.add_argument(
            '--venv-path',
            type=str,
            help='Custom path for virtual environment'
        )
        
        cli.add_argument(
            '--check-only',
            action='store_true',
            help='Only check environment, do not setup'
        )
        
        cli.add_common_arguments()
        
        return cli
    
    def add_step(self, step: SetupStep) -> None:
        """Add a setup step to tracking."""
        self.setup_steps.append(step)
        
        # Log the step result
        if step.skipped:
            self.logger.info(f"⏭️ {step.description} (skipped: {step.skip_reason})")
        elif step.success:
            self.logger.info(f"✅ {step.description} ({step.duration:.2f}s)")
        else:
            level = 'error' if step.required else 'warning'
            getattr(self.logger, level)(f"❌ {step.description}: {step.message}")
    
    def check_python_version(self, python_path: Optional[str] = None) -> SetupStep:
        """Check Python version requirements."""
        step = SetupStep(
            name="python_version",
            description="Python version check",
            required=True
        )
        
        try:
            if python_path:
                # Check specific Python executable
                result = self.process_utils.run_command(
                    f'"{python_path}" --version',
                    capture_output=True
                )
                if result.returncode != 0:
                    step.message = f"Cannot execute Python at {python_path}"
                    return step
                
                version_str = result.stdout.strip().split()[1]
                version_parts = [int(x) for x in version_str.split('.')[:2]]
                python_version = tuple(version_parts)
            else:
                # Check current Python
                python_version = sys.version_info[:2]
            
            if python_version >= self.min_python_version:
                step.success = True
                step.message = f"Python {'.'.join(map(str, python_version))}"
            else:
                step.message = f"Python {'.'.join(map(str, python_version))} < {'.'.join(map(str, self.min_python_version))}"
        
        except Exception as e:
            step.message = f"Error checking Python version: {e}"
        
        return step
    
    def check_required_files(self) -> SetupStep:
        """Check if required project files exist."""
        step = SetupStep(
            name="required_files",
            description="Required files check",
            required=True
        )
        
        missing_files = []
        for file_path in self.required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if not missing_files:
            step.success = True
            step.message = f"All {len(self.required_files)} required files found"
        else:
            step.message = f"Missing files: {', '.join(missing_files)}"
        
        return step
    
    def create_virtual_environment(self, venv_path: Optional[str] = None, python_path: Optional[str] = None) -> SetupStep:
        """Create virtual environment."""
        step = SetupStep(
            name="virtual_environment",
            description="Virtual environment creation",
            required=False
        )
        
        try:
            # Determine venv path
            if venv_path:
                venv_dir = Path(venv_path)
            else:
                venv_dir = self.project_root / ".venv"
            
            # Check if already exists
            if venv_dir.exists():
                step.success = True
                step.message = f"Virtual environment already exists at {venv_dir}"
                return step
            
            # Create virtual environment
            python_exe = python_path or sys.executable
            result = self.process_utils.run_command(
                f'"{python_exe}" -m venv "{venv_dir}"',
                capture_output=True
            )
            
            if result.returncode == 0:
                step.success = True
                step.message = f"Created virtual environment at {venv_dir}"
                step.duration = result.duration
            else:
                step.message = f"Failed to create virtual environment: {result.stderr}"
        
        except Exception as e:
            step.message = f"Error creating virtual environment: {e}"
        
        return step
    
    def get_venv_paths(self, venv_path: Optional[str] = None) -> Tuple[Path, Path, Path]:
        """Get virtual environment paths."""
        if venv_path:
            venv_dir = Path(venv_path)
        else:
            venv_dir = self.project_root / ".venv"
        
        if os.name == "nt":  # Windows
            python_exe = venv_dir / "Scripts" / "python.exe"
            pip_exe = venv_dir / "Scripts" / "pip.exe"
            activate_script = venv_dir / "Scripts" / "activate.bat"
        else:  # Unix-like
            python_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"
            activate_script = venv_dir / "bin" / "activate"
        
        return python_exe, pip_exe, activate_script
    
    def install_dependencies(self, venv_path: Optional[str] = None, force_reinstall: bool = False) -> List[SetupStep]:
        """Install project dependencies."""
        steps = []
        
        # Get environment configuration
        env_config = self.env_configs.get(self.environment_type, self.env_configs['development'])
        requirements_files = env_config.get('requirements_files', ['requirements.txt'])
        
        # Get pip executable
        _, pip_exe, _ = self.get_venv_paths(venv_path)
        
        # Install each requirements file
        for req_file in requirements_files:
            step = SetupStep(
                name=f"install_{req_file.replace('/', '_').replace('.txt', '')}",
                description=f"Install dependencies from {req_file}",
                required=req_file == 'requirements.txt'
            )
            
            try:
                req_path = self.project_root / req_file
                
                if not req_path.exists():
                    if step.required:
                        step.message = f"Required file {req_file} not found"
                    else:
                        step.skipped = True
                        step.skip_reason = f"Optional file {req_file} not found"
                        step.success = True
                    steps.append(step)
                    continue
                
                # Build install command
                cmd_parts = [str(pip_exe), "install"]
                if force_reinstall:
                    cmd_parts.append("--force-reinstall")
                cmd_parts.extend(["-r", str(req_path)])
                
                command = " ".join(f'"{part}"' if " " in part else part for part in cmd_parts)
                
                result = self.process_utils.run_command(
                    command,
                    capture_output=True
                )
                
                if result.returncode == 0:
                    step.success = True
                    step.message = f"Installed dependencies from {req_file}"
                    step.duration = result.duration
                else:
                    step.message = f"Failed to install from {req_file}: {result.stderr[:200]}"
            
            except Exception as e:
                step.message = f"Error installing from {req_file}: {e}"
            
            steps.append(step)
        
        return steps
    
    def setup_configuration_files(self) -> List[SetupStep]:
        """Setup configuration files."""
        steps = []
        
        # Setup .env file
        env_step = SetupStep(
            name="env_file",
            description="Environment configuration file",
            required=False
        )
        
        try:
            env_file = self.project_root / ".env"
            env_example = self.project_root / ".env.example"
            
            if env_file.exists():
                env_step.success = True
                env_step.message = ".env file already exists"
            elif env_example.exists():
                # Copy example to .env
                content = self.file_utils.read_text_file(env_example)
                self.file_utils.write_text_file(env_file, content)
                env_step.success = True
                env_step.message = "Created .env file from example"
            else:
                env_step.skipped = True
                env_step.skip_reason = "No .env.example file found"
                env_step.success = True
        
        except Exception as e:
            env_step.message = f"Error setting up .env file: {e}"
        
        steps.append(env_step)
        
        # Setup other config files if needed
        config_files = self.setup_config.get('config_files', {})
        for config_name, config_info in config_files.items():
            step = SetupStep(
                name=f"config_{config_name}",
                description=f"Setup {config_name} configuration",
                required=config_info.get('required', False)
            )
            
            try:
                target_path = self.project_root / config_info['path']
                template_path = self.project_root / config_info.get('template', f"{config_info['path']}.example")
                
                if target_path.exists():
                    step.success = True
                    step.message = f"{config_name} already exists"
                elif template_path.exists():
                    content = self.file_utils.read_text_file(template_path)
                    self.file_utils.write_text_file(target_path, content)
                    step.success = True
                    step.message = f"Created {config_name} from template"
                else:
                    if step.required:
                        step.message = f"Required template {template_path} not found"
                    else:
                        step.skipped = True
                        step.skip_reason = f"Template {template_path} not found"
                        step.success = True
            
            except Exception as e:
                step.message = f"Error setting up {config_name}: {e}"
            
            steps.append(step)
        
        return steps
    
    def install_development_tools(self, venv_path: Optional[str] = None) -> SetupStep:
        """Install development tools."""
        step = SetupStep(
            name="dev_tools",
            description="Development tools installation",
            required=False
        )
        
        try:
            # Get pip executable
            _, pip_exe, _ = self.get_venv_paths(venv_path)
            
            # Define development tools
            dev_tools = self.tools_config.get('development', [
                'black', 'isort', 'flake8', 'mypy', 'pytest', 'pytest-cov'
            ])
            
            if not dev_tools:
                step.skipped = True
                step.skip_reason = "No development tools configured"
                step.success = True
                return step
            
            # Install tools
            tools_str = " ".join(dev_tools)
            result = self.process_utils.run_command(
                f'"{pip_exe}" install {tools_str}',
                capture_output=True
            )
            
            if result.returncode == 0:
                step.success = True
                step.message = f"Installed development tools: {', '.join(dev_tools)}"
                step.duration = result.duration
            else:
                step.message = f"Failed to install development tools: {result.stderr[:200]}"
        
        except Exception as e:
            step.message = f"Error installing development tools: {e}"
        
        return step
    
    def run_tests(self, venv_path: Optional[str] = None) -> SetupStep:
        """Run tests to verify setup."""
        step = SetupStep(
            name="tests",
            description="Test suite execution",
            required=False
        )
        
        try:
            # Get Python executable
            python_exe, _, _ = self.get_venv_paths(venv_path)
            
            # Check if tests directory exists
            tests_dir = self.project_root / "tests"
            if not tests_dir.exists():
                step.skipped = True
                step.skip_reason = "No tests directory found"
                step.success = True
                return step
            
            # Run pytest
            result = self.process_utils.run_command(
                f'"{python_exe}" -m pytest tests/ -v --tb=short',
                capture_output=True
            )
            
            if result.returncode == 0:
                step.success = True
                step.message = "All tests passed"
                step.duration = result.duration
            else:
                step.message = f"Some tests failed: {result.stderr[:200]}"
        
        except Exception as e:
            step.message = f"Error running tests: {e}"
        
        return step
    
    def display_setup_summary(self, check_only: bool = False) -> None:
        """Display setup summary."""
        cli = CLIUtils(self.name, self.description, self.version)
        
        # Display header
        mode_text = "Environment Check" if check_only else "Environment Setup"
        cli.print_header("Development Setup", f"Weather Dashboard {mode_text}")
        
        # Display steps
        cli.print_section("Setup Steps")
        
        for step in self.setup_steps:
            if step.skipped:
                status = "⏭️ SKIP"
            elif step.success:
                status = "✅ PASS"
            else:
                status = "❌ FAIL" if step.required else "⚠️ WARN"
            
            duration_text = f"({step.duration:.2f}s)" if step.duration > 0 else ""
            print(f"{status} {step.description} {duration_text}")
            
            if step.message:
                print(f"  {step.message}")
        
        # Summary statistics
        total = len(self.setup_steps)
        passed = sum(1 for s in self.setup_steps if s.success)
        failed = sum(1 for s in self.setup_steps if not s.success and not s.skipped)
        skipped = sum(1 for s in self.setup_steps if s.skipped)
        required_failed = sum(1 for s in self.setup_steps if not s.success and s.required and not s.skipped)
        
        cli.print_summary("Summary", {
            'Total Steps': total,
            'Passed': passed,
            'Failed': failed,
            'Skipped': skipped,
            'Critical Failures': required_failed
        })
        
        # Next steps
        if not check_only and required_failed == 0:
            cli.print_section("Next Steps")
            
            # Get activation command
            _, _, activate_script = self.get_venv_paths()
            
            print("🎉 Setup completed successfully!")
            print("")
            print("📋 To start developing:")
            print(f"1. Activate virtual environment:")
            if os.name == "nt":
                print(f"   {activate_script}")
            else:
                print(f"   source {activate_script}")
            print("2. Edit .env file with your API keys")
            print("3. Run the application: python main.py")
            print("4. Run tests: python -m pytest tests/")
            print("5. Run pre-commit checks: python scripts/pre_commit_check.py")
    
    def run(self) -> int:
        """Main execution method."""
        try:
            # Setup CLI and parse arguments
            cli = self.setup_cli()
            args = cli.parse_args()
            
            # Configure logging
            self.configure_logging(args)
            
            # Set environment type
            self.environment_type = args.env
            
            self.logger.info(f"Starting {self.environment_type} environment setup")
            
            # Step 1: Check Python version
            step = self.check_python_version(args.python_path)
            self.add_step(step)
            
            if not step.success:
                cli.print_status("Python version check failed", "error")
                return 1
            
            # Step 2: Check required files
            step = self.check_required_files()
            self.add_step(step)
            
            if not step.success:
                cli.print_status("Required files check failed", "error")
                return 1
            
            # If check-only mode, stop here
            if args.check_only:
                self.display_setup_summary(check_only=True)
                return 0
            
            # Step 3: Create virtual environment
            if not args.skip_venv:
                step = self.create_virtual_environment(args.venv_path, args.python_path)
                self.add_step(step)
            
            # Step 4: Install dependencies
            if not args.skip_deps:
                steps = self.install_dependencies(args.venv_path, args.force_reinstall)
                for step in steps:
                    self.add_step(step)
            
            # Step 5: Setup configuration files
            if not args.skip_config:
                steps = self.setup_configuration_files()
                for step in steps:
                    self.add_step(step)
            
            # Step 6: Install development tools (if development environment)
            env_config = self.env_configs.get(self.environment_type, {})
            if env_config.get('install_dev_tools', False):
                step = self.install_development_tools(args.venv_path)
                self.add_step(step)
            
            # Step 7: Run tests (if enabled)
            if not args.skip_tests and env_config.get('run_tests', False):
                step = self.run_tests(args.venv_path)
                self.add_step(step)
            
            # Display summary
            if not args.quiet:
                self.display_setup_summary()
            
            # Check for critical failures
            critical_failures = sum(1 for s in self.setup_steps if not s.success and s.required and not s.skipped)
            
            if critical_failures == 0:
                cli.print_status("Environment setup completed successfully!", "success")
                return 0
            else:
                cli.print_status(f"{critical_failures} critical setup steps failed", "error")
                return 1
        
        except KeyboardInterrupt:
            self.logger.info("Setup cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error during setup: {e}")
            return 1


def main():
    """Main entry point."""
    setup = EnvironmentSetup()
    return setup.run()


if __name__ == "__main__":
    exit(main())
