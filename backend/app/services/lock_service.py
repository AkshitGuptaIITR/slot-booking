# backend/app/services/lock_service.py
"""Database lock service for managing PostgreSQL transaction-level advisory locks.

Transaction-scoped locks (`pg_advisory_xact_lock`) are held in memory by PostgreSQL
for the duration of the current database transaction and are automatically released
upon COMMIT or ROLLBACK.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseLockService:
    """Provides namespaced PostgreSQL advisory locks for fine-grained serialization."""

    async def acquire_lock(
        self, db: AsyncSession, namespace: str, resource_id: str
    ) -> None:
        """Acquires a transaction-level advisory lock on a namespaced resource key.

        Blocks concurrent transactions attempting to acquire a lock on the same
        `(namespace, resource_id)` until the holding transaction commits or rolls back.
        """
        lock_key = f"{namespace}:{resource_id}"
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": lock_key},
        )

    async def acquire_user_lock(self, db: AsyncSession, user_id: str) -> None:
        """Acquires a transaction lock on a specific user_id.

        Used to serialize concurrent requests by the same user (e.g. enforcing quota limits).
        """
        await self.acquire_lock(db, namespace="user", resource_id=user_id)

    async def acquire_slot_lock(self, db: AsyncSession, slot_start: str) -> None:
        """Acquires a transaction lock on a specific slot timestamp.

        Used to serialize concurrent booking attempts on the exact same slot.
        """
        await self.acquire_lock(db, namespace="slot", resource_id=slot_start)


# Global singleton instance for application use
lock_service = DatabaseLockService()
