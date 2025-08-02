"""Example integration of the data persistence system.

Demonstrates how to integrate the DataService into the weather dashboard.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .data_service import DataService


class WeatherDashboardIntegration:
    """Example integration of data persistence with weather dashboard."""

    def __init__(self):
        """Initialize the integration."""
        self._logger = logging.getLogger(__name__)
        self._data_service = DataService()
        self._current_user = "default_user"  # In real app, get from auth

    async def initialize(self) -> bool:
        """Initialize the data service.

        Returns:
            bool: True if initialization was successful
        """
        return await self._data_service.initialize()

    async def shutdown(self):
        """Shutdown the data service."""
        await self._data_service.shutdown()

    # Weather data integration
    async def save_current_weather(self, location: str, weather_data: Dict[str, Any]) -> bool:
        """Save current weather data.

        Args:
            location: Location name
            weather_data: Weather data from API

        Returns:
            bool: True if save was successful
        """
        try:
            # Extract relevant data
            temperature = weather_data.get("temperature", 0.0)
            conditions = weather_data.get("conditions", "Unknown")
            humidity = weather_data.get("humidity")
            wind_speed = weather_data.get("wind_speed")
            pressure = weather_data.get("pressure")

            # Save to database
            success = await self._data_service.save_weather_data(
                location=location,
                temperature=temperature,
                conditions=conditions,
                humidity=humidity,
                wind_speed=wind_speed,
                pressure=pressure,
            )

            if success:
                # Log the activity
                await self._data_service.log_activity(
                    user_id=self._current_user,
                    activity_type="weather_lookup",
                    activity_data={
                        "location": location,
                        "temperature": temperature,
                        "conditions": conditions,
                    },
                    location=location,
                )

            return success

        except Exception as e:
            self._logger.error(f"Failed to save weather data: {e}")
            return False

    async def get_location_weather_history(self, location: str, days: int = 7) -> Dict[str, Any]:
        """Get weather history for a location.

        Args:
            location: Location name
            days: Number of days to retrieve

        Returns:
            Dict[str, Any]: Weather history and statistics
        """
        try:
            # Get history
            history = await self._data_service.get_weather_history(location=location, days=days)

            # Get statistics
            stats = await self._data_service.get_weather_statistics(location)

            return {"location": location, "history": history, "statistics": stats, "days": days}

        except Exception as e:
            self._logger.error(f"Failed to get weather history: {e}")
            return {"location": location, "history": [], "statistics": {}, "days": days}

    # User preferences integration
    async def save_user_settings(self, settings: Dict[str, Any]) -> bool:
        """Save user settings.

        Args:
            settings: User settings dictionary

        Returns:
            bool: True if save was successful
        """
        try:
            success = True

            for key, value in settings.items():
                result = await self._data_service.save_user_preference(
                    user_id=self._current_user, key=key, value=value
                )
                if not result:
                    success = False

            return success

        except Exception as e:
            self._logger.error(f"Failed to save user settings: {e}")
            return False

    async def get_user_settings(self) -> Dict[str, Any]:
        """Get user settings.

        Returns:
            Dict[str, Any]: User settings
        """
        return await self._data_service.get_user_preferences(self._current_user)

    async def add_favorite_location(self, location: str) -> bool:
        """Add a favorite location.

        Args:
            location: Location to add

        Returns:
            bool: True if add was successful
        """
        success = await self._data_service.add_favorite_location(
            user_id=self._current_user, location=location
        )

        if success:
            # Log the activity
            await self._data_service.log_activity(
                user_id=self._current_user,
                activity_type="favorite_added",
                activity_data={"location": location},
                location=location,
            )

        return success

    async def get_favorite_locations(self) -> list[str]:
        """Get user's favorite locations.

        Returns:
            List[str]: Favorite locations
        """
        return await self._data_service.get_favorite_locations(self._current_user)

    async def add_search_to_history(self, search_term: str) -> bool:
        """Add search to history.

        Args:
            search_term: Search term

        Returns:
            bool: True if add was successful
        """
        success = await self._data_service.add_recent_search(
            user_id=self._current_user, search_term=search_term
        )

        if success:
            # Log the activity
            await self._data_service.log_activity(
                user_id=self._current_user,
                activity_type="search",
                activity_data={"search_term": search_term},
            )

        return success

    async def get_search_history(self, limit: int = 10) -> list[str]:
        """Get search history.

        Args:
            limit: Maximum number of searches to return

        Returns:
            List[str]: Recent searches
        """
        return await self._data_service.get_recent_searches(user_id=self._current_user, limit=limit)

    # Activity tracking integration
    async def log_user_activity(self, activity_type: str, activity_data: Dict[str, Any]) -> bool:
        """Log user activity.

        Args:
            activity_type: Type of activity
            activity_data: Activity data

        Returns:
            bool: True if log was successful
        """
        return await self._data_service.log_activity(
            user_id=self._current_user, activity_type=activity_type, activity_data=activity_data
        )

    async def get_user_activity_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary.

        Args:
            days: Number of days to analyze

        Returns:
            Dict[str, Any]: Activity summary
        """
        try:
            # Get activities
            activities = await self._data_service.get_user_activities(
                user_id=self._current_user, days=days
            )

            # Get statistics
            stats = await self._data_service.get_activity_statistics(self._current_user)

            return {"activities": activities, "statistics": stats, "period_days": days}

        except Exception as e:
            self._logger.error(f"Failed to get activity summary: {e}")
            return {"activities": [], "statistics": {}, "period_days": days}

    # Journal integration
    async def create_mood_entry(
        self, mood_score: float, notes: str = "", weather_data: Dict = None
    ) -> bool:
        """Create a mood journal entry.

        Args:
            mood_score: Mood score (1-10)
            notes: Optional notes
            weather_data: Optional current weather data

        Returns:
            bool: True if creation was successful
        """
        success = await self._data_service.create_journal_entry(
            user_id=self._current_user,
            mood_score=mood_score,
            notes=notes,
            weather_snapshot=weather_data,
        )

        if success:
            # Log the activity
            await self._data_service.log_activity(
                user_id=self._current_user,
                activity_type="journal_entry",
                activity_data={
                    "mood_score": mood_score,
                    "has_notes": bool(notes),
                    "has_weather": bool(weather_data),
                },
            )

        return success

    async def get_mood_journal(self, days: int = 30) -> Dict[str, Any]:
        """Get mood journal entries and trends.

        Args:
            days: Number of days to retrieve

        Returns:
            Dict[str, Any]: Journal entries and trends
        """
        try:
            # Get entries
            entries = await self._data_service.get_journal_entries(
                user_id=self._current_user, days=days
            )

            # Get trends
            trends = await self._data_service.get_mood_trends(user_id=self._current_user, days=days)

            return {"entries": entries, "trends": trends, "period_days": days}

        except Exception as e:
            self._logger.error(f"Failed to get mood journal: {e}")
            return {"entries": [], "trends": {}, "period_days": days}

    # Data management integration
    async def export_user_data(self, export_path: Path) -> bool:
        """Export user data.

        Args:
            export_path: Export file path

        Returns:
            bool: True if export was successful
        """
        return await self._data_service.export_data(
            export_file=export_path, user_id=self._current_user
        )

    async def import_user_data(
        self, import_path: Path, validate_only: bool = False
    ) -> Dict[str, Any]:
        """Import user data.

        Args:
            import_path: Import file path
            validate_only: If True, only validate without importing

        Returns:
            Dict[str, Any]: Import results
        """
        return await self._data_service.import_data(
            import_file=import_path, validate_only=validate_only
        )

    async def create_data_backup(self) -> Path:
        """Create a data backup.

        Returns:
            Path: Backup file path
        """
        backup_name = f"user_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return await self._data_service.create_backup(backup_name)

    # System management
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status.

        Returns:
            Dict[str, Any]: System status
        """
        try:
            # Get health check
            health = await self._data_service.health_check()

            # Get database info
            db_info = await self._data_service.get_database_info()

            # Get cache stats
            cache_stats = self._data_service.get_cache_statistics()

            # Get migration status
            migration_status = await self._data_service.get_migration_status()

            return {
                "health": health,
                "database": db_info,
                "cache": cache_stats,
                "migrations": migration_status,
            }

        except Exception as e:
            self._logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    async def cleanup_old_data(self) -> bool:
        """Cleanup old data.

        Returns:
            bool: True if cleanup was successful
        """
        try:
            # This would typically be handled by background tasks,
            # but can be triggered manually
            await self._data_service.vacuum_database()
            return True

        except Exception as e:
            self._logger.error(f"Failed to cleanup data: {e}")
            return False


# Example usage
async def example_usage():
    """Example of how to use the integration."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create integration
    integration = WeatherDashboardIntegration()

    try:
        # Initialize
        await integration.initialize()

        # Save some weather data
        weather_data = {
            "temperature": 22.5,
            "conditions": "Partly Cloudy",
            "humidity": 65,
            "wind_speed": 10.2,
            "pressure": 1013.25,
        }

        await integration.save_current_weather("New York", weather_data)

        # Add to favorites
        await integration.add_favorite_location("New York")

        # Add search to history
        await integration.add_search_to_history("New York weather")

        # Create mood entry
        await integration.create_mood_entry(
            mood_score=7.5, notes="Nice weather today!", weather_data=weather_data
        )

        # Get data
        favorites = await integration.get_favorite_locations()
        print(f"Favorite locations: {favorites}")

        history = await integration.get_location_weather_history("New York")
        print(f"Weather history entries: {len(history['history'])}")

        mood_journal = await integration.get_mood_journal()
        print(f"Journal entries: {len(mood_journal['entries'])}")

        # Get system status
        status = await integration.get_system_status()
        print(f"System status: {status['health']['status']}")

    finally:
        # Shutdown
        await integration.shutdown()


if __name__ == "__main__":
    asyncio.run(example_usage())
