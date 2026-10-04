from sqlalchemy import text


def sample_column_values(
    engine,
    table_name: str,
    column_name: str,
    limit: int = 5,
):
    query = text(
        f'''
        SELECT "{column_name}"
        FROM "{table_name}"
        LIMIT :limit
        '''
    )

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"limit": limit},
        )

        return [
            row[0]
            for row in result
        ]
    

def sample_table(
    engine,
    table_name: str,
    columns,
    limit: int = 5,
):
    samples = {}

    for column in columns:
        column_name = column["name"]

        samples[column_name] = sample_column_values(
            engine,
            table_name,
            column_name,
            limit,
        )

    return samples