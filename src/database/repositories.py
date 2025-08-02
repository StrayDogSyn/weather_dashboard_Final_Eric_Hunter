"""Repository classes for data access.

Implements repository pattern with async support for all data models.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

from .models import ActivityLog, JournalEntry, UserPreferences, WeatherHistory


class BaseRepository:
    """Base repository with common functionality."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: Database session
        """
        self._session = session
        self._logger = logging.getLogger(self.__class__.__name__)


class WeatherRepository(BaseRepository):
    """Repository for weather history data."""
    
    async def save_weather_data(self, weather_data: Dict[str, Any]) -> WeatherHistory:
        """Save weather data to database.
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            WeatherHistory: Saved weather record
        """
        try:
            weather_record = WeatherHistory(
                location=weather_data['location'],
                latitude=weather_data.get('latitude', 0.0),
                longitude=weather_data.get('longitude', 0.0),
                temperature=weather_data['temperature'],
                feels_like=weather_data.get('feels_like'),
                humidity=weather_data.get('humidity'),
                pressure=weather_data.get('pressure'),
                wind_speed=weather_data.get('wind_speed'),
                wind_direction=weather_data.get('wind_direction'),
                visibility=weather_data.get('visibility'),
                uv_index=weather_data.get('uv_index'),
                condition=weather_data['condition'],
                description=weather_data.get('description'),
                icon=weather_data.get('icon'),
                raw_data=weather_data.get('raw_data'),
                timestamp=weather_data.get('timestamp', datetime.utcnow())
            )
            
            self._session.add(weather_record)
            await self._session.commit()
            await self._session.refresh(weather_record)
            
            self._logger.debug(f"Saved weather data for {weather_data['location']}")
            return weather_record
            
        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Failed to save weather data: {e}")
            raise
    
    async def get_weather_history(
        self,
        location: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[WeatherHistory]:
        """Get weather history with optional filters.
        
        Args:
            location: Filter by location
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records
            
        Returns:
            List[WeatherHistory]: Weather history records
        """
        try:
            query = select(WeatherHistory)
            
            # Apply filters
            conditions = []
            if location:
                conditions.append(WeatherHistory.location.ilike(f"%{location}%"))
            if start_date:
                conditions.append(WeatherHistory.timestamp >= start_date)
            if end_date:
                conditions.append(WeatherHistory.timestamp <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Order by timestamp descending and limit
            query = query.order_by(desc(WeatherHistory.timestamp)).limit(limit)
            
            result = await self._session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            self._logger.error(f"Failed to get weather history: {e}")
            raise
    
    async def get_latest_weather(self, location: str) -> Optional[WeatherHistory]:
        """Get latest weather data for a location.
        
        Args:
            location: Location name
            
        Returns:
            Optional[WeatherHistory]: Latest weather record or None
        """
        try:
            query = select(WeatherHistory).where(
                WeatherHistory.location.ilike(f"%{location}%")
            ).order_by(desc(WeatherHistory.timestamp)).limit(1)
            
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self._logger.error(f"Failed to get latest weather for {location}: {e}")
            raise
    
    async def get_weather_statistics(
        self,
        location: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get weather statistics for a location.
        
        Args:
            location: Location name
            days: Number of days to analyze
            
        Returns:
            Dict[str, Any]: Weather statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(
                func.avg(WeatherHistory.temperature).label('avg_temp'),
                func.min(WeatherHistory.temperature).label('min_temp'),
                func.max(WeatherHistory.temperature).label('max_temp'),
                func.avg(WeatherHistory.humidity).label('avg_humidity'),
                func.avg(WeatherHistory.pressure).label('avg_pressure'),
                func.avg(WeatherHistory.wind_speed).label('avg_wind_speed'),
                func.count(WeatherHistory.id).label('record_count')
            ).where(
                and_(
                    WeatherHistory.location.ilike(f"%{location}%"),
                    WeatherHistory.timestamp >= start_date
                )
            )
            
            result = await self._session.execute(query)
            row = result.first()
            
            if row:
                return {
                    'location': location,
                    'period_days': days,
                    'avg_temperature': float(row.avg_temp) if row.avg_temp else None,
                    'min_temperature': float(row.min_temp) if row.min_temp else None,
                    'max_temperature': float(row.max_temp) if row.max_temp else None,
                    'avg_humidity': float(row.avg_humidity) if row.avg_humidity else None,
                    'avg_pressure': float(row.avg_pressure) if row.avg_pressure else None,
                    'avg_wind_speed': float(row.avg_wind_speed) if row.avg_wind_speed else None,
                    'record_count': int(row.record_count)
                }
            
            return {'location': location, 'period_days': days, 'record_count': 0}
            
        except Exception as e:
            self._logger.error(f"Failed to get weather statistics: {e}")
            raise
    
    async def get_all_history(self) -> List[WeatherHistory]:
        """Get all weather history records.
        
        Returns:
            List[WeatherHistory]: All weather records
        """
        try:
            query = select(WeatherHistory).order_by(desc(WeatherHistory.timestamp))
            result = await self._session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            self._logger.error(f"Failed to get all weather history: {e}")
            raise
    
    async def get_history_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[WeatherHistory]:
        """Get weather history within a date range.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List[WeatherHistory]: Weather records in range
        """
        try:
            query = select(WeatherHistory)
            
            # Apply date filters
            conditions = []
            if start_date:
                conditions.append(WeatherHistory.timestamp >= start_date)
            if end_date:
                conditions.append(WeatherHistory.timestamp <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(WeatherHistory.timestamp))
            result = await self._session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            self._logger.error(f"Failed to get weather history range: {e}")
            raise
    
    async def cleanup_old_records(self, days_to_keep: int = 365) -> int:
        """Clean up old weather records.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Count records to be deleted
            count_query = select(func.count(WeatherHistory.id)).where(
                WeatherHistory.timestamp < cutoff_date
            )
            result = await self._session.execute(count_query)
            count = result.scalar()
            
            if count > 0:
                # Delete old records
                delete_query = WeatherHistory.__table__.delete().where(
                    WeatherHistory.timestamp < cutoff_date
                )
                await self._session.execute(delete_query)
                await self._session.commit()
                
                self._logger.info(f"Cleaned up {count} old weather records")
            
            return count
            
        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Failed to cleanup old records: {e}")
            raise


class PreferencesRepository(BaseRepository):
    """Repository for user preferences."""
    
    async def get_preferences(self, user_id: str = 'default') -> Optional[UserPreferences]:
        """Get user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            Optional[UserPreferences]: User preferences or None
        """
        try:
            query = select(UserPreferences).where(UserPreferences.user_id == user_id)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self._logger.error(f"Failed to get preferences for {user_id}: {e}")
            raise
    
    async def save_preferences(self, preferences_data: Dict[str, Any], user_id: str = 'default') -> UserPreferences:
        """Save or update user preferences.
        
        Args:
            preferences_data: Preferences data
            user_id: User identifier
            
        Returns:
            UserPreferences: Saved preferences
        """
        try:
            # Try to get existing preferences
            existing = await self.get_preferences(user_id)
            
            if existing:
                # Update existing preferences
                for key, value in preferences_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                preferences = existing
            else:
                # Create new preferences
                preferences = UserPreferences(user_id=user_id, **preferences_data)
                self._session.add(preferences)
            
            await self._session.commit()
            await self._session.refresh(preferences)
            
            self._logger.debug(f"Saved preferences for {user_id}")
            return preferences
            
        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Failed to save preferences: {e}")
            raise
    
    async def update_favorite_locations(self, locations: List[str], user_id: str = 'default') -> None:
        """Update favorite locations.
        
        Args:
            locations: List of favorite locations
            user_id: User identifier
        """
        await self.save_preferences({'favorite_locations': locations}, user_id)
    
    async def update_recent_searches(self, searches: List[str], user_id: str = 'default') -> None:
        """Update recent searches.
        
        Args:
            searches: List of recent searches
            user_id: User identifier
        """
        await self.save_preferences({'recent_searches': searches}, user_id)
    
    async def get_dashboard_layout(self, user_id: str = 'default') -> Dict[str, Any]:
        """Get dashboard layout preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict[str, Any]: Dashboard layout
        """
        preferences = await self.get_preferences(user_id)
        return preferences.dashboard_layout if preferences else {}
    
    async def save_preference(self, key: str, value: Any, user_id: str = 'default') -> None:
        """Save a single preference.
        
        Args:
            key: Preference key
            value: Preference value
            user_id: User identifier
        """
        await self.save_preferences({key: value}, user_id)
    
    async def add_favorite_location(self, location: str, user_id: str = 'default') -> None:
        """Add a favorite location.
        
        Args:
            location: Location to add
            user_id: User identifier
        """
        preferences = await self.get_preferences(user_id)
        favorites = preferences.favorite_locations if preferences else []
        
        if location not in favorites:
            favorites.append(location)
            await self.update_favorite_locations(favorites, user_id)
    
    async def remove_favorite_location(self, location: str, user_id: str = 'default') -> None:
        """Remove a favorite location.
        
        Args:
            location: Location to remove
            user_id: User identifier
        """
        preferences = await self.get_preferences(user_id)
        favorites = preferences.favorite_locations if preferences else []
        
        if location in favorites:
            favorites.remove(location)
            await self.update_favorite_locations(favorites, user_id)
    
    async def add_recent_search(self, search: str, user_id: str = 'default', max_searches: int = 10) -> None:
        """Add a recent search.
        
        Args:
            search: Search term to add
            user_id: User identifier
            max_searches: Maximum number of searches to keep
        """
        preferences = await self.get_preferences(user_id)
        searches = preferences.recent_searches if preferences else []
        
        # Remove if already exists
        if search in searches:
            searches.remove(search)
        
        # Add to beginning
        searches.insert(0, search)
        
        # Limit to max_searches
        searches = searches[:max_searches]
        
        await self.update_recent_searches(searches, user_id)


