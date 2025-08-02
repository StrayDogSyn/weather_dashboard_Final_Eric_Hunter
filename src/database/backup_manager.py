"""Database backup manager.

Handles automated backups with rotation and compression.
"""

import gzip
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .database_manager import DatabaseManager
from .repositories import (
    WeatherRepository, PreferencesRepository, 
    ActivityRepository, JournalRepository
)


class BackupManager:
    """Manages database backups and restoration."""
    
    def __init__(self, db_manager: DatabaseManager, backup_dir: Optional[Path] = None):
        """Initialize backup manager.
        
        Args:
            db_manager: Database manager instance
            backup_dir: Directory for backups (defaults to data/backups)
        """
        self._db_manager = db_manager
        self._logger = logging.getLogger(__name__)
        
        # Set backup directory
        if backup_dir is None:
            backup_dir = Path("data/backups")
        
        self._backup_dir = backup_dir
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup settings
        self._max_backups = 5
        self._compression_enabled = True
        
        # Repository instances will be created with sessions when needed
        self._weather_repo = None
        self._prefs_repo = None
        self._activity_repo = None
        self._journal_repo = None
    
    async def create_backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """Create a full database backup.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Optional[Path]: Path to created backup file
        """
        try:
            # Generate backup filename
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"weather_dashboard_backup_{timestamp}"
            
            # Create backup data
            backup_data = await self._create_backup_data()
            
            # Save backup
            backup_file = self._backup_dir / f"{backup_name}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Compress if enabled
            if self._compression_enabled:
                compressed_file = self._backup_dir / f"{backup_name}.json.gz"
                
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                backup_file.unlink()
                backup_file = compressed_file
            
            # Rotate old backups
            await self._rotate_backups()
            
            self._logger.info(f"Created backup: {backup_file}")
            return backup_file
            
        except Exception as e:
            self._logger.error(f"Failed to create backup: {e}")
            return None
    
    async def _create_backup_data(self) -> Dict:
        """Create comprehensive backup data.
        
        Returns:
            Dict: Complete backup data
        """
        backup_data = {
            'metadata': {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'database_version': await self._get_database_version(),
                'backup_type': 'full'
            },
            'data': {}
        }
        
        try:
            # Get repositories with session
            async with self._db_manager.get_async_session() as session:
                weather_repo = WeatherRepository(session)
                prefs_repo = PreferencesRepository(session)
                activity_repo = ActivityRepository(session)
                journal_repo = JournalRepository(session)
                
                # Weather history
                weather_data = await weather_repo.get_all_history()
                backup_data['data']['weather_history'] = [
                    record.to_dict() for record in weather_data
                ]
                
                # User preferences
                prefs_data = await prefs_repo.get_all_preferences()
                backup_data['data']['user_preferences'] = [
                    pref.to_dict() for pref in prefs_data
                ]
                
                # Activity log
                activity_data = await activity_repo.get_all_activities()
                backup_data['data']['activity_log'] = [
                    activity.to_dict() for activity in activity_data
                ]
                
                # Journal entries
                journal_data = await journal_repo.get_all_entries()
                backup_data['data']['journal_entries'] = [
                    entry.to_dict() for entry in journal_data
                ]
            
            # Add statistics
            backup_data['metadata']['statistics'] = {
                'weather_records': len(backup_data['data']['weather_history']),
                'preference_records': len(backup_data['data']['user_preferences']),
                'activity_records': len(backup_data['data']['activity_log']),
                'journal_records': len(backup_data['data']['journal_entries'])
            }
            
        except Exception as e:
            self._logger.error(f"Failed to create backup data: {e}")
            raise
        
        return backup_data
    
    async def _get_database_version(self) -> Optional[str]:
        """Get current database version.
        
        Returns:
            Optional[str]: Database version
        """
        try:
            from .migration_manager import MigrationManager
            migration_manager = MigrationManager(self._db_manager)
            return await migration_manager.get_current_version()
        except Exception:
            return None
    
    async def restore_backup(self, backup_file: Path, validate_only: bool = False) -> bool:
        """Restore database from backup.
        
        Args:
            backup_file: Path to backup file
            validate_only: If True, only validate backup without restoring
            
        Returns:
            bool: True if restoration was successful
        """
        try:
            # Load backup data
            backup_data = await self._load_backup_file(backup_file)
            
            if backup_data is None:
                return False
            
            # Validate backup
            if not self._validate_backup_data(backup_data):
                self._logger.error("Backup validation failed")
                return False
            
            if validate_only:
                self._logger.info("Backup validation successful")
                return True
            
            # Create pre-restore backup
            pre_restore_backup = await self.create_backup("pre_restore_" + 
                datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            if pre_restore_backup is None:
                self._logger.warning("Failed to create pre-restore backup")
            
            # Restore data
            await self._restore_backup_data(backup_data)
            
            self._logger.info(f"Successfully restored backup from {backup_file}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to restore backup: {e}")
            return False
    
    async def _load_backup_file(self, backup_file: Path) -> Optional[Dict]:
        """Load backup data from file.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Optional[Dict]: Backup data or None if failed
        """
        try:
            if not backup_file.exists():
                self._logger.error(f"Backup file not found: {backup_file}")
                return None
            
            # Handle compressed files
            if backup_file.suffix == '.gz':
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
        except Exception as e:
            self._logger.error(f"Failed to load backup file: {e}")
            return None
    
    def _validate_backup_data(self, backup_data: Dict) -> bool:
        """Validate backup data structure.
        
        Args:
            backup_data: Backup data to validate
            
        Returns:
            bool: True if backup is valid
        """
        try:
            # Check required structure
            if 'metadata' not in backup_data or 'data' not in backup_data:
                return False
            
            metadata = backup_data['metadata']
            data = backup_data['data']
            
            # Check metadata
            required_metadata = ['version', 'created_at', 'backup_type']
            if not all(key in metadata for key in required_metadata):
                return False
            
            # Check data sections
            expected_sections = [
                'weather_history', 'user_preferences', 
                'activity_log', 'journal_entries'
            ]
            
            for section in expected_sections:
                if section not in data:
                    self._logger.warning(f"Missing data section: {section}")
                elif not isinstance(data[section], list):
                    self._logger.error(f"Invalid data section format: {section}")
                    return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"Backup validation error: {e}")
            return False
    
    async def _restore_backup_data(self, backup_data: Dict) -> None:
        """Restore data from backup.
        
        Args:
            backup_data: Validated backup data
        """
        data = backup_data['data']
        
        try:
            # Clear existing data (with confirmation in production)
            await self._clear_database()
            
            # Restore weather history
            if 'weather_history' in data:
                for record_data in data['weather_history']:
                    await self._weather_repo.save_weather_data(
                        location=record_data['location'],
                        temperature=record_data['temperature'],
                        conditions=record_data['conditions'],
                        humidity=record_data.get('humidity'),
                        wind_speed=record_data.get('wind_speed'),
                        pressure=record_data.get('pressure'),
                        timestamp=datetime.fromisoformat(record_data['timestamp'])
                    )
            
            # Restore user preferences
            if 'user_preferences' in data:
                for pref_data in data['user_preferences']:
                    await self._prefs_repo.save_preference(
                        user_id=pref_data['user_id'],
                        key=pref_data['preference_key'],
                        value=pref_data['preference_value']
                    )
            
            # Restore activity log
            if 'activity_log' in data:
                for activity_data in data['activity_log']:
                    await self._activity_repo.log_activity(
                        user_id=activity_data['user_id'],
                        activity_type=activity_data['activity_type'],
                        activity_data=activity_data['activity_data'],
                        location=activity_data.get('location'),
                        timestamp=datetime.fromisoformat(activity_data['selected_at'])
                    )
            
            # Restore journal entries
            if 'journal_entries' in data:
                for journal_data in data['journal_entries']:
                    await self._journal_repo.create_entry(
                        user_id=journal_data['user_id'],
                        mood_score=journal_data['mood_score'],
                        notes=journal_data['notes'],
                        weather_snapshot=journal_data['weather_snapshot'],
                        entry_date=datetime.fromisoformat(journal_data['entry_date'])
                    )
            
            self._logger.info("Database restoration completed")
            
        except Exception as e:
            self._logger.error(f"Failed to restore backup data: {e}")
            raise
    
    async def _clear_database(self) -> None:
        """Clear all data from database tables."""
        try:
            async with self._db_manager.get_async_session() as session:
                # Clear tables in correct order (respecting foreign keys)
                tables = [
                    'journal_entries',
                    'activity_log', 
                    'weather_history',
                    'user_preferences'
                ]
                
                for table in tables:
                    await session.execute(f"DELETE FROM {table}")
                
                await session.commit()
                
        except Exception as e:
            self._logger.error(f"Failed to clear database: {e}")
            raise
    
    async def _rotate_backups(self) -> None:
        """Remove old backups to maintain rotation limit."""
        try:
            # Get all backup files
            backup_files = list(self._backup_dir.glob("weather_dashboard_backup_*.json*"))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            if len(backup_files) > self._max_backups:
                for old_backup in backup_files[self._max_backups:]:
                    old_backup.unlink()
                    self._logger.info(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            self._logger.error(f"Failed to rotate backups: {e}")
    
    def list_backups(self) -> List[Dict]:
        """List available backups.
        
        Returns:
            List[Dict]: Backup information
        """
        try:
            backup_files = list(self._backup_dir.glob("*.json*"))
            backups = []
            
            for backup_file in backup_files:
                stat = backup_file.stat()
                
                backup_info = {
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'compressed': backup_file.suffix == '.gz'
                }
                
                backups.append(backup_info)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            self._logger.error(f"Failed to list backups: {e}")
            return []
    
    async def cleanup_old_backups(self, days: int = 30) -> int:
        """Clean up backups older than specified days.
        
        Args:
            days: Number of days to keep backups
            
        Returns:
            int: Number of backups removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            backup_files = list(self._backup_dir.glob("*.json*"))
            
            removed_count = 0
            
            for backup_file in backup_files:
                file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    self._logger.info(f"Removed old backup: {backup_file}")
            
            return removed_count
            
        except Exception as e:
            self._logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    async def get_backup_info(self, backup_file: Path) -> Optional[Dict]:
        """Get detailed information about a backup.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Optional[Dict]: Backup information
        """
        try:
            backup_data = await self._load_backup_file(backup_file)
            
            if backup_data is None:
                return None
            
            stat = backup_file.stat()
            
            info = {
                'file_info': {
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'compressed': backup_file.suffix == '.gz'
                },
                'metadata': backup_data.get('metadata', {}),
                'statistics': backup_data.get('metadata', {}).get('statistics', {}),
                'valid': self._validate_backup_data(backup_data)
            }
            
            return info
            
        except Exception as e:
            self._logger.error(f"Failed to get backup info: {e}")
            return None
    
    def set_backup_settings(self, max_backups: int = 5, compression: bool = True) -> None:
        """Update backup settings.
        
        Args:
            max_backups: Maximum number of backups to keep
            compression: Whether to compress backups
        """
        self._max_backups = max_backups
        self._compression_enabled = compression
        self._logger.info(f"Updated backup settings: max={max_backups}, compression={compression}")
    
    async def schedule_automatic_backup(self) -> bool:
        """Create an automatic backup if needed.
        
        Returns:
            bool: True if backup was created
        """
        try:
            # Check if we need a backup (daily)
            backups = self.list_backups()
            
            if backups:
                latest_backup = backups[0]
                time_since_backup = datetime.now() - latest_backup['created']
                
                # Skip if backup was created in last 24 hours
                if time_since_backup < timedelta(hours=24):
                    return False
            
            # Create automatic backup
            backup_file = await self.create_backup("auto_" + 
                datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            return backup_file is not None
            
        except Exception as e:
            self._logger.error(f"Failed to create automatic backup: {e}")
            return False