from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


MODEL_NAME = "all-MiniLM-L6-v2"


model = SentenceTransformer(
    MODEL_NAME
)


def normalize_text(text: str) -> str:
    return text.replace(
        "_",
        " ",
    ).strip().lower()


@lru_cache(maxsize=512)
def get_embedding(text: str):

    normalized_text = normalize_text(
        text
    )

    return model.encode(
        normalized_text,
        convert_to_tensor=True,
    )


def get_embeddings(texts):

    normalized_texts = [
        normalize_text(text)
        for text in texts
    ]

    return model.encode(
        normalized_texts,
        convert_to_tensor=True,
    )


def get_semantic_similarity(
    source_text: str,
    destination_text: str,
) -> float:

    source_embedding = get_embedding(
        source_text
    )

    destination_embedding = get_embedding(
        destination_text
    )

    similarity = cos_sim(
        source_embedding,
        destination_embedding,
    )

    return round(
        float(similarity.item()),
        4,
    )


def get_semantic_similarity_matrix(
    source_texts,
    destination_texts,
):

    source_embeddings = get_embeddings(
        source_texts
    )

    destination_embeddings = get_embeddings(
        destination_texts
    )

    similarities = cos_sim(
        source_embeddings,
        destination_embeddings,
    )

    return similarities