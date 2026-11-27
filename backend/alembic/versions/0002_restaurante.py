"""tabla restaurante

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "restaurante",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("ubicacion", sa.String(length=160), nullable=False),
        sa.Column("imagen_url", sa.String(length=500), nullable=False),
        sa.Column("imagen_comida_url", sa.String(length=500), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("precio_nivel", sa.SmallInteger(), nullable=False),
        sa.Column("categoria", sa.String(length=40), nullable=False),
        sa.Column("horario_resumen", sa.String(length=160), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=False),
        sa.Column("pagina", sa.String(length=160), nullable=False),
        sa.Column("popular", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "zona_horaria",
            sa.String(length=40),
            server_default="America/Bogota",
            nullable=False,
        ),
        sa.Column("duracion_franja_min", sa.Integer(), server_default="90", nullable=False),
        sa.Column("antelacion_max_dias", sa.Integer(), server_default="60", nullable=False),
        sa.Column("texto_busqueda", sa.Text(), server_default="", nullable=False),
        sa.Column("ubicacion_busqueda", sa.String(length=160), server_default="", nullable=False),
        sa.CheckConstraint("precio_nivel BETWEEN 1 AND 3", name="ck_restaurante_precio_nivel"),
        sa.CheckConstraint("rating >= 0 AND rating <= 5", name="ck_restaurante_rating"),
        sa.PrimaryKeyConstraint("id", name="pk_restaurante"),
        sa.UniqueConstraint("slug", name="uq_restaurante_slug"),
    )
    op.create_index("ix_restaurante_categoria", "restaurante", ["categoria"])


def downgrade() -> None:
    op.drop_index("ix_restaurante_categoria", table_name="restaurante")
    op.drop_table("restaurante")
