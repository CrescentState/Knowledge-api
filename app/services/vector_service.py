import re
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from app.core.database import get_db_connection
from loguru import logger

class VectorService:
    def __init__(self) -> None:
        # Lightweight CPU-friendly embedding model (384 dimensions)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Splits raw text/markdown into overlapping character chunks."""
        cleaned_text = re.sub(r'\n+', '\n', text)
        chunks = []
        start = 0
        
        while start < len(cleaned_text):
            end = start + chunk_size
            chunks.append(cleaned_text[start:end])
            start += (chunk_size - overlap)
            
        return chunks

    def process_and_store(self, document_name: str, content: str) -> int:
        """Chunks content, generates embeddings, and persists them into PGVector."""
        chunks = self._chunk_text(content)
        if not chunks:
            return 0

        embeddings = self.model.encode(chunks, show_progress_bar=False)

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # 1. Clear previous chunks for this document to prevent duplicate search results
                cur.execute(
                    "DELETE FROM document_chunks WHERE document_name = %s;",
                    (document_name,)
                )

                # 2. Insert fresh chunks
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    cur.execute(
                        """
                        INSERT INTO document_chunks (document_name, chunk_index, content, embedding)
                        VALUES (%s, %s, %s, %s::vector)
                        """,
                        (document_name, idx, chunk, embedding.tolist())
                    )
            conn.commit()
            logger.info(f"Stored {len(chunks)} chunks for document: {document_name}")
            return len(chunks)
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store chunks in PGVector: {str(e)}")
            raise
        finally:
            conn.close()

    def search_similar_chunks(self, query: str, top_k: int = 5) -> list[dict]:
        """Queries PGVector using Cosine Similarity (<=> operator)."""
        query_embedding = self.model.encode(query).tolist()

        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        id,
                        document_name,
                        chunk_index,
                        content,
                        (1 - (embedding <=> %s::vector))::float AS similarity_score
                    FROM document_chunks
                    ORDER BY embedding <=> %s::vector ASC
                    LIMIT %s;
                    """,
                    (str(query_embedding), str(query_embedding), top_k)
                )
                results = cur.fetchall()
                return [dict(row.items()) for row in results]
        except Exception as e:
            logger.error(f"Vector query execution failed: {str(e)}")
            raise
        finally:
            conn.close()