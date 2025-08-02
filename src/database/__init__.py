"""Database module for weather dashboard persistence.

Provides SQLite database with proper schema, repositories, and data management."""

from .backup_manager import BackupManager
from .cache_manager import CacheManager

# Main service
from .data_service import DataService

# Managers
from .database_manager import DatabaseManager
from .export_import_manager import ConflictResolution, ExportImportManager
from .migration_manager import MigrationManager

# Models
from .models import (
    ActivityLog,
    Base,
    DatabaseMigration,
    JournalEntry,
    UserPreferences,
    WeatherHistory,
)

# Repositories
from .repositories import (
    ActivityRepository,
    BaseRepository,
    JournalRepository,
    PreferencesRepository,
    WeatherRepository,
)

__all__ = [
    # Models
    "Base",
    "WeatherHistory",
    "UserPreferences",
    "ActivityLog",
    "JournalEntry",
    "DatabaseMigration",
    # Repositories
    "BaseRepository",
    "WeatherRepository",
    "PreferencesRepository",
    "ActivityRepository",
    "JournalRepository",
    # Managers
    "DatabaseManager",
    "MigrationManager",
    "BackupManager",
    "CacheManager",
    "ExportImportManager",
    "ConflictResolution",
    # Main service
    "DataService",
]
