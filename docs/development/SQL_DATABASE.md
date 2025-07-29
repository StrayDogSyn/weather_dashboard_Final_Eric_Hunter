# SQL Database Integration

The Weather Dashboard uses SQLite for robust data management with improved performance and data integrity.

## Overview

**Hybrid Storage System**:

- **JSON Files** - Backup storage and export
- **Automatic Backups** - Daily JSON backups

## Database Structure

**Tables**:

`user_preferences`, `favorite_cities`, `weather_history`, `journal_entries`, `activity_suggestions`

**Auto Migration**:

Creates database, migrates JSON data, backs up original files

## Setup

1. **Install Dependencies**: `pip install sqlalchemy` (optional)
2. **Run Setup**: `python setup_sql_database.py`
3. **Verify**: `python verify_sql_setup.py`

## Configuration

```env
WEATHER_STORAGE_TYPE=sql
WEATHER_DATABASE_PATH=data/weather_dashboard.db
```

## Architecture

**Storage Factory**: Automatically chooses SQL or file storage based on configuration
**Implementations**: SQLDataStorage (SQLAlchemy), FileDataStorage (JSON)
**Backward Compatibility**: Existing JSON installations continue to work

## Management

**Viewing Data**: Use SQLite browser or `sqlite3 data/weather_dashboard.db`
**Backup**: Copy `weather_dashboard.db` file
**Benefits**: Faster queries, data integrity, concurrent access, scalability

## Migration

**Automatic**: JSON files → SQL tables during setup

**Manual**: Use DataStorageFactory for programmatic migration

## Troubleshooting

**Common Issues**:

- Import errors → Run from project root, check virtual environment
- Database locked → Close other applications, restart
- Migration failures → Check file permissions, verify JSON format

**Revert to JSON**: Set `WEATHER_STORAGE_TYPE=file` and restore from `json_backup/`

## File Structure

```text
data/
├── weather_dashboard.db
├── database.py
└── json_backup/

src/services/
├── storage_factory.py
├── sql_data_storage.py
└── data_storage.py
```

---

For troubleshooting, run `python verify_sql_setup.py` and check application logs.
