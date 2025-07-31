#!/usr/bin/env python3
"""
MCP Server Verification Script for Weather Dashboard

This script verifies that MCP servers are properly installed and configured:
- UV package manager installation
- Required Python packages
- MCP configuration files
- Server accessibility and functionality
- Connection testing and diagnostics

Usage:
    python verify_mcp_setup.py [options]
    python verify_mcp_setup.py --fix-issues
    python verify_mcp_setup.py --server blender
    python verify_mcp_setup.py --export-report
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# Import common utilities
from common.base_script import BaseScript
from common.cli_utils import CLIUtils
from common.file_utils import FileUtils
from common.process_utils import ProcessUtils, ProcessResult


@dataclass
class VerificationResult:
    """Represents a verification check result."""
    name: str
    description: str
    success: bool = False
    message: str = ""
    details: Dict[str, Any] = None
    duration: float = 0.0
    severity: str = "error"  # error, warning, info
    fix_suggestion: str = ""
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class MCPVerifier(BaseScript):
    """MCP server setup verification manager."""
    
    def __init__(self):
        super().__init__(
            name="verify_mcp",
            description="Verify MCP server setup and configuration",
            version="2.0.0"
        )
        
        # Get configuration
        self.verify_config = self.config.get('scripts.verify_mcp', {})
        self.mcp_config = self.verify_config.get('mcp_servers', {})
        self.package_config = self.verify_config.get('packages', {})
        self.timeout_config = self.verify_config.get('timeouts', {})
        
        # Initialize utilities
        self.file_utils = FileUtils(logger=self.logger)
        self.process_utils = ProcessUtils(
            timeout=self.timeout_config.get('default', 30),
            logger=self.logger
        )
        
        # Verification tracking
        self.verification_results: List[VerificationResult] = []
        self.fix_issues = False
        
        # Define default configurations
        self.default_servers = self.mcp_config.get('servers', {
            'blender': {
                'command': 'uvx blender-mcp',
                'package': 'blender-mcp',
                'description': 'Blender 3D modeling integration',
                'required': True
            },
            'fetch': {
                'command': 'uvx mcp-server-fetch',
                'package': 'mcp-server-fetch', 
                'description': 'Web content fetching',
                'required': True
            }
        })
        
        self.required_packages = self.package_config.get('required', [
            'mcp', 'blender-mcp', 'mcp-server-fetch'
        ])
        
        self.config_paths = self.verify_config.get('config_paths', [
            '.claude/mcp_config.json',
            'mcp_config.json',
            '.config/claude/mcp_config.json'
        ])
    
    def setup_cli(self) -> CLIUtils:
        """Setup command line interface."""
        cli = CLIUtils(
            script_name=self.name,
            description=self.description,
            version=self.version
        )
        
        # Add arguments
        cli.add_argument(
            '--server',
            type=str,
            choices=list(self.default_servers.keys()) + ['all'],
            default='all',
            help='Specific server to verify (default: all)'
        )
        
        cli.add_argument(
            '--fix-issues',
            action='store_true',
            help='Attempt to automatically fix detected issues'
        )
        
        cli.add_argument(
            '--install-missing',
            action='store_true',
            help='Install missing packages automatically'
        )
        
        cli.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout for server checks in seconds (default: 30)'
        )
        
        cli.add_argument(
            '--export-report',
            type=str,
            help='Export verification report to file (JSON format)'
        )
        
        cli.add_argument(
            '--config-path',
            type=str,
            help='Custom path to MCP configuration file'
        )
        
        cli.add_argument(
            '--retry-count',
            type=int,
            default=3,
            help='Number of retries for failed checks (default: 3)'
        )
        
        cli.add_argument(
            '--skip-packages',
            action='store_true',
            help='Skip Python package verification'
        )
        
        cli.add_argument(
            '--skip-servers',
            action='store_true',
            help='Skip MCP server accessibility checks'
        )
        
        cli.add_common_arguments()
        
        return cli
    
    def add_result(self, result: VerificationResult) -> None:
        """Add a verification result to tracking."""
        self.verification_results.append(result)
        
        # Log the result
        if result.success:
            self.logger.info(f"✅ {result.description} ({result.duration:.2f}s)")
        else:
            level = 'error' if result.severity == 'error' else 'warning'
            getattr(self.logger, level)(f"❌ {result.description}: {result.message}")
            if result.fix_suggestion:
                self.logger.info(f"💡 Suggestion: {result.fix_suggestion}")
    
    def run_command_with_retry(self, command: str, retries: int = 3, timeout: int = 30) -> ProcessResult:
        """Run command with retry logic."""
        last_result = None
        
        for attempt in range(retries):
            try:
                result = self.process_utils.run_command(
                    command,
                    capture_output=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    return result
                
                last_result = result
                
                if attempt < retries - 1:
                    self.logger.debug(f"Command failed (attempt {attempt + 1}/{retries}), retrying...")
            
            except Exception as e:
                self.logger.debug(f"Command exception (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    # Create a failed result for the last attempt
                    last_result = ProcessResult(
                        returncode=1,
                        stdout="",
                        stderr=str(e),
                        duration=0.0
                    )
        
        return last_result
    
    def check_uv_installation(self) -> VerificationResult:
        """Check if UV package manager is installed and accessible."""
        result = VerificationResult(
            name="uv_installation",
            description="UV package manager installation",
            severity="error"
        )
        
        try:
            cmd_result = self.run_command_with_retry("uvx --version")
            
            if cmd_result.returncode == 0:
                version = cmd_result.stdout.strip()
                result.success = True
                result.message = f"UV installed: {version}"
                result.details = {'version': version}
                result.duration = cmd_result.duration
            else:
                result.message = f"UV not accessible: {cmd_result.stderr}"
                result.fix_suggestion = "Install UV package manager: pip install uv"
        
        except Exception as e:
            result.message = f"Error checking UV: {e}"
            result.fix_suggestion = "Install UV package manager: pip install uv"
        
        return result
    
    def check_python_packages(self, install_missing: bool = False) -> List[VerificationResult]:
        """Check if required Python packages are installed."""
        results = []
        
        for package in self.required_packages:
            result = VerificationResult(
                name=f"package_{package.replace('-', '_')}",
                description=f"Python package: {package}",
                severity="error" if package in ['mcp'] else "warning"
            )
            
            try:
                cmd_result = self.run_command_with_retry(f"pip show {package}")
                
                if cmd_result.returncode == 0:
                    # Extract version from pip show output
                    version = "unknown"
                    for line in cmd_result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split(':', 1)[1].strip()
                            break
                    
                    result.success = True
                    result.message = f"Installed: {version}"
                    result.details = {'version': version}
                    result.duration = cmd_result.duration
                else:
                    result.message = "Not installed"
                    result.fix_suggestion = f"Install package: pip install {package}"
                    
                    # Attempt to install if requested
                    if install_missing:
                        install_result = self.install_package(package)
                        if install_result.success:
                            result.success = True
                            result.message = f"Installed automatically: {install_result.message}"
            
            except Exception as e:
                result.message = f"Error checking package: {e}"
                result.fix_suggestion = f"Install package: pip install {package}"
            
            results.append(result)
        
        return results
    
    def install_package(self, package: str) -> VerificationResult:
        """Install a Python package."""
        result = VerificationResult(
            name=f"install_{package.replace('-', '_')}",
            description=f"Install {package}",
            severity="info"
        )
        
        try:
            self.logger.info(f"Installing {package}...")
            cmd_result = self.run_command_with_retry(f"pip install {package}")
            
            if cmd_result.returncode == 0:
                result.success = True
                result.message = "Installation successful"
                result.duration = cmd_result.duration
            else:
                result.message = f"Installation failed: {cmd_result.stderr}"
        
        except Exception as e:
            result.message = f"Error installing package: {e}"
        
        return result
    
    def find_config_file(self, custom_path: Optional[str] = None) -> Optional[Path]:
        """Find MCP configuration file."""
        search_paths = []
        
        if custom_path:
            search_paths.append(Path(custom_path))
        
        # Add configured paths
        for path_str in self.config_paths:
            search_paths.append(self.project_root / path_str)
            search_paths.append(Path.home() / path_str)
        
        for path in search_paths:
            if path.exists() and path.is_file():
                return path
        
        return None
    
    def check_config_file(self, custom_path: Optional[str] = None) -> VerificationResult:
        """Check if MCP configuration file exists and is valid."""
        result = VerificationResult(
            name="config_file",
            description="MCP configuration file",
            severity="warning"
        )
        
        try:
            config_path = self.find_config_file(custom_path)
            
            if not config_path:
                result.message = "Configuration file not found"
                result.fix_suggestion = "Create MCP configuration file (.claude/mcp_config.json)"
                result.details = {'searched_paths': [str(p) for p in [self.project_root / path for path in self.config_paths]]}
                return result
            
            # Try to parse the configuration
            try:
                content = self.file_utils.read_text_file(config_path)
                config = json.loads(content)
                
                servers = config.get('mcpServers', {})
                result.success = True
                result.message = f"Found configuration with {len(servers)} servers"
                result.details = {
                    'path': str(config_path),
                    'servers': list(servers.keys()),
                    'server_count': len(servers)
                }
            
            except json.JSONDecodeError as e:
                result.message = f"Invalid JSON in configuration file: {e}"
                result.fix_suggestion = "Fix JSON syntax in configuration file"
                result.details = {'path': str(config_path), 'json_error': str(e)}
        
        except Exception as e:
            result.message = f"Error checking configuration file: {e}"
        
        return result
    
    def check_mcp_server(self, server_name: str, server_config: Dict[str, Any], timeout: int = 30) -> VerificationResult:
        """Check if an MCP server is accessible."""
        result = VerificationResult(
            name=f"server_{server_name}",
            description=f"MCP server: {server_name}",
            severity="error" if server_config.get('required', True) else "warning"
        )
        
        try:
            command = server_config.get('command', f"uvx {server_config.get('package', server_name)}")
            
            # Try to get help/version info
            cmd_result = self.run_command_with_retry(f"{command} --help", timeout=timeout)
            
            if cmd_result.returncode == 0:
                result.success = True
                result.message = "Server accessible"
                result.details = {
                    'command': command,
                    'package': server_config.get('package'),
                    'description': server_config.get('description', '')
                }
                result.duration = cmd_result.duration
            else:
                result.message = f"Server not accessible: {cmd_result.stderr}"
                result.fix_suggestion = f"Install server: pip install {server_config.get('package', server_name)}"
                result.details = {
                    'command': command,
                    'error': cmd_result.stderr
                }
        
        except Exception as e:
            result.message = f"Error checking server: {e}"
            result.fix_suggestion = f"Install server: pip install {server_config.get('package', server_name)}"
        
        return result
    
    def export_report(self, file_path: str) -> VerificationResult:
        """Export verification report to file."""
        result = VerificationResult(
            name="export_report",
            description="Export verification report",
            severity="info"
        )
        
        try:
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'script_version': self.version,
                'summary': {
                    'total_checks': len(self.verification_results),
                    'passed': sum(1 for r in self.verification_results if r.success),
                    'failed': sum(1 for r in self.verification_results if not r.success),
                    'errors': sum(1 for r in self.verification_results if not r.success and r.severity == 'error'),
                    'warnings': sum(1 for r in self.verification_results if not r.success and r.severity == 'warning')
                },
                'results': [
                    {
                        'name': r.name,
                        'description': r.description,
                        'success': r.success,
                        'message': r.message,
                        'severity': r.severity,
                        'duration': r.duration,
                        'details': r.details,
                        'fix_suggestion': r.fix_suggestion
                    }
                    for r in self.verification_results
                ]
            }
            
            self.file_utils.write_json_file(Path(file_path), report_data)
            result.success = True
            result.message = f"Report exported to {file_path}"
        
        except Exception as e:
            result.message = f"Error exporting report: {e}"
        
        return result
    
    def display_verification_summary(self) -> None:
        """Display verification summary."""
        cli = CLIUtils(self.name, self.description, self.version)
        
        # Display header
        cli.print_header("MCP Verification", "Weather Dashboard MCP Server Setup")
        
        # Display results by category
        categories = {
            'Critical': [r for r in self.verification_results if r.severity == 'error'],
            'Warnings': [r for r in self.verification_results if r.severity == 'warning'],
            'Information': [r for r in self.verification_results if r.severity == 'info']
        }
        
        for category, results in categories.items():
            if not results:
                continue
                
            cli.print_section(category)
            
            for result in results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                duration_text = f"({result.duration:.2f}s)" if result.duration > 0 else ""
                print(f"{status} {result.description} {duration_text}")
                
                if result.message:
                    print(f"  {result.message}")
                
                if not result.success and result.fix_suggestion:
                    print(f"  💡 {result.fix_suggestion}")
        
        # Summary statistics
        total = len(self.verification_results)
        passed = sum(1 for r in self.verification_results if r.success)
        failed = sum(1 for r in self.verification_results if not r.success)
        errors = sum(1 for r in self.verification_results if not r.success and r.severity == 'error')
        warnings = sum(1 for r in self.verification_results if not r.success and r.severity == 'warning')
        
        cli.print_summary("Summary", {
            'Total Checks': total,
            'Passed': passed,
            'Failed': failed,
            'Errors': errors,
            'Warnings': warnings
        })
        
        # Next steps
        if errors == 0:
            cli.print_section("Next Steps")
            print("🎉 All critical checks passed! MCP servers are ready to use.")
            print("")
            print("📝 Recommended actions:")
            print("1. Install Blender addon (see docs/MCP_SETUP_GUIDE.md)")
            print("2. Configure Claude Desktop or Cursor IDE")
            print("3. Test MCP server functionality")
            print("4. Start using MCP servers in your workflow!")
        else:
            cli.print_section("Required Actions")
            print(f"⚠️ {errors} critical issues found. Please address them:")
            print("")
            
            for result in self.verification_results:
                if not result.success and result.severity == 'error' and result.fix_suggestion:
                    print(f"• {result.fix_suggestion}")
            
            print("")
            print("📖 See docs/MCP_SETUP_GUIDE.md for detailed troubleshooting.")
    
    def run(self) -> int:
        """Main execution method."""
        try:
            # Setup CLI and parse arguments
            cli = self.setup_cli()
            args = cli.parse_args()
            
            # Configure logging
            self.configure_logging(args)
            
            # Set options
            self.fix_issues = args.fix_issues
            
            self.logger.info("Starting MCP server verification")
            
            # Step 1: Check UV installation
            result = self.check_uv_installation()
            self.add_result(result)
            
            # Step 2: Check Python packages
            if not args.skip_packages:
                results = self.check_python_packages(args.install_missing)
                for result in results:
                    self.add_result(result)
            
            # Step 3: Check configuration file
            result = self.check_config_file(args.config_path)
            self.add_result(result)
            
            # Step 4: Check MCP servers
            if not args.skip_servers:
                servers_to_check = self.default_servers
                if args.server != 'all':
                    servers_to_check = {args.server: self.default_servers[args.server]}
                
                for server_name, server_config in servers_to_check.items():
                    result = self.check_mcp_server(server_name, server_config, args.timeout)
                    self.add_result(result)
            
            # Export report if requested
            if args.export_report:
                result = self.export_report(args.export_report)
                self.add_result(result)
            
            # Display summary
            if not args.quiet:
                self.display_verification_summary()
            
            # Determine exit code
            errors = sum(1 for r in self.verification_results if not r.success and r.severity == 'error')
            
            if errors == 0:
                cli.print_status("MCP verification completed successfully!", "success")
                return 0
            else:
                cli.print_status(f"{errors} critical issues found", "error")
                return 1
        
        except KeyboardInterrupt:
            self.logger.info("Verification cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error during verification: {e}")
            return 1


def main():
    """Main entry point."""
    verifier = MCPVerifier()
    return verifier.run()


if __name__ == "__main__":
    exit(main())