#!/usr/bin/env python3
"""One-click cleanup script for the weather dashboard project."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def clean_cache_files():
    """Remove Python cache files and directories."""
    print("\n🧹 Cleaning cache files...")
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            cache_path = Path(root) / "__pycache__"
            shutil.rmtree(cache_path, ignore_errors=True)
            print(f"  Removed: {cache_path}")
    
    # Remove .pyc files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc"):
                pyc_path = Path(root) / file
                pyc_path.unlink(missing_ok=True)
                print(f"  Removed: {pyc_path}")
    
    print("✅ Cache cleanup completed")
    return True


def clean_temp_files():
    """Remove temporary files and logs."""
    print("\n🗑️ Cleaning temporary files...")
    
    temp_patterns = [
        "*.tmp",
        "*.temp",
        "*.log",
        "*.bak",
        "*~",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    for pattern in temp_patterns:
        for file_path in Path(".").rglob(pattern):
            if file_path.is_file():
                file_path.unlink(missing_ok=True)
                print(f"  Removed: {file_path}")
    
    print("✅ Temporary file cleanup completed")
    return True


def format_code():
    """Format code using black and isort."""
    success = True
    
    # Sort imports
    success &= run_command(
        "isort src/ tests/ --profile black",
        "Sorting imports with isort"
    )
    
    # Format code (only format existing directories)
    dirs_to_format = []
    if Path("src").exists():
        dirs_to_format.append("src/")
    if Path("tests").exists():
        dirs_to_format.append("tests/")
    
    if dirs_to_format:
        success &= run_command(
            f"black {' '.join(dirs_to_format)} --line-length 100",
            "Formatting code with black"
        )
    else:
        print("⚠️ No directories found to format with black")
        success = False
    
    return success


def remove_unused_imports():
    """Remove unused imports using autoflake."""
    return run_command(
        "autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables src/",
        "Removing unused imports with autoflake"
    )


def run_linting():
    """Run code quality checks."""
    success = True
    
    # Check with flake8
    success &= run_command(
        "flake8 src/ --max-line-length=100 --extend-ignore=E203,W503",
        "Running flake8 linting"
    )
    
    return success


def main():
    """Main cleanup function."""
    print("🚀 Starting Weather Dashboard Cleanup")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Run cleanup steps
    steps = [
        (clean_cache_files, "Cache file cleanup"),
        (clean_temp_files, "Temporary file cleanup"),
        (format_code, "Code formatting"),
        (remove_unused_imports, "Unused import removal"),
        (run_linting, "Code quality checks")
    ]
    
    failed_steps = []
    
    for step_func, step_name in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    # Summary
    print("\n" + "=" * 50)
    if failed_steps:
        print(f"⚠️ Cleanup completed with {len(failed_steps)} failed steps:")
        for step in failed_steps:
            print(f"  - {step}")
        sys.exit(1)
    else:
        print("✅ All cleanup steps completed successfully!")
        print("🎉 Your codebase is now clean and formatted.")


if __name__ == "__main__":
    main()