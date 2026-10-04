import re

from app.embedding_engine import (
    get_semantic_similarity_matrix,
)


SYNONYMS = {
    "name": {
        "name",
        "full_name",
        "customer_name",
        "display_name",
    },
    "email": {
        "email",
        "email_address",
        "contact_email",
    },
    "phone": {
        "phone",
        "phone_number",
        "mobile",
        "mobile_number",
        "telephone",
    },
    "id": {
        "id",
        "customer_id",
        "user_id",
        "product_id",
    },
}


def normalize_name(name: str) -> str:

    return re.sub(
        r"[^a-z0-9]",
        "",
        name.lower(),
    )


def get_name_similarity(
    source_name: str,
    destination_name: str,
) -> float:

    source = normalize_name(source_name)
    destination = normalize_name(destination_name)

    if source == destination:
        return 1.0

    for synonyms in SYNONYMS.values():

        normalized_synonyms = {
            normalize_name(value)
            for value in synonyms
        }

        if (
            source in normalized_synonyms
            and destination in normalized_synonyms
        ):
            return 0.9

    if (
        source in destination
        or destination in source
    ):
        return 0.7

    return 0.0


def looks_like_email(value) -> bool:

    if not isinstance(value, str):
        return False

    return bool(
        re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            value,
        )
    )


def looks_like_phone(value) -> bool:

    if value is None:
        return False

    digits = re.sub(
        r"[^0-9]",
        "",
        str(value),
    )

    return 7 <= len(digits) <= 15


def looks_like_name(value) -> bool:

    if not isinstance(value, str):
        return False

    value = value.strip()

    if not value:
        return False

    words = value.split()

    if len(words) < 2:
        return False

    return all(
        word.replace("-", "").isalpha()
        for word in words
    )


def looks_like_id(value) -> bool:

    if value is None:
        return False

    return bool(
        re.fullmatch(
            r"\d+",
            str(value),
        )
    )


def detect_value_type(
    values,
    column=None,
) -> str | None:

    values = [
        value
        for value in values
        if value is not None
    ]

    if not values:
        return None

    if column and column.get("primary_key"):
        return "id"

    column_type = ""

    if column:
        column_type = column.get(
            "type",
            "",
        ).upper()

    if any(
        integer_type in column_type
        for integer_type in (
            "INTEGER",
            "BIGINT",
            "SMALLINT",
            "SERIAL",
        )
    ):

        if all(
            isinstance(value, int)
            for value in values
        ):
            return "id"

    detectors = [
        ("email", looks_like_email),
        ("name", looks_like_name),
    ]

    if any(
        text_type in column_type
        for text_type in (
            "CHAR",
            "VARCHAR",
            "TEXT",
        )
    ):

        detectors.append(
            ("phone", looks_like_phone)
        )

    detectors.append(
        ("id", looks_like_id)
    )

    best_type = None
    best_ratio = 0.0

    for value_type, detector in detectors:

        matches = sum(
            detector(value)
            for value in values
        )

        ratio = matches / len(values)

        if ratio > best_ratio:
            best_ratio = ratio
            best_type = value_type

    if best_ratio >= 0.8:
        return best_type

    return "unknown"


def get_database_type_family(
    column,
) -> str | None:

    if not column:
        return None

    column_type = column.get(
        "type",
        "",
    ).upper()

    if any(
        value in column_type
        for value in (
            "INTEGER",
            "BIGINT",
            "SMALLINT",
            "SERIAL",
            "NUMERIC",
            "DECIMAL",
            "REAL",
            "DOUBLE",
        )
    ):
        return "numeric"

    if any(
        value in column_type
        for value in (
            "CHAR",
            "VARCHAR",
            "TEXT",
        )
    ):
        return "text"

    if "DATE" in column_type:
        return "date"

    if "TIME" in column_type:
        return "datetime"

    if "BOOL" in column_type:
        return "boolean"

    return None


def get_destination_semantic_type(
    destination_name: str,
) -> str | None:

    normalized_destination = normalize_name(
        destination_name
    )

    for value_type, synonyms in SYNONYMS.items():

        normalized_synonyms = {
            normalize_name(value)
            for value in synonyms
        }

        if normalized_destination in normalized_synonyms:
            return value_type

    return None


