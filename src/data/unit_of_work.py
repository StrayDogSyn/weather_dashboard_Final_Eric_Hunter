"""Unit of Work Pattern Implementation

Provides transaction management and coordination across multiple repositories.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar

from .database_context import DatabaseContext
from .repositories.activity_repository import ActivityRepository
from .repositories.base_repository import BaseRepository
from .repositories.preference_repository import PreferenceRepository
from .repositories.weather_repository import ForecastRepository, WeatherRepository

T = TypeVar("T")


class TransactionState(Enum):
    """Transaction state enumeration."""

    PENDING = "pending"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class TransactionInfo:
    """Information about a transaction."""

    transaction_id: str
    state: TransactionState
    started_at: datetime
    completed_at: Optional[datetime] = None
    repositories: List[str] = None
    operations_count: int = 0
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.repositories is None:
            self.repositories = []


class IUnitOfWork(ABC):
    """Abstract Unit of Work interface."""

    @abstractmethod
    async def __aenter__(self):
        """Enter async context manager."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""

    @abstractmethod
    async def commit(self) -> bool:
        """Commit all changes."""

    @abstractmethod
    async def rollback(self) -> bool:
        """Rollback all changes."""

    @abstractmethod
    def get_repository(self, repository_type: Type[T]) -> T:
        """Get repository instance."""


