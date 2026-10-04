from sqlalchemy import text


def write_record(
    engine,
    table_name,
    record,
    key_column=None,
):
    columns = list(record.keys())

    if not columns:
        return "skipped"

    column_names = ", ".join(
        f'"{column}"'
        for column in columns
    )

    parameters = ", ".join(
        f":{column}"
        for column in columns
    )

    if key_column and key_column in record:
        update_columns = [
            column
            for column in columns
            if column != key_column
        ]

        # Record has only the key column.
        if not update_columns:
            query = text(
                f'''
                INSERT INTO "{table_name}"
                    ({column_names})
                VALUES
                    ({parameters})
                ON CONFLICT ("{key_column}")
                DO NOTHING
                '''
            )

            with engine.begin() as connection:
                result = connection.execute(query, record)

            if result.rowcount == 0:
                return "unchanged"

            return "inserted"

        update_clause = ", ".join(
            f'"{column}" = EXCLUDED."{column}"'
            for column in update_columns
        )

        query = text(
            f'''
            INSERT INTO "{table_name}"
                ({column_names})
            VALUES
                ({parameters})
            ON CONFLICT ("{key_column}")
            DO UPDATE SET
                {update_clause}
            RETURNING (xmax = 0) AS inserted
            '''
        )

        with engine.begin() as connection:
            result = connection.execute(query, record)
            row = result.fetchone()

        if row and row[0]:
            return "inserted"

        return "updated"

    # No reliable key was found.
    query = text(
        f'''
        INSERT INTO "{table_name}"
            ({column_names})
        VALUES
            ({parameters})
        '''
    )

    with engine.begin() as connection:
        connection.execute(query, record)

    return "inserted"