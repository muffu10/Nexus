from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.database import datasync_engine
from app.models import ConnectionCredential
from app.security import decrypt_value


def create_database_engine(database_url: str):
    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def test_database_connection(database_url: str):
    engine = create_database_engine(database_url)

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception:
        return False

    finally:
        engine.dispose()


def get_connection_engines(connection_id: int):
    with Session(datasync_engine) as session:
        credentials = (
            session.query(ConnectionCredential)
            .filter(
                ConnectionCredential.connection_id == connection_id
            )
            .first()
        )

        if not credentials:
            raise ValueError(
                "Connection credentials not found."
            )

        source_url = decrypt_value(
            credentials.encrypted_source_url
        )

        destination_url = decrypt_value(
            credentials.encrypted_destination_url
        )

    source_engine = create_database_engine(
        source_url
    )

    destination_engine = create_database_engine(
        destination_url
    )

    return source_engine, destination_engine