def get_value_similarity(
    source_values,
    source_column,
    destination_name,
    destination_values,
    destination_column,
) -> float:

    source_type = detect_value_type(
        source_values,
        source_column,
    )

    destination_value_type = detect_value_type(
        destination_values,
        destination_column,
    )

    destination_name_type = (
        get_destination_semantic_type(
            destination_name
        )
    )

    if destination_value_type:

        if source_type == destination_value_type:
            return 1.0

        return 0.0

    if destination_name_type:

        if source_type == destination_name_type:
            return 1.0

    return 0.0


def get_type_compatibility(
    source_column,
    destination_column,
) -> float:

    source_family = get_database_type_family(
        source_column
    )

    destination_family = get_database_type_family(
        destination_column
    )

    if not source_family or not destination_family:
        return 0.0

    if source_family == destination_family:
        return 0.8

    return 0.0


def get_similarity(
    source_column,
    destination_column,
    source_values=None,
    destination_values=None,
    semantic_score=0.0,
):

    source_values = source_values or []
    destination_values = destination_values or []

    source_name = source_column["name"]
    destination_name = destination_column["name"]

    name_score = get_name_similarity(
        source_name,
        destination_name,
    )

    value_score = get_value_similarity(
        source_values,
        source_column,
        destination_name,
        destination_values,
        destination_column,
    )

    type_score = get_type_compatibility(
        source_column,
        destination_column,
    )

    if value_score == 1.0:

        if name_score >= 0.7:
            final_score = 1.0
        else:
            final_score = 0.9

    else:

        final_score = (
            name_score * 0.35
            + type_score * 0.20
            + value_score * 0.25
            + semantic_score * 0.20
        )

        final_score = round(
            final_score,
            2,
        )

    return {
        "score": final_score,
        "signals": {
            "name_similarity": round(
                name_score,
                2,
            ),
            "value_similarity": round(
                value_score,
                2,
            ),
            "type_compatibility": round(
                type_score,
                2,
            ),
            "semantic_similarity": round(
                semantic_score,
                2,
            ),
        },
    }


def get_match_status(
    confidence: float,
    margin: float,
) -> str:

    if confidence < 0.5:
        return "low_confidence"

    if margin < 0.10:
        return "review_required"

    if confidence >= 0.85:
        return "high_confidence"

    return "medium_confidence"


def suggest_mappings(
    source_columns,
    destination_columns,
    source_samples=None,
    destination_samples=None,
):

    source_samples = source_samples or {}
    destination_samples = destination_samples or {}

    mappings = []

    source_names = [
        column["name"]
        for column in source_columns
    ]

    destination_names = [
        column["name"]
        for column in destination_columns
    ]

    semantic_matrix = (
        get_semantic_similarity_matrix(
            source_names,
            destination_names,
        )
    )

    for source_index, source in enumerate(
        source_columns
    ):

        candidates = []

        source_name = source["name"]

        for destination_index, destination in enumerate(
            destination_columns
        ):

            destination_name = destination["name"]

            semantic_score = float(
                semantic_matrix[
                    source_index
                ][destination_index]
            )

            result = get_similarity(
                source,
                destination,
                source_samples.get(
                    source_name,
                    [],
                ),
                destination_samples.get(
                    destination_name,
                    [],
                ),
                semantic_score,
            )

            candidates.append(
                {
                    "destination": destination,
                    "score": result["score"],
                    "signals": result["signals"],
                }
            )

        candidates.sort(
            key=lambda candidate: candidate["score"],
            reverse=True,
        )

        if not candidates:
            continue

        best_candidate = candidates[0]

        best_score = best_candidate["score"]

        if len(candidates) > 1:
            second_best_score = candidates[1]["score"]
        else:
            second_best_score = 0.0

        margin = round(
            best_score - second_best_score,
            2,
        )

        match_status = get_match_status(
            best_score,
            margin,
        )

        mappings.append(
            {
                "source": source_name,
                "destination": (
                    best_candidate[
                        "destination"
                    ]["name"]
                ),
                "confidence": round(
                    best_score,
                    2,
                ),
                "margin": margin,
                "match_status": match_status,
                "signals": best_candidate[
                    "signals"
                ],
            }
        )

    return mappings