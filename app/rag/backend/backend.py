import uuid
import threading
import time
import os
import threading
import requests

from pathlib import Path
from datetime import datetime

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    BackgroundTasks,
    HTTPException
)

from pydantic import BaseModel, Field

from app.config import(
    DATA_DIR
)
from app.indexer import index_documents
from app.rag import ask_question
from app.vector_store import (
    get_document_count,
    get_vector_store
)

from config import(
    OLLAMA_BASE_URL,
    CHROMA_HOST,
    CHROMA_PORT
)

print("BACKEND MODULE LOADED")
print("PID:", os.getpid())
print("THREAD:", threading.current_thread().name)

app = FastAPI(
    title="Knowledge RAG API",
    description="Qwen2.5 1.5B 기반 지식검색 API",
    version="1.0.0"
)

# 색인 작업 동시 실행 방지
index_lock = threading.Lock()

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".md",
    ".csv", ".xlsx", ".pptx", ".html", ".htm"
}

MAX_FILE_SIZE = 50 * 1024 * 1024


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000
    )
    top_k: int = Field(default=5, ge=1, le=10)

@app.middleware("http")
async def log_requests(request, call_next):

    start = time.time()

    print(f"요청 시작: {request.method} {request.url}")

    response = await call_next(request)

    elapsed = time.time() - start

    print(f"요청 완료: {elapsed:.2f}초")

    return response

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Knowledge RAG",
        "ollama": OLLAMA_BASE_URL,
        "chroma": f"{CHROMA_HOST}:{CHROMA_PORT}"
    }

@app.post("/api/upload")
def upload_documents(
    files: list[UploadFile] = File(...)
):

    uploaded = []
    errors = []

    for file in files:

        filename = Path(
            file.filename or ""
        ).name

        extension = Path(filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            errors.append({
                "filename": filename,
                "error": "지원하지 않는 파일 형식"
            })
            continue

        file_id = uuid.uuid4().hex

        save_path = (
            UPLOAD_DIR /
            f"{file_id}_{filename}"
        )

        size = 0

        try:
            with save_path.open("wb") as f:

                while True:

                    chunk = file.file.read(1024 * 1024)

                    if not chunk:
                        break

                    size += len(chunk)

                    if size > MAX_FILE_SIZE:
                        raise ValueError(
                            "파일 크기 제한 초과 (50MB)"
                        )

                    f.write(chunk)

            uploaded.append({
                "filename": filename,
                "stored_name": save_path.name,
                "size": size
            })

        except Exception as e:

            save_path.unlink(missing_ok=True)

            errors.append({
                "filename": filename,
                "error": str(e)
            })

    return {
        "uploaded": uploaded,
        "errors": errors,
        "total": len(uploaded)
    }

index_status = {
    "running": False,
    "status": "idle",
    "message": "대기 중",
    "started_at": None,
    "finished_at": None,
    "document_chunks": 0,
    "error": None
}

def run_indexing():
    print("[DEBUG] run_indexing 시작")
    
    try:
        index_status["status"] = "running"
        index_status["message"] = "문서 색인 중...."

        print("[DEBUG] index_documents 호출")

        result = index_documents()

        print("[DEBUG] index_documents 완료")
        
        index_status["document_chunks"] = (result["total_stored_chunks"])

        index_status["status"] = "completed"
        index_status["message"] = "문서 색인 완료"
    except Exception as e:
        index_status["status"] = "failed"
        index_status["message"] = "문서 색인 실패"
        index_status["error"] = str(e)

        print(f"[INDEX ERROR] {e}")
    finally:
        index_status["running"] = False
        index_status["finished_at"] = (datetime.now().isoformat())

        index_lock.release()

        print("[DEBUG] 색인 작업 종료")

@app.post("/api/index")
def create_index(background_tasks: BackgroundTasks):

    print("[DEBUG] /api/index 호출")

    if not index_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="이미 색인 작업이 진행 중입니다."
        )

    index_status.update({
        "running": True,
        "status": "queued",
        "message": "색인 작업 접수 완료",
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "document_chunks": 0,
        "error": None
    })

    background_tasks.add_task(run_indexing)

    print("[DEBUG] BackgroundTasks 등록 완료")

    return {
        "status": "accepted",
        "message": "문서 색인 작업이 시작되었습니다."
    }

@app.get("/api/index/status")
def get_index_status():
    return index_status.copy()

@app.post("/api/query")
def query(request: QueryRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="질문을 입력해 주세요."
        )

    try:

        # 기존 RAG 검색 함수 사용
        result = ask_question(
            question,
            top_k=request.top_k
        )

        return {
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/documents")
def documents():
    print("[DOCUMENTS] API START")

    try:
        print("[DOCUMENTS] vector store 연결")
        
        # 1. Vector Store 초기화
        vector_store = get_vector_store()

        collection = vector_store._collection

        count = collection.count()

        print("[Metadata] 조회 시작", flush=True)

        # 2. ChromaDB 문서 메타데이터 조회
        result = vector_store.get(
            include=["metadatas"]
        )

        print("[Metadata] 조회 완료", flush=True)

        metadatas = result.get("metadatas") or []

        print(f"[DOCUMENTS] 조회된 청크: {len(metadatas)}")

        files = {}

        # 3. 파일별 청크 개수 집계
        for metadata in metadatas:

            if not metadata:
                continue

            source = metadata.get("source", "Unknown")

            if source not in files:
                files[source] = {
                    "filename": metadata.get(
                        "file_name",
                        Path(source).name
                    ),
                    "chunks": 0
                }

            files[source]["chunks"] += 1

        total_chunks = get_document_count()

        print("[DOCUMENTS] API SUCCESS")

        # 4. 전체 현황 반환
        return {
            "total_files": len(files),
            "total_chunks": total_chunks,
            "documents": list(files.values())
        }
    except Exception as e:
        import traceback

        print("[DOCUMENT ERROR]")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/api/test")
def test():
    return {
        "message": "FastAPI 정상 작동",
        "status": "ok"
    }

@app.get("/api/ollama/health")
def ollama_health():

    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )

        response.raise_for_status()

        return {
            "status": "ok",
            "ollama": "connected"
        }

    except requests.RequestException as e:

        raise HTTPException(
            status_code=503,
            detail=f"Ollama 연결 실패: {str(e)}"
        )