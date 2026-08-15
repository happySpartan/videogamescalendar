"""enlarge companies.start_date to BIGINT

IGDB stores companies.start_date as a full 64-bit Unix epoch, which can be
negative for pre-1970 foundations (e.g. Nintendo, founded 1889 ->
-2533161600). INT4 overflows for those rows, so widen to BIGINT.

Revision ID: 2e9c41fbb2a7
Revises: dd989d2b1a17
Create Date: 2026-08-14 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2e9c41fbb2a7"
down_revision: Union[str, None] = "dd989d2b1a17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "companies",
        "start_date",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "companies",
        "start_date",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
