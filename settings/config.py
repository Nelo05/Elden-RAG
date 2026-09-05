from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AppSettings(BaseSettings):
    gigachat_credentials: SecretStr = Field(
        default=SecretStr(""), validation_alias="GIGACHAT_CREDENTIALS"
    )
    gigachat_model: str = Field(default="GigaChat-2", validation_alias="GIGACHAT_MODEL")
    verify_ssl_certs: bool = Field(
        default=False, validation_alias="GIGACHAT_VERIFY_SSL_CERTS"
    )

    headers_to_split_on: list[tuple[str, str]] = Field(
        default=[("##", "chapter"), ("###", "section"), ("####", "subsection")],
        validation_alias="SPLITTER_HEADERS_TO_SPLIT_ON",
    )
    chunk_size: int = Field(default=360, validation_alias="SPLITTER_CHUNK_SIZE")
    chunk_overlap: int = Field(default=40, validation_alias="SPLITTER_CHUNK_OVERLAP")
    min_chunk_length: int = Field(
        default=3, validation_alias="SPLITTER_MIN_CHUNK_LENGTH"
    )
    allowed_extensions: list[str] = Field(
        default=[".md"], validation_alias="SPLITTER_ALLOWED_EXTENSIONS"
    )
    qdrant_connection_mode: Literal["remote", "local"] = Field(
        default= "local",
        validation_alias="VECTORSTORE_CONNECTION_MODE"
    )
    qdrant_path: Path = Field(
        default=PROJECT_ROOT / "qdrant", validation_alias="VECTORSTORE_QDRANT_PATH"
    )
    qdrant_host: str | None = Field(
        default=None, validation_alias="VECTORSTORE_QDRANT_HOST"
    )
    qdrant_port: int | None = Field(default=None, validation_alias="VECTORSTORE_QDRANT_PORT")
    qdrant_grpc_port: int | None = Field(
        default=None, validation_alias="VECTORSTORE_QDRANT_GRPC_PORT"
    )
    collection_name: str = Field(
        default="my_documents", validation_alias="VECTORSTORE_COLLECTION_NAME"
    )
    embedding_model: str = Field(
        default="intfloat/multilingual-e5-base",
        validation_alias="VECTORSTORE_EMBEDDING_MODEL",
    )
    sparse_model: str = Field(
        default="Qdrant/bm25", validation_alias="VECTORSTORE_SPARSE_MODEL"
    )
    dense_vector_size: int = Field(
        default=768, validation_alias="VECTORSTORE_DENSE_VECTOR_SIZE"
    )
    distance: Literal["COSINE", "DOT", "EUCLID"] = Field(
        default="COSINE", validation_alias="VECTORSTORE_DISTANCE"
    )
    search_type: Literal["similarity", "mmr", "similarity_score_threshold"] = Field(
        default="mmr", validation_alias="VECTORSTORE_SEARCH_TYPE"
    )
    top_k: int = Field(default=10, validation_alias="VECTORSTORE_TOP_K")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode='after')
    def validate_connection(self):
        if self.qdrant_connection_mode == "remote":
            if not self.qdrant_host:
                raise ValueError("Для remote-режима необходимо задать qdrant_host")
            if not self.qdrant_port:
                raise ValueError("Для remote-режима необходимо задать qdrant_port")
            if not self.qdrant_grpc_port:
                raise ValueError("Для remote-режима необходимо задать qdrant_grpc_port")
        if self.qdrant_connection_mode == "local" and not self.qdrant_path:
            raise ValueError("Для local-режима необходимо задать qdrant_path")
        return self
    
    @field_validator("qdrant_path", mode="after")
    @classmethod
    def resolve_qdrant_path(cls, path: Path) -> Path:
        return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


config = AppSettings()
