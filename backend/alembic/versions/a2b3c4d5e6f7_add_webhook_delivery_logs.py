"""add webhook_delivery_logs table

Revision ID: a2b3c4d5e6f7
Revises: 19ceb3a9cbda
Create Date: 2026-06-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = '19ceb3a9cbda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('webhook_delivery_logs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('webhook_id', sa.String(), nullable=False),
    sa.Column('business_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=True),
    sa.Column('status_code', sa.Integer(), nullable=True),
    sa.Column('response_body', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('attempts', sa.Integer(), nullable=True),
    sa.Column('max_retries', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['webhook_id'], ['webhook_subscriptions.id'], ),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('webhook_delivery_logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_webhook_delivery_logs_webhook_id'), ['webhook_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_webhook_delivery_logs_business_id'), ['business_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('webhook_delivery_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_webhook_delivery_logs_business_id'))
        batch_op.drop_index(batch_op.f('ix_webhook_delivery_logs_webhook_id'))

    op.drop_table('webhook_delivery_logs')
