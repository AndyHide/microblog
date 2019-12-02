"""is breakfast lunch and/or dinner

Revision ID: 12cd831c1424
Revises: 579141f01d7c
Create Date: 2019-08-11 18:05:02.702389

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12cd831c1424'
down_revision = '579141f01d7c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recipe', sa.Column('isBreakfast', sa.Boolean(), nullable=True))
    op.add_column('recipe', sa.Column('isDinner', sa.Boolean(), nullable=True))
    op.add_column('recipe', sa.Column('isLunch', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_recipe_isBreakfast'), 'recipe', ['isBreakfast'], unique=False)
    op.create_index(op.f('ix_recipe_isDinner'), 'recipe', ['isDinner'], unique=False)
    op.create_index(op.f('ix_recipe_isLunch'), 'recipe', ['isLunch'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_recipe_isLunch'), table_name='recipe')
    op.drop_index(op.f('ix_recipe_isDinner'), table_name='recipe')
    op.drop_index(op.f('ix_recipe_isBreakfast'), table_name='recipe')
    op.drop_column('recipe', 'isLunch')
    op.drop_column('recipe', 'isDinner')
    op.drop_column('recipe', 'isBreakfast')
    # ### end Alembic commands ###