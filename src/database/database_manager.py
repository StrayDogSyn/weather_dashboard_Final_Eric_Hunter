"""Database manager for SQLite operations.

Provides thread-safe database connections, connection pooling,
and database initialization.
"""

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_path: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            database_path: Path to SQLite database file
        """
        self._logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        # Set default database path
        if database_path is None:
            database_path = Path.cwd() / "data" / "weather_dashboard.db"
        else:
            database_path = Path(database_path)
            
        # Ensure database directory exists
        database_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._database_path = database_path
        self._sync_engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize database engines and create tables."""
        with self._lock:
            if self._initialized:
                return
                
            try:
                # Create sync engine
                sync_url = f"sqlite:///{self._database_path}"
                self._sync_engine = create_engine(
                    sync_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30
                    },
                    echo=False
                )
                
                # Create async engine
                async_url = f"sqlite+aiosqlite:///{self._database_path}"
                self._async_engine = create_async_engine(
                    async_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30
                    },
                    echo=False
                )
                
                # Configure SQLite for better performance
                self._configure_sqlite()
                
                # Create session factories
                self._sync_session_factory = sessionmaker(
                    bind=self._sync_engine,
                    expire_on_commit=False
                )
                
                self._async_session_factory = async_sessionmaker(
                    bind=self._async_engine,
                    expire_on_commit=False
                )
                
                # Create tables
                await self._create_tables()
                
                self._initialized = True
                self._logger.info(f"Database initialized: {self._database_path}")
                
            except Exception as e:
                self._logger.error(f"Failed to initialize database: {e}")
                raise
    
    def _configure_sqlite(self) -> None:
        """Configure SQLite for optimal performance."""
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for performance and reliability."""
            cursor = dbapi_connection.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Set synchronous mode for balance of safety and performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Set cache size (negative value = KB)
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            
            # Set temp store to memory
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            # Set mmap size for memory-mapped I/O
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            cursor.close()
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if self._async_engine is None:
            raise RuntimeError("Database not initialized")
            
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        self._logger.info("Database tables created/verified")
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup.
        
        Yields:
            AsyncSession: Database session
        """
        if not self._initialized:
            await self.initialize()
            
        if self._async_session_factory is None:
            raise RuntimeError("Async session factory not initialized")
            
        async with self._async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_session(self) -> Session:
        """Get synchronous database session.
        
        Returns:
            Session: Database session (caller must close)
        """
        if not self._initialized:
            # For sync operations, we need to initialize synchronously
            asyncio.run(self.initialize())
            
        if self._sync_session_factory is None:
            raise RuntimeError("Sync session factory not initialized")
            
        return self._sync_session_factory()
    
    async def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> None:
        """Execute raw SQL statement.
        
        Args:
            sql: SQL statement to execute
            params: Optional parameters for the SQL statement
        """
        async with self.get_async_session() as session:
            await session.execute(sql, params or {})
            await session.commit()
    
    async def backup_database(self, backup_path: str) -> None:
        """Create a backup of the database.
        
        Args:
            backup_path: Path where backup should be saved
        """
        import shutil
        
        try:
            # Ensure we're not in the middle of a transaction
            async with self.get_async_session() as session:
                await session.execute(text("PRAGMA wal_checkpoint(FULL)"))
                await session.commit()
            
            # Copy the database file
            shutil.copy2(self._database_path, backup_path)
            self._logger.info(f"Database backed up to: {backup_path}")
            
        except Exception as e:
            self._logger.error(f"Failed to backup database: {e}")
            raise
    
    async def get_database_info(self) -> dict:
        """Get database information and statistics.
        
        Returns:
            dict: Database information
        """
        info = {
            "database_path": str(self._database_path),
            "database_size": self._database_path.stat().st_size if self._database_path.exists() else 0,
            "initialized": self._initialized
        }
        
        if self._initialized:
            async with self.get_async_session() as session:
                # Get table information
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = [row[0] for row in result.fetchall()]
                info["tables"] = tables
                
                # Get database version
                result = await session.execute(text("PRAGMA user_version"))
                info["schema_version"] = result.scalar()
                
                # Get page count and page size
                result = await session.execute(text("PRAGMA page_count"))
                page_count = result.scalar()
                
                result = await session.execute(text("PRAGMA page_size"))
                page_size = result.scalar()
                
                info["page_count"] = page_count
                info["page_size"] = page_size
                info["calculated_size"] = page_count * page_size
        
        return info
    
    async def close(self) -> None:
        """Close database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
            
        if self._sync_engine:
            self._sync_engine.dispose()
            
        self._initialized = False
        self._logger.info("Database connections closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            if self._sync_engine:
                self._sync_engine.dispose()
        except Exception:
            pass  # Ignore cleanup errors