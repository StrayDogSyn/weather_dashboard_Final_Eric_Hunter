"""Data Access Package

This package contains data access components:
- repositories: Repository pattern implementations
- unit_of_work: Unit of Work pattern implementation
- database_context: Database connection and transaction management
"""

from .unit_of_work import (
    TransactionState,
    TransactionInfo,
    IUnitOfWork,
    UnitOfWork,
    UnitOfWorkFactory,
    TransactionManager
)

from .database_context import (
    DatabaseType,
    ConnectionState,
    DatabaseConfig,
    ConnectionInfo,
    IDatabaseContext,
    DatabaseContext,
    DatabaseContextFactory
)

# Import repositories
from .repositories import (
    BaseRepository,
    ReadOnlyRepository,
    InMemoryRepository,
    WeatherRepository,
    ForecastRepository,
    PreferenceRepository,
    ActivityType,
    WeatherSuitability,
    ActivityRecommendation,
    ActivityRepository
)

__all__ = [
    # Unit of Work
    "TransactionState",
    "TransactionInfo",
    "IUnitOfWork",
    "UnitOfWork",
    "UnitOfWorkFactory",
    "TransactionManager",
    
    # Database Context
    "DatabaseType",
    "ConnectionState",
    "DatabaseConfig",
    "ConnectionInfo",
    "IDatabaseContext",
    "DatabaseContext",
    "DatabaseContextFactory",
    
    # Repositories
    "BaseRepository",
    "ReadOnlyRepository",
    "InMemoryRepository",
    "WeatherRepository",
    "ForecastRepository",
    "PreferenceRepository",
    "ActivityType",
    "WeatherSuitability",
    "ActivityRecommendation",
    "ActivityRepository"
]