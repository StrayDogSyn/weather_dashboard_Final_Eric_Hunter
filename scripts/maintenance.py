#!/usr/bin/env python3
"""Project Maintenance Script

Automated cleanup and organization tools for the weather dashboard project.
Provides functions for cache cleanup, import optimization, dead code detection,
and project structure validation.
"""

import os
import sys
import shutil
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime
import json
import logging
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ProjectMaintenance:
    """Main maintenance class for project cleanup and organization."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.archive_dir = self.project_root / 'archive'
        self.cleanup_log = []
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for maintenance operations."""
        log_dir = self.project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'maintenance.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def should_skip_directory(self, dir_path: str) -> bool:
        """Check if directory should be skipped during cleanup."""
        skip_dirs = {
            '__pycache__', '.pytest_cache', '.git', 'node_modules',
            '.idea', '.vscode', 'dist', 'build', '.venv', 'venv'
        }
        return any(skip_dir in str(dir_path) for skip_dir in skip_dirs)
        
    def clean_cache_files(self) -> List[str]:
        """Remove all Python cache files and directories."""
        removed_files = []
        cache_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '.pytest_cache',
            '.coverage',
            'htmlcov'
        ]
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip virtual environment and other excluded directories
            if self.should_skip_directory(root):
                continue
                
            # Remove __pycache__ directories
            if '__pycache__' in dirs:
                cache_dir = Path(root) / '__pycache__'
                try:
                    shutil.rmtree(cache_dir)
                    removed_files.append(str(cache_dir))
                    self.logger.info(f"Removed cache directory: {cache_dir}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {cache_dir}: {e}")
                    
            # Remove .pytest_cache directories
            if '.pytest_cache' in dirs:
                pytest_dir = Path(root) / '.pytest_cache'
                try:
                    shutil.rmtree(pytest_dir)
                    removed_files.append(str(pytest_dir))
                    self.logger.info(f"Removed pytest cache: {pytest_dir}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {pytest_dir}: {e}")
                    
            # Remove individual cache files
            for file in files:
                if file.endswith(('.pyc', '.pyo')) or file == '.coverage':
                    file_path = Path(root) / file
                    try:
                        file_path.unlink()
                        removed_files.append(str(file_path))
                        self.logger.info(f"Removed cache file: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove {file_path}: {e}")
                        
        return removed_files
        
    def find_unused_imports(self) -> Dict[str, List[str]]:
        """Find unused imports in Python files."""
        unused_imports = {}
        
        for py_file in self.project_root.rglob('*.py'):
            if self.should_skip_directory(str(py_file)):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                imports = self._extract_imports(tree)
                used_names = self._extract_used_names(tree)
                
                unused = []
                for imp in imports:
                    if imp not in used_names:
                        unused.append(imp)
                        
                if unused:
                    unused_imports[str(py_file)] = unused
                    
            except Exception as e:
                self.logger.warning(f"Could not analyze {py_file}: {e}")
                
        return unused_imports
        
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract all imported names from AST."""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.add(name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.add(name)
                    
        return imports
        
    def _extract_used_names(self, tree: ast.AST) -> Set[str]:
        """Extract all used names from AST."""
        used = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used.add(node.value.id)
                    
        return used
        
    def find_duplicate_files(self) -> Dict[str, List[str]]:
        """Find potential duplicate files based on content similarity."""
        file_hashes = defaultdict(list)
        
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'rb') as f:
                    content = f.read()
                    file_hash = hash(content)
                    file_hashes[file_hash].append(str(py_file))
            except Exception as e:
                self.logger.warning(f"Could not read {py_file}: {e}")
                
        # Return only files with duplicates
        duplicates = {h: files for h, files in file_hashes.items() if len(files) > 1}
        return duplicates
        
    def find_empty_files(self) -> List[str]:
        """Find empty or near-empty Python files."""
        empty_files = []
        
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                # Check if file is empty or only contains comments/docstrings
                if not content or self._is_stub_file(content):
                    empty_files.append(str(py_file))
                    
            except Exception as e:
                self.logger.warning(f"Could not read {py_file}: {e}")
                
        return empty_files
        
    def _is_stub_file(self, content: str) -> bool:
        """Check if file is a stub (only comments, docstrings, imports)."""
        try:
            tree = ast.parse(content)
            
            # Count meaningful statements (excluding imports, docstrings)
            meaningful_statements = 0
            for node in tree.body:
                if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr)):
                    meaningful_statements += 1
                elif isinstance(node, ast.Expr) and not isinstance(node.value, ast.Constant):
                    meaningful_statements += 1
                    
            return meaningful_statements == 0
            
        except:
            return False
            
    def validate_imports(self) -> Dict[str, List[str]]:
        """Validate all imports and find broken ones."""
        broken_imports = {}
        
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                broken = self._check_imports(content, py_file)
                if broken:
                    broken_imports[str(py_file)] = broken
                    
            except Exception as e:
                self.logger.warning(f"Could not validate imports in {py_file}: {e}")
                
        return broken_imports
        
    def _check_imports(self, content: str, file_path: Path) -> List[str]:
        """Check if imports in a file are valid."""
        broken = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Check relative imports
                        if node.level > 0:
                            module_path = self._resolve_relative_import(node.module, file_path, node.level)
                        else:
                            module_path = self._resolve_absolute_import(node.module)
                            
                        if module_path and not module_path.exists():
                            broken.append(f"from {node.module} import ...")
                            
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_path = self._resolve_absolute_import(alias.name)
                        if module_path and not module_path.exists():
                            broken.append(f"import {alias.name}")
                            
        except Exception as e:
            self.logger.warning(f"Error parsing imports: {e}")
            
        return broken
        
    def _resolve_relative_import(self, module: str, file_path: Path, level: int) -> Optional[Path]:
        """Resolve relative import to file path."""
        try:
            current_dir = file_path.parent
            for _ in range(level - 1):
                current_dir = current_dir.parent
                
            if module:
                module_path = current_dir / module.replace('.', os.sep)
            else:
                module_path = current_dir
                
            # Check for __init__.py or .py file
            if (module_path / '__init__.py').exists():
                return module_path / '__init__.py'
            elif (module_path.parent / f"{module_path.name}.py").exists():
                return module_path.parent / f"{module_path.name}.py"
                
        except Exception:
            pass
            
        return None
        
    def _resolve_absolute_import(self, module: str) -> Optional[Path]:
        """Resolve absolute import to file path."""
        # Only check local modules (in src/)
        if not module.startswith(('src', 'services', 'ui', 'models', 'utils')):
            return None
            
        try:
            module_path = self.project_root / 'src' / module.replace('.', os.sep)
            
            # Check for __init__.py or .py file
            if (module_path / '__init__.py').exists():
                return module_path / '__init__.py'
            elif (module_path.parent / f"{module_path.name}.py").exists():
                return module_path.parent / f"{module_path.name}.py"
                
        except Exception:
            pass
            
        return None
        
    def organize_test_files(self) -> List[str]:
        """Organize test files into proper structure."""
        moved_files = []
        tests_dir = self.project_root / 'tests'
        tests_dir.mkdir(exist_ok=True)
        
        # Create test subdirectories
        (tests_dir / 'unit').mkdir(exist_ok=True)
        (tests_dir / 'integration').mkdir(exist_ok=True)
        (tests_dir / 'fixtures').mkdir(exist_ok=True)
        
        # Find test files outside tests directory
        for test_file in self.project_root.rglob('test_*.py'):
            if 'tests' not in str(test_file) and not self.should_skip_directory(str(test_file)):
                new_path = tests_dir / 'unit' / test_file.name
                try:
                    shutil.move(str(test_file), str(new_path))
                    moved_files.append(f"{test_file} -> {new_path}")
                    self.logger.info(f"Moved test file: {test_file} -> {new_path}")
                except Exception as e:
                    self.logger.error(f"Failed to move {test_file}: {e}")
                    
        return moved_files
        
    def validate_project_structure(self) -> Dict[str, List[str]]:
        """Validate project structure against expected patterns."""
        issues = defaultdict(list)
        
        # Expected directories
        expected_dirs = [
            'src', 'tests', 'docs', 'scripts',
            'src/config', 'src/services', 'src/ui', 'src/models',
            'src/utils', 'src/controllers', 'src/processors',
            'src/parsers', 'src/mappers', 'src/interfaces'
        ]
        
        for dir_path in expected_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                issues['missing_directories'].append(dir_path)
                
        # Check for files in wrong locations
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            rel_path = py_file.relative_to(self.project_root)
            
            # Test files should be in tests/
            if py_file.name.startswith('test_') and 'tests' not in str(rel_path):
                issues['misplaced_test_files'].append(str(rel_path))
                
            # Service files should be in src/services/
            if 'service' in py_file.name.lower() and 'src/services' not in str(rel_path):
                issues['misplaced_service_files'].append(str(rel_path))
                
        return dict(issues)
        
    def fix_broken_imports(self) -> Dict[str, int]:
        """Fix common broken import patterns."""
        fixes_applied = defaultdict(int)
        
        # Common import fixes
        import_fixes = {
            '# from enhanced_weather_display import': '# # from enhanced_weather_display import',
            '# from enhanced_weather_dashboard_analytics import': '# # from enhanced_weather_dashboard_analytics import',
            '# import enhanced_weather_display': '# # import enhanced_weather_display',
            '# import enhanced_weather_dashboard_analytics': '# # import enhanced_weather_dashboard_analytics'
        }
        
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                original_content = content
                
                for broken_import, fix in import_fixes.items():
                    if broken_import in content:
                        content = content.replace(broken_import, fix)
                        fixes_applied[broken_import] += 1
                        
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"Fixed imports in: {py_file}")
                    
            except Exception as e:
                self.logger.error(f"Failed to fix imports in {py_file}: {e}")
                
        return dict(fixes_applied)
        
    def generate_cleanup_report(self) -> str:
        """Generate comprehensive cleanup report."""
        report = []
        report.append("# Project Cleanup Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("\n" + "="*50 + "\n")
        
        # Cache cleanup
        report.append("## Cache Files Cleanup")
        removed_cache = self.clean_cache_files()
        if removed_cache:
            report.append(f"Removed {len(removed_cache)} cache files/directories:")
            for item in removed_cache[:10]:  # Show first 10
                report.append(f"  - {item}")
            if len(removed_cache) > 10:
                report.append(f"  ... and {len(removed_cache) - 10} more")
        else:
            report.append("No cache files found to remove.")
        report.append("")
        
        # Broken imports
        report.append("## Broken Imports Fixed")
        import_fixes = self.fix_broken_imports()
        if import_fixes:
            for broken_import, count in import_fixes.items():
                report.append(f"  - Fixed '{broken_import}': {count} occurrences")
        else:
            report.append("No broken imports found.")
        report.append("")
        
        # Unused imports
        report.append("## Unused Imports Analysis")
        unused_imports = self.find_unused_imports()
        if unused_imports:
            report.append(f"Found unused imports in {len(unused_imports)} files:")
            for file_path, imports in list(unused_imports.items())[:5]:
                report.append(f"  - {file_path}: {', '.join(imports[:3])}")
                if len(imports) > 3:
                    report.append(f"    ... and {len(imports) - 3} more")
        else:
            report.append("No unused imports detected.")
        report.append("")
        
        # Empty files
        report.append("## Empty/Stub Files")
        empty_files = self.find_empty_files()
        if empty_files:
            report.append(f"Found {len(empty_files)} empty/stub files:")
            for file_path in empty_files:
                report.append(f"  - {file_path}")
        else:
            report.append("No empty files found.")
        report.append("")
        
        # Project structure validation
        report.append("## Project Structure Validation")
        structure_issues = self.validate_project_structure()
        if structure_issues:
            for issue_type, items in structure_issues.items():
                report.append(f"  {issue_type.replace('_', ' ').title()}:")
                for item in items:
                    report.append(f"    - {item}")
        else:
            report.append("Project structure is valid.")
        report.append("")
        
        # Test file organization
        report.append("## Test File Organization")
        moved_tests = self.organize_test_files()
        if moved_tests:
            report.append(f"Moved {len(moved_tests)} test files:")
            for move in moved_tests:
                report.append(f"  - {move}")
        else:
            report.append("All test files are properly organized.")
        
        return "\n".join(report)
        
    def run_full_cleanup(self) -> str:
        """Run complete cleanup and organization process."""
        self.logger.info("Starting full project cleanup...")
        
        # Ensure archive directory exists
        self.archive_dir.mkdir(exist_ok=True)
        
        # Generate and save cleanup report
        report = self.generate_cleanup_report()
        
        report_file = self.project_root / 'cleanup_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        self.logger.info(f"Cleanup completed. Report saved to: {report_file}")
        return report


def main():
    """Main entry point for maintenance script."""
    maintenance = ProjectMaintenance()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'clean-cache':
            removed = maintenance.clean_cache_files()
            print(f"Removed {len(removed)} cache files/directories")
            
        elif command == 'check-imports':
            unused = maintenance.find_unused_imports()
            broken = maintenance.validate_imports()
            print(f"Unused imports in {len(unused)} files")
            print(f"Broken imports in {len(broken)} files")
            
        elif command == 'organize-tests':
            moved = maintenance.organize_test_files()
            print(f"Moved {len(moved)} test files")
            
        elif command == 'validate-structure':
            issues = maintenance.validate_project_structure()
            if issues:
                print("Structure issues found:")
                for issue_type, items in issues.items():
                    print(f"  {issue_type}: {len(items)} items")
            else:
                print("Project structure is valid")
                
        elif command == 'full-cleanup':
            report = maintenance.run_full_cleanup()
            print("Full cleanup completed. Check cleanup_report.txt for details.")
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: clean-cache, check-imports, organize-tests, validate-structure, full-cleanup")
    else:
        # Run full cleanup by default
        report = maintenance.run_full_cleanup()
        print("Full cleanup completed. Check cleanup_report.txt for details.")


if __name__ == '__main__':
    main()