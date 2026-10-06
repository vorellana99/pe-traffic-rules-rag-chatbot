"""initial schema: vector extension + 4 tables with HNSW and GIN indexes

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-27
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensión pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # documents
    op.execute(
        """
        CREATE TABLE documents (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            filename      text NOT NULL,
            title         text,
            pages         integer,
            status        text NOT NULL DEFAULT 'processing',
            error_message text,
            chunk_count   integer NOT NULL DEFAULT 0,
            created_at    timestamptz NOT NULL DEFAULT now()
        );
        """
    )

    # chunks (embedding vector(1024) + content_tsv generado en español)
    op.execute(
        """
        CREATE TABLE chunks (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            content     text NOT NULL,
            page        integer,
            position    integer,
            embedding   vector(1024),
            content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('spanish', content)) STORED,
            created_at  timestamptz NOT NULL DEFAULT now()
        );
        """
    )
    # Índice HNSW (coseno) sobre el embedding
    op.execute(
        "CREATE INDEX chunks_embedding_hnsw ON chunks "
        "USING hnsw (embedding vector_cosine_ops);"
    )
    # Índice GIN sobre el tsvector (full-text)
    op.execute(
        "CREATE INDEX chunks_content_tsv_gin ON chunks USING gin (content_tsv);"
    )

    # conversations
    op.execute(
        """
        CREATE TABLE conversations (
            id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            title      text,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        """
    )

    # messages
    op.execute(
        """
        CREATE TABLE messages (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role            text NOT NULL,
            content         text NOT NULL,
            sources         jsonb,
            created_at      timestamptz NOT NULL DEFAULT now()
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS messages;")
    op.execute("DROP TABLE IF EXISTS conversations;")
    op.execute("DROP TABLE IF EXISTS chunks;")
    op.execute("DROP TABLE IF EXISTS documents;")
    # La extensión vector se deja instalada a propósito.
