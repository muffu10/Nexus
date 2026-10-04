from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    connection_number: Mapped[int] = mapped_column(
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    source_type: Mapped[str] = mapped_column(
        String(50)
    )

    destination_type: Mapped[str] = mapped_column(
        String(50)
    )

    source_table: Mapped[str] = mapped_column(
        String(100)
    )

    destination_table: Mapped[str] = mapped_column(
        String(100)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class FieldMapping(Base):
    __tablename__ = "field_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)

    connection_id: Mapped[int] = mapped_column(
        ForeignKey("connections.id")
    )

    source_field: Mapped[str] = mapped_column(String(100))
    destination_field: Mapped[str] = mapped_column(String(100))


class ConnectionCredential(Base):
    __tablename__ = "connection_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)

    connection_id: Mapped[int] = mapped_column(
        ForeignKey("connections.id"),
        unique=True,
    )

    encrypted_source_url: Mapped[str] = mapped_column(
        String(1000)
    )

    encrypted_destination_url: Mapped[str] = mapped_column(
        String(1000)
    )


class MappingSuggestion(Base):
    __tablename__ = "mapping_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)

    connection_id: Mapped[int] = mapped_column(
        ForeignKey("connections.id")
    )

    source_field: Mapped[str] = mapped_column(String(100))
    destination_field: Mapped[str] = mapped_column(String(100))

    confidence: Mapped[float]
    margin: Mapped[float]

    match_status: Mapped[str] = mapped_column(
        String(50)
    )

    signals: Mapped[str] = mapped_column(
        String(2000)
    )

    review_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    connection_id: Mapped[int] = mapped_column(
        ForeignKey("connections.id")
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="running",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    inserted_count: Mapped[int] = mapped_column(
        default=0
    )

    updated_count: Mapped[int] = mapped_column(
        default=0
    )

    failed_count: Mapped[int] = mapped_column(
        default=0
    )

    error_message: Mapped[str | None] = mapped_column(
        String(4000),
        nullable=True,
    )


class SyncError(Base):
    __tablename__ = "sync_errors"

    id: Mapped[int] = mapped_column(primary_key=True)

    sync_run_id: Mapped[int] = mapped_column(
        ForeignKey("sync_runs.id")
    )

    source_record: Mapped[str] = mapped_column(
        String(4000)
    )

    error_message: Mapped[str] = mapped_column(
        String(4000)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )