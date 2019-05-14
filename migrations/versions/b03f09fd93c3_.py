"""empty message

Revision ID: b03f09fd93c3
Revises: 76a6f18abd2b
Create Date: 2019-05-13 13:32:41.355539

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b03f09fd93c3'
down_revision = '76a6f18abd2b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('local_plan', sa.Column('last_updated_by', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('local_plan', 'last_updated_by')
    # ### end Alembic commands ###
