"""Updated JobDoctor model

Revision ID: 566e04cb86ca
Revises: 16d6f1d19fa1
Create Date: 2020-03-24 17:02:01.465730

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '566e04cb86ca'
down_revision = '16d6f1d19fa1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('jobdoctors', sa.Column('answered', sa.DateTime(), nullable=True))
    op.add_column('jobdoctors', sa.Column('candidate_id', sa.Integer(), nullable=True))
    op.add_column('jobdoctors', sa.Column('job_finish_id', sa.Integer(), nullable=True))
    op.add_column('jobdoctors', sa.Column('job_start_id', sa.Integer(), nullable=True))
    op.add_column('jobdoctors', sa.Column('job_started', sa.DateTime(), nullable=True))
    op.add_column('jobdoctors', sa.Column('job_time_estimate', sa.Integer(), nullable=True))
    op.add_column('jobdoctors', sa.Column('request_answer_id', sa.Integer(), nullable=True))
    op.add_column('jobdoctors', sa.Column('request_id', sa.Integer(), nullable=True))
    op.add_column('jobdoctors', sa.Column('request_started', sa.DateTime(), nullable=True))
    op.add_column('jobdoctors', sa.Column('request_time_estimate', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('jobdoctors', 'request_time_estimate')
    op.drop_column('jobdoctors', 'request_started')
    op.drop_column('jobdoctors', 'request_id')
    op.drop_column('jobdoctors', 'request_answer_id')
    op.drop_column('jobdoctors', 'job_time_estimate')
    op.drop_column('jobdoctors', 'job_started')
    op.drop_column('jobdoctors', 'job_start_id')
    op.drop_column('jobdoctors', 'job_finish_id')
    op.drop_column('jobdoctors', 'candidate_id')
    op.drop_column('jobdoctors', 'answered')
    # ### end Alembic commands ###
