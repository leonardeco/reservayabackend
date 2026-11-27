"""mesas, turnos y bloqueos

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mesa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurante_id", sa.Integer(), nullable=False),
        sa.Column("etiqueta", sa.String(length=30), nullable=False),
        sa.Column("capacidad_min", sa.Integer(), nullable=False),
        sa.Column("capacidad_max", sa.Integer(), nullable=False),
        sa.Column("activa", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint(
            "capacidad_min >= 1 AND capacidad_min <= capacidad_max AND capacidad_max <= 20",
            name="ck_mesa_capacidad",
        ),
        sa.ForeignKeyConstraint(
            ["restaurante_id"],
            ["restaurante.id"],
            name="fk_mesa_restaurante_id_restaurante",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_mesa"),
        sa.UniqueConstraint("restaurante_id", "etiqueta", name="uq_mesa_restaurante_etiqueta"),
    )
    op.create_index("ix_mesa_restaurante_id", "mesa", ["restaurante_id"])

    op.create_table(
        "horario_turno",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurante_id", sa.Integer(), nullable=False),
        sa.Column("dia_semana", sa.SmallInteger(), nullable=False),
        sa.Column("apertura", sa.Time(), nullable=False),
        sa.Column("ultima_franja", sa.Time(), nullable=False),
        sa.CheckConstraint("dia_semana BETWEEN 0 AND 6", name="ck_horario_turno_dia_semana"),
        sa.CheckConstraint("apertura <= ultima_franja", name="ck_horario_turno_rango"),
        sa.ForeignKeyConstraint(
            ["restaurante_id"],
            ["restaurante.id"],
            name="fk_horario_turno_restaurante_id_restaurante",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_horario_turno"),
    )
    op.create_index("ix_horario_turno_restaurante_id", "horario_turno", ["restaurante_id"])

    op.create_table(
        "bloqueo_fecha",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurante_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora_desde", sa.Time(), nullable=True),
        sa.Column("hora_hasta", sa.Time(), nullable=True),
        sa.Column("motivo", sa.String(length=120), nullable=False),
        sa.CheckConstraint(
            "(hora_desde IS NULL AND hora_hasta IS NULL) "
            "OR (hora_desde IS NOT NULL AND hora_hasta IS NOT NULL AND hora_desde < hora_hasta)",
            name="ck_bloqueo_fecha_rango",
        ),
        sa.ForeignKeyConstraint(
            ["restaurante_id"],
            ["restaurante.id"],
            name="fk_bloqueo_fecha_restaurante_id_restaurante",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bloqueo_fecha"),
    )
    op.create_index(
        "ix_bloqueo_fecha_restaurante_fecha", "bloqueo_fecha", ["restaurante_id", "fecha"]
    )


def downgrade() -> None:
    op.drop_index("ix_bloqueo_fecha_restaurante_fecha", table_name="bloqueo_fecha")
    op.drop_table("bloqueo_fecha")
    op.drop_index("ix_horario_turno_restaurante_id", table_name="horario_turno")
    op.drop_table("horario_turno")
    op.drop_index("ix_mesa_restaurante_id", table_name="mesa")
    op.drop_table("mesa")
