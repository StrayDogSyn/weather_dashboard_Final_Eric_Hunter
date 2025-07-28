#!/usr/bin/env python3
"""
Mock Database Implementation for Testing

This module provides a mock implementation of IDatabase interface
that can be used for unit testing and development scenarios
where a real database is not needed.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Mock Database Implementation)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.interfaces import IDatabase, WeatherDataDTO, JournalEntryDTO, UserPreferenceDTO, ILoggingService


class MockDatabase(IDatabase):
    """Mock database implementation for testing.
    
    This class provides a mock implementation of IDatabase
    that can be used for unit testing and development scenarios
    where a real database is not needed.
    """
    
    def __init__(self, logger_service: Optional[ILoggingService] = None):
        """Initialize the mock database.
        
        Args:
            logger_service: Optional logging service
        """
        self._logger_service = logger_service
        self._weather_data: List[WeatherDataDTO] = []
        self._journal_entries: List[JournalEntryDTO] = []
        self._user_preferences: Dict[str, UserPreferenceDTO] = {}
        self._should_fail = False
        
        self._log_info("MockDatabase initialized")
    
    def _log_info(self, message: str, **kwargs) -> None:
        """Log an info message if logger service is available."""
        if self._logger_service:
            self._logger_service.info(message, **kwargs)
    
    def set_should_fail(self, should_fail: bool) -> None:
        """Set whether the database should simulate failures.
        
        Args:
            should_fail: Whether to simulate failures
        """
        self._should_fail = should_fail
    
    def save_weather_data(self, weather_data: WeatherDataDTO) -> bool:
        """Save weather data to mock storage.
        
        Args:
            weather_data: Weather data to save
            
        Returns:
            True if saved successfully, False if simulating failure
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating save weather data failure")
            return False
        
        self._weather_data.append(weather_data)
        self._log_info(f"MockDatabase saved weather data for {weather_data.location}")
        return True
    
    def get_weather_history(self, location: str, days: int = 7) -> List[WeatherDataDTO]:
        """Get weather history from mock storage.
        
        Args:
            location: Location to get history for
            days: Number of days of history to retrieve
            
        Returns:
            List of historical weather data
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get weather history failure")
            return []
        
        # Filter by location
        filtered_data = [data for data in self._weather_data 
                        if data.location.lower() == location.lower()]
        
        self._log_info(f"MockDatabase returning {len(filtered_data)} weather history records")
        return filtered_data
    
    def save_journal_entry(self, journal_entry: JournalEntryDTO) -> bool:
        """Save journal entry to mock storage.
        
        Args:
            journal_entry: Journal entry to save
            
        Returns:
            True if saved successfully, False if simulating failure
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating save journal entry failure")
            return False
        
        self._journal_entries.append(journal_entry)
        self._log_info(f"MockDatabase saved journal entry: {journal_entry.title}")
        return True
    
    def get_journal_entries(self, limit: int = 50, offset: int = 0) -> List[JournalEntryDTO]:
        """Get journal entries from mock storage.
        
        Args:
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip
            
        Returns:
            List of journal entries
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get journal entries failure")
            return []
        
        entries = self._journal_entries[offset:offset + limit]
        self._log_info(f"MockDatabase returning {len(entries)} journal entries")
        return entries
    
    def save_user_preference(self, preference: UserPreferenceDTO) -> bool:
        """Save user preference to mock storage.
        
        Args:
            preference: User preference to save
            
        Returns:
            True if saved successfully, False if simulating failure
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating save user preference failure")
            return False
        
        self._user_preferences[preference.key] = preference
        self._log_info(f"MockDatabase saved user preference: {preference.key}")
        return True
    
    def get_user_preference(self, key: str) -> Optional[UserPreferenceDTO]:
        """Get user preference from mock storage.
        
        Args:
            key: Preference key to retrieve
            
        Returns:
            User preference or None if not found
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get user preference failure")
            return None
        
        preference = self._user_preferences.get(key)
        self._log_info(f"MockDatabase returning preference for key: {key}")
        return preference
    
    def get_all_user_preferences(self) -> List[UserPreferenceDTO]:
        """Get all user preferences from mock storage.
        
        Returns:
            List of all user preferences
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get all user preferences failure")
            return []
        
        preferences = list(self._user_preferences.values())
        self._log_info(f"MockDatabase returning {len(preferences)} user preferences")
        return preferences
    
    def get_recent_weather(self, limit: int = 10) -> List[WeatherDataDTO]:
        """Get recent weather data from mock storage.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent weather data
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get recent weather failure")
            return []
        
        # Return most recent entries (last added)
        recent_data = self._weather_data[-limit:] if len(self._weather_data) > limit else self._weather_data
        self._log_info(f"MockDatabase returning {len(recent_data)} recent weather records")
        return recent_data
    
    def get_weather_by_location(self, location: str, limit: int = 5) -> List[WeatherDataDTO]:
        """Get weather data for specific location from mock storage.
        
        Args:
            location: Location name to search for
            limit: Maximum number of records to return
            
        Returns:
            List of weather data for the location
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get weather by location failure")
            return []
        
        # Filter by location
        location_data = [data for data in self._weather_data 
                        if data.location.lower() == location.lower()]
        
        # Apply limit
        limited_data = location_data[:limit] if len(location_data) > limit else location_data
        
        self._log_info(f"MockDatabase returning {len(limited_data)} weather records for location {location}")
        return limited_data
    
    def get_preference(self, key: str) -> Optional[UserPreferenceDTO]:
        """Get a user preference from mock storage.
        
        Args:
            key: Preference key
            
        Returns:
            User preference or None if not found
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get preference failure")
            return None
        
        preference = self._user_preferences.get(key)
        self._log_info(f"MockDatabase returning preference for key: {key}")
        return preference
    
    def set_preference(self, preference: UserPreferenceDTO) -> None:
        """Set a user preference in mock storage.
        
        Args:
            preference: User preference to set
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating set preference failure")
            return
        
        self._user_preferences[preference.key] = preference
        self._log_info(f"MockDatabase set preference: {preference.key}")
    
    def test_connection(self) -> bool:
        """Test mock database connection.
        
        Returns:
            True unless simulating failure
        """
        result = not self._should_fail
        self._log_info(f"MockDatabase connection test: {result}")
        return result
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get mock database information.
        
        Returns:
            Dictionary containing mock database information
        """
        if self._should_fail:
            self._log_info("MockDatabase simulating get database info failure")
            return {}
        
        info = {
            'database_path': 'mock://database',
            'database_exists': True,
            'database_size': 1024,  # Mock size
            'connection_status': True,
            'last_check': datetime.now().isoformat(),
            'weather_records': len(self._weather_data),
            'journal_entries': len(self._journal_entries),
            'user_preferences': len(self._user_preferences),
            'should_fail': self._should_fail
        }
        
        self._log_info("MockDatabase returning database info")
        return info
    
    def clear_all_data(self) -> None:
        """Clear all mock data (useful for testing)."""
        self._weather_data.clear()
        self._journal_entries.clear()
        self._user_preferences.clear()
        self._log_info("MockDatabase cleared all data")
    
    def add_sample_data(self) -> None:
        """Add sample data for testing purposes."""
        # Add sample weather data
        sample_weather = WeatherDataDTO(
            location="New York",
            temperature=22.5,
            feels_like=24.0,
            humidity=65,
            pressure=1013.25,
            description="Partly cloudy",
            icon="partly-cloudy",
            wind_speed=5.2,
            wind_direction=180,
            visibility=10.0,
            uv_index=6.0,
            timestamp=datetime.now()
        )
        self._weather_data.append(sample_weather)
        
        # Add sample journal entry
        sample_journal = JournalEntryDTO(
            id=1,
            title="Beautiful Day",
            content="Today was a wonderful day with perfect weather!",
            mood="happy",
            weather_condition="sunny",
            location="New York",
            tags=["sunny", "happy", "outdoor"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._journal_entries.append(sample_journal)
        
        # Add sample preferences
        sample_prefs = [
            UserPreferenceDTO(
                key="theme",
                value="dark",
                category="ui",
                data_type="string",
                description="Application theme",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            UserPreferenceDTO(
                key="temperature_unit",
                value="celsius",
                category="weather",
                data_type="string",
                description="Temperature unit",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        for pref in sample_prefs:
            self._user_preferences[pref.key] = pref
        
        self._log_info("MockDatabase added sample data")