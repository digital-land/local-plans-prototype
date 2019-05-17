"""empty message

Revision ID: 4485e62818bd
Revises: b03f09fd93c3
Create Date: 2019-05-15 17:03:51.101139

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy.orm import Session

revision = '4485e62818bd'
down_revision = 'b03f09fd93c3'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute('ALTER TABLE local_plan ALTER COLUMN housing_numbers TYPE jsonb USING housing_numbers::text::jsonb;')


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute('ALTER TABLE local_plan ALTER COLUMN housing_numbers TYPE json USING housing_numbers::text::json;')
