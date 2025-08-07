"""Database migration manager.

Handles schema migrations and version tracking.
"""

import hashlib
import logging
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .database_manager import DatabaseManager
from .models import DatabaseMigration


class Migration:
    """Represents a database migration."""

    def __init__(self, version: str, description: str, sql: str):
        """Initialize migration.

        Args:
            version: Migration version (e.g., '001', '002')
            description: Human-readable description
            sql: SQL statements to execute
        """
        self.version = version
        self.description = description
        self.sql = sql
        self.checksum = hashlib.sha256(sql.encode()).hexdigest()


class MigrationManager:
    """Manages database schema migrations."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize migration manager.

        Args:
            db_manager: Database manager instance
        """
        self._db_manager = db_manager
        self._logger = logging.getLogger(__name__)
        self._migrations: List[Migration] = []
        self._load_migrations()

    def _load_migrations(self) -> None:
        """Load predefined migrations."""
        # Migration 001: Initial schema (already handled by SQLAlchemy)
        self._migrations.append(
            Migration(
                version="001",
                description="Initial schema creation",
                sql="-- Initial schema created by SQLAlchemy",
            )
        )

        # Migration 002: Add indexes for performance
        self._migrations.append(
            Migration(
                version="002",
                description="Add performance indexes",
                sql="""
            CREATE INDEX IF NOT EXISTS idx_weather_location_temp 
                ON weather_history(location, temperature);
            CREATE INDEX IF NOT EXISTS idx_activity_user_date 
                ON activity_log(user_id, selected_at);
            CREATE INDEX IF NOT EXISTS idx_journal_user_mood 
                ON journal_entries(user_id, mood_score);
            """,
            )
        )

        # Migration 003: Add weather alerts table
        self._migrations.append(
            Migration(
                version="003",
                description="Add weather alerts functionality",
                sql="""
            CREATE TABLE IF NOT EXISTS weather_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                location TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                threshold_value REAL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_alerts_user_active 
                ON weather_alerts(user_id, is_active);
            CREATE INDEX IF NOT EXISTS idx_alerts_location ON weather_alerts(location);
            """,
            )
        )

        # Migration 004: Add weather comparison cache
        self._migrations.append(
            Migration(
                version="004",
                description="Add weather comparison cache table",
                sql="""
            CREATE TABLE IF NOT EXISTS weather_comparison_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                locations TEXT NOT NULL,
                comparison_data TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_comparison_cache_key 
                ON weather_comparison_cache(cache_key);
            CREATE INDEX IF NOT EXISTS idx_comparison_expires 
                ON weather_comparison_cache(expires_at);
            """,
            )
        )

        # Migration 005: Add user sessions table
        self._migrations.append(
            Migration(
                version="005",
                description="Add user sessions tracking",
                sql="""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                session_start DATETIME NOT NULL,
                session_end DATETIME,
                actions_count INTEGER DEFAULT 0,
                locations_viewed TEXT,
                features_used TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_sessions_user_start ON user_sessions(user_id, session_start);
            """,
            )
        )

    async def get_current_version(self) -> Optional[str]:
        """Get current database schema version.

        Returns:
            Optional[str]: Current version or None if no migrations applied
        """
        try:
            async with self._db_manager.get_async_session() as session:
                # Check if migrations table exists
                result = await session.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name='database_migrations'"
                    )
                )

                if not result.fetchone():
                    return None

                # Get latest migration
                result = await session.execute(
                    text(
                        "SELECT version FROM database_migrations "
                        "ORDER BY applied_at DESC LIMIT 1"
                    )
                )

                row = result.fetchone()
                return row[0] if row else None

        except Exception as e:
            self._logger.error(f"Failed to get current version: {e}")
            return None

    async def get_applied_migrations(self) -> List[DatabaseMigration]:
        """Get list of applied migrations.

        Returns:
            List[DatabaseMigration]: Applied migrations
        """
        try:
            async with self._db_manager.get_async_session() as session:
                # Check if migrations table exists
                result = await session.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name='database_migrations'"
                    )
                )

                if not result.fetchone():
                    return []

                # Get all migrations
                result = await session.execute(
                    text("SELECT * FROM database_migrations ORDER BY applied_at")
                )

                migrations = []
                for row in result.fetchall():
                    migration = DatabaseMigration(
                        id=row.id,
                        version=row.version,
                        description=row.description,
                        applied_at=row.applied_at,
                        checksum=row.checksum,
                    )
                    migrations.append(migration)

                return migrations

        except Exception as e:
            self._logger.error(f"Failed to get applied migrations: {e}")
            return []

    async def migrate(self) -> bool:
        """Apply pending migrations.

        Returns:
            bool: True if migrations were applied successfully
        """
        try:
            await self.get_current_version()
            applied_migrations = await self.get_applied_migrations()
            applied_versions = {m.version for m in applied_migrations}

            # Find pending migrations
            pending_migrations = [
                m for m in self._migrations if m.version not in applied_versions
            ]

            if not pending_migrations:
                self._logger.info("No pending migrations")
                return True

            # Sort migrations by version
            pending_migrations.sort(key=lambda x: x.version)

            async with self._db_manager.get_async_session() as session:
                # Ensure migrations table exists
                await self._ensure_migrations_table(session)

                # Apply each pending migration
                for migration in pending_migrations:
                    await self._apply_migration(session, migration)
                    self._logger.info(
                        f"Applied migration {migration.version}: "
                        f"{migration.description}"
                    )

                await session.commit()

            self._logger.info(f"Applied {len(pending_migrations)} migrations")
            return True

        except Exception as e:
            self._logger.error(f"Failed to apply migrations: {e}")
            return False

    async def _ensure_migrations_table(self, session: AsyncSession) -> None:
        """Ensure migrations table exists.

        Args:
            session: Database session
        """
        await session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS database_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                description TEXT,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        """
            )
        )

    async def _apply_migration(self, session: AsyncSession, migration: Migration) -> None:
        """Apply a single migration.

        Args:
            session: Database session
            migration: Migration to apply
        """
        try:
            # Execute migration SQL
            if migration.sql.strip() and not migration.sql.strip().startswith("--"):
                # Split SQL into individual statements
                statements = [s.strip() for s in migration.sql.split(";") if s.strip()]

                for statement in statements:
                    await session.execute(text(statement))

            # Record migration as applied
            await session.execute(
                text(
                    """
                INSERT INTO database_migrations (version, description, checksum)
                VALUES (:version, :description, :checksum)
            """
                ),
                {
                    "version": migration.version,
                    "description": migration.description,
                    "checksum": migration.checksum,
                },
            )

        except Exception as e:
            self._logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise

    async def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration (if possible).

        Args:
            version: Migration version to rollback

        Returns:
            bool: True if rollback was successful
        """
        try:
            async with self._db_manager.get_async_session() as session:
                # Remove migration record
                await session.execute(
                    text("DELETE FROM database_migrations WHERE version = :version"),
                    {"version": version},
                )

                await session.commit()

            self._logger.info(f"Rolled back migration {version}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to rollback migration {version}: {e}")
            return False

    async def validate_migrations(self) -> Dict[str, bool]:
        """Validate applied migrations against checksums.

        Returns:
            Dict[str, bool]: Validation results by version
        """
        try:
            applied_migrations = await self.get_applied_migrations()
            migration_map = {m.version: m for m in self._migrations}

            validation_results = {}

            for applied in applied_migrations:
                if applied.version in migration_map:
                    expected_checksum = migration_map[applied.version].checksum
                    validation_results[applied.version] = applied.checksum == expected_checksum
                else:
                    # Migration not found in current definitions
                    validation_results[applied.version] = False

            return validation_results

        except Exception as e:
            self._logger.error(f"Failed to validate migrations: {e}")
            return {}

    def add_migration(self, version: str, description: str, sql: str) -> None:
        """Add a new migration.

        Args:
            version: Migration version
            description: Migration description
            sql: SQL statements
        """
        migration = Migration(version, description, sql)
        self._migrations.append(migration)
        self._logger.info(f"Added migration {version}: {description}")

    async def apply_pending_migrations(self) -> bool:
        """Apply pending migrations (alias for migrate method).

        Returns:
            bool: True if migrations were applied successfully
        """
        return await self.migrate()

    async def get_migration_status(self) -> Dict[str, any]:
        """Get comprehensive migration status.

        Returns:
            Dict[str, any]: Migration status information
        """
        try:
            current_version = await self.get_current_version()
            applied_migrations = await self.get_applied_migrations()
            validation_results = await self.validate_migrations()

            applied_versions = {m.version for m in applied_migrations}
            pending_migrations = [m for m in self._migrations if m.version not in applied_versions]

            return {
                "current_version": current_version,
                "total_migrations": len(self._migrations),
                "applied_count": len(applied_migrations),
                "pending_count": len(pending_migrations),
                "pending_versions": [m.version for m in pending_migrations],
                "validation_results": validation_results,
                "all_valid": all(validation_results.values()) if validation_results else True,
            }

        except Exception as e:
            self._logger.error(f"Failed to get migration status: {e}")
            return {
                "current_version": None,
                "total_migrations": 0,
                "applied_count": 0,
                "pending_count": 0,
                "pending_versions": [],
                "validation_results": {},
                "all_valid": False,
            }
