"""empty message

Revision ID: f1053a0fc6f2
Revises: 1b8a20c84d1e
Create Date: 2020-03-30 22:55:43.464460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1053a0fc6f2'
down_revision = '1b8a20c84d1e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('shows', 'artist_image_link')
    op.drop_column('shows', 'venue_name')
    op.drop_column('shows', 'artist_name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('shows', sa.Column('artist_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('shows', sa.Column('venue_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('shows', sa.Column('artist_image_link', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
