"""Initial migration - Create all tables

Revision ID: 0001
Revises: 
Create Date: 2025-08-20 08:26:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    doc_type_enum = postgresql.ENUM('law', 'regulation', 'circular', 'guideline', name='doc_type_enum')
    doc_type_enum.create(op.get_bind())
    
    doc_status_enum = postgresql.ENUM('draft', 'in_review', 'approved', 'published', name='doc_status_enum')
    doc_status_enum.create(op.get_bind())
    
    unit_type_enum = postgresql.ENUM('part', 'chapter', 'section', 'article', 'paragraph', 'clause', 'item', 'note', 'annex', name='unit_type_enum')
    unit_type_enum.create(op.get_bind())
    
    licensing_enum = postgresql.ENUM('allowed', 'restricted', name='licensing_enum')
    licensing_enum.create(op.get_bind())
    
    pii_status_enum = postgresql.ENUM('clean', 'contains', name='pii_status_enum')
    pii_status_enum.create(op.get_bind())

    # Create official_documents table
    op.create_table('official_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('doc_type', doc_type_enum, nullable=False),
        sa.Column('jurisdiction', sa.String(length=255), nullable=True),
        sa.Column('authority', sa.String(length=255), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('amended_date', sa.Date(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('file_s3', sa.Text(), nullable=True),
        sa.Column('status', doc_status_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_official_documents_status'), 'official_documents', ['status'], unique=False)
    op.create_index(op.f('ix_official_documents_title'), 'official_documents', ['title'], unique=False)

    # Create legal_units table
    op.create_table('legal_units',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_type', unit_type_enum, nullable=False),
        sa.Column('num_label', sa.String(length=100), nullable=True),
        sa.Column('heading', sa.Text(), nullable=True),
        sa.Column('text_plain', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['official_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create qa_entries table
    op.create_table('qa_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('topic_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('org', sa.String(length=255), nullable=True),
        sa.Column('answered_at', sa.Date(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('licensing', licensing_enum, nullable=True),
        sa.Column('pii_status', pii_status_enum, nullable=True),
        sa.Column('moderation_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qa_entries_answer'), 'qa_entries', ['answer'], unique=False)
    op.create_index(op.f('ix_qa_entries_moderation_status'), 'qa_entries', ['moderation_status'], unique=False)
    op.create_index(op.f('ix_qa_entries_question'), 'qa_entries', ['question'], unique=False)
    op.create_index(op.f('ix_qa_entries_topic_tags'), 'qa_entries', ['topic_tags'], unique=False, postgresql_using='gin')

    # Create users table (reserved for future use)
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create sync_watermarks table
    op.create_table('sync_watermarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('last_imported_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('sync_watermarks')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_qa_entries_topic_tags'), table_name='qa_entries')
    op.drop_index(op.f('ix_qa_entries_question'), table_name='qa_entries')
    op.drop_index(op.f('ix_qa_entries_moderation_status'), table_name='qa_entries')
    op.drop_index(op.f('ix_qa_entries_answer'), table_name='qa_entries')
    op.drop_table('qa_entries')
    op.drop_table('legal_units')
    op.drop_index(op.f('ix_official_documents_title'), table_name='official_documents')
    op.drop_index(op.f('ix_official_documents_status'), table_name='official_documents')
    op.drop_table('official_documents')
    
    # Drop ENUM types
    doc_type_enum = postgresql.ENUM('law', 'regulation', 'circular', 'guideline', name='doc_type_enum')
    doc_type_enum.drop(op.get_bind())
    
    doc_status_enum = postgresql.ENUM('draft', 'in_review', 'approved', 'published', name='doc_status_enum')
    doc_status_enum.drop(op.get_bind())
    
    unit_type_enum = postgresql.ENUM('part', 'chapter', 'section', 'article', 'paragraph', 'clause', 'item', 'note', 'annex', name='unit_type_enum')
    unit_type_enum.drop(op.get_bind())
    
    licensing_enum = postgresql.ENUM('allowed', 'restricted', name='licensing_enum')
    licensing_enum.drop(op.get_bind())
    
    pii_status_enum = postgresql.ENUM('clean', 'contains', name='pii_status_enum')
    pii_status_enum.drop(op.get_bind())
