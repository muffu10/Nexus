from app.data_reader import read_records
from app.data_writer import write_record
from app.key_detector import find_sync_key
from app.transformer import transform_record
from app.schema_inspector import get_database_schema
from app.incremental_sync import (
    find_updated_at_column,
    get_last_successful_sync,
)


def sync_table(
    source_engine,
    destination_engine,
    source_table,
    destination_table,
    mappings,
    sync_run_id=None,
    datasync_engine=None,
    connection_id=None,
):
    source_schema = get_database_schema(
        source_engine
    )

    source_columns = source_schema.get(
        source_table,
        [],
    )

    destination_schema = get_database_schema(
        destination_engine
    )

    destination_columns = destination_schema.get(
        destination_table,
        [],
    )

    # Find the source timestamp column.
    updated_at_column = find_updated_at_column(
        source_columns
    )

    # Find when this connection was last successfully synced.
    last_sync_time = None

    if connection_id and datasync_engine:
        last_sync_time = get_last_successful_sync(
            datasync_engine,
            connection_id,
        )

    # Find the destination key used for UPSERT.
    key_column = find_sync_key(
        destination_columns,
        mappings,
    )

    # Read either all records or only changed records.
    records = read_records(
        source_engine,
        source_table,
        updated_at_column=updated_at_column,
        last_sync_time=last_sync_time,
    )

    inserted_count = 0
    updated_count = 0
    failed_count = 0

    for record in records:
        try:
            transformed_record = transform_record(
                record,
                mappings,
            )

            result = write_record(
                destination_engine,
                destination_table,
                transformed_record,
                key_column=key_column,
            )

            if result == "inserted":
                inserted_count += 1

            elif result == "updated":
                updated_count += 1

        except Exception as error:
            failed_count += 1

            if sync_run_id and datasync_engine:
                from sqlalchemy.orm import Session
                from app.models import SyncError

                with Session(datasync_engine) as session:
                    sync_error = SyncError(
                        sync_run_id=sync_run_id,
                        source_record=str(record),
                        error_message=str(error),
                    )

                    session.add(sync_error)
                    session.commit()

    return {
        "processed_count": len(records),
        "inserted_count": inserted_count,
        "updated_count": updated_count,
        "failed_count": failed_count,
        "incremental": (
            updated_at_column is not None
            and last_sync_time is not None
        ),
        "updated_at_column": updated_at_column,
        "last_sync_time": last_sync_time,
    }