import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "NEXUS"
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH: str = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "nexus.db"))
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    PRIMARY_AI_PROVIDER: str = os.environ.get("PRIMARY_AI_PROVIDER", "gemini")
    FALLBACK_AI_PROVIDER: str = os.environ.get("FALLBACK_AI_PROVIDER", "ollama")
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "mistral")

settings = Settings()
