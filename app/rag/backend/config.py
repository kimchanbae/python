import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434" 
)

CHROMA_HOST = os.getenv(
    "CHROMA_HOST",
    "127.0.0.1"
)
CHROMA_PORT = int(
    os.getenv("CHROMA_PORT", 8001)
)