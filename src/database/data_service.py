"""Data service for weather dashboard.

Provides high-level interface for all data operations.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .database_manager import DatabaseManager
from .repositories import (
    WeatherRepository, PreferencesRepository,
    ActivityRepository, JournalRepository
)
from .migration_manager import MigrationManager
from .backup_manager import BackupManager
from .cache_manager import CacheManager
from .export_import_manager import ExportImportManager, ConflictResolution


class DataService:
    """High-level data service for the weather dashboard."""
    
    def __init__(self, database_path: Optional[Path] = None):
        """Initialize data service.
        
        Args:
            database_path: Optional custom database path
        """
        self._logger = logging.getLogger(__name__)
        
        # Initialize database manager
        if database_path is None:
            database_path = Path("data/weather_dashboard.db")
        
        self._db_manager = DatabaseManager(database_path)
        
        # Repository instances will be created with sessions when needed
        self._weather_repo = None
        self._prefs_repo = None
        self._activity_repo = None
        self._journal_repo = None
        
        # Initialize managers
        self._migration_manager = MigrationManager(self._db_manager)
        self._backup_manager = BackupManager(self._db_manager)
        self._cache_manager = CacheManager()
        self._export_import_manager = ExportImportManager(self._db_manager)
        
        # Service state
        self._initialized = False
        self._background_tasks = set()
    
    @asynccontextmanager
    async def _get_repositories(self):
        """Get repository instances with database session.
        
        Yields:
            Tuple of (weather_repo, prefs_repo, activity_repo, journal_repo)
        """
        async with self._db_manager.get_async_session() as session:
            weather_repo = WeatherRepository(session)
            prefs_repo = PreferencesRepository(session)
            activity_repo = ActivityRepository(session)
            journal_repo = JournalRepository(session)
            
            yield weather_repo, prefs_repo, activity_repo, journal_repo
    
    async def initialize(self) -> bool:
        """Initialize the data service.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            if self._initialized:
                return True
            
            self._logger.info("Initializing data service...")
            
            # Initialize database
            await self._db_manager.initialize()
            
            # Run migrations
            migration_result = await self._migration_manager.apply_pending_migrations()
            if not migration_result:
                self._logger.error("Migration failed")
                return False
            
            # Initialize cache
            await self._cache_manager.initialize()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self._initialized = True
            self._logger.info("Data service initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize data service: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the data service."""
        try:
            self._logger.info("Shutting down data service...")
            
            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()
            
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            # Save cache
            self._cache_manager.save_to_file()
            
            # Close database connections
            await self._db_manager.close()
            
            self._initialized = False
            self._logger.info("Data service shutdown complete")
            
        except Exception as e:
            self._logger.error(f"Error during shutdown: {e}")
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks."""
        # Cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_task())
        self._background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self._background_tasks.discard)
        
        # Backup task
        backup_task = asyncio.create_task(self._backup_task())
        self._background_tasks.add(backup_task)
        backup_task.add_done_callback(self._background_tasks.discard)
        
        # Cache maintenance task
        cache_task = asyncio.create_task(self._cache_maintenance_task())
        self._background_tasks.add(cache_task)
        cache_task.add_done_callback(self._background_tasks.discard)
    
    async def _cleanup_task(self):
        """Background task for data cleanup."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean old weather data (older than 1 year)
                cutoff_date = datetime.now() - timedelta(days=365)
                await self._weather_repo.cleanup_old_data(cutoff_date)
                
                # Clean old activity logs (older than 6 months)
                cutoff_date = datetime.now() - timedelta(days=180)
                await self._activity_repo.cleanup_old_activities(cutoff_date)
                
                self._logger.debug("Data cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cleanup task: {e}")
    
    async def _backup_task(self):
        """Background task for automated backups."""
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                
                # Create daily backup
                backup_name = f"daily_{datetime.now().strftime('%Y%m%d')}"
                await self._backup_manager.create_backup(backup_name)
                
                # Clean old backups
                await self._backup_manager.cleanup_old_backups()
                
                self._logger.debug("Automated backup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in backup task: {e}")
    
    async def _cache_maintenance_task(self):
        """Background task for cache maintenance."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean expired cache entries
                self._cache_manager.cleanup_expired()
                
                # Save cache periodically
                await self._cache_manager.save_to_file()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cache maintenance task: {e}")
    
    # Weather data methods
    async def save_weather_data(self, 
                              location: str,
                              temperature: float,
                              conditions: str,
                              **kwargs) -> bool:
        """Save weather data.
        
        Args:
            location: Location name
            temperature: Temperature value
            conditions: Weather conditions
            **kwargs: Additional weather data
            
        Returns:
            bool: True if save was successful
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                weather_data = {
                    'location': location,
                    'temperature': temperature,
                    'conditions': conditions,
                    **kwargs
                }
                await weather_repo.save_weather_data(weather_data)
            
            # Invalidate related cache entries
            cache_key = f"weather_history_{location}"
            self._cache_manager.delete(cache_key)
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to save weather data: {e}")
            return False
    
    async def get_weather_history(self, 
                                location: str,
                                days: int = 30,
                                use_cache: bool = True) -> List[Dict]:
        """Get weather history for a location.
        
        Args:
            location: Location name
            days: Number of days to retrieve
            use_cache: Whether to use cache
            
        Returns:
            List[Dict]: Weather history records
        """
        cache_key = f"weather_history_{location}_{days}"
        
        if use_cache:
            cached_data = self._cache_manager.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            records = await self._weather_repo.get_location_history(
                location=location,
                start_date=start_date
            )
            
            result = [record.to_dict() for record in records]
            
            if use_cache:
                # Cache for 1 hour
                self._cache_manager.set(cache_key, result, ttl=3600)
            
            return result
            
        except Exception as e:
            self._logger.error(f"Failed to get weather history: {e}")
            return []
    
    async def get_weather_statistics(self, location: str) -> Dict[str, Any]:
        """Get weather statistics for a location.
        
        Args:
            location: Location name
            
        Returns:
            Dict[str, Any]: Weather statistics
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                return await weather_repo.get_weather_statistics(location)
        except Exception as e:
            self._logger.error(f"Failed to get weather statistics: {e}")
            return {}
    
    # User preferences methods
    async def save_user_preference(self, 
                                 user_id: str,
                                 key: str,
                                 value: Any) -> bool:
        """Save user preference.
        
        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
            
        Returns:
            bool: True if save was successful
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                await prefs_repo.save_preference(key, value, user_id)
            
            # Invalidate cache
            cache_key = f"user_prefs_{user_id}"
            self._cache_manager.delete(cache_key)
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to save user preference: {e}")
            return False
    
    async def get_user_preferences(self, 
                                 user_id: str,
                                 use_cache: bool = True) -> Dict[str, Any]:
        """Get user preferences.
        
        Args:
            user_id: User ID
            use_cache: Whether to use cache
            
        Returns:
            Dict[str, Any]: User preferences
        """
        cache_key = f"user_prefs_{user_id}"
        
        if use_cache:
            cached_data = self._cache_manager.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            preferences = await self._prefs_repo.get_user_preferences(user_id)
            result = {pref.preference_key: pref.preference_value for pref in preferences}
            
            if use_cache:
                # Cache for 30 minutes
                self._cache_manager.set(cache_key, result, ttl=1800)
            
            return result
            
        except Exception as e:
            self._logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    async def add_favorite_location(self, user_id: str, location: str) -> bool:
        """Add favorite location for user.
        
        Args:
            user_id: User ID
            location: Location to add
            
        Returns:
            bool: True if add was successful
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                await prefs_repo.add_favorite_location(location, user_id)
                return True
        except Exception as e:
            self._logger.error(f"Failed to add favorite location: {e}")
            return False
    
    async def get_favorite_locations(self, user_id: str) -> List[str]:
        """Get user's favorite locations.
        
        Args:
            user_id: User ID
            
        Returns:
            List[str]: Favorite locations
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                preferences = await prefs_repo.get_preferences(user_id)
                return preferences.favorite_locations if preferences else []
        except Exception as e:
            self._logger.error(f"Failed to get favorite locations: {e}")
            return []
    
    async def add_recent_search(self, user_id: str, search_term: str) -> bool:
        """Add recent search for user.
        
        Args:
            user_id: User ID
            search_term: Search term
            
        Returns:
            bool: True if add was successful
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                await prefs_repo.add_recent_search(search_term, user_id)
                return True
        except Exception as e:
            self._logger.error(f"Failed to add recent search: {e}")
            return False
    
    async def get_recent_searches(self, user_id: str, limit: int = 10) -> List[str]:
        """Get user's recent searches.
        
        Args:
            user_id: User ID
            limit: Maximum number of searches to return
            
        Returns:
            List[str]: Recent searches
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                preferences = await prefs_repo.get_preferences(user_id)
                searches = preferences.recent_searches if preferences else []
                return searches[:limit]
        except Exception as e:
            self._logger.error(f"Failed to get recent searches: {e}")
            return []
    
    # Activity logging methods
    async def log_activity(self, 
                         user_id: str,
                         activity_type: str,
                         activity_data: Dict[str, Any],
                         location: Optional[str] = None) -> bool:
        """Log user activity.
        
        Args:
            user_id: User ID
            activity_type: Type of activity
            activity_data: Activity data
            location: Optional location
            
        Returns:
            bool: True if log was successful
        """
        try:
            await self._activity_repo.log_activity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                location=location
            )
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to log activity: {e}")
            return False
    
    async def get_user_activities(self, 
                                user_id: str,
                                days: int = 30) -> List[Dict]:
        """Get user activities.
        
        Args:
            user_id: User ID
            days: Number of days to retrieve
            
        Returns:
            List[Dict]: User activities
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            activities = await self._activity_repo.get_user_activities(
                user_id=user_id,
                start_date=start_date
            )
            return [activity.to_dict() for activity in activities]
            
        except Exception as e:
            self._logger.error(f"Failed to get user activities: {e}")
            return []
    
    async def get_activity_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get activity statistics for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: Activity statistics
        """
        try:
            async with self._get_repositories() as (weather_repo, prefs_repo, activity_repo, journal_repo):
                return await activity_repo.get_activity_statistics(user_id)
        except Exception as e:
            self._logger.error(f"Failed to get activity statistics: {e}")
            return {}
    
    # Journal methods
    async def create_journal_entry(self, 
                                 user_id: str,
                                 mood_score: float,
                                 notes: str = "",
                                 weather_snapshot: Optional[Dict] = None) -> bool:
        """Create journal entry.
        
        Args:
            user_id: User ID
            mood_score: Mood score (1-10)
            notes: Optional notes
            weather_snapshot: Optional weather data
            
        Returns:
            bool: True if creation was successful
        """
        try:
            await self._journal_repo.create_entry(
                user_id=user_id,
                mood_score=mood_score,
                notes=notes,
                weather_snapshot=weather_snapshot or {}
            )
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to create journal entry: {e}")
            return False
    
    async def get_journal_entries(self, 
                                user_id: str,
                                days: int = 30) -> List[Dict]:
        """Get journal entries for user.
        
        Args:
            user_id: User ID
            days: Number of days to retrieve
            
        Returns:
            List[Dict]: Journal entries
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            entries = await self._journal_repo.get_user_entries(
                user_id=user_id,
                start_date=start_date
            )
            return [entry.to_dict() for entry in entries]
            
        except Exception as e:
            self._logger.error(f"Failed to get journal entries: {e}")
            return []
    
    async def get_mood_trends(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get mood trends for user.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dict[str, Any]: Mood trends
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            return await self._journal_repo.get_mood_trends(
                user_id=user_id,
                start_date=start_date
            )
        except Exception as e:
            self._logger.error(f"Failed to get mood trends: {e}")
            return {}
    
    # Data management methods
    async def export_data(self, 
                        export_file: Path,
                        user_id: Optional[str] = None,
                        tables: Optional[List[str]] = None,
                        date_range: Optional[Tuple[datetime, datetime]] = None) -> bool:
        """Export data to file.
        
        Args:
            export_file: Export file path
            user_id: Optional user ID filter
            tables: Optional table filter
            date_range: Optional date range filter
            
        Returns:
            bool: True if export was successful
        """
        return await self._export_import_manager.export_data(
            export_file=export_file,
            tables=tables,
            date_range=date_range,
            user_id=user_id
        )
    
    async def import_data(self, 
                        import_file: Path,
                        conflict_resolution: str = ConflictResolution.SKIP,
                        validate_only: bool = False) -> Dict[str, Any]:
        """Import data from file.
        
        Args:
            import_file: Import file path
            conflict_resolution: How to handle conflicts
            validate_only: If True, only validate without importing
            
        Returns:
            Dict[str, Any]: Import results
        """
        return await self._export_import_manager.import_data(
            import_file=import_file,
            conflict_resolution=conflict_resolution,
            validate_only=validate_only
        )
    
    async def create_backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """Create database backup.
        
        Args:
            backup_name: Optional backup name
            
        Returns:
            Optional[Path]: Backup file path if successful
        """
        return await self._backup_manager.create_backup(backup_name)
    
    async def restore_backup(self, backup_file: Path) -> bool:
        """Restore database from backup.
        
        Args:
            backup_file: Backup file path
            
        Returns:
            bool: True if restore was successful
        """
        return await self._backup_manager.restore_backup(backup_file)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups.
        
        Returns:
            List[Dict[str, Any]]: Backup information
        """
        return self._backup_manager.list_backups()
    
    # Cache management methods
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        return self._cache_manager.get_statistics()
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries.
        
        Args:
            pattern: Optional pattern to match keys
        """
        if pattern:
            # Clear matching keys
            keys_to_delete = [
                key for key in self._cache_manager._cache.keys()
                if pattern in key
            ]
            for key in keys_to_delete:
                self._cache_manager.delete(key)
        else:
            # Clear all
            self._cache_manager.clear()
    
    def configure_cache(self, 
                       max_size: Optional[int] = None,
                       default_ttl: Optional[int] = None):
        """Configure cache settings.
        
        Args:
            max_size: Maximum cache size
            default_ttl: Default TTL in seconds
        """
        self._cache_manager.configure(
            max_size=max_size,
            default_ttl=default_ttl
        )
    
    # Database management methods
    async def get_database_info(self) -> Dict[str, Any]:
        """Get database information.
        
        Returns:
            Dict[str, Any]: Database information
        """
        return await self._db_manager.get_database_info()
    
    async def vacuum_database(self) -> bool:
        """Vacuum the database to reclaim space.
        
        Returns:
            bool: True if vacuum was successful
        """
        try:
            await self._db_manager.execute_raw_sql("VACUUM")
            self._logger.info("Database vacuum completed")
            return True
        except Exception as e:
            self._logger.error(f"Failed to vacuum database: {e}")
            return False
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status.
        
        Returns:
            Dict[str, Any]: Migration status
        """
        return await self._migration_manager.get_migration_status()
    
    # Health check methods
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on data service.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        health = {
            'status': 'healthy',
            'initialized': self._initialized,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        try:
            # Check database
            db_info = await self._db_manager.get_database_info()
            health['components']['database'] = {
                'status': 'healthy',
                'size': db_info.get('size', 0),
                'tables': len(db_info.get('tables', []))
            }
        except Exception as e:
            health['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'degraded'
        
        try:
            # Check cache
            cache_stats = self._cache_manager.get_statistics()
            health['components']['cache'] = {
                'status': 'healthy',
                'entries': cache_stats['entries'],
                'hit_rate': cache_stats['hit_rate']
            }
        except Exception as e:
            health['components']['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'degraded'
        
        # Check background tasks
        active_tasks = len([t for t in self._background_tasks if not t.done()])
        health['components']['background_tasks'] = {
            'status': 'healthy',
            'active_tasks': active_tasks
        }
        
        return health