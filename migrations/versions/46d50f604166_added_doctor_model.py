"""Added Doctor model

Revision ID: 46d50f604166
Revises: 8c10f4d3d7a8
Create Date: 2020-03-02 11:11:57.758021

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '46d50f604166'
down_revision = '8c10f4d3d7a8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('doctors',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('comment', sa.String(length=512), nullable=True),
    sa.Column('assigned_name', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.Integer(), nullable=True),
    sa.Column('region_id', sa.Integer(), nullable=True),
    sa.Column('country_id', sa.Integer(), nullable=True),
    sa.Column('first_client_message', sa.DateTime(), nullable=True),
    sa.Column('last_client_message', sa.DateTime(), nullable=True),
    sa.Column('extra_comment_1', sa.String(length=512), nullable=True),
    sa.Column('extra_comment_2', sa.String(length=512), nullable=True),
    sa.Column('extra_comment_3', sa.String(length=512), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('doctors')
    # ### end Alembic commands ###
