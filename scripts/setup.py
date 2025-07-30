#!/usr/bin/env python3
"""
Development Environment Setup Script for Weather Dashboard

This script sets up the development environment for new contributors.
"""

import os
import subprocess
import sys
from pathlib import Path


def setup_environment():
    """Set up the development environment."""
    project_root = Path(__file__).parent.parent

    print("🚀 Setting up Weather Dashboard development environment...")

    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False

    print(
        f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    # Create virtual environment if it doesn't exist
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
    else:
        print("✅ Virtual environment already exists")

    # Determine activation script based on OS
    if os.name == "nt":  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:  # Unix-like
        activate_script = venv_path / "bin" / "activate"
        pip_executable = venv_path / "bin" / "pip"

    # Install requirements
    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        print("📚 Installing requirements...")
        subprocess.run([str(pip_executable), "install", "-r", str(requirements_file)])

    # Install development requirements if they exist
    dev_requirements = project_root / "docs" / "development" / "requirements-dev.txt"
    if dev_requirements.exists():
        print("🛠️  Installing development requirements...")
        subprocess.run([str(pip_executable), "install", "-r", str(dev_requirements)])

    # Create .env file from example if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists() and env_example.exists():
        print("⚙️  Creating .env file from example...")
        with open(env_example, "r") as src, open(env_file, "w") as dst:
            dst.write(src.read())
        print("🔑 Please edit .env file with your API keys")

    # Run tests to verify setup
    print("🧪 Running tests to verify setup...")
    test_result = subprocess.run(
        [str(pip_executable), "install", "pytest"], capture_output=True
    )

    if test_result.returncode == 0:
        subprocess.run(
            [
                str(venv_path / ("Scripts" if os.name == "nt" else "bin") / "python"),
                "-m",
                "pytest",
                "tests/",
                "-v",
            ]
        )

    print("\n✅ Setup completed!")
    print("\n📋 Next steps: ")
    print("1. Activate virtual environment: ")
    if os.name == "nt":
        print(f"   {activate_script}")
    else:
        print(f"   source {activate_script}")
    print("2. Edit .env file with your API keys")
    print("3. Run the application: python main.py")


if __name__ == "__main__":
    setup_environment()
