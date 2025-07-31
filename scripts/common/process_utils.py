#!/usr/bin/env python3
"""
Process Utilities for Weather Dashboard Scripts

Provides consistent subprocess execution:
- Command execution with timeout and error handling
- Output capture and streaming
- Environment variable management
- Process monitoring and control
- Cross-platform compatibility
"""

import subprocess
import sys
import os
import signal
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager
import shlex


@dataclass
class ProcessResult:
    """Result of process execution."""
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    command: str
    success: bool = None
    
    def __post_init__(self):
        if self.success is None:
            self.success = self.returncode == 0


class ProcessTimeout(Exception):
    """Exception raised when process times out."""
    pass


class ProcessUtils:
    """Utilities for process execution and management."""
    
    def __init__(self, default_timeout: int = 300, default_cwd: Union[str, Path] = None):
        self.default_timeout = default_timeout
        self.default_cwd = Path(default_cwd) if default_cwd else None
        self.processes = {}  # Track running processes
    
    def run_command(
        self,
        command: Union[str, List[str]],
        cwd: Union[str, Path] = None,
        timeout: int = None,
        capture_output: bool = True,
        check: bool = False,
        env: Dict[str, str] = None,
        input_data: str = None,
        shell: bool = None
    ) -> ProcessResult:
        """Run command and return result."""
        
        # Prepare command
        if isinstance(command, str):
            if shell is None:
                shell = True
            cmd_str = command
            cmd_list = shlex.split(command) if not shell else command
        else:
            if shell is None:
                shell = False
            cmd_str = ' '.join(command)
            cmd_list = command
        
        # Set working directory
        work_dir = Path(cwd) if cwd else self.default_cwd
        
        # Set timeout
        exec_timeout = timeout if timeout is not None else self.default_timeout
        
        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # Configure output capture
        stdout = subprocess.PIPE if capture_output else None
        stderr = subprocess.PIPE if capture_output else None
        
        start_time = time.time()
        
        try:
            # Start process
            process = subprocess.Popen(
                cmd_list if not shell else cmd_str,
                stdout=stdout,
                stderr=stderr,
                stdin=subprocess.PIPE if input_data else None,
                cwd=work_dir,
                env=process_env,
                shell=shell,
                text=True,
                universal_newlines=True
            )
            
            # Store process for potential cleanup
            self.processes[process.pid] = process
            
            try:
                # Wait for completion with timeout
                stdout_data, stderr_data = process.communicate(
                    input=input_data,
                    timeout=exec_timeout
                )
            except subprocess.TimeoutExpired:
                # Kill process on timeout
                self._kill_process(process)
                raise ProcessTimeout(f"Command timed out after {exec_timeout} seconds: {cmd_str}")
            
            finally:
                # Remove from tracking
                self.processes.pop(process.pid, None)
            
            execution_time = time.time() - start_time
            
            # Create result
            result = ProcessResult(
                returncode=process.returncode,
                stdout=stdout_data or '',
                stderr=stderr_data or '',
                execution_time=execution_time,
                command=cmd_str
            )
            
            # Check for errors if requested
            if check and not result.success:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    cmd_str,
                    output=result.stdout,
                    stderr=result.stderr
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Return error result
            return ProcessResult(
                returncode=-1,
                stdout='',
                stderr=str(e),
                execution_time=execution_time,
                command=cmd_str,
                success=False
            )
    
    def run_command_streaming(
        self,
        command: Union[str, List[str]],
        output_callback: Callable[[str], None] = None,
        error_callback: Callable[[str], None] = None,
        cwd: Union[str, Path] = None,
        timeout: int = None,
        env: Dict[str, str] = None,
        shell: bool = None
    ) -> ProcessResult:
        """Run command with real-time output streaming."""
        
        # Prepare command
        if isinstance(command, str):
            if shell is None:
                shell = True
            cmd_str = command
            cmd_list = shlex.split(command) if not shell else command
        else:
            if shell is None:
                shell = False
            cmd_str = ' '.join(command)
            cmd_list = command
        
        # Set working directory
        work_dir = Path(cwd) if cwd else self.default_cwd
        
        # Set timeout
        exec_timeout = timeout if timeout is not None else self.default_timeout
        
        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        start_time = time.time()
        stdout_lines = []
        stderr_lines = []
        
        try:
            # Start process
            process = subprocess.Popen(
                cmd_list if not shell else cmd_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=work_dir,
                env=process_env,
                shell=shell,
                text=True,
                universal_newlines=True,
                bufsize=1
            )
            
            # Store process for potential cleanup
            self.processes[process.pid] = process
            
            # Create threads for output streaming
            def read_stdout():
                for line in iter(process.stdout.readline, ''):
                    line = line.rstrip('\n\r')
                    stdout_lines.append(line)
                    if output_callback:
                        output_callback(line)
                process.stdout.close()
            
            def read_stderr():
                for line in iter(process.stderr.readline, ''):
                    line = line.rstrip('\n\r')
                    stderr_lines.append(line)
                    if error_callback:
                        error_callback(line)
                process.stderr.close()
            
            # Start output threads
            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for process completion with timeout
            try:
                process.wait(timeout=exec_timeout)
            except subprocess.TimeoutExpired:
                self._kill_process(process)
                raise ProcessTimeout(f"Command timed out after {exec_timeout} seconds: {cmd_str}")
            
            # Wait for output threads to complete
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            
            # Remove from tracking
            self.processes.pop(process.pid, None)
            
            execution_time = time.time() - start_time
            
            return ProcessResult(
                returncode=process.returncode,
                stdout='\n'.join(stdout_lines),
                stderr='\n'.join(stderr_lines),
                execution_time=execution_time,
                command=cmd_str
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ProcessResult(
                returncode=-1,
                stdout='\n'.join(stdout_lines),
                stderr=str(e),
                execution_time=execution_time,
                command=cmd_str,
                success=False
            )
    
    def check_command_available(self, command: str) -> bool:
        """Check if command is available in PATH."""
        try:
            result = self.run_command(
                f"where {command}" if sys.platform == "win32" else f"which {command}",
                timeout=10,
                capture_output=True
            )
            return result.success
        except Exception:
            return False
    
    def get_command_version(self, command: str, version_arg: str = "--version") -> Optional[str]:
        """Get version of command."""
        try:
            result = self.run_command(
                f"{command} {version_arg}",
                timeout=10,
                capture_output=True
            )
            if result.success:
                # Return first line of output
                return result.stdout.split('\n')[0].strip()
            return None
        except Exception:
            return None
    
    def run_python_script(
        self,
        script_path: Union[str, Path],
        args: List[str] = None,
        python_executable: str = None,
        **kwargs
    ) -> ProcessResult:
        """Run Python script with specified interpreter."""
        
        # Use current Python executable by default
        python_exe = python_executable or sys.executable
        
        # Build command
        command = [python_exe, str(script_path)]
        if args:
            command.extend(args)
        
        return self.run_command(command, shell=False, **kwargs)
    
    def run_pip_command(
        self,
        pip_args: List[str],
        python_executable: str = None,
        **kwargs
    ) -> ProcessResult:
        """Run pip command."""
        
        # Use current Python executable by default
        python_exe = python_executable or sys.executable
        
        # Build command
        command = [python_exe, "-m", "pip"] + pip_args
        
        return self.run_command(command, shell=False, **kwargs)
    
    def install_package(
        self,
        package: str,
        upgrade: bool = False,
        user: bool = False,
        **kwargs
    ) -> ProcessResult:
        """Install Python package using pip."""
        
        args = ["install"]
        
        if upgrade:
            args.append("--upgrade")
        
        if user:
            args.append("--user")
        
        args.append(package)
        
        return self.run_pip_command(args, **kwargs)
    
    def check_package_installed(self, package: str) -> bool:
        """Check if Python package is installed."""
        try:
            result = self.run_pip_command(["show", package], timeout=30)
            return result.success
        except Exception:
            return False
    
    def get_package_version(self, package: str) -> Optional[str]:
        """Get version of installed Python package."""
        try:
            result = self.run_pip_command(["show", package], timeout=30)
            if result.success:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':', 1)[1].strip()
            return None
        except Exception:
            return None
    
    def _kill_process(self, process: subprocess.Popen) -> None:
        """Kill process and its children."""
        try:
            if sys.platform == "win32":
                # On Windows, use taskkill to kill process tree
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    timeout=10
                )
            else:
                # On Unix-like systems, send SIGTERM then SIGKILL
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        except Exception:
            # If all else fails, try direct kill
            try:
                process.kill()
            except Exception:
                pass
    
    def kill_all_processes(self) -> None:
        """Kill all tracked processes."""
        for process in list(self.processes.values()):
            self._kill_process(process)
        self.processes.clear()
    
    @contextmanager
    def environment_variables(self, env_vars: Dict[str, str]):
        """Context manager for temporary environment variables."""
        old_env = {}
        
        # Save old values and set new ones
        for key, value in env_vars.items():
            old_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            yield
        finally:
            # Restore old values
            for key, old_value in old_env.items():
                if old_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = old_value
    
    @contextmanager
    def working_directory(self, directory: Union[str, Path]):
        """Context manager for temporary working directory."""
        old_cwd = os.getcwd()
        try:
            os.chdir(directory)
            yield
        finally:
            os.chdir(old_cwd)
    
    def run_commands_parallel(
        self,
        commands: List[Union[str, List[str]]],
        max_workers: int = None,
        **kwargs
    ) -> List[ProcessResult]:
        """Run multiple commands in parallel."""
        import concurrent.futures
        
        if max_workers is None:
            max_workers = min(len(commands), os.cpu_count() or 1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all commands
            futures = []
            for command in commands:
                future = executor.submit(self.run_command, command, **kwargs)
                futures.append(future)
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Create error result
                    results.append(ProcessResult(
                        returncode=-1,
                        stdout='',
                        stderr=str(e),
                        execution_time=0,
                        command='unknown',
                        success=False
                    ))
        
        return results
    
    def monitor_process(
        self,
        process: subprocess.Popen,
        callback: Callable[[Dict[str, Any]], None] = None,
        interval: float = 1.0
    ) -> None:
        """Monitor process and call callback with status updates."""
        import psutil
        
        try:
            ps_process = psutil.Process(process.pid)
            
            while process.poll() is None:
                try:
                    # Get process info
                    info = {
                        'pid': process.pid,
                        'status': ps_process.status(),
                        'cpu_percent': ps_process.cpu_percent(),
                        'memory_info': ps_process.memory_info(),
                        'create_time': ps_process.create_time(),
                        'running_time': time.time() - ps_process.create_time()
                    }
                    
                    if callback:
                        callback(info)
                    
                    time.sleep(interval)
                
                except psutil.NoSuchProcess:
                    break
                except Exception:
                    # Continue monitoring even if we can't get some info
                    time.sleep(interval)
        
        except ImportError:
            # psutil not available, basic monitoring
            while process.poll() is None:
                if callback:
                    callback({
                        'pid': process.pid,
                        'status': 'running',
                        'running_time': time.time()
                    })
                time.sleep(interval)
    
    def __del__(self):
        """Cleanup on destruction."""
        self.kill_all_processes()