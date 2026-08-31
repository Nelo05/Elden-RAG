from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams
from langchain_core.documents import Document

from settings.vector_store_settings import vector_config


class VectorStoreManager:
    def __init__(self):
        self.collection_name = vector_config.collection_name
        self.client = self._create_qdrant_client()
        self.dense_embedding = HuggingFaceEmbeddings(
            model_name=vector_config.embedding_model,
            encode_kwargs={"prompt": "passage: ", "normalize_embeddings": True},
            query_encode_kwargs={"prompt": "query: ", "normalize_embeddings": True},
        )
        self.sparse_embedding = FastEmbedSparse(model_name=vector_config.sparse_model)

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
        if vector_config.qdrant_host:
            print(
                f"Подключение к Qdrant по адресу {vector_config.qdrant_host}:{vector_config.qdrant_port}"
            )
            return QdrantClient(
                host=vector_config.qdrant_host,
                port=vector_config.qdrant_port,
                grpc_port=vector_config.qdrant_grpc_port,
            )
        else:
            path = str(vector_config.qdrant_path)
            print(f"Использование локального хранилища Qdrant по пути {path}")
            return QdrantClient(path=path)

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
        distance = distance_map.get(vector_config.distance, Distance.COSINE)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=vector_config.dense_vector_size,
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
        print(f"Добавление {len(documents)} чанков.")
        self.vector_store.add_documents(documents)


    def as_retriever(
        self
    ):
        return self.vector_store.as_retriever(
            search_type=vector_config.search_type,
            search_kwargs={"k": vector_config.top_k}
        )

vectore_store = VectorStoreManager()