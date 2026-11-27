"""administradores del panel

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "administrador",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario", sa.String(length=60), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column("restaurante_id", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(
            ["restaurante_id"],
            ["restaurante.id"],
            name="fk_administrador_restaurante_id_restaurante",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_administrador"),
        sa.UniqueConstraint("restaurante_id", name="uq_administrador_restaurante_id"),
        sa.UniqueConstraint("usuario", name="uq_administrador_usuario"),
    )


def downgrade() -> None:
    op.drop_table("administrador")
