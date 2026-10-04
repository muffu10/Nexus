def transform_record(record, mappings):
    transformed = {}

    for mapping in mappings:
        source_field = mapping["source"]
        destination_field = mapping["destination"]

        if source_field in record:
            transformed[destination_field] = record[source_field]

    return transformed