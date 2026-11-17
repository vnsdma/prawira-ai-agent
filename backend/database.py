import logging
import json
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, Numeric, DateTime, func, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from config import settings

logger = logging.getLogger("prawira_agent.database")

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    similarity_grade = Column(String(50), default="premium")
    stock = Column(Integer, nullable=False, default=0)
    unit = Column(String(20), default="pack")
    weight_grams = Column(Integer, default=100)
    price = Column(Numeric(12, 2), nullable=False)
    shelf_location = Column(String(50))
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_name = Column(String(255), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    # Stored as Vector in PostgreSQL and as JSON in SQLite
    embedding = Column(Vector, nullable=True)
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Engine & Session Setup
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = None
SessionLocal = None
is_sqlite = False

def create_db_engine():
    global engine, SessionLocal, is_sqlite
    try:
        test_engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 3} if "postgresql" in db_url else {})
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        is_sqlite = "sqlite" in db_url
        logger.info(f"Connected to database: {'SQLite' if is_sqlite else 'PostgreSQL'}")
        return True
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite dev database for immediate offline readiness.")
        fallback_url = "sqlite:///./prawira_dev.db"
        engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        is_sqlite = True
        return True

create_db_engine()

def get_db():
    if SessionLocal is None:
        create_db_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes tables and seeds default products if empty."""
    global engine, SessionLocal, is_sqlite
    if engine is None:
        create_db_engine()

    try:
        # If PostgreSQL, try enabling pgvector extension
        if not is_sqlite:
            try:
                with engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
            except Exception as pe:
                logger.warning(f"pgvector extension check: {pe}")

        # Create tables
        Base.metadata.create_all(bind=engine)

        # Ensure embedding_json column exists on PostgreSQL if created from init_db.sql
        if not is_sqlite:
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_json TEXT;"))
                    conn.commit()
            except Exception as ce:
                logger.warning(f"Column check: {ce}")

        # Clean tables initialization (NO DUMMY SEEDS)
        return True
    except Exception as e:
        logger.error(f"Error during init_db: {e}")
        return False
