import os
from typing import List, Union
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# Load .env manually if exists
env_path = BASE_DIR / ".env"
if not env_path.exists():
    env_path = ROOT_DIR / ".env"

if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                val = val.strip().strip('"').strip("'")
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = val

# Ensure SQLite URL is always resolved to an absolute path inside ROOT_DIR
raw_db_url = os.getenv("DATABASE_URL", "")
if not raw_db_url or raw_db_url.startswith("sqlite:///."):
    db_file_path = (ROOT_DIR / "sfrt.db").resolve().as_posix()
    normalized_db_url = f"sqlite:///{db_file_path}"
else:
    normalized_db_url = raw_db_url

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Smart Financial Reporting Tool")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = normalized_db_url
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sfrt-dev-super-secure-key-2026-financial-tool-engine-32chars")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    SESSION_EXPIRE_MINUTES: int = int(os.getenv("SESSION_EXPIRE_MINUTES", "1440"))
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "INR")
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")
    COOKIE_NAME: str = "sfrt_session"
    ALLOWED_ORIGINS: List[str] = ["*"]
    MAX_CSV_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB

settings = Settings()
