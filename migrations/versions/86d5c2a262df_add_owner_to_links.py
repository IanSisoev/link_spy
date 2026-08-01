"""add owner to links

Revision ID: 86d5c2a262df
Revises: 2daf4eee9966
Create Date: 2026-08-01 03:41:35.762762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86d5c2a262df'
down_revision: Union[str, Sequence[str], None] = '2daf4eee9966'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("links", sa.Column("owner", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_links_owner_users", "links", "users", ["owner"], ["username"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_links_owner_users", "links", type_="foreignkey")
    op.drop_column("links", "owner")
