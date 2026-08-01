"""add index on links owner

Revision ID: 0f371373f19e
Revises: 86d5c2a262df
Create Date: 2026-08-01 05:07:11.152897

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0f371373f19e'
down_revision: Union[str, Sequence[str], None] = '86d5c2a262df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_links_owner", "links", ["owner"])


def downgrade() -> None:
    op.drop_index("ix_links_owner", table_name="links")
