"""empty message

Revision ID: 68fd598458dc
Revises: 
Create Date: 2019-06-04 16:26:12.565112

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '68fd598458dc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('local_plan',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('local_plan', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('plan_start_year', sa.Date(), nullable=True),
    sa.Column('plan_end_year', sa.Date(), nullable=True),
    sa.Column('housing_numbers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('plan_period_found', sa.Boolean(), nullable=True),
    sa.Column('housing_numbers_found', sa.Boolean(), nullable=True),
    sa.Column('published_date', sa.Date(), nullable=True),
    sa.Column('submitted_date', sa.Date(), nullable=True),
    sa.Column('sound_date', sa.Date(), nullable=True),
    sa.Column('adopted_date', sa.Date(), nullable=True),
    sa.Column('created_date', sa.DateTime(), nullable=True),
    sa.Column('updated_date', sa.DateTime(), nullable=True),
    sa.Column('deleted', sa.Boolean(), nullable=True),
    sa.Column('last_updated_by', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('planning_authority',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('ons_code', sa.String(length=9), nullable=True),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('website', sa.String(), nullable=True),
    sa.Column('local_scheme_url', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('planning_authority_plan',
    sa.Column('planning_authority_id', sa.String(length=64), nullable=False),
    sa.Column('local_plan_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['local_plan_id'], ['local_plan.id'], name='planning_authority_plan_local_plan_id_fkey'),
    sa.ForeignKeyConstraint(['planning_authority_id'], ['planning_authority.id'], name='planning_authority_plan_planning_authority_id_fkey'),
    sa.PrimaryKeyConstraint('planning_authority_id', 'local_plan_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('planning_authority_plan')
    op.drop_table('planning_authority')
    op.drop_table('local_plan')
    # ### end Alembic commands ###
