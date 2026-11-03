# backend/app/services/hold_service.py
"""
NOTE:
This in-memory implementation is intended strictly for demonstration and
single-process development environments.

In a production environment (with multiple Uvicorn workers or multi-instance
deployments behind a load balancer), this in-memory dictionary is NOT shared
across worker processes. For production systems, replace this service with a
distributed store such as Redis (e.g., using `SET slot_key user_id NX EX ttl_seconds`
or a Redlock pattern) to ensure hold states are globally coordinated across all instances.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import threading
import time
from typing import Optional


@dataclass
class SlotHold:
    slot_start: str
    user_id: str
    expires_at: float  # Unix timestamp in seconds


class InMemoryHoldService:
    """Thread-safe in-memory store for managing temporary slot holds with TTL."""

    def __init__(self, default_ttl_seconds: int = 120):
        # Maps slot_start (ISO string or identifier) -> SlotHold
        self._holds: dict[str, SlotHold] = {}
        self._lock = threading.Lock()
        self.default_ttl_seconds = default_ttl_seconds

    def acquire_hold(
        self, slot_start: str, user_id: str, ttl_seconds: Optional[int] = None
    ) -> bool:
        """Attempts to hold a slot for a specific user.

        - If the slot is currently held by ANOTHER user and not expired, returns False.
        - If the slot is not held, held by the SAME user, or the previous hold has expired,
          creates or refreshes the hold and returns True.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        now = time.time()

        with self._lock:
            existing = self._holds.get(slot_start)

            # Check if active hold is owned by someone else
            if existing and existing.expires_at > now and existing.user_id != user_id:
                return False

            # Acquire or renew hold
            self._holds[slot_start] = SlotHold(
                slot_start=slot_start,
                user_id=user_id,
                expires_at=now + ttl,
            )
            return True

    def is_held_by_other(self, slot_start: str, user_id: str) -> bool:
        """Checks if a slot is actively held by a user other than user_id.

        Expired holds are cleaned up lazily.
        """
        now = time.time()

        with self._lock:
            existing = self._holds.get(slot_start)
            if not existing:
                return False

            if existing.expires_at <= now:
                # Expired hold: prune lazily
                del self._holds[slot_start]
                return False

            return existing.user_id != user_id

    def release_hold(self, slot_start: str, user_id: str) -> bool:
        """Releases a hold if it is owned by the specified user.

        Returns True if released, False if not found or owned by someone else.
        """
        with self._lock:
            existing = self._holds.get(slot_start)
            if existing and existing.user_id == user_id:
                del self._holds[slot_start]
                return True
            return False

    def get_hold_info(self, slot_start: str) -> Optional[dict]:
        """Returns the hold details and remaining seconds if actively held."""
        now = time.time()

        with self._lock:
            existing = self._holds.get(slot_start)
            if not existing:
                return None

            remaining = existing.expires_at - now
            if remaining <= 0:
                del self._holds[slot_start]
                return None

            return {
                "slot_start": existing.slot_start,
                "user_id": existing.user_id,
                "remaining_seconds": max(0, int(remaining)),
            }

    def cleanup_expired(self) -> int:
        """Removes all expired holds and returns the count of removed items."""
        now = time.time()
        removed_count = 0

        with self._lock:
            expired_keys = [
                key for key, hold in self._holds.items() if hold.expires_at <= now
            ]
            for key in expired_keys:
                del self._holds[key]
                removed_count += 1

        return removed_count


# Global singleton instance for application use
hold_service = InMemoryHoldService()
