"""empty message

Revision ID: 21cbff069e42
Revises: 5b9c80bae971
Create Date: 2019-03-13 11:52:55.727140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21cbff069e42'
down_revision = '5b9c80bae971'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('emerging_fact', sa.Column('image_url', sa.String(), nullable=True))
    op.add_column('fact', sa.Column('image_url', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('fact', 'image_url')
    op.drop_column('emerging_fact', 'image_url')
    # ### end Alembic commands ###