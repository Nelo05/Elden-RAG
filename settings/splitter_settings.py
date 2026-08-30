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
        extra="ignore",
    )

    @field_validator("headers_to_split_on", mode="before")
    @classmethod
    def parse_headers(cls, v):
        if isinstance(v, str):
            headers = []
            for part in v.split(";"):
                if "," in part:
                    h, label = part.split(",", 1)
                    headers.append((h.strip(), label.strip()))
            if not headers:
                return cls.model_fields["headers_to_split_on"].default
            return headers
        return v

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",") if ext.strip()]
        return v


config = SplitterConfig()
