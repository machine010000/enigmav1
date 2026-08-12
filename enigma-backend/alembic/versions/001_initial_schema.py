"""Initial schema for Enigma Profile, Marketplace, and OAuth tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(conn)

    def table_exists(name: str) -> bool:
        return name in inspector.get_table_names()

    def index_exists(table: str, name: str) -> bool:
        try:
            return any(idx.get('name') == name for idx in inspector.get_indexes(table))
        except Exception:
            return False

    def enum_exists(name: str) -> bool:
        try:
            result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = :name"), {'name': name})
            return result.first() is not None
        except Exception:
            return False

    # Create account_status_enum
    account_status_enum = postgresql.ENUM(
        'active', 'suspended', 'verified', 'unverified', 'restricted', 'unknown',
        name='account_status_enum'
    )
    if not enum_exists('account_status_enum'):
        account_status_enum.create(op.get_bind())

    # Create data_source_enum
    data_source_enum = postgresql.ENUM(
        'manual_input', 'api_integration', 'mock_adapter', 'unknown',
        name='data_source_enum'
    )
    if not enum_exists('data_source_enum'):
        data_source_enum.create(op.get_bind())

    # Create freshness_status_enum
    freshness_status_enum = postgresql.ENUM(
        'fresh', 'stale', 'expired', 'unknown',
        name='freshness_status_enum'
    )
    if not enum_exists('freshness_status_enum'):
        freshness_status_enum.create(op.get_bind())

    # Create application_status_enum
    application_status_enum = postgresql.ENUM(
        'draft', 'submitted', 'withdrawn', 'accepted', 'rejected', 'archived', 'unknown',
        name='application_status_enum'
    )
    if not enum_exists('application_status_enum'):
        application_status_enum.create(op.get_bind())

    # Create auth_status_enum
    auth_status_enum = postgresql.ENUM(
        'authenticated', 'not_authenticated', 'expired', 'refresh_needed', 'error',
        name='auth_status_enum'
    )
    if not enum_exists('auth_status_enum'):
        auth_status_enum.create(op.get_bind())

    # Create enigma_profiles table (skip if it already exists)
    if not table_exists('enigma_profiles'):
        op.create_table(
            'enigma_profiles',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('profession', sa.String(), nullable=True),
            sa.Column('expertise_domains', sa.JSON(), nullable=True),
            sa.Column('capabilities', sa.JSON(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: profile_metadata
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('profile_id')
        )
    if not index_exists('enigma_profiles', 'ix_enigma_profiles_profile_id'):
        op.create_index('ix_enigma_profiles_profile_id', 'enigma_profiles', ['profile_id'])
    
    # Create knowledge_progress table
    if not table_exists('knowledge_progress'):
        op.create_table(
            'knowledge_progress',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('domain', sa.String(), nullable=False),
            sa.Column('maturity_score', sa.Float(), nullable=True),
            sa.Column('freshness_score', sa.Float(), nullable=True),
            sa.Column('confidence_score', sa.Float(), nullable=True),
            sa.Column('last_updated', sa.DateTime(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: profile_metadata (for EnigmaProfile)
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('profile_id', 'domain')
        )
    if not index_exists('knowledge_progress', 'ix_knowledge_progress_profile_id'):
        op.create_index('ix_knowledge_progress_profile_id', 'knowledge_progress', ['profile_id'])
    
    # Create training_items table
    if not table_exists('training_items'):
        op.create_table(
            'training_items',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('skill_name', sa.String(), nullable=False),
            sa.Column('current_level', sa.String(), nullable=True),
            sa.Column('target_level', sa.String(), nullable=True),
            sa.Column('progress_percentage', sa.Float(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: profile_metadata (for EnigmaProfile)
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('profile_id', 'skill_name')
        )
    if not index_exists('training_items', 'ix_training_items_profile_id'):
        op.create_index('ix_training_items_profile_id', 'training_items', ['profile_id'])
    
    # Create platform_readiness table
    if not table_exists('platform_readiness'):
        op.create_table(
            'platform_readiness',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('platform', sa.String(), nullable=False),
            sa.Column('readiness_score', sa.Float(), nullable=True),
            sa.Column('account_status', sa.String(), nullable=True),
            sa.Column('credits_available', sa.Integer(), nullable=True),
            sa.Column('last_verified', sa.DateTime(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: profile_metadata (for EnigmaProfile)
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('profile_id', 'platform')
        )
    if not index_exists('platform_readiness', 'ix_platform_readiness_profile_id'):
        op.create_index('ix_platform_readiness_profile_id', 'platform_readiness', ['profile_id'])
    
    # Create development_priorities table
    if not table_exists('development_priorities'):
        op.create_table(
            'development_priorities',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('priority', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('estimated_effort', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('development_priorities', 'ix_development_priorities_profile_id'):
        op.create_index('ix_development_priorities_profile_id', 'development_priorities', ['profile_id'])
    
    # Create issues table
    if not table_exists('issues'):
        op.create_table(
            'issues',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('issue_id', sa.String(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('severity', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: issue_metadata
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('profile_id', 'issue_id')
        )
    if not index_exists('issues', 'ix_issues_profile_id'):
        op.create_index('ix_issues_profile_id', 'issues', ['profile_id'])
    
    # Create marketplace_account_states table
    if not table_exists('marketplace_account_states'):
        op.create_table(
            'marketplace_account_states',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.String(), nullable=False),
            sa.Column('platform', sa.String(), nullable=False),
            sa.Column('account_id', sa.String(), nullable=True),
            sa.Column('account_status', account_status_enum, nullable=True),
            sa.Column('credits_available', sa.Integer(), nullable=True),
            sa.Column('credits_pending', sa.Integer(), nullable=True),
            sa.Column('credits_used', sa.Integer(), nullable=True),
            sa.Column('credits_limit', sa.Integer(), nullable=True),
            sa.Column('credits_currency', sa.String(), nullable=True),
            sa.Column('wallet_available', sa.Numeric(10, 2), nullable=True),
            sa.Column('wallet_currency', sa.String(), nullable=True),
            sa.Column('subscription_plan_name', sa.String(), nullable=True),
            sa.Column('subscription_plan_type', sa.String(), nullable=True),
            sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
            sa.Column('subscription_features', sa.JSON(), nullable=True),
            sa.Column('last_verified_at', sa.DateTime(), nullable=True),
            sa.Column('source', data_source_enum, nullable=True),
            sa.Column('confidence', sa.Float(), nullable=True),
            sa.Column('freshness', freshness_status_enum, nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: account_metadata
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('profile_id', 'platform')
        )
    if not index_exists('marketplace_account_states', 'ix_marketplace_account_state_profile_platform'):
        op.create_index('ix_marketplace_account_state_profile_platform', 'marketplace_account_states', ['profile_id', 'platform'])
    
    # Create marketplace_jobs table
    if not table_exists('marketplace_jobs'):
        op.create_table(
        'marketplace_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('platform_job_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('budget_min', sa.Numeric(10, 2), nullable=True),
        sa.Column('budget_max', sa.Numeric(10, 2), nullable=True),
        sa.Column('budget_type', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('client_info', sa.JSON(), nullable=True),
        sa.Column('skills_required', sa.JSON(), nullable=True),
        sa.Column('job_type', sa.String(), nullable=True),
        sa.Column('duration', sa.String(), nullable=True),
        sa.Column('posted_date', sa.DateTime(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: job_metadata
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'platform', 'platform_job_id')
    )
    if not index_exists('marketplace_jobs', 'ix_marketplace_jobs_profile_platform_job_id'):
        op.create_index('ix_marketplace_jobs_profile_platform_job_id', 'marketplace_jobs', ['profile_id', 'platform', 'platform_job_id'])
    if not index_exists('marketplace_jobs', 'ix_marketplace_jobs_job_id'):
        op.create_index('ix_marketplace_jobs_job_id', 'marketplace_jobs', ['job_id'])
    
    # Create marketplace_job_assessments table
    if not table_exists('marketplace_job_assessments'):
        op.create_table(
        'marketplace_job_assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('knowledge_match_score', sa.Float(), nullable=True),
        sa.Column('evidence_match_score', sa.Float(), nullable=True),
        sa.Column('execution_match_score', sa.Float(), nullable=True),
        sa.Column('overall_readiness_score', sa.Float(), nullable=True),
        sa.Column('win_probability', sa.Float(), nullable=True),
        sa.Column('recommended_action', sa.String(), nullable=True),
        sa.Column('blockers', sa.JSON(), nullable=True),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), nullable=True),
        sa.Column('assessment_version', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: assessment_metadata
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'job_id')
    )
    if not index_exists('marketplace_job_assessments', 'ix_marketplace_job_assessments_profile_job'):
        op.create_index('ix_marketplace_job_assessments_profile_job', 'marketplace_job_assessments', ['profile_id', 'job_id'])
    
    # Create marketplace_applications table
    if not table_exists('marketplace_applications'):
        op.create_table(
        'marketplace_applications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('application_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('platform_job_id', sa.String(), nullable=False),
        sa.Column('platform_application_id', sa.String(), nullable=True),
        sa.Column('status', application_status_enum, nullable=True),
        sa.Column('status_history', sa.JSON(), nullable=True),
        sa.Column('proposal_text', sa.Text(), nullable=True),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('bid_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: application_metadata
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id')
    )
    if not index_exists('marketplace_applications', 'ix_marketplace_applications_profile_job'):
        op.create_index('ix_marketplace_applications_profile_job', 'marketplace_applications', ['profile_id', 'job_id'])
    if not index_exists('marketplace_applications', 'ix_marketplace_applications_platform_application_id'):
        op.create_index('ix_marketplace_applications_platform_application_id', 'marketplace_applications', ['platform', 'platform_application_id'])
    
    # Create marketplace_active_work table
    if not table_exists('marketplace_active_work'):
        op.create_table(
        'marketplace_active_work',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('work_id', sa.String(), nullable=False),
        sa.Column('application_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('platform_work_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('milestones_completed', sa.Integer(), nullable=True),
        sa.Column('milestones_total', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Python attribute: work_metadata
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_id')
    )
    if not index_exists('marketplace_active_work', 'ix_marketplace_active_work_profile_application'):
        op.create_index('ix_marketplace_active_work_profile_application', 'marketplace_active_work', ['profile_id', 'application_id'])
    if not index_exists('marketplace_active_work', 'ix_marketplace_active_work_platform_work_id'):
        op.create_index('ix_marketplace_active_work_platform_work_id', 'marketplace_active_work', ['platform', 'platform_work_id'])
    
    # Create oauth_tokens table
    if not table_exists('oauth_tokens'):
        op.create_table(
        'oauth_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(), nullable=True),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('auth_status', auth_status_enum, nullable=True),
        sa.Column('is_connected', sa.Boolean(), nullable=True),
        sa.Column('platform_user_id', sa.String(), nullable=True),
        sa.Column('platform_username', sa.String(), nullable=True),
        sa.Column('additional_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('last_refreshed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'platform')
    )
    if not index_exists('oauth_tokens', 'ix_oauth_tokens_profile_platform'):
        op.create_index('ix_oauth_tokens_profile_platform', 'oauth_tokens', ['profile_id', 'platform'])
    if not index_exists('oauth_tokens', 'ix_oauth_tokens_expires_at'):
        op.create_index('ix_oauth_tokens_expires_at', 'oauth_tokens', ['expires_at'])
    
    # Create oauth_states table
    if not table_exists('oauth_states'):
        op.create_table(
        'oauth_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('state_id', sa.String(), nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('redirect_uri', sa.Text(), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('code_challenge', sa.Text(), nullable=True),
        sa.Column('code_challenge_method', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_consumed', sa.Boolean(), nullable=True),
        sa.Column('consumed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),  # Python attribute: state_metadata
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('state_id')
    )
    if not index_exists('oauth_states', 'ix_oauth_states_state_id'):
        op.create_index('ix_oauth_states_state_id', 'oauth_states', ['state_id'])
    if not index_exists('oauth_states', 'ix_oauth_states_profile_platform'):
        op.create_index('ix_oauth_states_profile_platform', 'oauth_states', ['profile_id', 'platform'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_oauth_states_profile_platform', table_name='oauth_states')
    op.drop_index('ix_oauth_states_state_id', table_name='oauth_states')
    op.drop_table('oauth_states')
    
    op.drop_index('ix_oauth_tokens_expires_at', table_name='oauth_tokens')
    op.drop_index('ix_oauth_tokens_profile_platform', table_name='oauth_tokens')
    op.drop_table('oauth_tokens')
    
    op.drop_index('ix_marketplace_active_work_platform_work_id', table_name='marketplace_active_work')
    op.drop_index('ix_marketplace_active_work_profile_application', table_name='marketplace_active_work')
    op.drop_table('marketplace_active_work')
    
    op.drop_index('ix_marketplace_applications_platform_application_id', table_name='marketplace_applications')
    op.drop_index('ix_marketplace_applications_profile_job', table_name='marketplace_applications')
    op.drop_table('marketplace_applications')
    
    op.drop_index('ix_marketplace_job_assessments_profile_job', table_name='marketplace_job_assessments')
    op.drop_table('marketplace_job_assessments')
    
    op.drop_index('ix_marketplace_jobs_job_id', table_name='marketplace_jobs')
    op.drop_index('ix_marketplace_jobs_profile_platform_job_id', table_name='marketplace_jobs')
    op.drop_table('marketplace_jobs')
    
    op.drop_index('ix_marketplace_account_state_profile_platform', table_name='marketplace_account_states')
    op.drop_table('marketplace_account_states')
    
    op.drop_index('ix_issues_profile_id', table_name='issues')
    op.drop_table('issues')
    
    op.drop_index('ix_development_priorities_profile_id', table_name='development_priorities')
    op.drop_table('development_priorities')
    
    op.drop_index('ix_platform_readiness_profile_id', table_name='platform_readiness')
    op.drop_table('platform_readiness')
    
    op.drop_index('ix_training_items_profile_id', table_name='training_items')
    op.drop_table('training_items')
    
    op.drop_index('ix_knowledge_progress_profile_id', table_name='knowledge_progress')
    op.drop_table('knowledge_progress')
    
    op.drop_index('ix_enigma_profiles_profile_id', table_name='enigma_profiles')
    op.drop_table('enigma_profiles')
    
    # Drop enums
    postgresql.ENUM(name='auth_status_enum').drop(op.get_bind())
    postgresql.ENUM(name='application_status_enum').drop(op.get_bind())
    postgresql.ENUM(name='freshness_status_enum').drop(op.get_bind())
    postgresql.ENUM(name='data_source_enum').drop(op.get_bind())
    postgresql.ENUM(name='account_status_enum').drop(op.get_bind())
