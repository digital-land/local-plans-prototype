"""empty message

Revision ID: 8b06da1ec5da
Revises: e21e477c9337
Create Date: 2019-03-26 12:10:19.879706

"""
import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Session = sessionmaker()
Base = declarative_base()

# revision identifiers, used by Alembic.
revision = '8b06da1ec5da'
down_revision = 'e21e477c9337'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('document', sa.Column('created_date', sa.DateTime(), nullable=True))

    class Document(Base):

        __tablename__ = 'document'

        id = sa.Column(UUID(as_uuid=True), primary_key=True)
        created_date = sa.Column(sa.DateTime())

    bind = op.get_bind()
    session = Session(bind=bind)

    for doc in session.query(Document):
        doc.created_date = datetime.datetime.utcnow()
        session.add(doc)
        session.commit()

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('document', 'created_date')
    # ### end Alembic commands ###