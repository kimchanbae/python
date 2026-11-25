from functools import lru_cache

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.rag.config.config import (
    OLLAMA_BASE_URL,
    EMBED_MODEL,
    CHROMA_DIR,
    COLLECTION_NAME
)


@lru_cache(maxsize=1)
def get_embeddings():

    return OllamaEmbeddings(
        model=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )


@lru_cache(maxsize=1)
def get_vector_store():

    embeddings = get_embeddings()

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR)
    )


def get_document_count():
    try:
        store = get_vector_store()

        return store._collection.count()
    except Exception as e:
        print(f"[CHROMA COUNT ERROR] {repr(e)}")
        raise

def test_chroma_save():

    vector_store = get_vector_store()

    print("[TEST] ChromaDB 저장 테스트 시작", flush=True)

    test_text = "ChromaDB 저장 테스트 문서입니다."

    test_embedding = get_embeddings().embed_documents(
        [test_text]
    )

    print("[TEST] 임베딩 생성 완료", flush=True)

    vector_store._collection.add(
        ids=["test_chroma_001"],
        embeddings=test_embedding,
        documents=[test_text],
        metadatas=[{"source": "test"}]
    )

    print("[TEST] ChromaDB 저장 완료", flush=True)

    vector_store._collection.delete(
        ids=["test_chroma_001"]
    )

    print("[TEST] 테스트 데이터 삭제 완료", flush=True)