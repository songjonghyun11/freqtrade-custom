"""add trading_reflection table

Revision ID: 0001_add_trading_reflection
Revises: 
Create Date: 2025-05-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_trading_reflection'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'trading_reflection',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('data', sa.JSON, nullable=False),
    )

def downgrade():
    op.drop_table('trading_reflection')
