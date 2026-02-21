"""schema complet initial

Revision ID: 0001_schema_complet
Revises:
Create Date: 2025-02-21

Migration initiale complète : toutes les tables du projet LeBonCap.
Remplace les deux migrations précédentes (dupliquées / conflictuelles).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '0001_schema_complet'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name):
    """Vérifie si une table existe déjà (robustesse pour DB déjà initialisées)."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    # ── Table users ──────────────────────────────────────────────────
    if _table_exists('users'):
        return  # DB déjà initialisée (db.create_all avait été utilisé), on passe
    op.create_table(
        'users',
        sa.Column('id',                sa.Integer(),     nullable=False),
        sa.Column('nom',               sa.String(100),   nullable=False),
        sa.Column('email',             sa.String(150),   nullable=False),
        sa.Column('password_hash',     sa.String(256),   nullable=False),
        sa.Column('confirme',          sa.Boolean(),     nullable=True),
        sa.Column('actif',             sa.Boolean(),     nullable=True),
        sa.Column('created_at',        sa.DateTime(),    nullable=True),
        sa.Column('rgpd_consent',      sa.Boolean(),     nullable=True),
        sa.Column('rgpd_consent_date', sa.DateTime(),    nullable=True),
        sa.Column('parcoursup_2026',   sa.Boolean(),     nullable=True),
        sa.Column('role',              sa.String(20),    nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ── Table contact_requests ────────────────────────────────────────
    op.create_table(
        'contact_requests',
        sa.Column('id',           sa.Integer(),     nullable=False),
        sa.Column('nom',          sa.String(100),   nullable=False),
        sa.Column('email',        sa.String(150),   nullable=False),
        sa.Column('telephone',    sa.String(30),    nullable=True),
        sa.Column('rgpd_consent', sa.Boolean(),     nullable=False),
        sa.Column('is_read',      sa.Boolean(),     nullable=True),
        sa.Column('created_at',   sa.DateTime(),    nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── Table question_messages ────────────────────────────────────────
    op.create_table(
        'question_messages',
        sa.Column('id',         sa.Integer(),   nullable=False),
        sa.Column('nom',        sa.String(100), nullable=False),
        sa.Column('email',      sa.String(150), nullable=False),
        sa.Column('message',    sa.Text(),      nullable=False),
        sa.Column('is_read',    sa.Boolean(),   nullable=True),
        sa.Column('created_at', sa.DateTime(),  nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── Table parcoursup2026_messages ──────────────────────────────────
    op.create_table(
        'parcoursup2026_messages',
        sa.Column('id',         sa.Integer(),   nullable=False),
        sa.Column('nom',        sa.String(100), nullable=False),
        sa.Column('email',      sa.String(150), nullable=False),
        sa.Column('message',    sa.Text(),      nullable=False),
        sa.Column('is_read',    sa.Boolean(),   nullable=True),
        sa.Column('created_at', sa.DateTime(),  nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── Table events ───────────────────────────────────────────────────
    op.create_table(
        'events',
        sa.Column('id',           sa.Integer(),     nullable=False),
        sa.Column('titre',        sa.String(200),   nullable=False),
        sa.Column('thematique',   sa.String(200),   nullable=False),
        sa.Column('precisions',   sa.Text(),        nullable=True),
        sa.Column('date_event',   sa.DateTime(),    nullable=False),
        sa.Column('mode',         sa.String(20),    nullable=False),
        sa.Column('lieu',         sa.String(300),   nullable=True),
        sa.Column('places_max',   sa.Integer(),     nullable=False),
        sa.Column('is_published', sa.Boolean(),     nullable=True),
        sa.Column('created_at',   sa.DateTime(),    nullable=True),
        sa.Column('created_by',   sa.Integer(),     nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── Table registrations ────────────────────────────────────────────
    op.create_table(
        'registrations',
        sa.Column('id',           sa.Integer(),     nullable=False),
        sa.Column('user_id',      sa.Integer(),     nullable=False),
        sa.Column('event_id',     sa.Integer(),     nullable=False),
        sa.Column('nom_public',   sa.String(100),   nullable=True),
        sa.Column('email_public', sa.String(150),   nullable=True),
        sa.Column('status',       sa.String(20),    nullable=True),
        sa.Column('token',        sa.String(64),    nullable=False),
        sa.Column('confirmed_at', sa.DateTime(),    nullable=True),
        sa.Column('created_at',   sa.DateTime(),    nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.ForeignKeyConstraint(['user_id'],  ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
        sa.UniqueConstraint('user_id', 'event_id', name='uq_user_event'),
    )

    # ── Table event_registrations_public ──────────────────────────────
    op.create_table(
        'event_registrations_public',
        sa.Column('id',           sa.Integer(),     nullable=False),
        sa.Column('event_id',     sa.Integer(),     nullable=False),
        sa.Column('nom',          sa.String(100),   nullable=False),
        sa.Column('email',        sa.String(150),   nullable=False),
        sa.Column('telephone',    sa.String(30),    nullable=True),
        sa.Column('status',       sa.String(20),    nullable=True),
        sa.Column('token',        sa.String(64),    nullable=False),
        sa.Column('rgpd_consent', sa.Boolean(),     nullable=True),
        sa.Column('created_at',   sa.DateTime(),    nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )


def downgrade():
    op.drop_table('event_registrations_public')
    op.drop_table('registrations')
    op.drop_table('events')
    op.drop_table('parcoursup2026_messages')
    op.drop_table('question_messages')
    op.drop_table('contact_requests')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
