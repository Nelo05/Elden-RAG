from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from settings.config import AppSettings


class MarkdownProcessor:

    def __init__(self, config: AppSettings):
        self.headers_to_split_on = config.headers_to_split_on
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap
        self.min_chunk_length = config.min_chunk_length
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def _process_document(self, document: Document) -> List[Document]:

        try:
            header_splits = self.header_splitter.split_text(document.page_content)
        except Exception as e:
            print(
                f"Ошибка разбиения документа "
                f"{document.metadata.get('title', '')}: {e}"
            )
            return []

        chunks = []

        for doc in header_splits:

            try:
                sub_splits = self.text_splitter.split_documents([doc])
            except Exception as e:
                print(
                    f"Ошибка рекурсивного разбиения "
                    f"{document.metadata.get('title', '')}: {e}"
                )
                continue

            for chunk in sub_splits:

                if len(chunk.page_content.strip()) < self.min_chunk_length:
                    continue

                chunk.metadata.update(document.metadata)

                chunks.append(chunk)

        return chunks

    def process_documents(
        self,
        documents: List[Document],
    ) -> List[Document]:

        chunks = []

        for document in documents:
            chunks.extend(self._process_document(document))

        return chunks
