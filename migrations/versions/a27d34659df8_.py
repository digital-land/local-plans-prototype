"""empty message

Revision ID: a27d34659df8
Revises: 09265b125512
Create Date: 2019-07-25 10:20:44.998332

"""
from alembic import op
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = 'a27d34659df8'
down_revision = '09265b125512'
branch_labels = None
depends_on = None


local_auths = [("local-authority-eng:BPC","E06000058","Bournemouth, Christchurch and Poole","https://www.bcpcouncil.gov.uk"),
               ("local-authority-eng:DST","E06000059","Dorset Council","https://www.dorsetcouncil.gov.uk"),
               ("local-authority-eng:SWT","E07000246","Somerset West and Taunton","https://www.somersetwestandtaunton.gov.uk"),
               ("local-authority-eng:WSK","E07000245","West Suffolk","https://www.westsuffolk.gov.uk"),
               ("local-authority-eng:ESK","E07000244","East Suffolk","https://www.eastsuffolk.gov.uk")]


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    for l in local_auths:
        insert = f'INSERT INTO planning_authority (id, ons_code, name, website)  VALUES {l[0],l[1],l[2],l[3]}'
        op.execute(insert)
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    ids = tuple([local_auth[0] for local_auth in local_auths])
    op.execute(f'DELETE FROM planning_authority WHERE id in {ids}')
    session.commit()
