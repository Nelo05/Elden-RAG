from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorStoreConfig(BaseSettings):

    qdrant_path: Optional[Path] = Path("../qdrant")
    qdrant_host: Optional[str] = None
    qdrant_port: Optional[int] = 6333
    qdrant_grpc_port: Optional[int] = 6334
    collection_name: str = "my_documents"
    embedding_model: str = "intfloat/multilingual-e5-base"
    sparse_model: str = "Qdrant/bm25"
    dense_vector_size: int = 768
    distance: Literal["COSINE", "DOT", "EUCLID"] = "COSINE"
    search_type: Literal["similarity", "mmr", "similarity_score_threshold"] = "mmr"
    top_k: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="VECTORSTORE_"
    )


vector_config = VectorStoreConfig()