import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("sfrt.database")

database_url = settings.DATABASE_URL
connect_args = {}

if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    if database_url.startswith("mysql"):
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        # Test connection
        with engine.connect() as conn:
            logger.info("Successfully connected to MySQL database.")
    else:
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True
        )
except Exception as e:
    logger.warning(
        f"Failed to connect to primary database at {database_url} ({e}). "
        f"Falling back to local SQLite database to ensure high availability."
    )
    from app.config import ROOT_DIR
    fallback_url = f"sqlite:///{(ROOT_DIR / 'sfrt.db').resolve().as_posix()}"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes tables without dropping existing data."""
    import app.models  # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema verified/initialized successfully.")
