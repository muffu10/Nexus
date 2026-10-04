from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Connection, SyncRun
from app.sync_status import (
    SYNC_COMPLETED_WITH_ERRORS,
    SYNC_FAILED,
    SYNC_RUNNING,
    SYNC_SUCCESS,
)
from app.sync_service import sync_table


def run_sync(
    datasync_engine,
    source_engine,
    destination_engine,
    connection_id,
):
    """
    Executes a sync and manages the SyncRun lifecycle.

    This is shared by:
    - normal syncs
    - retries
    """

    # Get connection metadata
    with Session(datasync_engine) as session:
        connection = (
            session.query(Connection)
            .filter(Connection.id == connection_id)
            .first()
        )

        if not connection:
            raise ValueError(
                f"Connection {connection_id} does not exist"
            )

        source_table = connection.source_table
        destination_table = connection.destination_table

    # Create a new sync run
    with Session(datasync_engine) as session:
        sync_run = SyncRun(
            connection_id=connection_id,
            status=SYNC_RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        session.add(sync_run)
        session.commit()
        session.refresh(sync_run)

        sync_run_id = sync_run.id

    try:
        # Get approved mappings
        from app.models import FieldMapping

        with Session(datasync_engine) as session:
            mappings_db = (
                session.query(FieldMapping)
                .filter(
                    FieldMapping.connection_id == connection_id
                )
                .all()
            )

            mappings = [
                {
                    "source": mapping.source_field,
                    "destination": mapping.destination_field,
                }
                for mapping in mappings_db
            ]

        if not mappings:
            raise ValueError(
                "No approved field mappings exist for this connection"
            )

        # Execute sync
        result = sync_table(
            source_engine=source_engine,
            destination_engine=destination_engine,
            source_table=source_table,
            destination_table=destination_table,
            mappings=mappings,
            sync_run_id=sync_run_id,
            datasync_engine=datasync_engine,
            connection_id=connection_id,
        )

        # Determine final status
        if result["failed_count"] > 0:
            final_status = SYNC_COMPLETED_WITH_ERRORS
        else:
            final_status = SYNC_SUCCESS

        # Update SyncRun
        with Session(datasync_engine) as session:
            sync_run = (
                session.query(SyncRun)
                .filter(SyncRun.id == sync_run_id)
                .first()
            )

            sync_run.status = final_status
            sync_run.finished_at = datetime.now(timezone.utc)
            sync_run.inserted_count = result["inserted_count"]
            sync_run.updated_count = result["updated_count"]
            sync_run.failed_count = result["failed_count"]

            session.commit()

        return {
            "sync_run_id": sync_run_id,
            "connection_id": connection_id,
            "source_table": source_table,
            "destination_table": destination_table,
            "status": final_status,
            **result,
        }

    except Exception as error:
        # Mark the run as completely failed
        with Session(datasync_engine) as session:
            sync_run = (
                session.query(SyncRun)
                .filter(SyncRun.id == sync_run_id)
                .first()
            )

            if sync_run:
                sync_run.status = SYNC_FAILED
                sync_run.finished_at = datetime.now(timezone.utc)
                sync_run.error_message = str(error)

                session.commit()

        raise