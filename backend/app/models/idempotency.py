from sqlalchemy import Integer, String

from app.db.base import Base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
