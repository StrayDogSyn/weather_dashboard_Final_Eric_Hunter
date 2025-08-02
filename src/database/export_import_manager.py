"""Data export/import manager.

Handles data export to JSON with validation and conflict resolution.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .database_manager import DatabaseManager
from .repositories import (
    WeatherRepository, PreferencesRepository,
    ActivityRepository, JournalRepository
)
from .backup_manager import BackupManager


class ConflictResolution:
    """Conflict resolution strategies."""
    SKIP = "skip"  # Skip conflicting records
    OVERWRITE = "overwrite"  # Overwrite existing records
    MERGE = "merge"  # Merge data where possible
    PROMPT = "prompt"  # Prompt user for decision


class ValidationError(Exception):
    """Data validation error."""
    pass


class ImportConflict:
    """Represents an import conflict."""
    
    def __init__(self, table: str, key: str, existing_data: Dict, new_data: Dict):
        """Initialize conflict.
        
        Args:
            table: Table name
            key: Conflict key
            existing_data: Existing record data
            new_data: New record data
        """
        self.table = table
        self.key = key
        self.existing_data = existing_data
        self.new_data = new_data
        self.resolution = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary.
        
        Returns:
            Dict: Conflict data
        """
        return {
            'table': self.table,
            'key': self.key,
            'existing_data': self.existing_data,
            'new_data': self.new_data,
            'resolution': self.resolution
        }


