"""Data Access Package

This package contains data access components:
- repositories: Repository pattern implementations
- unit_of_work: Unit of Work pattern implementation
- database_context: Database connection and transaction management
"""

from .database_context import (
    ConnectionInfo,
    ConnectionState,
    DatabaseConfig,
    DatabaseContext,
    DatabaseContextFactory,
    DatabaseType,
    IDatabaseContext,
)

# Import repositories
from .repositories import (
    ActivityRecommendation,
    ActivityRepository,
    ActivityType,
    BaseRepository,
    ForecastRepository,
    InMemoryRepository,
    PreferenceRepository,
    ReadOnlyRepository,
    WeatherRepository,
    WeatherSuitability,
)
from .unit_of_work import (
    IUnitOfWork,
    TransactionInfo,
    TransactionManager,
    TransactionState,
    UnitOfWork,
    UnitOfWorkFactory,
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
    "ActivityRepository",
]
