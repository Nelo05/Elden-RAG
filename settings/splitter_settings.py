from typing import List, Tuple
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SplitterConfig(BaseSettings):
    headers_to_split_on: List[Tuple[str, str]] = Field(
        default=[("##", "chapter"), ("###", "section"), ("####", "subsection")]
    )
    chunk_size: int = 360
    chunk_overlap: int = 40
    min_chunk_length: int = 3
    allowed_extensions: List[str] = [".md"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SPLITTER_",
        extra="ignore",
    )


config = SplitterConfig()
