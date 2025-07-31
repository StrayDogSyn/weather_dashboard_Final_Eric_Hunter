#!/usr/bin/env python3
"""
Weather Dashboard Project Cleanup Tool

Optimized cleanup tool specifically designed for the Weather Dashboard project.
Automatically cleans up legacy files, organizes backups, maintains clean
project structure, and handles weather-specific cache and data files.

Features:
- Weather cache management
- Chart export cleanup
- UI component optimization
- Performance monitoring
- Smart backup retention
- Configurable cleanup strategies
- Parallel processing support
- Comprehensive reporting
"""

import os
import ast
import re
import time
from pathlib import Path
from typing import Set, List, Dict, Optional, Any
from datetime import datetime, timedelta

# Import common utilities
from common.base_script import BaseScript
from common.cli_utils import CLIUtils
from common.file_utils import FileUtils
from common.process_utils import ProcessUtils

class ProjectCleaner(BaseScript):
    """Enhanced project cleanup tool with configurable strategies and parallel processing."""
    
    def __init__(self):
        super().__init__(
            script_name="cleanup_project",
            description="Enhanced project cleanup tool with configurable strategies and parallel processing",
            version="2.0.0"
        )
        self.active_imports = set()
        self.stats = {
            'files_cleaned': 0,
            'space_freed': 0,
            'cache_files': 0,
            'backup_files': 0,
            'temp_files': 0,
            'legacy_files': 0,
            'export_files': 0
        }
        
        # Load cleanup configuration
        self.cleanup_config = self.config.get('cleanup', {})
        
        # Try to load patterns config if it exists
        patterns_file = self.project_root / 'scripts' / 'config' / 'cleanup_patterns.yaml'
        if patterns_file.exists():
            try:
                self.config.load_custom_config(patterns_file)
                self.patterns_config = self.config.get('patterns', {})
            except Exception as e:
                self.logger.warning(f"Could not load patterns config: {e}")
                self.patterns_config = {}
        else:
            self.patterns_config = {}
        
        # Initialize file utilities
        self.file_utils = FileUtils()
        self.process_utils = ProcessUtils()
        
        # Set up archive directory
        self.archive_dir = self.project_root / 'archive'
        
    def scan_active_imports(self) -> Set[str]:
        """Scan all Python files for import statements to identify active files."""
        self.logger.info("Scanning for active imports...")
        
        exclude_patterns = self.patterns_config.get('exclude_patterns', [])
        
        for py_file in self.project_root.rglob('*.py'):
            # Skip excluded directories
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue
                
            try:
                content = self.file_utils.read_text_file(py_file)
                if not content:
                    continue
                    
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
                self.logger.warning(f"Error scanning {py_file}: {e}")
                
        self.logger.info(f"Found {len(self.active_imports)} active imports")
        return self.active_imports
    
    def identify_legacy_files(self) -> List[Path]:
        """Identify legacy, backup, and unused files based on configuration."""
        self.logger.info("Identifying legacy files...")
        
        legacy_files = []
        legacy_patterns = self.patterns_config.get('legacy_patterns', [])
        protected_files = self.patterns_config.get('protected_files', [])
        protected_patterns = self.patterns_config.get('protected_patterns', [])
        
        # Find files matching legacy patterns
        for pattern in legacy_patterns:
            for file_path in self.project_root.rglob('*'):
                if file_path.is_file() and re.match(pattern, str(file_path.name)):
                    legacy_files.append(file_path)
        
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
        
        self.stats['legacy_files'] = len(filtered_legacy)
        self.logger.info(f"Identified {len(filtered_legacy)} legacy files")
        return filtered_legacy
    
    def identify_temp_files(self) -> List[Path]:
        """Identify temporary and cache files based on configuration."""
        self.logger.info("Identifying temporary files...")
        
        temp_patterns = self.patterns_config.get('temp_patterns', [])
        temp_files = []
        
        for pattern in temp_patterns:
            temp_files.extend(self.project_root.glob(pattern))
            
        # Filter out non-existent files
        temp_files = [f for f in temp_files if f.exists()]
        
        self.stats['temp_files'] = len(temp_files)
        self.logger.info(f"Found {len(temp_files)} temporary files")
        return temp_files
    
    def clean_weather_cache(self) -> List[Path]:
        """Clean old weather cache files based on retention policy."""
        self.logger.info("Cleaning weather cache files...")
        
        cache_files = []
        strategy = self.cleanup_config.get('strategy', 'standard')
        cache_retention_days = self.cleanup_config.get('cache_retention_days', 7)
        
        # Get strategy-specific settings
        strategy_config = self.patterns_config.get('strategies', {}).get(strategy, {})
        retention_days = strategy_config.get('cache_retention_days', cache_retention_days)
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cache_patterns = self.patterns_config.get('cache_patterns', [])
        
        for pattern in cache_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    # Check file age
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date or strategy == 'aggressive':
                        cache_files.append(file_path)
        
        # Clean specific cache directories
        cache_dirs = self.patterns_config.get('cache_directories', [])
        for cache_dir in cache_dirs:
            cache_path = self.project_root / cache_dir
            if cache_path.exists():
                for file_path in cache_path.rglob('*'):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date or strategy == 'aggressive':
                            cache_files.append(file_path)
        
        self.stats['cache_files'] = len(cache_files)
        self.logger.info(f"Found {len(cache_files)} cache files to clean")
        return cache_files
    
    def clean_chart_exports(self) -> List[Path]:
        """Clean old chart export files."""
        self.logger.info("Cleaning chart export files...")
        
        export_files = []
        strategy = self.cleanup_config.get('strategy', 'standard')
        export_retention_days = self.cleanup_config.get('export_retention_days', 30)
        
        # Get strategy-specific settings
        strategy_config = self.patterns_config.get('strategies', {}).get(strategy, {})
        retention_days = strategy_config.get('export_retention_days', export_retention_days)
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        export_patterns = self.patterns_config.get('export_patterns', [])
        
        for pattern in export_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date or strategy == 'aggressive':
                        export_files.append(file_path)
        
        self.stats['export_files'] = len(export_files)
        self.logger.info(f"Found {len(export_files)} export files to clean")
        return export_files
    
    def optimize_pycache(self) -> List[Path]:
        """Optimize __pycache__ directories by removing old .pyc files."""
        self.logger.info("Optimizing Python cache files...")
        
        pycache_files = []
        strategy = self.cleanup_config.get('strategy', 'standard')
        
        # Find all __pycache__ directories in specified paths
        search_paths = self.patterns_config.get('pycache_search_paths', ['src'])
        
        for search_path in search_paths:
            path = self.project_root / search_path
            if path.exists():
                for pycache_dir in path.rglob('__pycache__'):
                    if pycache_dir.is_dir():
                        for pyc_file in pycache_dir.glob('*.pyc'):
                            # Check if corresponding .py file exists
                            py_file = pyc_file.parent.parent / (pyc_file.stem.split('.')[0] + '.py')
                            if not py_file.exists() or strategy == 'aggressive':
                                pycache_files.append(pyc_file)
        
        self.logger.info(f"Found {len(pycache_files)} cache files to optimize")
        return pycache_files
    
    def analyze_project_health(self) -> Dict[str, any]:
        """Analyze project health and provide recommendations."""
        self.logger.info("Analyzing project health...")
        
        health_report = {
            'total_files': 0,
            'python_files': 0,
            'large_files': [],
            'duplicate_patterns': [],
            'recommendations': [],
            'directory_stats': {}
        }
        
        # Get health check thresholds from config
        thresholds = self.patterns_config.get('health_thresholds', {})
        large_file_mb = thresholds.get('large_file_mb', 1)
        max_files_warning = thresholds.get('max_files_warning', 500)
        
        exclude_patterns = self.patterns_config.get('exclude_patterns', [])
        
        # Count files and identify large ones
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                # Skip excluded directories
                if any(pattern in str(file_path) for pattern in exclude_patterns):
                    continue
                    
                health_report['total_files'] += 1
                
                if file_path.suffix == '.py':
                    health_report['python_files'] += 1
                
                # Check for large files
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > large_file_mb:
                    health_report['large_files'].append({
                        'path': str(file_path.relative_to(self.project_root)),
                        'size_mb': round(file_size_mb, 2)
                    })
        
        # Generate directory statistics
        for dir_path in ['src', 'tests', 'scripts', 'docs']:
            path = self.project_root / dir_path
            if path.exists():
                stats = self.file_utils.get_directory_stats(path)
                health_report['directory_stats'][dir_path] = stats
        
        # Generate recommendations
        if len(health_report['large_files']) > 0:
            health_report['recommendations'].append(
                f"Consider optimizing {len(health_report['large_files'])} large files"
            )
        
        if health_report['total_files'] > max_files_warning:
            health_report['recommendations'].append(
                "Project has many files - consider regular cleanup"
            )
        
        return health_report
    
    def _clean_files(self, files: List[Path], file_type: str) -> int:
        """Generic method to clean files with progress tracking."""
        if not files:
            return 0
        
        cleaned_count = 0
        total_size = 0
        errors = []
        
        self.logger.info(f"Cleaning {len(files)} {file_type} files...")
        
        # Use parallel processing if enabled
        if self.cleanup_config.get('parallel_processing', False):
            cleaned_count, total_size, errors = self._clean_files_parallel(files, file_type)
        else:
            for i, file_path in enumerate(files, 1):
                try:
                    if not self.dry_run:
                        file_size = file_path.stat().st_size
                        if file_path.is_dir():
                            import shutil
                            shutil.rmtree(file_path)
                        else:
                            file_path.unlink()
                        total_size += file_size
                        cleaned_count += 1
                    else:
                        total_size += file_path.stat().st_size
                        cleaned_count += 1
                    
                    # Progress indicator
                    if i % 10 == 0 or i == len(files):
                        progress = (i / len(files)) * 100
                        self.logger.debug(f"Progress: {progress:.1f}% ({i}/{len(files)})")
                        
                except Exception as e:
                    error_msg = f"Error cleaning {file_path}: {e}"
                    self.logger.warning(error_msg)
                    errors.append(error_msg)
        
        # Update stats
        self.stats['files_cleaned'] += cleaned_count
        self.stats['space_freed'] += total_size
        if 'errors' not in self.stats:
            self.stats['errors'] = []
        self.stats['errors'].extend(errors)
        
        size_mb = total_size / (1024 * 1024)
        action = "Would clean" if self.dry_run else "Cleaned"
        self.logger.info(f"{action} {cleaned_count} {file_type} files ({size_mb:.2f} MB)")
        
        return cleaned_count
    
    def _clean_files_parallel(self, files: List[Path], file_type: str) -> tuple[int, int, List[str]]:
        """Clean files using parallel processing."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        cleaned_count = 0
        total_size = 0
        errors = []
        lock = threading.Lock()
        
        max_workers = self.cleanup_config.get('max_workers', 4)
        
        def clean_single_file(file_path: Path) -> tuple[bool, int, str]:
            try:
                if not self.dry_run:
                    file_size = file_path.stat().st_size
                    if file_path.is_dir():
                        import shutil
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                    return True, file_size, ""
                else:
                    file_size = file_path.stat().st_size
                    return True, file_size, ""
            except Exception as e:
                return False, 0, str(e)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(clean_single_file, file_path): file_path 
                            for file_path in files}
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success, size, error = future.result()
                    with lock:
                        if success:
                            cleaned_count += 1
                            total_size += size
                        else:
                            errors.append(f"Error cleaning {file_path}: {error}")
                except Exception as e:
                    with lock:
                        errors.append(f"Unexpected error cleaning {file_path}: {e}")
        
        return cleaned_count, total_size, errors
    
    def _calculate_cleanup_stats(self, files_by_type: Dict[str, List[Path]]) -> Dict[str, any]:
        """Calculate comprehensive cleanup statistics."""
        stats = {
            'total_files': sum(len(files) for files in files_by_type.values()),
            'total_size_mb': 0,
            'by_type': {},
            'largest_files': [],
            'cleanup_efficiency': 0,
            'recommendations': []
        }
        
        all_files = []
        for file_type, files in files_by_type.items():
            type_size = sum(f.stat().st_size for f in files if f.exists())
            stats['by_type'][file_type] = {
                'count': len(files),
                'size_mb': round(type_size / (1024 * 1024), 2)
            }
            stats['total_size_mb'] += type_size / (1024 * 1024)
            all_files.extend(files)
        
        # Find largest files
        if all_files:
            sorted_files = sorted(
                [(f, f.stat().st_size) for f in all_files if f.exists()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            stats['largest_files'] = [
                {
                    'path': str(f.relative_to(self.project_root)),
                    'size_mb': round(size / (1024 * 1024), 2)
                }
                for f, size in sorted_files
            ]
        
        # Calculate cleanup efficiency
        if stats['total_files'] > 0:
            stats['cleanup_efficiency'] = min(100, (stats['total_size_mb'] / stats['total_files']) * 10)
        
        # Generate recommendations
        if stats['total_size_mb'] > 100:
            stats['recommendations'].append("Consider more frequent cleanup cycles")
        if stats['by_type'].get('cache_files', {}).get('count', 0) > 50:
            stats['recommendations'].append("Review cache retention policies")
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        
        # Update instance stats
        self.stats['space_freed'] = stats['total_size_mb'] * 1024 * 1024
        self.stats['files_cleaned'] = stats['total_files']
        
        return stats
    
    def create_archive(self, files: List[Path], archive_type: str = 'cleanup') -> Optional[Path]:
        """Create archive of files before deletion."""
        if not files or self.dry_run:
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_dir = self.project_root / 'archive' / f'{archive_type}_{timestamp}'
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Creating archive in {archive_dir}...")
        
        archived_count = 0
        archive_config = self.cleanup_config.get('archive', {})
        compress_archive = archive_config.get('compress', False)
        
        if compress_archive:
            # Create compressed archive
            archive_file = archive_dir.with_suffix('.tar.gz')
            archived_count = self.file_utils.create_compressed_archive(files, archive_file, self.project_root)
        else:
            # Create directory archive
            for file_path in files:
                try:
                    # Maintain directory structure in archive
                    relative_path = file_path.relative_to(self.project_root)
                    archive_file = archive_dir / relative_path
                    archive_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file to archive
                    import shutil
                    shutil.copy2(file_path, archive_file)
                    archived_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Error archiving {file_path}: {e}")
        
        self.logger.info(f"Archived {archived_count} files")
        return archive_dir if not compress_archive else archive_file
     
    def generate_enhanced_cleanup_report(
        self, legacy_files: List[Path], temp_files: List[Path], 
        cache_files: List[Path], export_files: List[Path], 
        pycache_files: List[Path], health_report: Optional[Dict], 
        reorganize_stats: Optional[Dict], archive_path: Optional[Path]
    ) -> str:
        """Generate comprehensive cleanup report with weather dashboard specifics."""
        
        total_files = len(legacy_files) + len(temp_files) + len(cache_files) + len(export_files) + len(pycache_files)
        space_freed_mb = self.stats['space_freed'] / (1024 * 1024)
        
        report = f"""# 🌤️ Weather Dashboard Cleanup Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}
