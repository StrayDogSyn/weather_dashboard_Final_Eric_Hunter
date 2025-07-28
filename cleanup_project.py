#!/usr/bin/env python3
"""
Project File Structure Cleanup Tool

Automatically cleans up legacy files, organizes backups, and maintains
clean project directory structure. Designed for repeated use during
development maintenance cycles.
"""

import os
import shutil
import ast
import re
from pathlib import Path
from typing import Set, List, Dict, Tuple
from datetime import datetime, timedelta
import json

class ProjectCleaner:
    def __init__(self, project_root: str, dry_run: bool = True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.active_imports = set()
        self.legacy_patterns = [
            r'.*_legacy\.py$', r'.*_backup\.py$', r'.*_old\.py$',
            r'.*\.py\.bak$', r'.*~$', r'.*\.orig$', r'.*\.tmp$'
        ]
        self.archive_dir = self.project_root / 'archive'
        
    def scan_active_imports(self) -> Set[str]:
        """Scan all Python files for import statements to identify active files."""
        print("🔍 Scanning for active imports...")
        
        for py_file in self.project_root.rglob('*.py'):
            if 'archive' in str(py_file) or 'legacy' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse AST to find imports
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.active_imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.active_imports.add(node.module)
                            
                # Also check string-based imports
                import_matches = re.findall(r'from\s+([^\s]+)\s+import|import\s+([^\s,]+)', content)
                for match in import_matches:
                    for group in match:
                        if group:
                            self.active_imports.add(group.strip())
                            
            except Exception as e:
                print(f"⚠️ Error scanning {py_file}: {e}")
                
        print(f"✅ Found {len(self.active_imports)} active imports")
        return self.active_imports
    
    def identify_legacy_files(self) -> List[Path]:
        """Identify legacy, backup, and unused files."""
        print("🔍 Identifying legacy files...")
        
        legacy_files = []
        
        # Pattern-based legacy files (only these should be archived)
        for pattern in self.legacy_patterns:
            for file_path in self.project_root.rglob('*'):
                if re.match(pattern, str(file_path.name)):
                    legacy_files.append(file_path)
        
        # Additional files to keep (never archive)
        protected_files = [
            'main.py', '__init__.py', 'setup.py', 'config.py',
            'cleanup_project.py', 'requirements.txt', 'README.md',
            'LICENSE', '.gitignore', '.env.example'
        ]
        
        protected_patterns = [
            r'.*test.*\.py$',  # Keep test files
            r'.*config.*\.py$',  # Keep config files
            r'.*settings.*\.py$',  # Keep settings files
        ]
        
        # Filter out protected files
        filtered_legacy = []
        for file_path in legacy_files:
            file_name = file_path.name
            
            # Skip protected files
            if file_name in protected_files:
                continue
                
            # Skip files matching protected patterns
            is_protected = any(re.match(pattern, file_name) for pattern in protected_patterns)
            if is_protected:
                continue
                
            filtered_legacy.append(file_path)
        
        print(f"📋 Identified {len(filtered_legacy)} legacy files")
        return filtered_legacy
    
    def identify_temp_files(self) -> List[Path]:
        """Identify temporary and cache files."""
        print("🔍 Identifying temporary files...")
        
        temp_patterns = [
            '**/__pycache__/**', '**/*.pyc', '**/*.pyo',
            '**/.pytest_cache/**', '**/.coverage', '**/coverage.xml',
            '**/.DS_Store', '**/Thumbs.db', '**/.vscode/settings.json',
            '**/node_modules/**', '**/.git/**', '**/*.log'
        ]
        
        temp_files = []
        for pattern in temp_patterns:
            temp_files.extend(self.project_root.glob(pattern))
            
        print(f"🗑️ Found {len(temp_files)} temporary files")
        return temp_files
    
    def create_archive_structure(self):
        """Create organized archive directory structure."""
        if not self.dry_run:
            self.archive_dir.mkdir(exist_ok=True)
            (self.archive_dir / 'legacy_code').mkdir(exist_ok=True)
            (self.archive_dir / 'backups').mkdir(exist_ok=True)
            (self.archive_dir / 'unused_files').mkdir(exist_ok=True)
            
        print(f"📁 Archive structure ready at {self.archive_dir}")
    
    def archive_legacy_files(self, legacy_files: List[Path]):
        """Move legacy files to organized archive."""
        print("📦 Archiving legacy files...")
        
        archive_manifest = {
            'archived_date': datetime.now().isoformat(),
            'files': []
        }
        
        for file_path in legacy_files:
            try:
                relative_path = file_path.relative_to(self.project_root)
                
                # Determine archive subdirectory
                if any(pattern in str(file_path) for pattern in ['legacy', 'backup', 'old']):
                    archive_subdir = self.archive_dir / 'legacy_code'
                else:
                    archive_subdir = self.archive_dir / 'unused_files'
                
                # Preserve directory structure in archive
                archive_path = archive_subdir / relative_path
                
                if not self.dry_run:
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(archive_path))
                
                archive_manifest['files'].append({
                    'original_path': str(relative_path),
                    'archive_path': str(archive_path.relative_to(self.archive_dir)),
                    'size_bytes': file_path.stat().st_size if file_path.exists() else 0,
                    'reason': 'legacy_pattern' if any(p in str(file_path) for p in ['legacy', 'backup']) else 'unused_import'
                })
                
                print(f"📦 {'[DRY RUN] ' if self.dry_run else ''}Archived: {relative_path}")
                
            except Exception as e:
                print(f"❌ Error archiving {file_path}: {e}")
        
        # Save archive manifest
        if not self.dry_run:
            manifest_path = self.archive_dir / 'archive_manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(archive_manifest, f, indent=2)
    
    def clean_temp_files(self, temp_files: List[Path]):
        """Remove temporary files and caches."""
        print("🧹 Cleaning temporary files...")
        
        for file_path in temp_files:
            try:
                if not self.dry_run:
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                        
                print(f"🗑️ {'[DRY RUN] ' if self.dry_run else ''}Removed: {file_path.relative_to(self.project_root)}")
                
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
    
    def reorganize_directories(self):
        """Reorganize directory structure for better maintainability."""
        print("📁 Reorganizing directory structure...")
        
        # Define ideal directory structure
        ideal_structure = {
            'src/': 'Core application source code',
            'src/core/': 'Core interfaces and models',
            'src/services/': 'Business logic services',
            'src/ui/': 'User interface components',
            'src/features/': 'Feature-specific modules',
            'src/utils/': 'Utility functions and helpers',
            'tests/': 'Test files and test data',
            'docs/': 'Documentation files',
            'config/': 'Configuration files',
            'data/': 'Data files and databases',
            'assets/': 'Static assets (images, etc.)',
            'scripts/': 'Utility scripts and tools'
        }
        
        for dir_path, description in ideal_structure.items():
            target_dir = self.project_root / dir_path
            if not self.dry_run:
                target_dir.mkdir(exist_ok=True)
            print(f"📁 {'[DRY RUN] ' if self.dry_run else ''}Directory: {dir_path} - {description}")
    
    def generate_cleanup_report(self, legacy_files: List[Path], temp_files: List[Path]) -> str:
        """Generate detailed cleanup report."""
        report = f"""
# Project Cleanup Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}

## Summary
- Legacy files processed: {len(legacy_files)}
- Temporary files cleaned: {len(temp_files)}
- Active imports found: {len(self.active_imports)}
- Archive directory: {self.archive_dir}

## Legacy Files {'(Would be archived)' if self.dry_run else '(Archived)'}
"""
        for file_path in legacy_files[:10]:  # Show first 10
            relative_path = file_path.relative_to(self.project_root)
            report += f"- {relative_path}\n"
        
        if len(legacy_files) > 10:
            report += f"- ... and {len(legacy_files) - 10} more\n"
        
        report += f"\n## Temporary Files {'(Would be removed)' if self.dry_run else '(Removed)'}\n"
        for file_path in temp_files[:10]:  # Show first 10
            relative_path = file_path.relative_to(self.project_root)
            report += f"- {relative_path}\n"
        
        if len(temp_files) > 10:
            report += f"- ... and {len(temp_files) - 10} more\n"
        
        return report
    
    def run_cleanup(self):
        """Execute complete project cleanup process."""
        print("🚀 Starting project cleanup...")
        print(f"📁 Project root: {self.project_root}")
        print(f"🔧 Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        
        # Step 1: Scan for active imports
        self.scan_active_imports()
        
        # Step 2: Identify files to clean
        legacy_files = self.identify_legacy_files()
        temp_files = self.identify_temp_files()
        
        # Step 3: Create archive structure
        self.create_archive_structure()
        
        # Step 4: Archive legacy files
        if legacy_files:
            self.archive_legacy_files(legacy_files)
        
        # Step 5: Clean temporary files
        if temp_files:
            self.clean_temp_files(temp_files)
        
        # Step 6: Reorganize directories
        self.reorganize_directories()
        
        # Step 7: Generate report
        report = self.generate_cleanup_report(legacy_files, temp_files)
        
        report_path = self.project_root / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        if not self.dry_run:
            with open(report_path, 'w') as f:
                f.write(report)
        
        print("\n" + "="*50)
        print(report)
        print("="*50)
        print(f"✅ Cleanup {'simulation' if self.dry_run else 'execution'} complete!")
        if not self.dry_run:
            print(f"📄 Report saved: {report_path}")

# Usage functions
def run_project_cleanup(project_root: str = ".", dry_run: bool = True):
    """Run project cleanup with specified options."""
    cleaner = ProjectCleaner(project_root, dry_run)
    cleaner.run_cleanup()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up project file structure')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--execute', action='store_true', help='Execute cleanup (default is dry run)')
    
    args = parser.parse_args()
    
    run_project_cleanup(args.project_root, dry_run=not args.execute)