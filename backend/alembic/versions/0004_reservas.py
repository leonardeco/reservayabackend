"""reservas

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reserva",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("restaurante_id", sa.Integer(), nullable=False),
        sa.Column("mesa_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("personas", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=False),
        sa.Column("correo", sa.String(length=160), nullable=False),
        sa.Column("notas", sa.Text(), server_default="", nullable=False),
        sa.Column("estado", sa.String(length=12), server_default="confirmada", nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("personas BETWEEN 1 AND 20", name="ck_reserva_personas"),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'confirmada', 'cancelada')", name="ck_reserva_estado"
        ),
        sa.ForeignKeyConstraint(
            ["mesa_id"], ["mesa.id"], name="fk_reserva_mesa_id_mesa", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["restaurante_id"],
            ["restaurante.id"],
            name="fk_reserva_restaurante_id_restaurante",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reserva"),
        sa.UniqueConstraint("codigo", name="uq_reserva_codigo"),
    )
    op.create_index("ix_reserva_mesa_id", "reserva", ["mesa_id"])
    op.create_index("ix_reserva_restaurante_fecha", "reserva", ["restaurante_id", "fecha"])


def downgrade() -> None:
    op.drop_index("ix_reserva_restaurante_fecha", table_name="reserva")
    op.drop_index("ix_reserva_mesa_id", table_name="reserva")
    op.drop_table("reserva")