Strategy: {self.cleanup_config.get('strategy', 'standard')}

## 📊 Summary Statistics
- **Total files processed**: {total_files}
- **Space freed**: {space_freed_mb:.2f} MB
- **Legacy files**: {len(legacy_files)}
- **Temporary files**: {len(temp_files)}
- **Weather cache files**: {len(cache_files)}
- **Chart export files**: {len(export_files)}
- **Python cache files**: {len(pycache_files)}
- **Active imports found**: {len(self.active_imports)}

## 🌤️ Weather-Specific Cleanup

### Cache Files {'(Would be cleaned)' if self.dry_run else '(Cleaned)'}
"""
        
        if cache_files:
            for file_path in cache_files[:10]:
                relative_path = file_path.relative_to(self.project_root)
                file_age = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
                report += f"- {relative_path} (Age: {file_age} days)\n"
            if len(cache_files) > 10:
                report += f"- ... and {len(cache_files) - 10} more cache files\n"
        else:
            report += "- No cache files found to clean\n"
        
        report += f"\n### Chart Exports {'(Would be cleaned)' if self.dry_run else '(Cleaned)'}\n"
        
        if export_files:
            for file_path in export_files[:5]:
                relative_path = file_path.relative_to(self.project_root)
                file_size = file_path.stat().st_size / 1024  # KB
                report += f"- {relative_path} ({file_size:.1f} KB)\n"
            if len(export_files) > 5:
                report += f"- ... and {len(export_files) - 5} more export files\n"
        else:
            report += "- No export files found to clean\n"
        
        # Add health report if available
        if health_report:
            report += f"\n## 🔍 Project Health Analysis\n"
            report += f"- **Total files**: {health_report['total_files']}\n"
            report += f"- **Python files**: {health_report['python_files']}\n"
            
            if health_report['large_files']:
                report += f"\n### Large Files (>1MB)\n"
                for large_file in health_report['large_files'][:5]:
                    report += f"- {large_file['path']} ({large_file['size_mb']} MB)\n"
            
            if health_report['recommendations']:
                report += f"\n### 💡 Recommendations\n"
                for rec in health_report['recommendations']:
                    report += f"- {rec}\n"
        
        # Add legacy and temp files sections
        report += f"\n## 📦 Legacy Files {'(Would be archived)' if self.dry_run else '(Archived)'}\n"
        if legacy_files:
            for file_path in legacy_files[:5]:
                relative_path = file_path.relative_to(self.project_root)
                report += f"- {relative_path}\n"
            if len(legacy_files) > 5:
                report += f"- ... and {len(legacy_files) - 5} more legacy files\n"
        else:
            report += "- No legacy files found\n"
        
        report += f"\n## 🗑️ Temporary Files {'(Would be removed)' if self.dry_run else '(Removed)'}\n"
        if temp_files:
            for file_path in temp_files[:5]:
                relative_path = file_path.relative_to(self.project_root)
                report += f"- {relative_path}\n"
            if len(temp_files) > 5:
                report += f"- ... and {len(temp_files) - 5} more temporary files\n"
        else:
            report += "- No temporary files found\n"
        
        # Add performance tips
        report += f"\n## ⚡ Performance Tips\n"
        report += f"- Run cleanup weekly for optimal performance\n"
        report += f"- Use `--aggressive` mode for deep cleaning\n"
        report += f"- Monitor cache retention settings\n"
        report += f"- Consider archiving old chart exports\n"
        
        if archive_path:
            report += f"\n## 📁 Archive Location\n"
            report += f"- Archived files: `{archive_path}`\n"
        
        return report
     
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
    
    def reorganize_directories(self) -> Dict[str, int]:
        """Reorganize project directories for better structure."""
        self.logger.info("Reorganizing project directories...")
        
        reorganize_stats = {
            'moved_files': 0,
            'created_dirs': 0,
            'removed_empty_dirs': 0
        }
        
        # Get reorganization rules from config
        reorganize_config = self.patterns_config.get('reorganize', {})
        if not reorganize_config.get('enabled', False):
            self.logger.info("Directory reorganization is disabled")
            return reorganize_stats
        
        target_structure = reorganize_config.get('target_structure', {
            'src/utils': ['*_utils.py', '*_helper.py'],
            'src/models': ['*_model.py', '*_schema.py'],
            'src/services': ['*_service.py', '*_client.py'],
            'tests/unit': ['test_*.py'],
            'docs/api': ['*.md'],
            'scripts/maintenance': ['cleanup_*.py', 'verify_*.py']
        })
        
        for target_dir, patterns in target_structure.items():
            target_path = self.project_root / target_dir
            
            if not self.dry_run:
                target_path.mkdir(parents=True, exist_ok=True)
                reorganize_stats['created_dirs'] += 1
            
            # Move matching files
            for pattern in patterns:
                for file_path in self.project_root.rglob(pattern):
                    if file_path.is_file() and target_dir not in str(file_path):
                        if not self.dry_run:
                            new_path = target_path / file_path.name
                            if not new_path.exists():
                                try:
                                    file_path.rename(new_path)
                                    reorganize_stats['moved_files'] += 1
                                except Exception as e:
                                    self.logger.warning(f"Error moving {file_path}: {e}")
        
        # Remove empty directories
        if reorganize_config.get('remove_empty_dirs', True):
            for dir_path in self.project_root.rglob('*'):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    if not self.dry_run:
                        try:
                            dir_path.rmdir()
                            reorganize_stats['removed_empty_dirs'] += 1
                        except Exception as e:
                            self.logger.warning(f"Error removing empty directory {dir_path}: {e}")
        
        action = "Would reorganize" if self.dry_run else "Reorganized"
        self.logger.info(f"{action} directories: {reorganize_stats}")
        
        return reorganize_stats
    
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
    
    def run_cleanup(self, include_health_check: bool = True) -> Dict[str, any]:
        """Execute complete weather dashboard cleanup process."""
        start_time = time.time()
        
        self.logger.info("Starting project cleanup process")
        self.logger.info(f"Project Root: {self.project_root}")
        self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE CLEANUP'}")
        
        strategy = self.cleanup_config.get('strategy', 'standard')
        self.logger.info(f"Strategy: {strategy}")
        
        try:
            # Step 1: Project health analysis (if requested)
            health_report = None
            if include_health_check:
                self.logger.info("Analyzing project health...")
                health_report = self.analyze_project_health()
                self.logger.info(f"Health analysis complete: {health_report['total_files']} files, {len(health_report['large_files'])} large files")
            
            # Step 2: Scan for active imports
            self.logger.info("Scanning active imports...")
            self.scan_active_imports()
            self.logger.info(f"Found {len(self.active_imports)} active imports")
            
            # Step 3: Identify files to clean
            self.logger.info("Identifying files to clean...")
            legacy_files = self.identify_legacy_files()
            temp_files = self.identify_temp_files()
            
            # Step 4: Weather-specific cleanup
            cache_files = self.clean_weather_cache()
            export_files = self.clean_chart_exports()
            pycache_files = self.optimize_pycache()
            
            # Step 5: Create archive if needed
            all_files = legacy_files + temp_files + cache_files + export_files + pycache_files
            archive_path = None
            if all_files and self.cleanup_config.get('create_archive', False):
                self.logger.info("Creating archive...")
                archive_path = self.create_archive(all_files)
            
            # Step 6: Execute cleanup operations
            files_by_type = {
                'legacy': legacy_files,
                'temporary': temp_files,
                'cache': cache_files,
                'export': export_files,
                'pycache': pycache_files
            }
            
            for file_type, files in files_by_type.items():
                if files:
                    self._clean_files(files, file_type)
            
            # Step 7: Reorganize directories
            reorganize_stats = None
            if self.cleanup_config.get('reorganize_directories', False):
                self.logger.info("Reorganizing directories...")
                reorganize_stats = self.reorganize_directories()
            
            # Step 8: Calculate statistics
            cleanup_stats = self._calculate_cleanup_stats(files_by_type)
            
            # Step 9: Generate comprehensive report
            self.logger.info("Generating cleanup report...")
            report = self.generate_enhanced_cleanup_report(
                legacy_files, temp_files, cache_files, export_files, 
                pycache_files, health_report, reorganize_stats, archive_path
            )
            
            execution_time = time.time() - start_time
            space_freed_mb = self.stats['space_freed'] / (1024 * 1024)
            
            self.logger.info("Cleanup completed successfully")
            self.logger.info(f"Execution Time: {execution_time:.2f} seconds")
            self.logger.info(f"Files Processed: {self.stats['files_cleaned']}")
            self.logger.info(f"Space Freed: {space_freed_mb:.2f} MB")
            
            if self.dry_run:
                self.logger.info("This was a DRY RUN. No files were actually modified.")
            
            return {
                'success': True,
                'stats': self.stats,
                'execution_time': execution_time,
                'archive_path': str(archive_path) if archive_path else None,
                'cleanup_report': report,
                'cleanup_stats': cleanup_stats
            }
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    

    
    def _export_report(self, report: str, file_path: str) -> None:
        """Export cleanup report to file."""
        try:
            report_path = Path(file_path)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            if report_path.suffix.lower() == '.json':
                # Convert markdown report to JSON structure
                import json
                report_data = {
                    'timestamp': datetime.now().isoformat(),
                    'report': report,
                    'stats': self.stats
                }
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2)
            else:
                # Save as markdown/text
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report)
            
            self.logger.info(f"Report exported to: {report_path}")
        except Exception as e:
            self.logger.error(f"Failed to export report: {e}")

    def setup_args(self) -> None:
        """Setup command-line arguments."""
        self.cli.add_argument(
            '--strategy',
            choices=['conservative', 'standard', 'aggressive'],
            default='standard',
            help='Cleanup strategy to use'
        )
        

        
        self.cli.add_argument(
            '--cache-days',
            type=int,
            help='Number of days to retain cache files'
        )
        
        self.cli.add_argument(
            '--export-days',
            type=int,
            help='Number of days to retain export files'
        )
        
        self.cli.add_argument(
            '--parallel',
            action='store_true',
            help='Enable parallel processing for file operations'
        )
        
        self.cli.add_argument(
            '--max-workers',
            type=int,
            default=4,
            help='Maximum number of worker threads for parallel processing'
        )
    
    def run(self) -> Dict[str, Any]:
        """Run the cleanup process."""
        # Update configuration based on arguments
        if hasattr(self.args, 'strategy') and self.args.strategy:
            self.cleanup_config['strategy'] = self.args.strategy
        if hasattr(self.args, 'cache_days') and self.args.cache_days:
            self.cleanup_config['cache_retention_days'] = self.args.cache_days
        if hasattr(self.args, 'export_days') and self.args.export_days:
            self.cleanup_config['export_retention_days'] = self.args.export_days
        if hasattr(self.args, 'skip_health') and self.args.skip_health:
            self.cleanup_config['health_analysis'] = False
        if hasattr(self.args, 'skip_archive') and self.args.skip_archive:
            self.cleanup_config['create_archive'] = False
        if hasattr(self.args, 'skip_reorganize') and self.args.skip_reorganize:
            self.cleanup_config['reorganize_directories'] = False
        if hasattr(self.args, 'parallel') and self.args.parallel:
            self.cleanup_config['parallel_processing'] = True
        if hasattr(self.args, 'max_workers') and self.args.max_workers:
            self.cleanup_config['max_workers'] = self.args.max_workers
        
        if hasattr(self.args, 'dry_run'):
            self.dry_run = self.args.dry_run
        
        # Configuration check
        if hasattr(self.args, 'config_check') and self.args.config_check:
            self.logger.info("Cleanup configuration:")
            for key, value in self.cleanup_config.items():
                self.logger.info(f"  {key}: {value}")
            return {'success': True, 'message': 'Configuration displayed'}
        
        # Run cleanup
        result = self.run_cleanup()
        
        # Export report if requested
        if hasattr(self.args, 'export_report') and self.args.export_report and result.get('cleanup_report'):
            self._export_report(result['cleanup_report'], self.args.export_report)
        
        return result


def run_project_cleanup(project_root: str = ".", dry_run: bool = True):
    """Run project cleanup with specified options."""
    cleaner = ProjectCleaner()
    cleaner.run_cleanup()


def main():
    """Main function to run the cleanup process."""
    cleaner = ProjectCleaner()
    return cleaner.execute()

if __name__ == "__main__":
    import sys
    sys.exit(main())