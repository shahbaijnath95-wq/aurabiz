"""Add wholesale features

Revision ID: b892e140d706
Revises: a2b3c4d5e6f7
Create Date: 2026-07-09 18:51:56.438062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b892e140d706'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_wholesaler', sa.Boolean(), nullable=True, server_default=sa.text('0')))
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('wholesale_price', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema — reverse of upgrade only."""
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('wholesale_price')

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_column('is_wholesaler')