class UnitOfWork(IUnitOfWork):
    """Concrete Unit of Work implementation."""

    def __init__(self, db_context: DatabaseContext):
        self.db_context = db_context
        self._repositories: Dict[Type, BaseRepository] = {}
        self._transaction_info: Optional[TransactionInfo] = None
        self._is_active = False
        self._operations: List[Dict[str, Any]] = []

        # Initialize repositories
        self._weather_repository = None
        self._forecast_repository = None
        self._preference_repository = None
        self._activity_repository = None

    @property
    def weather_repository(self) -> WeatherRepository:
        """Get weather repository."""
        if self._weather_repository is None:
            self._weather_repository = WeatherRepository(self.db_context.weather_db_path)
        return self._weather_repository

    @property
    def forecast_repository(self) -> ForecastRepository:
        """Get forecast repository."""
        if self._forecast_repository is None:
            self._forecast_repository = ForecastRepository(self.db_context.forecast_db_path)
        return self._forecast_repository

    @property
    def preference_repository(self) -> PreferenceRepository:
        """Get preference repository."""
        if self._preference_repository is None:
            self._preference_repository = PreferenceRepository(self.db_context.preferences_db_path)
        return self._preference_repository

    @property
    def activity_repository(self) -> ActivityRepository:
        """Get activity repository."""
        if self._activity_repository is None:
            self._activity_repository = ActivityRepository(self.db_context.activities_db_path)
        return self._activity_repository

    @property
    def transaction_info(self) -> Optional[TransactionInfo]:
        """Get current transaction information."""
        return self._transaction_info

    @property
    def is_active(self) -> bool:
        """Check if transaction is active."""
        return self._is_active

    async def __aenter__(self):
        """Start transaction context."""
        await self.begin_transaction()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End transaction context."""
        if exc_type is not None:
            await self.rollback()
            return False
        else:
            await self.commit()
            return True

    async def begin_transaction(self) -> str:
        """Begin a new transaction."""
        if self._is_active:
            raise RuntimeError("Transaction is already active")

        transaction_id = f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        self._transaction_info = TransactionInfo(
            transaction_id=transaction_id, state=TransactionState.PENDING, started_at=datetime.now()
        )

        try:
            # Begin transaction in database context
            await self.db_context.begin_transaction()

            self._is_active = True
            self._transaction_info.state = TransactionState.ACTIVE
            self._operations.clear()

            return transaction_id

        except Exception as e:
            self._transaction_info.state = TransactionState.FAILED
            self._transaction_info.error_message = str(e)
            raise

    async def commit(self) -> bool:
        """Commit all changes in the transaction."""
        if not self._is_active:
            raise RuntimeError("No active transaction to commit")

        try:
            # Validate all repositories before committing
            await self._validate_repositories()

            # Commit in database context
            await self.db_context.commit_transaction()

            # Update transaction info
            self._transaction_info.state = TransactionState.COMMITTED
            self._transaction_info.completed_at = datetime.now()
            self._transaction_info.operations_count = len(self._operations)

            self._is_active = False

            return True

        except Exception as e:
            self._transaction_info.state = TransactionState.FAILED
            self._transaction_info.error_message = str(e)
            await self.rollback()
            raise

    async def rollback(self) -> bool:
        """Rollback all changes in the transaction."""
        if not self._is_active:
            return True  # Nothing to rollback

        try:
            # Rollback in database context
            await self.db_context.rollback_transaction()

            # Clear repository caches
            await self._clear_repository_caches()

            # Update transaction info
            self._transaction_info.state = TransactionState.ROLLED_BACK
            self._transaction_info.completed_at = datetime.now()

            self._is_active = False

            return True

        except Exception as e:
            self._transaction_info.state = TransactionState.FAILED
            self._transaction_info.error_message = str(e)
            raise

    def get_repository(self, repository_type: Type[T]) -> T:
        """Get repository instance by type."""
        if repository_type == WeatherRepository:
            return self.weather_repository
        elif repository_type == ForecastRepository:
            return self.forecast_repository
        elif repository_type == PreferenceRepository:
            return self.preference_repository
        elif repository_type == ActivityRepository:
            return self.activity_repository
        else:
            raise ValueError(f"Unknown repository type: {repository_type}")

    def register_operation(
        self,
        operation_type: str,
        repository: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Register an operation for tracking."""
        operation = {
            "type": operation_type,
            "repository": repository,
            "entity_id": entity_id,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }

        self._operations.append(operation)

        if self._transaction_info and repository not in self._transaction_info.repositories:
            self._transaction_info.repositories.append(repository)

    async def _validate_repositories(self) -> bool:
        """Validate all repositories before commit."""
        repositories = [
            ("weather", self._weather_repository),
            ("forecast", self._forecast_repository),
            ("preference", self._preference_repository),
            ("activity", self._activity_repository),
        ]

        for name, repo in repositories:
            if repo is not None:
                try:
                    is_healthy = await repo.health_check()
                    if not is_healthy:
                        raise RuntimeError(f"Repository {name} failed health check")
                except Exception as e:
                    raise RuntimeError(f"Repository {name} validation failed: {str(e)}")

        return True

    async def _clear_repository_caches(self):
        """Clear caches in all repositories."""
        repositories = [
            self._weather_repository,
            self._forecast_repository,
            self._preference_repository,
            self._activity_repository,
        ]

        for repo in repositories:
            if repo is not None:
                try:
                    repo._clear_cache()
                except AttributeError:
                    # Repository doesn't have cache clearing method
                    pass

    async def save_changes(self) -> bool:
        """Save all pending changes without committing transaction."""
        if not self._is_active:
            raise RuntimeError("No active transaction")

        # This could be used for intermediate saves
        # For now, just validate repositories
        return await self._validate_repositories()

    def get_operations_summary(self) -> Dict[str, Any]:
        """Get summary of operations in current transaction."""
        if not self._transaction_info:
            return {}

        operations_by_type = {}
        operations_by_repo = {}

        for op in self._operations:
            op_type = op["type"]
            repo = op["repository"]

            operations_by_type[op_type] = operations_by_type.get(op_type, 0) + 1
            operations_by_repo[repo] = operations_by_repo.get(repo, 0) + 1

        return {
            "transaction_id": self._transaction_info.transaction_id,
            "state": self._transaction_info.state.value,
            "started_at": self._transaction_info.started_at.isoformat(),
            "operations_count": len(self._operations),
            "operations_by_type": operations_by_type,
            "operations_by_repository": operations_by_repo,
            "repositories_involved": self._transaction_info.repositories.copy(),
        }


