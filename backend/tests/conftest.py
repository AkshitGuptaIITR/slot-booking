import pytest
from sqlalchemy import text
from app.db.session import engine


@pytest.fixture(scope="session", autouse=True)
async def cleanup_database_session():
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Cleans up any test-generated bookings and idempotency records before and after each test."""
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "DELETE FROM bookings WHERE user_id LIKE 'alice_%' OR user_id LIKE 'bob_%' OR user_id LIKE 'concurrent_%'"
            )
        )
        await conn.execute(
            text(
                "DELETE FROM idempotency_records WHERE user_id LIKE 'alice_%' OR user_id LIKE 'bob_%' OR user_id LIKE 'concurrent_%'"
            )
        )
    yield
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "DELETE FROM bookings WHERE user_id LIKE 'alice_%' OR user_id LIKE 'bob_%' OR user_id LIKE 'concurrent_%'"
            )
        )
        await conn.execute(
            text(
                "DELETE FROM idempotency_records WHERE user_id LIKE 'alice_%' OR user_id LIKE 'bob_%' OR user_id LIKE 'concurrent_%'"
            )
        )
