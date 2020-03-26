"""updated2 IncartJob model

Revision ID: 30e9f58587e8
Revises: 0d66fc6d5ad1
Create Date: 2020-03-27 09:44:05.350138

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30e9f58587e8'
down_revision = '0d66fc6d5ad1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('incartjobs', sa.Column('concl_parts', sa.String(length=128), nullable=True))
    op.add_column('incartjobs', sa.Column('link_analyze', sa.String(length=128), nullable=True))
    op.drop_column('incartjobs', 'perm_link')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('incartjobs', sa.Column('perm_link', sa.VARCHAR(length=128), nullable=True))
    op.drop_column('incartjobs', 'link_analyze')
    op.drop_column('incartjobs', 'concl_parts')
    # ### end Alembic commands ###
