"""Doctor model add field is_active

Revision ID: e32c709591a4
Revises: 30e9f58587e8
Create Date: 2020-03-27 11:41:19.748482

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e32c709591a4'
down_revision = '30e9f58587e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('doctors', sa.Column('is_active', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('doctors', 'is_active')
    # ### end Alembic commands ###
