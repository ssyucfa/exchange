"""game_models migration

Revision ID: d50d5f588587
Revises: 
Create Date: 2022-02-25 20:51:19.752271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd50d5f588587'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('development',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.Column('diff', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.Date(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('users_finished_round', sa.String(), nullable=False),
    sa.Column('state', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('securities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('start_cost', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('vk_id', sa.Integer(), nullable=False),
    sa.Column('fio', sa.String(), nullable=False),
    sa.Column('create_at', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('vk_id')
    )
    op.create_table('brokerage_account',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('money', sa.Integer(), nullable=False),
    sa.Column('securities', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('securities_for_game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('cost', sa.String(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('securities_for_game')
    op.drop_table('game_users')
    op.drop_table('brokerage_account')
    op.drop_table('user')
    op.drop_table('securities')
    op.drop_table('game')
    op.drop_table('development')
    op.drop_table('admins')
    # ### end Alembic commands ###