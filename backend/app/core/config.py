import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "NEXUS"
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH: str = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "nexus.db"))
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

settings = Settings()
