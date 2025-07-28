"""Database operations for team collaboration feature.

This module handles all data persistence and retrieval operations for the
team collaboration system, including local storage and GitHub synchronization.
"""

import json
import os
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path

from .models import (
    TeamMember, CityData, TeamComparison, ActivityItem, SyncStatus,
    CollaborationConfig
)
from ...utils.logger import LoggerMixin


class CollaborationDatabase(LoggerMixin):
    """Database manager for team collaboration data."""
    
    def __init__(self, data_dir: str = None):
        """Initialize database.
        
        Args:
            data_dir: Directory for local data storage
        """
        LoggerMixin.__init__(self)
        
        # Set up data directory
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".weather_dashboard", "collaboration")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.config_file = self.data_dir / "config.json"
        self.cities_file = self.data_dir / "cities.json"
        self.comparisons_file = self.data_dir / "comparisons.json"
        self.members_file = self.data_dir / "members.json"
        self.activity_file = self.data_dir / "activity.json"
        self.sync_status_file = self.data_dir / "sync_status.json"
        
        # Thread lock for file operations
        self._file_lock = threading.Lock()
        
        # In-memory cache
        self._config_cache: Optional[CollaborationConfig] = None
        self._cities_cache: Optional[List[CityData]] = None
        self._comparisons_cache: Optional[List[TeamComparison]] = None
        self._members_cache: Optional[List[TeamMember]] = None
        self._activity_cache: Optional[List[ActivityItem]] = None
        self._sync_status_cache: Optional[SyncStatus] = None
        
        # Cache timestamps
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        
        age = datetime.now() - self._cache_timestamps[cache_key]
        return age.total_seconds() < self._cache_ttl

    def _update_cache_timestamp(self, cache_key: str):
        """Update cache timestamp."""
        self._cache_timestamps[cache_key] = datetime.now()

    def _load_json_file(self, file_path: Path, default_value: Any = None) -> Any:
        """Load data from JSON file safely."""
        try:
            with self._file_lock:
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    return default_value if default_value is not None else {}
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return default_value if default_value is not None else {}

    def _save_json_file(self, file_path: Path, data: Any) -> bool:
        """Save data to JSON file safely."""
        try:
            with self._file_lock:
                # Create backup of existing file
                backup_path = file_path.with_suffix('.bak')
                if file_path.exists():
                    file_path.replace(backup_path)
                
                # Write new data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
                # Remove backup on success
                if backup_path.exists():
                    backup_path.unlink()
                
                return True
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")
            
            # Restore backup if available
            backup_path = file_path.with_suffix('.bak')
            if backup_path.exists():
                try:
                    backup_path.replace(file_path)
                    self.logger.info(f"Restored backup for {file_path}")
                except Exception as restore_error:
                    self.logger.error(f"Error restoring backup: {restore_error}")
            
            return False

    # Configuration methods
    def load_config(self) -> CollaborationConfig:
        """Load collaboration configuration."""
        if self._config_cache and self._is_cache_valid('config'):
            return self._config_cache
        
        data = self._load_json_file(self.config_file)
        
        try:
            self._config_cache = CollaborationConfig.from_dict(data) if data else CollaborationConfig()
        except Exception as e:
            self.logger.error(f"Error parsing config: {e}")
            self._config_cache = CollaborationConfig()
        
        self._update_cache_timestamp('config')
        return self._config_cache

    def save_config(self, config: CollaborationConfig) -> bool:
        """Save collaboration configuration."""
        success = self._save_json_file(self.config_file, config.to_dict())
        if success:
            self._config_cache = config
            self._update_cache_timestamp('config')
        return success

    # Cities methods
    def load_cities(self) -> List[CityData]:
        """Load shared cities data."""
        if self._cities_cache and self._is_cache_valid('cities'):
            return self._cities_cache.copy()
        
        data = self._load_json_file(self.cities_file, [])
        
        cities = []
        for city_dict in data:
            try:
                cities.append(CityData.from_dict(city_dict))
            except Exception as e:
                self.logger.warning(f"Skipping invalid city data: {e}")
        
        self._cities_cache = cities
        self._update_cache_timestamp('cities')
        return cities.copy()

    def save_cities(self, cities: List[CityData]) -> bool:
        """Save shared cities data."""
        data = [city.to_dict() for city in cities]
        success = self._save_json_file(self.cities_file, data)
        if success:
            self._cities_cache = cities.copy()
            self._update_cache_timestamp('cities')
        return success

    def add_city(self, city: CityData) -> bool:
        """Add a new city to the database."""
        cities = self.load_cities()
        
        # Check for duplicates
        for existing_city in cities:
            if (existing_city.city_name == city.city_name and 
                existing_city.country == city.country):
                # Update existing city instead
                existing_city.current_weather = city.current_weather
                existing_city.last_updated = datetime.now()
                existing_city.tags = list(set(existing_city.tags + city.tags))
                if city.description:
                    existing_city.description = city.description
                return self.save_cities(cities)
        
        cities.append(city)
        return self.save_cities(cities)

    def remove_city(self, city_id: str) -> bool:
        """Remove a city from the database."""
        cities = self.load_cities()
        cities = [city for city in cities if city.id != city_id]
        return self.save_cities(cities)

    def find_cities(self, search_term: str = "", favorites_only: bool = False) -> List[CityData]:
        """Find cities matching search criteria."""
        cities = self.load_cities()
        
        # Filter by favorites
        if favorites_only:
            cities = [city for city in cities if city.is_favorite]
        
        # Filter by search term
        if search_term:
            cities = [city for city in cities if city.matches_search(search_term)]
        
        # Sort by last updated (most recent first)
        cities.sort(key=lambda x: x.last_updated or x.shared_at, reverse=True)
        
        return cities

    # Comparisons methods
    def load_comparisons(self) -> List[TeamComparison]:
        """Load team comparisons data."""
        if self._comparisons_cache and self._is_cache_valid('comparisons'):
            return self._comparisons_cache.copy()
        
        data = self._load_json_file(self.comparisons_file, [])
        
        comparisons = []
        for comp_dict in data:
            try:
                comparisons.append(TeamComparison.from_dict(comp_dict))
            except Exception as e:
                self.logger.warning(f"Skipping invalid comparison data: {e}")
        
        self._comparisons_cache = comparisons
        self._update_cache_timestamp('comparisons')
        return comparisons.copy()

    def save_comparisons(self, comparisons: List[TeamComparison]) -> bool:
        """Save team comparisons data."""
        data = [comp.to_dict() for comp in comparisons]
        success = self._save_json_file(self.comparisons_file, data)
        if success:
            self._comparisons_cache = comparisons.copy()
            self._update_cache_timestamp('comparisons')
        return success

    def add_comparison(self, comparison: TeamComparison) -> bool:
        """Add a new comparison to the database."""
        comparisons = self.load_comparisons()
        comparisons.append(comparison)
        return self.save_comparisons(comparisons)

    def remove_comparison(self, comparison_id: str) -> bool:
        """Remove a comparison from the database."""
        comparisons = self.load_comparisons()
        comparisons = [comp for comp in comparisons if comp.id != comparison_id]
        return self.save_comparisons(comparisons)

    def update_comparison(self, comparison: TeamComparison) -> bool:
        """Update an existing comparison."""
        comparisons = self.load_comparisons()
        
        for i, existing_comp in enumerate(comparisons):
            if existing_comp.id == comparison.id:
                comparisons[i] = comparison
                return self.save_comparisons(comparisons)
        
        # If not found, add as new
        return self.add_comparison(comparison)

    # Team members methods
    def load_members(self) -> List[TeamMember]:
        """Load team members data."""
        if self._members_cache and self._is_cache_valid('members'):
            return self._members_cache.copy()
        
        data = self._load_json_file(self.members_file, [])
        
        members = []
        for member_dict in data:
            try:
                members.append(TeamMember.from_dict(member_dict))
            except Exception as e:
                self.logger.warning(f"Skipping invalid member data: {e}")
        
        self._members_cache = members
        self._update_cache_timestamp('members')
        return members.copy()

    def save_members(self, members: List[TeamMember]) -> bool:
        """Save team members data."""
        data = [member.to_dict() for member in members]
        success = self._save_json_file(self.members_file, data)
        if success:
            self._members_cache = members.copy()
            self._update_cache_timestamp('members')
        return success

    def update_member(self, member: TeamMember) -> bool:
        """Update or add a team member."""
        members = self.load_members()
        
        for i, existing_member in enumerate(members):
            if existing_member.id == member.id:
                members[i] = member
                return self.save_members(members)
        
        # If not found, add as new
        members.append(member)
        return self.save_members(members)

    # Activity methods
    def load_activity(self, days: int = 30) -> List[ActivityItem]:
        """Load team activity data."""
        if self._activity_cache and self._is_cache_valid('activity'):
            activities = self._activity_cache.copy()
        else:
            data = self._load_json_file(self.activity_file, [])
            
            activities = []
            for activity_dict in data:
                try:
                    activities.append(ActivityItem.from_dict(activity_dict))
                except Exception as e:
                    self.logger.warning(f"Skipping invalid activity data: {e}")
            
            self._activity_cache = activities
            self._update_cache_timestamp('activity')
        
        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_activities = [
            activity for activity in activities 
            if activity.timestamp >= cutoff_date
        ]
        
        # Sort by timestamp (most recent first)
        filtered_activities.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_activities

    def save_activity(self, activities: List[ActivityItem]) -> bool:
        """Save team activity data."""
        data = [activity.to_dict() for activity in activities]
        success = self._save_json_file(self.activity_file, data)
        if success:
            self._activity_cache = activities.copy()
            self._update_cache_timestamp('activity')
        return success

    def add_activity(self, activity: ActivityItem) -> bool:
        """Add a new activity item."""
        activities = self.load_activity(days=365)  # Load full year for adding
        activities.append(activity)
        
        # Keep only recent activities to prevent file growth
        cutoff_date = datetime.now() - timedelta(days=90)
        activities = [a for a in activities if a.timestamp >= cutoff_date]
        
        return self.save_activity(activities)

    # Sync status methods
    def load_sync_status(self) -> SyncStatus:
        """Load synchronization status."""
        if self._sync_status_cache and self._is_cache_valid('sync_status'):
            return self._sync_status_cache
        
        data = self._load_json_file(self.sync_status_file)
        
        try:
            self._sync_status_cache = SyncStatus.from_dict(data) if data else SyncStatus()
        except Exception as e:
            self.logger.error(f"Error parsing sync status: {e}")
            self._sync_status_cache = SyncStatus()
        
        self._update_cache_timestamp('sync_status')
        return self._sync_status_cache

    def save_sync_status(self, sync_status: SyncStatus) -> bool:
        """Save synchronization status."""
        success = self._save_json_file(self.sync_status_file, sync_status.to_dict())
        if success:
            self._sync_status_cache = sync_status
            self._update_cache_timestamp('sync_status')
        return success

    def update_sync_status(self, **kwargs) -> bool:
        """Update specific sync status fields."""
        sync_status = self.load_sync_status()
        
        for key, value in kwargs.items():
            if hasattr(sync_status, key):
                setattr(sync_status, key, value)
        
        return self.save_sync_status(sync_status)

    # Utility methods
    def clear_cache(self):
        """Clear all cached data."""
        self._config_cache = None
        self._cities_cache = None
        self._comparisons_cache = None
        self._members_cache = None
        self._activity_cache = None
        self._sync_status_cache = None
        self._cache_timestamps.clear()

    def export_all_data(self, export_path: str) -> bool:
        """Export all collaboration data to a single file."""
        try:
            export_data = {
                "config": self.load_config().to_dict(),
                "cities": [city.to_dict() for city in self.load_cities()],
                "comparisons": [comp.to_dict() for comp in self.load_comparisons()],
                "members": [member.to_dict() for member in self.load_members()],
                "activity": [activity.to_dict() for activity in self.load_activity(days=365)],
                "sync_status": self.load_sync_status().to_dict(),
                "exported_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return False

    def import_all_data(self, import_path: str, merge: bool = True) -> bool:
        """Import collaboration data from file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Import config
            if 'config' in import_data:
                try:
                    config = CollaborationConfig.from_dict(import_data['config'])
                    self.save_config(config)
                except Exception as e:
                    self.logger.warning(f"Error importing config: {e}")
            
            # Import cities
            if 'cities' in import_data:
                try:
                    imported_cities = [CityData.from_dict(city_dict) for city_dict in import_data['cities']]
                    
                    if merge:
                        existing_cities = self.load_cities()
                        # Merge without duplicates
                        existing_keys = {f"{c.city_name}_{c.country}" for c in existing_cities}
                        new_cities = [c for c in imported_cities 
                                    if f"{c.city_name}_{c.country}" not in existing_keys]
                        all_cities = existing_cities + new_cities
                    else:
                        all_cities = imported_cities
                    
                    self.save_cities(all_cities)
                except Exception as e:
                    self.logger.warning(f"Error importing cities: {e}")
            
            # Import comparisons
            if 'comparisons' in import_data:
                try:
                    imported_comparisons = [TeamComparison.from_dict(comp_dict) 
                                          for comp_dict in import_data['comparisons']]
                    
                    if merge:
                        existing_comparisons = self.load_comparisons()
                        existing_ids = {c.id for c in existing_comparisons}
                        new_comparisons = [c for c in imported_comparisons if c.id not in existing_ids]
                        all_comparisons = existing_comparisons + new_comparisons
                    else:
                        all_comparisons = imported_comparisons
                    
                    self.save_comparisons(all_comparisons)
                except Exception as e:
                    self.logger.warning(f"Error importing comparisons: {e}")
            
            # Import members
            if 'members' in import_data:
                try:
                    imported_members = [TeamMember.from_dict(member_dict) 
                                      for member_dict in import_data['members']]
                    
                    if merge:
                        existing_members = self.load_members()
                        existing_ids = {m.id for m in existing_members}
                        new_members = [m for m in imported_members if m.id not in existing_ids]
                        all_members = existing_members + new_members
                    else:
                        all_members = imported_members
                    
                    self.save_members(all_members)
                except Exception as e:
                    self.logger.warning(f"Error importing members: {e}")
            
            # Clear cache to reload imported data
            self.clear_cache()
            
            return True
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get database storage statistics."""
        stats = {
            "data_directory": str(self.data_dir),
            "total_size_mb": 0,
            "files": {}
        }
        
        try:
            for file_path in [self.config_file, self.cities_file, self.comparisons_file,
                            self.members_file, self.activity_file, self.sync_status_file]:
                if file_path.exists():
                    size = file_path.stat().st_size
                    stats["files"][file_path.name] = {
                        "size_bytes": size,
                        "size_kb": round(size / 1024, 2),
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
                    stats["total_size_mb"] += size
            
            stats["total_size_mb"] = round(stats["total_size_mb"] / (1024 * 1024), 2)
            
            # Add record counts
            stats["record_counts"] = {
                "cities": len(self.load_cities()),
                "comparisons": len(self.load_comparisons()),
                "members": len(self.load_members()),
                "activities": len(self.load_activity(days=365))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            stats["error"] = str(e)
        
        return stats