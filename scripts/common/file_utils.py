#!/usr/bin/env python3
"""
File Utilities for Weather Dashboard Scripts

Provides consistent file operations:
- Safe file reading/writing with encoding handling
- Directory operations with error handling
- File pattern matching and filtering
- Archive creation and extraction
- File size and modification time utilities
- Backup and restore operations
"""

import os
import shutil
import zipfile
import tarfile
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator, Callable
from datetime import datetime, timedelta
import fnmatch
import hashlib
import tempfile
from contextlib import contextmanager


class FileUtils:
    """Utilities for file and directory operations."""
    
    @staticmethod
    def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Safely read text file with proper encoding."""
        path = Path(file_path)
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            # Try common encodings
            for enc in ['utf-8-sig', 'latin1', 'cp1252']:
                try:
                    return path.read_text(encoding=enc)
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not decode file {path} with any common encoding")
    
    @staticmethod
    def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8', backup: bool = False) -> None:
        """Safely write text file with optional backup."""
        path = Path(file_path)
        
        # Create backup if requested and file exists
        if backup and path.exists():
            backup_path = path.with_suffix(f"{path.suffix}.bak")
            shutil.copy2(path, backup_path)
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        path.write_text(content, encoding=encoding)
    
    @staticmethod
    def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read JSON file with error handling."""
        try:
            content = FileUtils.read_text_file(file_path)
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
    
    @staticmethod
    def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2, backup: bool = False) -> None:
        """Write JSON file with formatting."""
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        FileUtils.write_text_file(file_path, content, backup=backup)
    
    @staticmethod
    def read_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read YAML file with error handling."""
        try:
            content = FileUtils.read_text_file(file_path)
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
    
    @staticmethod
    def write_yaml_file(file_path: Union[str, Path], data: Dict[str, Any], backup: bool = False) -> None:
        """Write YAML file with formatting."""
        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        FileUtils.write_text_file(file_path, content, backup=backup)
    
    @staticmethod
    def ensure_directory(dir_path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary."""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path], preserve_metadata: bool = True) -> None:
        """Copy file with optional metadata preservation."""
        src_path = Path(src)
        dst_path = Path(dst)
        
        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        if preserve_metadata:
            shutil.copy2(src_path, dst_path)
        else:
            shutil.copy(src_path, dst_path)
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Move file to new location."""
        src_path = Path(src)
        dst_path = Path(dst)
        
        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(src_path), str(dst_path))
    
    @staticmethod
    def delete_file(file_path: Union[str, Path], missing_ok: bool = True) -> bool:
        """Delete file safely."""
        path = Path(file_path)
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            if not missing_ok:
                raise
            return False
    
    @staticmethod
    def delete_directory(dir_path: Union[str, Path], missing_ok: bool = True) -> bool:
        """Delete directory and all contents."""
        path = Path(dir_path)
        try:
            shutil.rmtree(path)
            return True
        except FileNotFoundError:
            if not missing_ok:
                raise
            return False
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """Get file size in bytes."""
        return Path(file_path).stat().st_size
    
    @staticmethod
    def get_file_modified_time(file_path: Union[str, Path]) -> datetime:
        """Get file modification time."""
        timestamp = Path(file_path).stat().st_mtime
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def is_file_older_than(file_path: Union[str, Path], days: int) -> bool:
        """Check if file is older than specified days."""
        modified_time = FileUtils.get_file_modified_time(file_path)
        cutoff_time = datetime.now() - timedelta(days=days)
        return modified_time < cutoff_time
    
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = True) -> List[Path]:
        """Find files matching pattern."""
        path = Path(directory)
        if recursive:
            return list(path.rglob(pattern))
        else:
            return list(path.glob(pattern))
    
    @staticmethod
    def find_files_by_extension(directory: Union[str, Path], extensions: List[str], recursive: bool = True) -> List[Path]:
        """Find files with specific extensions."""
        files = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = f".{ext}"
            pattern = f"*{ext}"
            files.extend(FileUtils.find_files(directory, pattern, recursive))
        return files
    
    @staticmethod
    def filter_files(files: List[Path], include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> List[Path]:
        """Filter files by include/exclude patterns."""
        filtered = files.copy()
        
        # Apply include patterns
        if include_patterns:
            included = []
            for file_path in filtered:
                for pattern in include_patterns:
                    if fnmatch.fnmatch(file_path.name, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                        included.append(file_path)
                        break
            filtered = included
        
        # Apply exclude patterns
        if exclude_patterns:
            excluded = []
            for file_path in filtered:
                should_exclude = False
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(file_path.name, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                        should_exclude = True
                        break
                if not should_exclude:
                    excluded.append(file_path)
            filtered = excluded
        
        return filtered
    
    @staticmethod
    def calculate_directory_size(directory: Union[str, Path]) -> int:
        """Calculate total size of directory and all contents."""
        total_size = 0
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, FileNotFoundError):
                    # Skip files that can't be accessed
                    continue
        return total_size
    
    @staticmethod
    def get_directory_stats(directory: Union[str, Path]) -> Dict[str, Any]:
        """Get comprehensive directory statistics."""
        path = Path(directory)
        if not path.exists():
            return {'exists': False}
        
        stats = {
            'exists': True,
            'total_files': 0,
            'total_directories': 0,
            'total_size': 0,
            'file_types': {},
            'largest_file': None,
            'largest_file_size': 0,
            'oldest_file': None,
            'newest_file': None
        }
        
        oldest_time = None
        newest_time = None
        
        for item in path.rglob('*'):
            try:
                if item.is_file():
                    stats['total_files'] += 1
                    
                    # File size
                    size = item.stat().st_size
                    stats['total_size'] += size
                    
                    # Track largest file
                    if size > stats['largest_file_size']:
                        stats['largest_file'] = str(item)
                        stats['largest_file_size'] = size
                    
                    # File type
                    ext = item.suffix.lower() or 'no_extension'
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                    
                    # Modification time
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if oldest_time is None or mtime < oldest_time:
                        oldest_time = mtime
                        stats['oldest_file'] = str(item)
                    if newest_time is None or mtime > newest_time:
                        newest_time = mtime
                        stats['newest_file'] = str(item)
                
                elif item.is_dir():
                    stats['total_directories'] += 1
            
            except (OSError, FileNotFoundError):
                # Skip items that can't be accessed
                continue
        
        return stats
    
    @staticmethod
    def create_archive(archive_path: Union[str, Path], source_dir: Union[str, Path], compression: str = 'zip') -> None:
        """Create archive from directory."""
        archive_path = Path(archive_path)
        source_dir = Path(source_dir)
        
        # Ensure archive directory exists
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        if compression.lower() == 'zip':
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)
        
        elif compression.lower() in ['tar', 'tar.gz', 'tgz']:
            mode = 'w:gz' if compression.lower() in ['tar.gz', 'tgz'] else 'w'
            with tarfile.open(archive_path, mode) as tarf:
                tarf.add(source_dir, arcname=source_dir.name)
        
        else:
            raise ValueError(f"Unsupported compression format: {compression}")
    
    @staticmethod
    def extract_archive(archive_path: Union[str, Path], extract_dir: Union[str, Path]) -> None:
        """Extract archive to directory."""
        archive_path = Path(archive_path)
        extract_dir = Path(extract_dir)
        
        # Ensure extraction directory exists
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(extract_dir)
        
        elif archive_path.suffix.lower() in ['.tar', '.gz', '.tgz']:
            with tarfile.open(archive_path, 'r:*') as tarf:
                tarf.extractall(extract_dir)
        
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
    
    @staticmethod
    def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
        """Calculate file hash."""
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    @contextmanager
    def temporary_directory():
        """Context manager for temporary directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield Path(temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    @contextmanager
    def temporary_file(suffix: str = '', prefix: str = 'tmp'):
        """Context manager for temporary file."""
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        try:
            os.close(fd)
            yield Path(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
    
    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_dir: Union[str, Path] = None) -> Path:
        """Create backup of file with timestamp."""
        file_path = Path(file_path)
        
        if backup_dir:
            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}"
        else:
            backup_path = file_path.with_name(f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}")
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    @staticmethod
    def clean_old_backups(backup_dir: Union[str, Path], pattern: str, keep_count: int = 5) -> List[Path]:
        """Clean old backup files, keeping only the most recent ones."""
        backup_dir = Path(backup_dir)
        if not backup_dir.exists():
            return []
        
        # Find backup files matching pattern
        backup_files = list(backup_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old backups
        removed_files = []
        for backup_file in backup_files[keep_count:]:
            try:
                backup_file.unlink()
                removed_files.append(backup_file)
            except OSError:
                pass
        
        return removed_files
    
    @staticmethod
    def walk_directory(directory: Union[str, Path], callback: Callable[[Path], None], file_filter: Callable[[Path], bool] = None) -> None:
        """Walk directory and apply callback to each file."""
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                if file_filter is None or file_filter(file_path):
                    callback(file_path)