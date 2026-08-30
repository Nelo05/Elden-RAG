from pathlib import Path
from typing import List

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_core.documents import Document


from settings.splitter_settings import SplitterConfig, config


class MarkdownProcessor:
    def __init__(self, config: SplitterConfig):
        self.config = config
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=config.headers_to_split_on
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
        )

    def process_file(self, filepath: Path) -> List[Document]:
        if not filepath.is_file():
            return []
        if (
            self.config.allowed_extensions
            and filepath.suffix not in self.config.allowed_extensions
        ):
            print(f"Пропущен файл {filepath} – неподдерживаемое расширение")
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = f.read()
        except (UnicodeDecodeError, OSError) as e:
            print(f"Ошибка чтения файла {filepath}: {e}")
            return []

        try:
            header_splits = self.header_splitter.split_text(data)
        except Exception as e:
            print(f"Ошибка разбиения по заголовкам для {filepath}: {e}")
            return []

        chunks = []
        file_stem = filepath.stem

        for doc in header_splits:
            doc.metadata.setdefault("name", file_stem)

            try:
                sub_splits = self.text_splitter.split_documents([doc])
            except Exception as e:
                print(f"Ошибка при разбиении документа {filepath}: {e}")
                continue

            for sub_chunk in sub_splits:
                if len(sub_chunk.page_content) < self.config.min_chunk_length:
                    continue
                headers_str = "; ".join(str(v) for v in sub_chunk.metadata.values())
                sub_chunk.page_content = f"{headers_str}\n{sub_chunk.page_content}"
                chunks.append(sub_chunk)

        print(f"Обработан файл {filepath}, создано {len(chunks)} чанков")
        return chunks

    def process_folder(
        self, folder_path: Path, recursive: bool = True
    ) -> List[Document]:
        if not folder_path.exists():
            print(f"Папка не существует: {folder_path}")
            return []

        all_chunks = []
        pattern = "**/*" if recursive else "*"

        for filepath in folder_path.glob(pattern):
            chunks = self.process_file(filepath)
            all_chunks.extend(chunks)

        return all_chunks


splitter = MarkdownProcessor(config)
