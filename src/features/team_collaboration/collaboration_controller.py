"""Business logic controller for team collaboration functionality.

This module handles the core business logic for team collaboration including
synchronization, data management, and team interactions.
"""

import uuid
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
import logging

from .models import CollaborationConfig, TeamActivity, SyncStatus, CollaborationSession


class CollaborationController:
    """Controller for managing team collaboration business logic."""

    def __init__(self, github_service, config: Optional[CollaborationConfig] = None):
        self.github_service = github_service
        self.config = config or CollaborationConfig()
        self.logger = logging.getLogger(__name__)

        # Data storage
        self.team_members: List = []
        self.shared_cities: List = []
        self.team_comparisons: List = []
        self.activities: List[TeamActivity] = []
        self.current_session: Optional[CollaborationSession] = None
        
        # Sync status
        self.sync_status = SyncStatus()
        
        # Auto-sync timer
        self.sync_timer = None
        
        # Callbacks
        self.on_data_updated: Optional[Callable] = None
        self.on_sync_completed: Optional[Callable] = None
        self.on_error: Optional[Callable[[str], None]] = None

    def start_collaboration_session(self, participants: List[str]) -> str:
        """Start a new collaboration session."""
        session_id = str(uuid.uuid4())
        self.current_session = CollaborationSession(
            session_id=session_id,
            participants=participants,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self._log_activity("session_started", f"Session {session_id}", 
                          details=f"Participants: {', '.join(participants)}")
        return session_id

    def end_collaboration_session(self):
        """End the current collaboration session."""
        if self.current_session:
            self._log_activity("session_ended", self.current_session.session_id)
            self.current_session = None

    def add_shared_city(self, city_data, user: str = "Unknown") -> bool:
        """Add a city to shared collaboration data."""
        try:
            if not self._is_city_already_shared(city_data.name):
                self.shared_cities.append(city_data)
                self._log_activity("city_added", city_data.name, user)
                self._trigger_sync()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error adding shared city: {e}")
            if self.on_error:
                self.on_error(f"Failed to add city: {e}")
            return False

    def remove_shared_city(self, city_name: str, user: str = "Unknown") -> bool:
        """Remove a city from shared data."""
        try:
            initial_count = len(self.shared_cities)
            self.shared_cities = [city for city in self.shared_cities if city.name != city_name]
            
            if len(self.shared_cities) < initial_count:
                self._log_activity("city_removed", city_name, user)
                self._trigger_sync()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing shared city: {e}")
            if self.on_error:
                self.on_error(f"Failed to remove city: {e}")
            return False

    def create_team_comparison(self, comparison_data, user: str = "Unknown") -> bool:
        """Create a new team comparison."""
        try:
            self.team_comparisons.append(comparison_data)
            self._log_activity("comparison_created", comparison_data.name, user)
            self._trigger_sync()
            return True
        except Exception as e:
            self.logger.error(f"Error creating comparison: {e}")
            if self.on_error:
                self.on_error(f"Failed to create comparison: {e}")
            return False

    def sync_with_remote(self) -> bool:
        """Synchronize data with remote GitHub repository."""
        if self.sync_status.is_syncing:
            return False
            
        self.sync_status.is_syncing = True
        self.sync_status.last_error = None
        
        try:
            # Push local data to GitHub
            self._push_data_to_github()
            
            # Pull remote data from GitHub
            self._pull_data_from_github()
            
            self.sync_status.last_sync = datetime.now()
            self.sync_status.pending_changes = 0
            
            if self.on_sync_completed:
                self.on_sync_completed()
                
            self.logger.info("Sync completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Sync failed: {e}"
            self.sync_status.last_error = error_msg
            self.logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg)
            return False
        finally:
            self.sync_status.is_syncing = False

    def start_auto_sync(self):
        """Start automatic synchronization."""
        if self.config.auto_sync and not self.sync_timer:
            self._schedule_next_sync()

    def stop_auto_sync(self):
        """Stop automatic synchronization."""
        if self.sync_timer:
            self.sync_timer.cancel()
            self.sync_timer = None

    def get_recent_activities(self, limit: int = 20) -> List[TeamActivity]:
        """Get recent team activities."""
        return sorted(self.activities, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get collaboration statistics."""
        now = datetime.now()
        recent_activities = [a for a in self.activities 
                           if now - a.timestamp < timedelta(days=7)]
        
        return {
            'total_cities': len(self.shared_cities),
            'total_comparisons': len(self.team_comparisons),
            'team_members': len(self.team_members),
            'recent_activities': len(recent_activities),
            'last_sync': self.sync_status.last_sync,
            'pending_changes': self.sync_status.pending_changes,
            'current_session': self.current_session.session_id if self.current_session else None
        }

    def search_cities(self, query: str) -> List:
        """Search shared cities by name or criteria."""
        query_lower = query.lower()
        return [city for city in self.shared_cities 
                if query_lower in city.name.lower()]

    def filter_comparisons(self, criteria: Dict[str, Any]) -> List:
        """Filter team comparisons by criteria."""
        filtered = self.team_comparisons
        
        if 'created_by' in criteria:
            filtered = [c for c in filtered if c.created_by == criteria['created_by']]
            
        if 'date_range' in criteria:
            start_date, end_date = criteria['date_range']
            filtered = [c for c in filtered 
                       if start_date <= c.created_at <= end_date]
                       
        return filtered

    def update_config(self, new_config: CollaborationConfig):
        """Update collaboration configuration."""
        old_auto_sync = self.config.auto_sync
        self.config = new_config
        
        # Restart auto-sync if setting changed
        if not old_auto_sync and new_config.auto_sync:
            self.start_auto_sync()
        elif old_auto_sync and not new_config.auto_sync:
            self.stop_auto_sync()

    def _is_city_already_shared(self, city_name: str) -> bool:
        """Check if city is already in shared data."""
        return any(city.name == city_name for city in self.shared_cities)

    def _log_activity(self, action: str, target: str, user: str = "Unknown", details: str = None):
        """Log a team activity."""
        activity = TeamActivity(
            id=str(uuid.uuid4()),
            user=user,
            action=action,
            target=target,
            timestamp=datetime.now(),
            details=details
        )
        self.activities.append(activity)
        
        # Update session activity
        if self.current_session:
            self.current_session.last_activity = datetime.now()

    def _trigger_sync(self):
        """Trigger synchronization if auto-sync is enabled."""
        self.sync_status.pending_changes += 1
        if self.config.auto_sync:
            # Schedule immediate sync in background
            threading.Thread(target=self.sync_with_remote, daemon=True).start()

    def _schedule_next_sync(self):
        """Schedule the next automatic sync."""
        if self.config.auto_sync:
            self.sync_timer = threading.Timer(
                self.config.sync_interval, 
                self._auto_sync_callback
            )
            self.sync_timer.start()

    def _auto_sync_callback(self):
        """Callback for automatic sync timer."""
        self.sync_with_remote()
        self._schedule_next_sync()

    def _push_data_to_github(self):
        """Push local data to GitHub repository."""
        if not self.github_service:
            return
            
        # Prepare data for GitHub
        data = {
            'cities': [city.to_dict() if hasattr(city, 'to_dict') else city 
                      for city in self.shared_cities],
            'comparisons': [comp.to_dict() if hasattr(comp, 'to_dict') else comp 
                           for comp in self.team_comparisons],
            'activities': [activity.to_dict() for activity in self.activities[-100:]],  # Last 100 activities
            'last_updated': datetime.now().isoformat()
        }
        
        # Use GitHub service to push data
        self.github_service.push_team_data(data)

    def _pull_data_from_github(self):
        """Pull data from GitHub repository."""
        if not self.github_service:
            return
            
        try:
            remote_data = self.github_service.pull_team_data()
            if remote_data:
                # Update local data with remote data
                if 'cities' in remote_data:
                    self.shared_cities = remote_data['cities']
                if 'comparisons' in remote_data:
                    self.team_comparisons = remote_data['comparisons']
                if 'activities' in remote_data:
                    # Merge activities avoiding duplicates
                    remote_activities = [TeamActivity.from_dict(a) 
                                       for a in remote_data['activities']]
                    existing_ids = {a.id for a in self.activities}
                    new_activities = [a for a in remote_activities 
                                    if a.id not in existing_ids]
                    self.activities.extend(new_activities)
                    
                if self.on_data_updated:
                    self.on_data_updated()
                    
        except Exception as e:
            self.logger.error(f"Error pulling data from GitHub: {e}")
            raise