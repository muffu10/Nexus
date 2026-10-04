from app.embedding_engine import (
    get_semantic_similarity_matrix,
)


source_columns = [
    "client identity",
    "contact mail",
    "telephone contact",
    "buyer identifier",
]

destination_columns = [
    "name",
    "email",
    "phone number",
    "id",
]


matrix = get_semantic_similarity_matrix(
    source_columns,
    destination_columns,
)


print("\nSemantic similarity matrix:\n")

print(
    " " * 22
    + " ".join(
        f"{name:>10}"
        for name in destination_columns
    )
)

for source_name, row in zip(
    source_columns,
    matrix,
):

    values = [
        f"{float(value):.3f}"
        for value in row
    ]

    print(
        f"{source_name:<22}"
        + " ".join(
            f"{value:>10}"
            for value in values
        )
    )