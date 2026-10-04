from sqlalchemy.orm import Session

from app.models import SyncRun


TIMESTAMP_COLUMN_NAMES = {
    "updated_at",
    "update_time",
    "updated_on",
    "last_updated",
    "modified_at",
    "modified_on",
    "last_modified",
}


def find_updated_at_column(source_columns):
    for column in source_columns:
        column_name = column["name"].lower()

        if column_name in TIMESTAMP_COLUMN_NAMES:
            column_type = column["type"].upper()

            if "DATE" in column_type or "TIME" in column_type:
                return column["name"]

    return None


def get_last_successful_sync(
    datasync_engine,
    connection_id,
):
    with Session(datasync_engine) as session:
        sync_run = (
            session.query(SyncRun)
            .filter(
                SyncRun.connection_id == connection_id,
                SyncRun.status == "success",
                SyncRun.finished_at.is_not(None),
            )
            .order_by(
                SyncRun.finished_at.desc()
            )
            .first()
        )

        if not sync_run:
            return None

        return sync_run.finished_at