from pathlib import Path
import hashlib

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from app.config import (
    DATA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    BATCH_SIZE
)

from app.document_loader import (
    load_document,
    file_hash,
    SUPPORTED_EXTENSIONS
)

from app.vector_store import (
    get_vector_store,
    get_document_count
)


def make_chunk_id(source, file_hash_value, index):
    """파일 및 청크별 고유 ID"""

    raw = f"{source}:{file_hash_value}:{index}"

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def index_documents():
    print("index_documents 시작", flush=True)

    vector_store = get_vector_store()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    total_files = 0
    total_chunks = 0

    # 기존 파일별 색인 정보
    existing = vector_store.get(
        include=["metadatas"]
    )

    print("[기존 파일별] 색인정보", flush=True)

    indexed_files = {}

    for metadata in existing["metadatas"]:
        if not metadata:
            continue

        source = metadata.get("source")
        content_hash = metadata.get("file_hash")

        if source and content_hash:
            indexed_files[source] = content_hash

    print("전체 문서 검색 시작...", flush=True)

    # 전체 문서 폴더 검색
    for path in DATA_DIR.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        source = str(path.resolve())

        try:
            current_hash = file_hash(path)

            # 변경되지 않은 파일은 생략
            if indexed_files.get(source) == current_hash:
                print(f"[SKIP] {path.name}")
                continue

            print(f"[INDEX] {path.name}", flush=True)

            # 변경된 파일의 기존 청크 제거
            if source in indexed_files:
                vector_store.delete(
                    where={"source": source}
                )

            # 문서 로딩
            documents = load_document(path)

            print(
                f"[STEP 1] 문서 로딩 완료: {len(documents)}",
                flush=True
            )

            if not documents:
                print(f"[EMPTY] {path.name}")
                continue

            # 문서 분할
            chunks = splitter.split_documents(
                documents
            )

            print(
                f"[STEP 2] 문서 분할 완료: {len(chunks)} chunks",
                flush=True
            )

            ids = []

            print(
                f"[STEP 2-1] 전체 청크 수: {len(chunks)}",
                flush=True
            )

            for i, chunk in enumerate(chunks):
                if i % 100 == 0:
                    print(
                        f"[STEP 2-1] ID 생성 진행: {i}/{len(chunks)}",
                        flush=True
                    )

                chunk.metadata["file_hash"] = (
                    current_hash
                )

                chunk.metadata["file_name"] = (
                    path.name
                )

                chunk.metadata["chunk_index"] = i

                ids.append(
                    make_chunk_id(
                        source,
                        current_hash,
                        i
                    )
                )

                print(
                    f"[STEP 2-1] ID 생성 완료: {len(ids)}",
                    flush=True
                )

            print("[STEP 3] 벡터 저장 시작", flush=True)    

            # 배치 단위로 벡터 저장
            for start in range(0, len(chunks), BATCH_SIZE):

                end = start + BATCH_SIZE

                print(
                    f"[STEP 3] 벡터 저장: {start} ~ {min(end, len(chunks))}",
                    flush=True
                )

                texts = [
                    chunk.page_content
                    for chunk  in chunks[start:end]
                ]

                metadatas = [
                    chunk.metadata
                    for chunk in chunks[start:end]
                ]

                embeddings = vector_store.embeddings.embed_documents(texts)

                # 임베딩 검증
                import numpy as np

                embeddings = np.asarray(
                    embeddings,
                    dtype=np.float32
                )

                print("Shape:", embeddings.shape, flush=True)
                print("Dimension:", embeddings.shape[1], flush=True)
                print("Dtype:", embeddings.dtype, flush=True)

                print(
                    "NaN 존재:",
                    np.isnan(embeddings).any(),
                    flush=True
                )

                print(
                    "Inf 존재:",
                    np.isinf(embeddings).any(),
                    flush=True
                )

                print(
                    "첫 번째 벡터:",
                    embeddings[0][:10],
                    flush=True
                )

                print("Embedding shape:", embeddings.shape, flush=True)
                print("Embedding dtype:", embeddings.dtype, flush=True)
                print("Embedding finite:", np.isfinite(embeddings).all(), flush=True)

                collection = vector_store._collection

                print("ID:", ids[start:end], flush=True)
                print("TEXT COUNT:", len(texts), flush=True)
                print("METADATA COUNT:", len(metadatas), flush=True)
                print("EMBEDDING COUNT:", len(embeddings), flush=True)

                print("[TEST 2] 저장 데이터 확인 완료", flush=True)

                # 실제 저장
                print("[TEST 3] upsert 시작", flush=True)

                collection.upsert(
                    ids=ids[start:end],
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas
                )

                print("[TEST 3] upsert 완료", flush=True)

            print("[STEP 3] 벡터 저장 완료", flush=True)

            total_files += 1
            total_chunks += len(chunks)

            print(
                f"[DONE] {path.name} "
                f"({len(chunks)} chunks)"
            )

        except Exception as e:
            print(
                f"[ERROR] {path.name}: {e}"
            )

    print("\n========== 색인 완료 ==========")
    print(f"색인 파일 수: {total_files}")
    print(f"색인 청크 수: {total_chunks}")
    print(f"전체 저장 청크: "f"{vector_store._collection.count()}")

    # 색인 결과 반환
    return {
        "total_files": total_files,
        "total_chunks": total_chunks,
        "total_stored_chunks": get_document_count()
    }


if __name__ == "__main__":
    index_documents()