from sqlalchemy import inspect


def get_database_schema(engine):
    inspector = inspect(engine)

    tables = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)

        primary_key_columns = set(
            inspector.get_pk_constraint(table_name).get(
                "constrained_columns",
                []
            )
        )

        unique_columns = set()

        for constraint in inspector.get_unique_constraints(
            table_name
        ):
            for column in constraint.get(
                "column_names",
                []
            ):
                unique_columns.add(column)

        tables[table_name] = [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "primary_key": (
                    column["name"]
                    in primary_key_columns
                ),
                "unique": (
                    column["name"]
                    in unique_columns
                ),
            }
            for column in columns
        ]

    return tables