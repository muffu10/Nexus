def find_sync_key(
    destination_columns,
    mappings,
):
    """
    Find the destination primary-key or unique column
    that has an approved source-to-destination mapping.
    """

    mapped_destinations = {
        mapping["destination"]
        for mapping in mappings
    }

    # Prefer a primary key.
    for column in destination_columns:
        if (
            column["primary_key"]
            and column["name"] in mapped_destinations
        ):
            return column["name"]

    # If no primary key is mapped,
    # look for a unique column.
    for column in destination_columns:
        if (
            column["unique"]
            and column["name"] in mapped_destinations
        ):
            return column["name"]

    return None