class ActivityRepository(BaseRepository):
    """Repository for activity tracking."""
    
    async def log_activity(
        self,
        activity_data: Dict[str, Any],
        user_id: str = 'default'
    ) -> ActivityLog:
        """Log an activity selection or completion.
        
        Args:
            activity_data: Activity data
            user_id: User identifier
            
        Returns:
            ActivityLog: Saved activity log
        """
        try:
            activity_log = ActivityLog(
                user_id=user_id,
                activity_name=activity_data['activity_name'],
                activity_category=activity_data.get('activity_category'),
                activity_difficulty=activity_data.get('activity_difficulty'),
                location=activity_data['location'],
                weather_condition=activity_data.get('weather_condition'),
                temperature=activity_data.get('temperature'),
                selected_at=activity_data.get('selected_at', datetime.utcnow()),
                completed_at=activity_data.get('completed_at'),
                duration_minutes=activity_data.get('duration_minutes'),
                rating=activity_data.get('rating'),
                feedback=activity_data.get('feedback'),
                would_recommend=activity_data.get('would_recommend'),
                weather_snapshot=activity_data.get('weather_snapshot')
            )
            
            self._session.add(activity_log)
            await self._session.commit()
            await self._session.refresh(activity_log)
            
            self._logger.debug(f"Logged activity: {activity_data['activity_name']}")
            return activity_log
            
        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Failed to log activity: {e}")
            raise
    
    async def get_activity_history(
        self,
        user_id: str = 'default',
        activity_name: Optional[str] = None,
        location: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[ActivityLog]:
        """Get activity history.
        
        Args:
            user_id: User identifier
            activity_name: Filter by activity name
            location: Filter by location
            days: Number of days to look back
            limit: Maximum number of records
            
        Returns:
            List[ActivityLog]: Activity history
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(ActivityLog).where(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.selected_at >= start_date
                )
            )
            
            # Apply filters
            if activity_name:
                query = query.where(ActivityLog.activity_name.ilike(f"%{activity_name}%"))
            if location:
                query = query.where(ActivityLog.location.ilike(f"%{location}%"))
            
            query = query.order_by(desc(ActivityLog.selected_at)).limit(limit)
            
            result = await self._session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            self._logger.error(f"Failed to get activity history: {e}")
            raise
    
    async def get_activity_statistics(
        self,
        user_id: str = 'default',
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity statistics.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict[str, Any]: Activity statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get basic statistics
            query = select(
                func.count(ActivityLog.id).label('total_activities'),
                func.count(ActivityLog.completed_at).label('completed_activities'),
                func.avg(ActivityLog.rating).label('avg_rating'),
                func.avg(ActivityLog.duration_minutes).label('avg_duration')
            ).where(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.selected_at >= start_date
                )
            )
            
            result = await self._session.execute(query)
            row = result.first()
            
            # Get most popular activities
            popular_query = select(
                ActivityLog.activity_name,
                func.count(ActivityLog.id).label('count')
            ).where(
                and_(
                    ActivityLog.user_id == user_id,
                    ActivityLog.selected_at >= start_date
                )
            ).group_by(ActivityLog.activity_name).order_by(
                desc(func.count(ActivityLog.id))
            ).limit(5)
            
            popular_result = await self._session.execute(popular_query)
            popular_activities = [
                {'activity': row.activity_name, 'count': row.count}
                for row in popular_result.fetchall()
            ]
            
            return {
                'period_days': days,
                'total_activities': int(row.total_activities) if row.total_activities else 0,
                'completed_activities': int(row.completed_activities) if row.completed_activities else 0,
                'completion_rate': (
                    (row.completed_activities / row.total_activities * 100)
                    if row.total_activities and row.completed_activities else 0
                ),
                'avg_rating': float(row.avg_rating) if row.avg_rating else None,
                'avg_duration_minutes': float(row.avg_duration) if row.avg_duration else None,
                'popular_activities': popular_activities
            }
            
        except Exception as e:
            self._logger.error(f"Failed to get activity statistics: {e}")
            raise


class JournalRepository(BaseRepository):
    """Repository for journal entries."""
    
    async def create_entry(self, entry_data: Dict[str, Any], user_id: str = 'default') -> JournalEntry:
        """Create a new journal entry.
        
        Args:
            entry_data: Journal entry data
            user_id: User identifier
            
        Returns:
            JournalEntry: Created journal entry
        """
        try:
            entry = JournalEntry(
                user_id=user_id,
                date=entry_data.get('date', datetime.utcnow()),
                title=entry_data.get('title'),
                notes=entry_data.get('notes'),
                mood=entry_data.get('mood'),
                mood_score=entry_data.get('mood_score'),
                energy_level=entry_data.get('energy_level'),
                weather_impact=entry_data.get('weather_impact'),
                weather_preference=entry_data.get('weather_preference'),
                location=entry_data.get('location'),
                weather_snapshot=entry_data.get('weather_snapshot'),
                tags=entry_data.get('tags', []),
                category=entry_data.get('category'),
                is_private=entry_data.get('is_private', True)
            )
            
            self._session.add(entry)
            await self._session.commit()
            await self._session.refresh(entry)
            
            self._logger.debug(f"Created journal entry for {user_id}")
            return entry
            
        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Failed to create journal entry: {e}")
            raise
    
    async def get_entries(
        self,
        user_id: str = 'default',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        mood: Optional[str] = None,
        limit: int = 50
    ) -> List[JournalEntry]:
        """Get journal entries with optional filters.
        
        Args:
            user_id: User identifier
            start_date: Filter by start date
            end_date: Filter by end date
            mood: Filter by mood
            limit: Maximum number of entries
            
        Returns:
            List[JournalEntry]: Journal entries
        """
        try:
            query = select(JournalEntry).where(JournalEntry.user_id == user_id)
            
            # Apply filters
            conditions = []
            if start_date:
                conditions.append(JournalEntry.date >= start_date)
            if end_date:
                conditions.append(JournalEntry.date <= end_date)
            if mood:
                conditions.append(JournalEntry.mood == mood)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(JournalEntry.date)).limit(limit)
            
            result = await self._session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            self._logger.error(f"Failed to get journal entries: {e}")
            raise
    
    async def get_mood_trends(
        self,
        user_id: str = 'default',
        days: int = 30
    ) -> Dict[str, Any]:
        """Get mood trends and weather correlations.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict[str, Any]: Mood trends and statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get mood statistics
            query = select(
                func.avg(JournalEntry.mood_score).label('avg_mood'),
                func.avg(JournalEntry.energy_level).label('avg_energy'),
                func.count(JournalEntry.id).label('entry_count')
            ).where(
                and_(
                    JournalEntry.user_id == user_id,
                    JournalEntry.date >= start_date
                )
            )
            
            result = await self._session.execute(query)
            row = result.first()
            
            # Get mood distribution
            mood_query = select(
                JournalEntry.mood,
                func.count(JournalEntry.id).label('count')
            ).where(
                and_(
                    JournalEntry.user_id == user_id,
                    JournalEntry.date >= start_date
                )
            ).group_by(JournalEntry.mood)
            
            mood_result = await self._session.execute(mood_query)
            mood_distribution = {
                row.mood: row.count for row in mood_result.fetchall() if row.mood
            }
            
            return {
                'period_days': days,
                'avg_mood_score': float(row.avg_mood) if row.avg_mood else None,
                'avg_energy_level': float(row.avg_energy) if row.avg_energy else None,
                'entry_count': int(row.entry_count),
                'mood_distribution': mood_distribution
            }
            
        except Exception as e:
            self._logger.error(f"Failed to get mood trends: {e}")
            raise