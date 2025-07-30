#!/usr/bin/env python3
"""
Pre-commit code quality check script.
Ensures all code passes black, isort, flake8, and mypy before committing.
"""

import subprocess
import sys
from pathlib import Path


def run_check(command: str, description: str) -> bool:
    """Run a code quality check command."""
    print(f"🔍 {description}...")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode == 0:
            print(f"  ✅ {description} passed")
            return True
        else:
            print(f"  ❌ {description} failed")
            if result.stdout:
                print(f"     STDOUT: {result.stdout}")
            if result.stderr:
                print(f"     STDERR: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error running {description}: {e}")
        return False


def main():
    """Run all pre-commit checks."""
    print("🚀 Pre-commit Code Quality Checks")
    print("=" * 40)

    # Define all checks
    checks = [
        (
            "python -m black --check --diff src/ tests/ scripts/ main.py",
            "Black formatting check",
        ),
        (
            "python -m isort --check-only --diff src/ tests/ scripts/ main.py",
            "isort import organization check",
        ),
        (
            "python -m flake8 src/ tests/ scripts/ main.py --config=setup.cfg",
            "flake8 style check",
        ),
        ("python -m mypy src/ --config-file=setup.cfg", "mypy type checking"),
    ]

    # Run all checks
    results = []
    for command, description in checks:
        success = run_check(command, description)
        results.append((description, success))

    # Summary
    print("\n" + "=" * 40)
    print("📊 Summary")
    print("=" * 40)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")

    print(f"\nResult: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! Code is ready to commit.")
        return True
    else:
        print("\n⚠️  Some checks failed. Please fix issues before committing.")
        print("\n💡 To auto-fix formatting issues, run:")
        print("   python -m black src/ tests/ scripts/ main.py")
        print("   python -m isort src/ tests/ scripts/ main.py")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