class ExportImportManager:
    """Manages data export and import operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize export/import manager.
        
        Args:
            db_manager: Database manager instance
        """
        self._db_manager = db_manager
        self._logger = logging.getLogger(__name__)
        
        # Repository instances will be created with sessions when needed
        self._weather_repo = None
        self._prefs_repo = None
        self._activity_repo = None
        self._journal_repo = None
        
        # Initialize backup manager
        self._backup_manager = BackupManager(db_manager)
    
    async def export_data(self, 
                         export_file: Path,
                         tables: Optional[List[str]] = None,
                         date_range: Optional[Tuple[datetime, datetime]] = None,
                         user_id: Optional[str] = None) -> bool:
        """Export data to JSON file.
        
        Args:
            export_file: Output file path
            tables: Optional list of tables to export
            date_range: Optional date range filter
            user_id: Optional user ID filter
            
        Returns:
            bool: True if export was successful
        """
        try:
            # Default to all tables
            if tables is None:
                tables = ['weather_history', 'user_preferences', 'activity_log', 'journal_entries']
            
            export_data = {
                'metadata': {
                    'version': '1.0',
                    'exported_at': datetime.now().isoformat(),
                    'export_type': 'selective',
                    'tables': tables,
                    'date_range': {
                        'start': date_range[0].isoformat() if date_range else None,
                        'end': date_range[1].isoformat() if date_range else None
                    },
                    'user_id': user_id,
                    'schema_version': await self._get_schema_version()
                },
                'data': {}
            }
            
            # Export each table
            for table in tables:
                table_data = await self._export_table(table, date_range, user_id)
                export_data['data'][table] = table_data
            
            # Add statistics
            export_data['metadata']['statistics'] = {
                table: len(data) for table, data in export_data['data'].items()
            }
            
            # Save to file
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self._logger.info(f"Data exported to {export_file}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to export data: {e}")
            return False
    
    async def _export_table(self, 
                           table: str,
                           date_range: Optional[Tuple[datetime, datetime]] = None,
                           user_id: Optional[str] = None) -> List[Dict]:
        """Export data from a specific table.
        
        Args:
            table: Table name
            date_range: Optional date range filter
            user_id: Optional user ID filter
            
        Returns:
            List[Dict]: Table data
        """
        async with self._db_manager.get_async_session() as session:
            weather_repo = WeatherRepository(session)
            prefs_repo = PreferencesRepository(session)
            activity_repo = ActivityRepository(session)
            journal_repo = JournalRepository(session)
            
            if table == 'weather_history':
                records = await weather_repo.get_history_range(
                    start_date=date_range[0] if date_range else None,
                    end_date=date_range[1] if date_range else None
                )
                return [record.to_dict() for record in records]
            
            elif table == 'user_preferences':
                if user_id:
                    records = await prefs_repo.get_user_preferences(user_id)
                    return [record.to_dict() for record in records]
                else:
                    records = await prefs_repo.get_all_preferences()
                    return [record.to_dict() for record in records]
        
            elif table == 'activity_log':
                records = await activity_repo.get_activities_range(
                    user_id=user_id,
                    start_date=date_range[0] if date_range else None,
                    end_date=date_range[1] if date_range else None
                )
                return [record.to_dict() for record in records]
            
            elif table == 'journal_entries':
                records = await journal_repo.get_entries_range(
                    user_id=user_id,
                    start_date=date_range[0] if date_range else None,
                    end_date=date_range[1] if date_range else None
                )
                return [record.to_dict() for record in records]
            
            else:
                self._logger.warning(f"Unknown table: {table}")
                return []
    
    async def import_data(self, 
                         import_file: Path,
                         conflict_resolution: str = ConflictResolution.SKIP,
                         validate_only: bool = False,
                         create_backup: bool = True) -> Dict[str, Any]:
        """Import data from JSON file.
        
        Args:
            import_file: Input file path
            conflict_resolution: How to handle conflicts
            validate_only: If True, only validate without importing
            create_backup: Whether to create backup before import
            
        Returns:
            Dict[str, Any]: Import results
        """
        try:
            # Load import data
            import_data = await self._load_import_file(import_file)
            
            if import_data is None:
                return {'success': False, 'error': 'Failed to load import file'}
            
            # Validate import data
            validation_result = await self._validate_import_data(import_data)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': validation_result['errors']
                }
            
            if validate_only:
                return {
                    'success': True,
                    'validation_only': True,
                    'statistics': validation_result['statistics']
                }
            
            # Create backup if requested
            backup_file = None
            if create_backup:
                backup_file = await self._backup_manager.create_backup(
                    f"pre_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            # Detect conflicts
            conflicts = await self._detect_conflicts(import_data)
            
            # Import data
            import_result = await self._import_data_with_conflicts(
                import_data, conflicts, conflict_resolution
            )
            
            return {
                'success': True,
                'imported_records': import_result['imported'],
                'skipped_records': import_result['skipped'],
                'conflicts': len(conflicts),
                'backup_file': str(backup_file) if backup_file else None,
                'statistics': validation_result['statistics']
            }
            
        except Exception as e:
            self._logger.error(f"Failed to import data: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _load_import_file(self, import_file: Path) -> Optional[Dict]:
        """Load import data from file.
        
        Args:
            import_file: Import file path
            
        Returns:
            Optional[Dict]: Import data or None if failed
        """
        try:
            if not import_file.exists():
                self._logger.error(f"Import file not found: {import_file}")
                return None
            
            with open(import_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self._logger.error(f"Failed to load import file: {e}")
            return None
    
    async def _validate_import_data(self, import_data: Dict) -> Dict[str, Any]:
        """Validate import data structure and content.
        
        Args:
            import_data: Import data to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        errors = []
        statistics = {}
        
        try:
            # Check required structure
            if 'metadata' not in import_data:
                errors.append("Missing metadata section")
            
            if 'data' not in import_data:
                errors.append("Missing data section")
                return {'valid': False, 'errors': errors, 'statistics': {}}
            
            # Validate metadata
            metadata = import_data['metadata']
            required_metadata = ['version', 'exported_at']
            
            for field in required_metadata:
                if field not in metadata:
                    errors.append(f"Missing metadata field: {field}")
            
            # Validate data sections
            data = import_data['data']
            
            for table_name, table_data in data.items():
                if not isinstance(table_data, list):
                    errors.append(f"Invalid data format for table: {table_name}")
                    continue
                
                # Validate table records
                table_errors = await self._validate_table_data(table_name, table_data)
                errors.extend(table_errors)
                
                statistics[table_name] = len(table_data)
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'statistics': statistics
            }
            
        except Exception as e:
            self._logger.error(f"Validation error: {e}")
            return {
                'valid': False,
                'errors': [f"Validation exception: {str(e)}"],
                'statistics': {}
            }
    
    async def _validate_table_data(self, table_name: str, table_data: List[Dict]) -> List[str]:
        """Validate data for a specific table.
        
        Args:
            table_name: Table name
            table_data: Table data to validate
            
        Returns:
            List[str]: Validation errors
        """
        errors = []
        
        # Define required fields for each table
        required_fields = {
            'weather_history': ['location', 'temperature', 'conditions', 'timestamp'],
            'user_preferences': ['user_id', 'preference_key', 'preference_value'],
            'activity_log': ['user_id', 'activity_type', 'selected_at'],
            'journal_entries': ['user_id', 'entry_date', 'mood_score']
        }
        
        if table_name not in required_fields:
            errors.append(f"Unknown table: {table_name}")
            return errors
        
        required = required_fields[table_name]
        
        for i, record in enumerate(table_data):
            if not isinstance(record, dict):
                errors.append(f"{table_name}[{i}]: Record must be a dictionary")
                continue
            
            # Check required fields
            for field in required:
                if field not in record:
                    errors.append(f"{table_name}[{i}]: Missing required field '{field}'")
            
            # Validate data types and formats
            validation_errors = self._validate_record_fields(table_name, record, i)
            errors.extend(validation_errors)
        
        return errors
    
    def _validate_record_fields(self, table_name: str, record: Dict, index: int) -> List[str]:
        """Validate individual record fields.
        
        Args:
            table_name: Table name
            record: Record to validate
            index: Record index for error reporting
            
        Returns:
            List[str]: Validation errors
        """
        errors = []
        
        try:
            if table_name == 'weather_history':
                # Validate temperature
                if 'temperature' in record:
                    try:
                        float(record['temperature'])
                    except (ValueError, TypeError):
                        errors.append(f"{table_name}[{index}]: Invalid temperature value")
                
                # Validate timestamp
                if 'timestamp' in record:
                    try:
                        datetime.fromisoformat(str(record['timestamp']).replace('Z', '+00:00'))
                    except ValueError:
                        errors.append(f"{table_name}[{index}]: Invalid timestamp format")
            
            elif table_name == 'journal_entries':
                # Validate mood score
                if 'mood_score' in record:
                    try:
                        score = float(record['mood_score'])
                        if not (1 <= score <= 10):
                            errors.append(f"{table_name}[{index}]: Mood score must be between 1 and 10")
                    except (ValueError, TypeError):
                        errors.append(f"{table_name}[{index}]: Invalid mood score")
                
                # Validate entry date
                if 'entry_date' in record:
                    try:
                        datetime.fromisoformat(str(record['entry_date']).replace('Z', '+00:00'))
                    except ValueError:
                        errors.append(f"{table_name}[{index}]: Invalid entry date format")
            
            elif table_name == 'activity_log':
                # Validate selected_at
                if 'selected_at' in record:
                    try:
                        datetime.fromisoformat(str(record['selected_at']).replace('Z', '+00:00'))
                    except ValueError:
                        errors.append(f"{table_name}[{index}]: Invalid selected_at format")
        
        except Exception as e:
            errors.append(f"{table_name}[{index}]: Validation error - {str(e)}")
        
        return errors
    
    async def _detect_conflicts(self, import_data: Dict) -> List[ImportConflict]:
        """Detect conflicts between import data and existing data.
        
        Args:
            import_data: Import data
            
        Returns:
            List[ImportConflict]: Detected conflicts
        """
        conflicts = []
        
        try:
            data = import_data['data']
            
            for table_name, table_data in data.items():
                table_conflicts = await self._detect_table_conflicts(table_name, table_data)
                conflicts.extend(table_conflicts)
        
        except Exception as e:
            self._logger.error(f"Failed to detect conflicts: {e}")
        
        return conflicts
    
    async def _detect_table_conflicts(self, table_name: str, table_data: List[Dict]) -> List[ImportConflict]:
        """Detect conflicts for a specific table.
        
        Args:
            table_name: Table name
            table_data: Table data
            
        Returns:
            List[ImportConflict]: Table conflicts
        """
        conflicts = []
        
        # For now, we'll implement basic conflict detection
        # In a real implementation, you'd check against existing database records
        
        # Example: Check for duplicate entries within import data
        seen_keys = set()
        
        for record in table_data:
            # Create a key based on table type
            if table_name == 'weather_history':
                key = f"{record.get('location')}_{record.get('timestamp')}"
            elif table_name == 'user_preferences':
                key = f"{record.get('user_id')}_{record.get('preference_key')}"
            elif table_name == 'activity_log':
                key = f"{record.get('user_id')}_{record.get('selected_at')}"
            elif table_name == 'journal_entries':
                key = f"{record.get('user_id')}_{record.get('entry_date')}"
            else:
                continue
            
            if key in seen_keys:
                conflict = ImportConflict(
                    table=table_name,
                    key=key,
                    existing_data={},  # Would be populated from database
                    new_data=record
                )
                conflicts.append(conflict)
            else:
                seen_keys.add(key)
        
        return conflicts
    
    async def _import_data_with_conflicts(self, 
                                        import_data: Dict,
                                        conflicts: List[ImportConflict],
                                        resolution: str) -> Dict[str, int]:
        """Import data handling conflicts according to resolution strategy.
        
        Args:
            import_data: Import data
            conflicts: Detected conflicts
            resolution: Conflict resolution strategy
            
        Returns:
            Dict[str, int]: Import statistics
        """
        imported = 0
        skipped = 0
        
        try:
            data = import_data['data']
            
            for table_name, table_data in data.items():
                table_result = await self._import_table_data(
                    table_name, table_data, conflicts, resolution
                )
                imported += table_result['imported']
                skipped += table_result['skipped']
        
        except Exception as e:
            self._logger.error(f"Failed to import data: {e}")
            raise
        
        return {'imported': imported, 'skipped': skipped}
    
    async def _import_table_data(self, 
                               table_name: str,
                               table_data: List[Dict],
                               conflicts: List[ImportConflict],
                               resolution: str) -> Dict[str, int]:
        """Import data for a specific table.
        
        Args:
            table_name: Table name
            table_data: Table data
            conflicts: Conflicts for this table
            resolution: Conflict resolution strategy
            
        Returns:
            Dict[str, int]: Import statistics
        """
        imported = 0
        skipped = 0
        
        # Get conflicts for this table
        table_conflicts = {c.key: c for c in conflicts if c.table == table_name}
        
        for record in table_data:
            try:
                # Check if this record has conflicts
                record_key = self._get_record_key(table_name, record)
                
                if record_key in table_conflicts:
                    # Handle conflict based on resolution strategy
                    if resolution == ConflictResolution.SKIP:
                        skipped += 1
                        continue
                    elif resolution == ConflictResolution.OVERWRITE:
                        # Continue with import (will overwrite)
                        pass
                    # Add more resolution strategies as needed
                
                # Import the record
                success = await self._import_record(table_name, record)
                
                if success:
                    imported += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                self._logger.error(f"Failed to import record: {e}")
                skipped += 1
        
        return {'imported': imported, 'skipped': skipped}
    
    def _get_record_key(self, table_name: str, record: Dict) -> str:
        """Generate a key for a record.
        
        Args:
            table_name: Table name
            record: Record data
            
        Returns:
            str: Record key
        """
        if table_name == 'weather_history':
            return f"{record.get('location')}_{record.get('timestamp')}"
        elif table_name == 'user_preferences':
            return f"{record.get('user_id')}_{record.get('preference_key')}"
        elif table_name == 'activity_log':
            return f"{record.get('user_id')}_{record.get('selected_at')}"
        elif table_name == 'journal_entries':
            return f"{record.get('user_id')}_{record.get('entry_date')}"
        else:
            return str(hash(str(record)))
    
    async def _import_record(self, table_name: str, record: Dict) -> bool:
        """Import a single record.
        
        Args:
            table_name: Table name
            record: Record data
            
        Returns:
            bool: True if import was successful
        """
        try:
            if table_name == 'weather_history':
                await self._weather_repo.save_weather_data(
                    location=record['location'],
                    temperature=record['temperature'],
                    conditions=record['conditions'],
                    humidity=record.get('humidity'),
                    wind_speed=record.get('wind_speed'),
                    pressure=record.get('pressure'),
                    timestamp=datetime.fromisoformat(str(record['timestamp']).replace('Z', '+00:00'))
                )
            
            elif table_name == 'user_preferences':
                await self._prefs_repo.save_preference(
                    user_id=record['user_id'],
                    key=record['preference_key'],
                    value=record['preference_value']
                )
            
            elif table_name == 'activity_log':
                await self._activity_repo.log_activity(
                    user_id=record['user_id'],
                    activity_type=record['activity_type'],
                    activity_data=record.get('activity_data', '{}'),
                    location=record.get('location'),
                    timestamp=datetime.fromisoformat(str(record['selected_at']).replace('Z', '+00:00'))
                )
            
            elif table_name == 'journal_entries':
                await self._journal_repo.create_entry(
                    user_id=record['user_id'],
                    mood_score=record['mood_score'],
                    notes=record.get('notes', ''),
                    weather_snapshot=record.get('weather_snapshot', '{}'),
                    entry_date=datetime.fromisoformat(str(record['entry_date']).replace('Z', '+00:00'))
                )
            
            else:
                self._logger.warning(f"Unknown table for import: {table_name}")
                return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to import record to {table_name}: {e}")
            return False
    
    async def _get_schema_version(self) -> Optional[str]:
        """Get current database schema version.
        
        Returns:
            Optional[str]: Schema version
        """
        try:
            from .migration_manager import MigrationManager
            migration_manager = MigrationManager(self._db_manager)
            return await migration_manager.get_current_version()
        except Exception:
            return None
    
    async def export_schema(self, schema_file: Path) -> bool:
        """Export database schema information.
        
        Args:
            schema_file: Output file for schema
            
        Returns:
            bool: True if export was successful
        """
        try:
            schema_info = await self._db_manager.get_database_info()
            
            schema_data = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'database_version': await self._get_schema_version()
                },
                'schema': schema_info
            }
            
            schema_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2, default=str)
            
            self._logger.info(f"Schema exported to {schema_file}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to export schema: {e}")
            return False