from app.incremental_sync import find_updated_at_column


columns_with_timestamp = [
    {
        "name": "customer_id",
        "type": "INTEGER",
    },
    {
        "name": "customer_name",
        "type": "VARCHAR(100)",
    },
    {
        "name": "updated_at",
        "type": "TIMESTAMP",
    },
]

columns_without_timestamp = [
    {
        "name": "customer_id",
        "type": "INTEGER",
    },
    {
        "name": "customer_name",
        "type": "VARCHAR(100)",
    },
]


print(
    find_updated_at_column(
        columns_with_timestamp
    )
)

print(
    find_updated_at_column(
        columns_without_timestamp
    )
)