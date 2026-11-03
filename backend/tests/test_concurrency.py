import asyncio
from datetime import datetime, time, timedelta, timezone
import uuid
from zoneinfo import ZoneInfo
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


def get_weekday_slot(days_ahead: int, hour: int, minute: int) -> datetime:
    """Helper to return a valid upcoming weekday slot in UTC."""
    now_ist = datetime.now(KOLKATA_TZ)
    target = (now_ist + timedelta(days=days_ahead)).date()
    while target.weekday() >= 5:
        days_ahead += 1
        target = (now_ist + timedelta(days=days_ahead)).date()

    slot_ist = datetime.combine(target, time(hour, minute), tzinfo=KOLKATA_TZ)
    return slot_ist.astimezone(timezone.utc)


@pytest.mark.asyncio
async def test_concurrent_bookings_same_user_cannot_bypass_quota():
    """Verify that multiple simultaneous booking requests by the SAME user for DIFFERENT

    slots are serialized by the database advisory lock and cannot exceed the 2-booking quota.
    """
    user_id = f"concurrent_user_{uuid.uuid4().hex[:8]}"

    # Three completely distinct valid upcoming slots
    slot1 = get_weekday_slot(days_ahead=3, hour=10, minute=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    slot2 = get_weekday_slot(days_ahead=3, hour=11, minute=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    slot3 = get_weekday_slot(days_ahead=3, hour=12, minute=0).strftime("%Y-%m-%dT%H:%M:%SZ")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: User creates their 1st booking normally -> succeeds (active_count = 1)
        res1 = await client.post(
            "/bookings",
            headers={
                "X-User-Id": user_id,
                "Idempotency-Key": f"idemp-1-{uuid.uuid4()}",
            },
            json={
                "slotStart": slot1,
                "name": "Concurrent Tester",
                "email": "tester@example.com",
            },
        )
        assert res1.status_code == 201

        # Step 2: User now attempts to book slot2 AND slot3 SIMULTANEOUSLY in parallel
        # Allowed limit is 2. Since user already has 1, only ONE of these should succeed,
        # and the other MUST be rejected with 409 BOOKING_LIMIT_REACHED.
        async def send_booking(slot_start: str):
            return await client.post(
                "/bookings",
                headers={
                    "X-User-Id": user_id,
                    "Idempotency-Key": f"idemp-{uuid.uuid4()}",
                },
                json={
                    "slotStart": slot_start,
                    "name": "Concurrent Tester",
                    "email": "tester@example.com",
                },
            )

        parallel_responses = await asyncio.gather(
            send_booking(slot2),
            send_booking(slot3),
        )

        status_codes = [r.status_code for r in parallel_responses]

        # Exactly one must succeed (201) and exactly one must fail (409)
        assert status_codes.count(201) == 1, f"Expected exactly one 201, got {status_codes}"
        assert status_codes.count(409) == 1, f"Expected exactly one 409, got {status_codes}"

        # Verify the 409 error is specifically BOOKING_LIMIT_REACHED
        rejected_res = next(r for r in parallel_responses if r.status_code == 409)
        assert rejected_res.json()["error"]["code"] == "BOOKING_LIMIT_REACHED"

        # Step 3: Verify the user has exactly 2 active bookings in total
        user_bookings_res = await client.get(
            "/bookings",
            headers={"X-User-Id": user_id},
        )
        assert user_bookings_res.status_code == 200
        active_bookings = [
            b for b in user_bookings_res.json() if b["status"] == "ACTIVE"
        ]
        assert len(active_bookings) == 2
