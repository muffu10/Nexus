from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import datasync_engine
from app.models import Connection, FieldMapping



connection = Connection(
    name="Customer Sync",
    source_type="postgresql",
    destination_type="postgresql",
    source_table="customers",
    destination_table="customers",
)

with Session(datasync_engine) as session:
    session.add(connection)
    session.flush()

    mappings = [
        FieldMapping(
            connection_id=connection.id,
            source_field="customer_id",
            destination_field="id",
        ),
        FieldMapping(
            connection_id=connection.id,
            source_field="customer_name",
            destination_field="name",
        ),
        FieldMapping(
            connection_id=connection.id,
            source_field="email_address",
            destination_field="email",
        ),
        FieldMapping(
            connection_id=connection.id,
            source_field="mobile",
            destination_field="phone_number",
        ),
    ]

    session.add_all(mappings)
    session.commit()

print("Seed data created.")