import streamlit as st

from src.rag_pipeline import RAGPipeline
from settings.config import config

st.set_page_config(
    page_title="Elden RAG",
    page_icon="⚔️",
    layout="centered",
)


@st.cache_resource
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline(config)


rag_pipeline = get_rag_pipeline()

documents = rag_pipeline.get_resources()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("База знаний Междуземья")

    st.subheader("Добавить документ")

    document_url = st.text_input(
        "URL страницы Wiki",
        placeholder="https://eldenring.fandom.com/ru/wiki/...",
    )

    if st.button("Добавить", use_container_width=True):
        if not document_url:
            st.warning("Введите URL.")

        else:
            with st.spinner("Загружаю страницу..."):
                try:
                    rag_pipeline.add_documents(document_url)

                    st.success("Документ добавлен.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Ошибка: {e}")

    st.divider()

    with st.expander(f"Источники ({len(documents)})", expanded=False):
        if not documents:
            st.caption("В базе пока нет документов.")

        else:
            for document in documents:
                st.markdown(f"- [{document['title']}]({document['source']})")

st.title("Elden RAG")

st.caption("Спросите о боссах, оружии, NPC, локациях и квестах.")


for message in st.session_state.messages:
    with st.chat_message(
        message["role"],
        avatar="🧙‍♂️" if message["role"] == "assistant" else "⚔️",
    ):
        st.markdown(message["content"])


question = st.chat_input("Спросите о Междуземье...")

if question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user", avatar="⚔️"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🧙‍♂️"):
        with st.spinner("Ищу знания в Междуземье..."):
            try:
                answer = rag_pipeline.ask(question)

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as e:
                st.error(f"Ошибка: {e}")
