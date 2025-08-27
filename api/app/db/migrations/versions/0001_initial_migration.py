from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()

    # --- Create enums only if missing
    doc_type_enum = postgresql.ENUM(
        'law', 'regulation', 'circular', 'guideline',
        name='doc_type_enum'
    )
    status_enum = postgresql.ENUM(
        'draft', 'in_review', 'approved', 'published',
        name='status_enum'
    )

    # idempotent pre-create (won't fail if exists)
    doc_type_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    # IMPORTANT: when using already-created enums on columns,
    # pass create_type=False so SQLAlchemy doesn't try to CREATE TYPE again.
    doc_type_ref = postgresql.ENUM(name='doc_type_enum', create_type=False)
    status_ref   = postgresql.ENUM(name='status_enum',   create_type=False)

    op.create_table(
        'official_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('doc_type', doc_type_ref, nullable=False),
        sa.Column('jurisdiction', sa.Text()),
        sa.Column('authority', sa.Text()),
        sa.Column('effective_date', sa.Date()),
        sa.Column('amended_date', sa.Date()),
        sa.Column('source_url', sa.Text()),
        sa.Column('file_s3', sa.Text()),
        sa.Column('status', status_ref, server_default='published', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_official_status', 'official_documents', ['status'])
    op.create_index('idx_official_title', 'official_documents', ['title'])

    # other enums used here are licensing_enum / pii_status_enum (for QA)
    licensing_enum = postgresql.ENUM('allowed','restricted', name='licensing_enum')
    pii_enum = postgresql.ENUM('clean','contains', name='pii_status_enum')
    licensing_enum.create(bind, checkfirst=True)
    pii_enum.create(bind, checkfirst=True)

    licensing_ref = postgresql.ENUM(name='licensing_enum', create_type=False)
    pii_ref       = postgresql.ENUM(name='pii_status_enum', create_type=False)

    op.create_table(
        'qa_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('topic_tags', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('source_url', sa.Text()),
        sa.Column('author', sa.String(255)),
        sa.Column('org', sa.String(255)),
        sa.Column('answered_at', sa.Date()),
        sa.Column('quality_score', sa.Float()),
        sa.Column('licensing', licensing_ref, server_default='allowed', nullable=False),
        sa.Column('pii_status', pii_ref, server_default='clean', nullable=False),
        sa.Column('moderation_status', sa.String(50), server_default='published', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_qa_status', 'qa_entries', ['moderation_status'])

def downgrade():
    # drop tables first
    op.drop_index('idx_qa_status', table_name='qa_entries')
    op.drop_table('qa_entries')

    op.drop_index('idx_official_status', table_name='official_documents')
    op.drop_index('idx_official_title', table_name='official_documents')
    op.drop_table('official_documents')

    # enums removal (if you really want to drop types; safe-guard pattern)
    bind = op.get_bind()
    for enum_name in ['pii_status_enum', 'licensing_enum', 'status_enum', 'doc_type_enum']:
        op.execute(f"""DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE t.typname = '{enum_name}') THEN
                -- will fail if any column still depends on it; that's expected
                -- in production we usually keep types to avoid cascade issues.
                NULL;
            END IF;
        END
        $$;""")
