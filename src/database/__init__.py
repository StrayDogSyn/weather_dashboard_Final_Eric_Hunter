"""Database module for weather dashboard persistence.

Provides SQLite database with proper schema, repositories, and data management."""

# Models
from .models import (
    Base, WeatherHistory, UserPreferences, 
    ActivityLog, JournalEntry, DatabaseMigration
)

# Repositories
from .repositories import (
    BaseRepository, WeatherRepository, PreferencesRepository,
    ActivityRepository, JournalRepository
)

# Managers
from .database_manager import DatabaseManager
from .migration_manager import MigrationManager
from .backup_manager import BackupManager
from .cache_manager import CacheManager
from .export_import_manager import ExportImportManager, ConflictResolution

# Main service
from .data_service import DataService

__all__ = [
    # Models
    'Base', 'WeatherHistory', 'UserPreferences', 
    'ActivityLog', 'JournalEntry', 'DatabaseMigration',
    
    # Repositories
    'BaseRepository', 'WeatherRepository', 'PreferencesRepository',
    'ActivityRepository', 'JournalRepository',
    
    # Managers
    'DatabaseManager', 'MigrationManager', 'BackupManager', 'CacheManager',
    'ExportImportManager', 'ConflictResolution',
    
    # Main service
    'DataService'
]