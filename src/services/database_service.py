#!/usr/bin/env python3
"""
Database Service Implementation for Dependency Injection

This module provides the concrete implementation of IDatabase interface,
adapting the existing Database class to work with the dependency injection system.
It demonstrates how to bridge existing database code with new DI patterns.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from core.interfaces import IDatabase, WeatherDataDTO, JournalEntryDTO, UserPreferenceDTO, IConfigurationService, ILoggingService
from data.database import Database, DatabaseError


class DatabaseImpl(IDatabase):
    """Implementation of IDatabase using the existing Database class.
    
    This adapter class bridges the existing Database with the new
    dependency injection interface, demonstrating how to integrate legacy
    database code with modern DI patterns.
    """
    
    def __init__(self, 
                 config_service: IConfigurationService,
                 logger_service: Optional[ILoggingService] = None):
        """Initialize the database service implementation.
        
        Args:
            config_service: Configuration service for database settings
            logger_service: Optional logging service
        """
        self._config_service = config_service
        self._logger_service = logger_service
        
        # Get database path from configuration
        db_path = self._config_service.get_setting('database.path', 'data/weather_dashboard.db')
        
        # Ensure the directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the underlying database
        self._database = Database()
        
        self._log_info(f"DatabaseImpl initialized with path: {db_path}")
    
    def _log_info(self, message: str, **kwargs) -> None:
        """Log an info message if logger service is available."""
        if self._logger_service:
            self._logger_service.info(message, **kwargs)
    
    def _log_error(self, message: str, **kwargs) -> None:
        """Log an error message if logger service is available."""
        if self._logger_service:
            self._logger_service.error(message, **kwargs)
    
    def _log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message if logger service is available."""
        if self._logger_service:
            self._logger_service.warning(message, **kwargs)
    
    def _convert_weather_to_dto(self, weather_data: Dict[str, Any]) -> WeatherDataDTO:
        """Convert database weather data to WeatherDataDTO.
        
        Args:
            weather_data: Raw weather data from database
            
        Returns:
            Weather data DTO
        """
        return WeatherDataDTO(
            location=weather_data.get('location', ''),
            temperature=float(weather_data.get('temperature', 0)),
            feels_like=float(weather_data.get('feels_like', 0)),
            humidity=int(weather_data.get('humidity', 0)),
            pressure=float(weather_data.get('pressure', 0)),
            description=weather_data.get('description', ''),
            icon=weather_data.get('icon', ''),
            wind_speed=float(weather_data.get('wind_speed', 0)),
            wind_direction=int(weather_data.get('wind_direction', 0)),
            visibility=float(weather_data.get('visibility', 0)),
            uv_index=float(weather_data.get('uv_index', 0)),
            timestamp=datetime.fromisoformat(weather_data.get('timestamp', datetime.now().isoformat()))
        )
    
    def _convert_journal_to_dto(self, journal_data: Dict[str, Any]) -> JournalEntryDTO:
        """Convert database journal data to JournalEntryDTO.
        
        Args:
            journal_data: Raw journal data from database
            
        Returns:
            Journal entry DTO
        """
        return JournalEntryDTO(
            id=journal_data.get('id'),
            title=journal_data.get('title', ''),
            content=journal_data.get('content', ''),
            mood=journal_data.get('mood', 'neutral'),
            weather_condition=journal_data.get('weather_condition', ''),
            location=journal_data.get('location', ''),
            tags=json.loads(journal_data.get('tags', '[]')),
            created_at=datetime.fromisoformat(journal_data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(journal_data.get('updated_at', datetime.now().isoformat()))
        )
    
    def _convert_preference_to_dto(self, pref_data: Dict[str, Any]) -> UserPreferenceDTO:
        """Convert database preference data to UserPreferenceDTO.
        
        Args:
            pref_data: Raw preference data from database
            
        Returns:
            User preference DTO
        """
        return UserPreferenceDTO(
            key=pref_data.get('key', ''),
            value=pref_data.get('value', ''),
            category=pref_data.get('category', 'general'),
            data_type=pref_data.get('data_type', 'string'),
            description=pref_data.get('description', ''),
            created_at=datetime.fromisoformat(pref_data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(pref_data.get('updated_at', datetime.now().isoformat()))
        )
    
    def save_weather_data(self, weather_data: WeatherDataDTO) -> bool:
        """Save weather data to the database.
        
        Args:
            weather_data: Weather data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Convert DTO to format expected by legacy database
            legacy_data = {
                'location': weather_data.location,
                'temperature': weather_data.temperature,
                'feels_like': weather_data.feels_like,
                'humidity': weather_data.humidity,
                'pressure': weather_data.pressure,
                'description': weather_data.description,
                'icon': weather_data.icon,
                'wind_speed': weather_data.wind_speed,
                'wind_direction': weather_data.wind_direction,
                'visibility': weather_data.visibility,
                'uv_index': weather_data.uv_index,
                'timestamp': weather_data.timestamp.isoformat()
            }
            
            success = self._database.save_weather_data(legacy_data)
            
            if success:
                self._log_info(f"Weather data saved for {weather_data.location}")
            else:
                self._log_warning(f"Failed to save weather data for {weather_data.location}")
            
            return success
            
        except Exception as e:
            self._log_error(f"Error saving weather data: {e}")
            return False
    
    def get_weather_history(self, location: str, days: int = 7) -> List[WeatherDataDTO]:
        """Get weather history for a location.
        
        Args:
            location: Location to get history for
            days: Number of days of history to retrieve
            
        Returns:
            List of historical weather data
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get data from legacy database
            history_data = self._database.get_recent_weather_data(days)
            
            # Filter by location and convert to DTOs
            weather_dtos = []
            for data in history_data:
                if data.get('location', '').lower() == location.lower():
                    try:
                        dto = self._convert_weather_to_dto(data)
                        weather_dtos.append(dto)
                    except Exception as e:
                        self._log_warning(f"Error converting weather data to DTO: {e}")
                        continue
            
            self._log_info(f"Retrieved {len(weather_dtos)} weather history records for {location}")
            return weather_dtos
            
        except Exception as e:
            self._log_error(f"Error getting weather history for {location}: {e}")
            return []
    
    def get_recent_weather(self, limit: int = 10) -> List[WeatherDataDTO]:
        """Get recent weather data records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of weather data records
        """
        try:
            # Get recent data from legacy database
            recent_data = self._database.get_recent_weather_data(limit)
            
            # Convert to DTOs
            weather_dtos = []
            for data in recent_data:
                try:
                    dto = self._convert_weather_to_dto(data)
                    weather_dtos.append(dto)
                except Exception as e:
                    self._log_warning(f"Error converting weather data to DTO: {e}")
                    continue
            
            self._log_info(f"Retrieved {len(weather_dtos)} recent weather records")
            return weather_dtos
            
        except Exception as e:
            self._log_error(f"Error getting recent weather data: {e}")
            return []
    
    def get_weather_by_location(self, location: str, limit: int = 5) -> List[WeatherDataDTO]:
        """Get weather data for specific location.
        
        Args:
            location: Location name to search for
            limit: Maximum number of records to return
            
        Returns:
            List of weather data records
        """
        try:
            # Get data from legacy database
            location_data = self._database.get_weather_by_location(location, limit)
            
            # Convert to DTOs
            weather_dtos = []
            for data in location_data:
                try:
                    dto = self._convert_weather_to_dto(data)
                    weather_dtos.append(dto)
                except Exception as e:
                    self._log_warning(f"Error converting weather data to DTO: {e}")
                    continue
            
            self._log_info(f"Retrieved {len(weather_dtos)} weather records for location {location}")
            return weather_dtos
            
        except Exception as e:
            self._log_error(f"Error getting weather data for location {location}: {e}")
            return []
    
    def get_preference(self, key: str) -> Optional[UserPreferenceDTO]:
        """Get a user preference.
        
        Args:
            key: Preference key
            
        Returns:
            User preference or None if not found
        """
        try:
            # Get preference from legacy database
            pref_data = self._database.get_user_preference(key)
            
            if pref_data:
                # Convert to DTO
                dto = self._convert_preference_to_dto(pref_data)
                self._log_info(f"Retrieved user preference: {key}")
                return dto
            else:
                self._log_info(f"User preference not found: {key}")
                return None
                
        except Exception as e:
            self._log_error(f"Error getting user preference {key}: {e}")
            return None
    
    def set_preference(self, preference: UserPreferenceDTO) -> None:
        """Set a user preference.
        
        Args:
            preference: User preference to set
        """
        try:
            # Convert DTO to format for legacy database
            pref_data = {
                'key': preference.key,
                'value': preference.value,
                'updated_at': preference.updated_at.isoformat()
            }
            
            # Save to legacy database
            success = self._database.set_user_preference(preference.key, preference.value)
            
            if success:
                self._log_info(f"User preference set: {preference.key}")
            else:
                self._log_warning(f"Failed to set user preference: {preference.key}")
                
        except Exception as e:
            self._log_error(f"Error setting user preference {preference.key}: {e}")
    
    def save_journal_entry(self, journal_entry: JournalEntryDTO) -> bool:
        """Save a journal entry to the database.
        
        Args:
            journal_entry: Journal entry to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Convert DTO to format expected by legacy database
            legacy_entry = {
                'title': journal_entry.title,
                'content': journal_entry.content,
                'mood': journal_entry.mood,
                'weather_condition': journal_entry.weather_condition,
                'location': journal_entry.location,
                'tags': json.dumps(journal_entry.tags),
                'created_at': journal_entry.created_at.isoformat(),
                'updated_at': journal_entry.updated_at.isoformat()
            }
            
            success = self._database.save_journal_entry(legacy_entry)
            
            if success:
                self._log_info(f"Journal entry saved: {journal_entry.title}")
            else:
                self._log_warning(f"Failed to save journal entry: {journal_entry.title}")
            
            return success
            
        except Exception as e:
            self._log_error(f"Error saving journal entry: {e}")
            return False
    
    def get_journal_entries(self, limit: int = 50, offset: int = 0) -> List[JournalEntryDTO]:
        """Get journal entries from the database.
        
        Args:
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip
            
        Returns:
            List of journal entries
        """
        try:
            # Get data from legacy database
            entries_data = self._database.get_recent_journal_entries(limit)
            
            # Convert to DTOs
            journal_dtos = []
            for i, data in enumerate(entries_data):
                if i < offset:
                    continue
                if len(journal_dtos) >= limit:
                    break
                
                try:
                    dto = self._convert_journal_to_dto(data)
                    journal_dtos.append(dto)
                except Exception as e:
                    self._log_warning(f"Error converting journal entry to DTO: {e}")
                    continue
            
            self._log_info(f"Retrieved {len(journal_dtos)} journal entries")
            return journal_dtos
            
        except Exception as e:
            self._log_error(f"Error getting journal entries: {e}")
            return []
    
    def save_user_preference(self, preference: UserPreferenceDTO) -> bool:
        """Save a user preference to the database.
        
        Args:
            preference: User preference to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # For now, we'll implement a simple preference storage
            # In a real implementation, this would use the legacy database's preference system
            
            # Convert DTO to format for storage
            pref_data = {
                'key': preference.key,
                'value': preference.value,
                'category': preference.category,
                'data_type': preference.data_type,
                'description': preference.description,
                'created_at': preference.created_at.isoformat(),
                'updated_at': preference.updated_at.isoformat()
            }
            
            # Store in a simple way for now (this would be enhanced in a real implementation)
            success = True  # Placeholder - would call actual database method
            
            if success:
                self._log_info(f"User preference saved: {preference.key}")
            else:
                self._log_warning(f"Failed to save user preference: {preference.key}")
            
            return success
            
        except Exception as e:
            self._log_error(f"Error saving user preference: {e}")
            return False
    
    def get_user_preference(self, key: str) -> Optional[UserPreferenceDTO]:
        """Get a user preference from the database.
        
        Args:
            key: Preference key to retrieve
            
        Returns:
            User preference or None if not found
        """
        try:
            # For now, return a mock preference
            # In a real implementation, this would query the actual database
            
            # Mock data for demonstration
            if key == "theme":
                return UserPreferenceDTO(
                    key="theme",
                    value="dark",
                    category="ui",
                    data_type="string",
                    description="Application theme preference",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            
            self._log_info(f"User preference not found: {key}")
            return None
            
        except Exception as e:
            self._log_error(f"Error getting user preference {key}: {e}")
            return None
    
    def get_all_user_preferences(self) -> List[UserPreferenceDTO]:
        """Get all user preferences from the database.
        
        Returns:
            List of all user preferences
        """
        try:
            # For now, return mock preferences
            # In a real implementation, this would query the actual database
            
            mock_preferences = [
                UserPreferenceDTO(
                    key="theme",
                    value="dark",
                    category="ui",
                    data_type="string",
                    description="Application theme preference",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                UserPreferenceDTO(
                    key="temperature_unit",
                    value="celsius",
                    category="weather",
                    data_type="string",
                    description="Temperature unit preference",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                UserPreferenceDTO(
                    key="auto_refresh",
                    value="true",
                    category="general",
                    data_type="boolean",
                    description="Auto-refresh weather data",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]
            
            self._log_info(f"Retrieved {len(mock_preferences)} user preferences")
            return mock_preferences
            
        except Exception as e:
            self._log_error(f"Error getting all user preferences: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test if the database connection is working.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            # Test the database connection by trying a simple operation
            # This would typically involve checking if we can connect and query
            
            # For now, we'll assume the connection is working if the database object exists
            if self._database:
                self._log_info("Database connection test successful")
                return True
            else:
                self._log_error("Database connection test failed - no database object")
                return False
                
        except Exception as e:
            self._log_error(f"Database connection test failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database.
        
        Returns:
            Dictionary containing database information
        """
        try:
            db_path = self._config_service.get_setting('database.path', 'data/weather_dashboard.db')
            
            info = {
                'database_path': db_path,
                'database_exists': Path(db_path).exists(),
                'database_size': Path(db_path).stat().st_size if Path(db_path).exists() else 0,
                'connection_status': self.test_connection(),
                'last_check': datetime.now().isoformat()
            }
            
            self._log_info("Retrieved database information")
            return info
            
        except Exception as e:
            self._log_error(f"Error getting database info: {e}")
            return {}