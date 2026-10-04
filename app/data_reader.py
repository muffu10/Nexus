from sqlalchemy import text


def read_records(
    engine,
    table_name,
    updated_at_column=None,
    last_sync_time=None,
):
    if updated_at_column and last_sync_time:
        query = text(
            f'''
            SELECT *
            FROM "{table_name}"
            WHERE "{updated_at_column}" > :last_sync_time
            '''
        )

        parameters = {
            "last_sync_time": last_sync_time,
        }

    else:
        query = text(
            f'''
            SELECT *
            FROM "{table_name}"
            '''
        )

        parameters = {}

    with engine.connect() as connection:
        result = connection.execute(
            query,
            parameters,
        )

        return [
            dict(row._mapping)
            for row in result
        ]