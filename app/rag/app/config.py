from pathlib import Path

# 프로젝트 경로
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Ollama 설정
OLLAMA_BASE_URL = "http://127.0.0.1:11434"

LLM_MODEL = "qwen2.5:1.5b"
EMBED_MODEL = "nomic-embed-text"

# ChromaDB 설정
COLLECTION_NAME = "knowledge_base"

# 문서 분할 설정
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# 검색 설정
TOP_K = 5

# 임베딩 처리 배치 크기
BATCH_SIZE = 64

# LLM 생성 설정
TEMPERATURE = 0.1
NUM_CTX = 4096
NUM_PREDICT = 1024

# 폴더 자동 생성
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

print("BASE_DIR:", BASE_DIR)
print("CHROMA_DIR:", CHROMA_DIR)
print("CHROMA EXISTS:", CHROMA_DIR.exists())
print("SQLITE EXISTS:", (CHROMA_DIR / "chroma.sqlite3").exists())