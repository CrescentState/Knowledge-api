import os
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from loguru import logger
from app.core.config import settings

load_dotenv()

# Neon / Railway PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("CRITICAL: DATABASE_URL environment variable is missing!")

def get_db_connection():
    conn = psycopg2.connect(settings.DATABASE_URL)
    register_vector(conn)
    return conn

def init_db():
    """Initializes the vector extension and document_chunks table."""
    # 1. Open a raw connection without register_vector
    raw_conn = psycopg2.connect(settings.DATABASE_URL)
    
    try:
        with raw_conn.cursor() as cur:
            # 2. Enable the extension FIRST
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        raw_conn.commit()
    except Exception as e:
        raw_conn.rollback()
        logger.error(f"Failed to enable vector extension: {str(e)}")
        raise
    finally:
        raw_conn.close()

    # 3. Now register vector and create table safely
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id SERIAL PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    chunk_index INT NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(384),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
        logger.info("Successfully initialized PostgreSQL database with pgvector extension.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to initialize database tables: {str(e)}")
        raise
    finally:
        conn.close()