class UnitOfWorkFactory:
    """Factory for creating Unit of Work instances."""

    def __init__(self, db_context: DatabaseContext):
        self.db_context = db_context

    def create(self) -> UnitOfWork:
        """Create a new Unit of Work instance."""
        return UnitOfWork(self.db_context)

    @asynccontextmanager
    async def create_scope(self):
        """Create a Unit of Work scope with automatic cleanup."""
        uow = self.create()
        try:
            async with uow:
                yield uow
        finally:
            # Ensure cleanup
            if uow.is_active:
                await uow.rollback()


class TransactionManager:
    """Manages multiple transactions and provides transaction history."""

    def __init__(self, uow_factory: UnitOfWorkFactory):
        self.uow_factory = uow_factory
        self._transaction_history: List[TransactionInfo] = []
        self._active_transactions: Dict[str, UnitOfWork] = {}

    async def create_transaction(self) -> UnitOfWork:
        """Create and start a new transaction."""
        uow = self.uow_factory.create()
        transaction_id = await uow.begin_transaction()

        self._active_transactions[transaction_id] = uow

        return uow

    async def complete_transaction(self, transaction_id: str, commit: bool = True) -> bool:
        """Complete a transaction by committing or rolling back."""
        if transaction_id not in self._active_transactions:
            raise ValueError(f"Transaction {transaction_id} not found")

        uow = self._active_transactions[transaction_id]

        try:
            if commit:
                result = await uow.commit()
            else:
                result = await uow.rollback()

            # Move to history
            if uow.transaction_info:
                self._transaction_history.append(uow.transaction_info)

            # Remove from active
            del self._active_transactions[transaction_id]

            return result

        except Exception as e:
            # Ensure cleanup on error
            if uow.transaction_info:
                uow.transaction_info.state = TransactionState.FAILED
                uow.transaction_info.error_message = str(e)
                self._transaction_history.append(uow.transaction_info)

            if transaction_id in self._active_transactions:
                del self._active_transactions[transaction_id]

            raise

    def get_active_transactions(self) -> List[str]:
        """Get list of active transaction IDs."""
        return list(self._active_transactions.keys())

    def get_transaction_history(self, limit: int = 50) -> List[TransactionInfo]:
        """Get transaction history."""
        return self._transaction_history[-limit:]

    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics."""
        total_transactions = len(self._transaction_history)

        if total_transactions == 0:
            return {
                "total_transactions": 0,
                "active_transactions": len(self._active_transactions),
                "success_rate": 0.0,
            }

        successful = sum(
            1 for t in self._transaction_history if t.state == TransactionState.COMMITTED
        )
        failed = sum(1 for t in self._transaction_history if t.state == TransactionState.FAILED)
        rolled_back = sum(
            1 for t in self._transaction_history if t.state == TransactionState.ROLLED_BACK
        )

        return {
            "total_transactions": total_transactions,
            "active_transactions": len(self._active_transactions),
            "successful_transactions": successful,
            "failed_transactions": failed,
            "rolled_back_transactions": rolled_back,
            "success_rate": successful / total_transactions if total_transactions > 0 else 0.0,
        }

    async def cleanup_completed_transactions(self, max_history: int = 1000):
        """Clean up old transaction history."""
        if len(self._transaction_history) > max_history:
            self._transaction_history = self._transaction_history[-max_history:]

    async def rollback_all_active(self) -> int:
        """Rollback all active transactions (emergency cleanup)."""
        count = 0
        transaction_ids = list(self._active_transactions.keys())

        for transaction_id in transaction_ids:
            try:
                await self.complete_transaction(transaction_id, commit=False)
                count += 1
            except Exception:
                # Continue with other transactions
                pass

        return count
