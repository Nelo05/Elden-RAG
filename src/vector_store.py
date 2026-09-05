from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams
from langchain_core.documents import Document

from settings.config import AppSettings


class VectorStoreManager:
    def __init__(self, config: AppSettings):
        self.collection_name = config.collection_name
        self.qdrant_connection_mode = config.qdrant_connection_mode
        self.qdrant_host = config.qdrant_host
        self.qdrant_port = config.qdrant_port
        self.qdrant_grpc_port = config.qdrant_grpc_port
        self.qdrant_path = config.qdrant_path
        self.top_k = config.top_k
        self.search_type = config.search_type
        self.dense_vector_size = config.dense_vector_size
        self.distance = config.distance
        self.client = self._create_qdrant_client()
        self.dense_embedding = HuggingFaceEmbeddings(
            model_name=config.embedding_model,
            encode_kwargs={"prompt": "passage: ", "normalize_embeddings": True},
            query_encode_kwargs={"prompt": "query: ", "normalize_embeddings": True},
        )
        self.sparse_embedding = FastEmbedSparse(model_name=config.sparse_model)
        self._ensure_collection()
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.dense_embedding,
            sparse_embedding=self.sparse_embedding,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse",
        )

    def _create_qdrant_client(self):
        if self.qdrant_connection_mode == "remote":
            return QdrantClient(
                host=self.qdrant_host,
                port=self.qdrant_port,
                grpc_port=self.qdrant_grpc_port
            )
        else:
            return QdrantClient(path=str(self.qdrant_path))

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        if any(c.name == self.collection_name for c in collections):
            print(f"Коллекция '{self.collection_name}' уже существует.")
            return
        print(f"Создание коллекции '{self.collection_name}'.")

        distance_map = {
            "COSINE": Distance.COSINE,
            "DOT": Distance.DOT,
            "EUCLID": Distance.EUCLID,
        }
        distance = distance_map.get(self.distance, Distance.COSINE)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=self.dense_vector_size,
                    distance=distance,
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            },
        )

    def add_documents(self, documents: List[Document]):
        if not documents:
            print("Нет документов для добавления.")
            return
        self.vector_store.add_documents(documents)

    def as_retriever(self):
        return self.vector_store.as_retriever(
            search_type=self.search_type,
            search_kwargs={"k": self.top_k},
        )
