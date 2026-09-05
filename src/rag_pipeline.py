from langchain_core.prompts import ChatPromptTemplate
from langchain_gigachat.chat_models import GigaChat

from settings.config import AppSettings

from src.vector_store import VectorStoreManager
from src.loader import MediaWikiLoader
from src.splitter import MarkdownProcessor


class RAGPipeline:
    def __init__(self, config: AppSettings):

        self.loader = MediaWikiLoader()
        self.splitter = MarkdownProcessor(config)

        self.llm = GigaChat(
            credentials=config.gigachat_credentials.get_secret_value(),
            model=config.gigachat_model,
            verify_ssl_certs=config.verify_ssl_certs,
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Ты — полезный ассистент. Отвечай на вопрос, используя только предоставленный контекст. "
                    "Если в контексте нет ответа, скажи: «Информация не найдена». Не добавляй ничего от себя.\n\n"
                    "Контекст:\n{context}",
                ),
                ("human", "{input}"),
            ]
        )

        self.vector_store = VectorStoreManager(config)

    def ask(self, query: str) -> str:
        try:

            docs = self.vector_store.as_retriever().invoke(query)
            context = "\n\n---\n\n".join([doc.page_content for doc in docs])
            message = self.prompt.format_messages(context=context, input=query)
            response = self.llm.invoke(message)
            return response.content
        except Exception as e:
            print(f"Ошибка при выполнении запроса: {e}", exc_info=True)
            return "Произошла ошибка при обработке запроса."

    def add_documents(self, url: str) -> None:
        try:
            docs = self.loader.load(url)
            chunks = self.splitter.process_documents(docs)
            self.vector_store.add_documents(chunks)
            print(f"Добавлено: {len(docs)} документов, включающих {len(chunks)} чанков")
        except Exception as e:
            print(f"Ошибка при выполнении запроса: {e}", exc_info=True)
            return "Произошла ошибка при обработке запроса."
