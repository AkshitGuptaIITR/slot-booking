from datetime import datetime, time, timedelta, timezone
import time as stdlib_time
import uuid
from zoneinfo import ZoneInfo
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.hold_service import InMemoryHoldService, hold_service

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


def get_next_valid_weekday_slot(hour: int = 10, minute: int = 0) -> datetime:
    """Helper to return a valid upcoming weekday slot in UTC."""
    now_ist = datetime.now(KOLKATA_TZ)
    days_ahead = 2
    target = (now_ist + timedelta(days=days_ahead)).date()
    while target.weekday() >= 5:
        days_ahead += 1
        target = (now_ist + timedelta(days=days_ahead)).date()

    slot_ist = datetime.combine(target, time(hour, minute), tzinfo=KOLKATA_TZ)
    return slot_ist.astimezone(timezone.utc)


# ==========================================
# 1. Unit Tests for InMemoryHoldService
# ==========================================


def test_hold_service_acquire_and_release():
    service = InMemoryHoldService(default_ttl_seconds=10)
    slot_key = "2026-11-05T04:30:00Z"

    # User A acquires hold
    assert service.acquire_hold(slot_key, "user_A") is True
    assert service.is_held_by_other(slot_key, "user_A") is False
    assert service.is_held_by_other(slot_key, "user_B") is True

    # User A releases hold
    assert service.release_hold(slot_key, "user_A") is True
    assert service.is_held_by_other(slot_key, "user_B") is False


def test_hold_service_collision_prevention():
    service = InMemoryHoldService(default_ttl_seconds=10)
    slot_key = "2026-11-05T04:30:00Z"

    # User A acquires hold
    assert service.acquire_hold(slot_key, "user_A") is True

    # User B attempts to acquire hold on same slot -> blocked
    assert service.acquire_hold(slot_key, "user_B") is False

    # User A can re-acquire/renew hold
    assert service.acquire_hold(slot_key, "user_A") is True


def test_hold_service_unauthorized_release_fails():
    service = InMemoryHoldService(default_ttl_seconds=10)
    slot_key = "2026-11-05T04:30:00Z"

    service.acquire_hold(slot_key, "user_A")

    # User B cannot release User A's hold
    assert service.release_hold(slot_key, "user_B") is False
    # Hold is still active for User A
    assert service.is_held_by_other(slot_key, "user_B") is True


def test_hold_service_ttl_automatic_expiration():
    service = InMemoryHoldService(default_ttl_seconds=1)
    slot_key = "2026-11-05T04:30:00Z"

    # User A acquires a 1-second hold
    service.acquire_hold(slot_key, "user_A", ttl_seconds=1)
    assert service.is_held_by_other(slot_key, "user_B") is True

    # Wait for TTL to expire
    stdlib_time.sleep(1.1)

    # Lock is now expired and automatically freed
    assert service.is_held_by_other(slot_key, "user_B") is False

    # User B can now acquire the freed slot
    assert service.acquire_hold(slot_key, "user_B") is True


def test_hold_service_cleanup_expired():
    service = InMemoryHoldService(default_ttl_seconds=1)
    service.acquire_hold("slot_1", "user_A", ttl_seconds=1)
    service.acquire_hold("slot_2", "user_B", ttl_seconds=10)

    stdlib_time.sleep(1.1)

    # slot_1 has expired, slot_2 is still active
    removed = service.cleanup_expired()
    assert removed == 1
    assert service.is_held_by_other("slot_2", "user_A") is True


# ==========================================
# 2. Integration / API Endpoints Tests
# ==========================================


@pytest.mark.asyncio
async def test_api_hold_and_collision_flow():
    user_alice = f"alice_{uuid.uuid4().hex[:8]}"
    user_bob = f"bob_{uuid.uuid4().hex[:8]}"

    slot_utc = get_next_valid_weekday_slot(10, 0)
    slot_iso = slot_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Clean state
    hold_service.release_hold(slot_iso, user_alice)
    hold_service.release_hold(slot_iso, user_bob)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Alice holds the slot
        alice_res = await client.post(
            "/slots/hold",
            headers={"X-User-Id": user_alice},
            json={"slotStart": slot_iso},
        )
        assert alice_res.status_code == 200
        alice_data = alice_res.json()
        assert alice_data["success"] is True
        assert alice_data["remainingSeconds"] > 0

        # Step 2: Bob tries to hold the same slot -> 409 Conflict
        bob_res = await client.post(
            "/slots/hold",
            headers={"X-User-Id": user_bob},
            json={"slotStart": slot_iso},
        )
        assert bob_res.status_code == 409
        bob_err = bob_res.json()["error"]
        assert bob_err["code"] == "SLOT_HELD"

        # Step 3: GET /slots shows slot as held for Bob
        target_date_str = slot_utc.astimezone(KOLKATA_TZ).strftime("%Y-%m-%d")
        slots_res = await client.get(
            f"/slots?date={target_date_str}",
            headers={"X-User-Id": user_bob},
        )
        assert slots_res.status_code == 200
        slots = slots_res.json()
        target_slot = next((s for s in slots if s["start"] == slot_iso), None)
        assert target_slot is not None
        assert target_slot["held"] is True
        assert target_slot["available"] is False

        # Step 4: Alice releases the hold
        release_res = await client.post(
            "/slots/release-hold",
            headers={"X-User-Id": user_alice},
            json={"slotStart": slot_iso},
        )
        assert release_res.status_code == 200
        assert release_res.json()["success"] is True

        # Step 5: Now Bob can successfully hold the slot
        bob_retry = await client.post(
            "/slots/hold",
            headers={"X-User-Id": user_bob},
            json={"slotStart": slot_iso},
        )
        assert bob_retry.status_code == 200
        assert bob_retry.json()["success"] is True

        # Clean up
        hold_service.release_hold(slot_iso, user_bob)


@pytest.mark.asyncio
async def test_api_booking_rejected_when_held_by_other_user():
    user_alice = f"alice_{uuid.uuid4().hex[:8]}"
    user_bob = f"bob_{uuid.uuid4().hex[:8]}"

    slot_utc = get_next_valid_weekday_slot(11, 30)
    slot_iso = slot_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Clean state
    hold_service.release_hold(slot_iso, user_alice)
    hold_service.release_hold(slot_iso, user_bob)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Alice holds the slot
        hold_res = await client.post(
            "/slots/hold",
            headers={"X-User-Id": user_alice},
            json={"slotStart": slot_iso},
        )
        assert hold_res.status_code == 200

        # Bob attempts to book this slot directly -> 409 SLOT_HELD
        booking_res = await client.post(
            "/bookings",
            headers={
                "X-User-Id": user_bob,
                "Idempotency-Key": f"test-idemp-{stdlib_time.time()}",
            },
            json={
                "slotStart": slot_iso,
                "name": "Bob Smith",
                "email": "bob@example.com",
            },
        )
        assert booking_res.status_code == 409
        err = booking_res.json()["error"]
        assert err["code"] == "SLOT_HELD"

        # Alice completes booking -> 201 Created
        alice_booking_res = await client.post(
            "/bookings",
            headers={
                "X-User-Id": user_alice,
                "Idempotency-Key": f"test-idemp-alice-{stdlib_time.time()}",
            },
            json={
                "slotStart": slot_iso,
                "name": "Alice Johnson",
                "email": "alice@example.com",
            },
        )
        assert alice_booking_res.status_code == 201

        # Hold is automatically released after Alice's successful booking
        assert hold_service.is_held_by_other(slot_iso, user_bob) is False
