"""add_document_to_mediatype_enum

Revision ID: 2a27d273b48c
Revises: fa1dbf5dd801
Create Date: 2025-10-07 13:11:34.055993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a27d273b48c'
down_revision: Union[str, Sequence[str], None] = 'fa1dbf5dd801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
