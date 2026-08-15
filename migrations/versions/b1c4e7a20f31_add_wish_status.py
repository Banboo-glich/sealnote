"""気になるリスト用に status / wished_at を追加し、logged_date を NULL 可にする

要件21-3。既存データはすべて記録済みなので status に "done" を一括で入れる
（server_default により、追加した時点で既存行が "done" になる）。

Revision ID: b1c4e7a20f31
Revises: 9dadcfe381e2
Create Date: 2026-08-15
"""
import sqlalchemy as sa
from alembic import op

revision = "b1c4e7a20f31"
down_revision = "9dadcfe381e2"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite は ALTER COLUMN を直接扱えないため batch（テーブル作り直し）で行う。
    with op.batch_alter_table("contents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=10),
                nullable=False,
                server_default="done",
            )
        )
        batch_op.add_column(sa.Column("wished_at", sa.DateTime(), nullable=True))
        # 気になる項目は記録日を持たないため NULL 可にする
        batch_op.alter_column(
            "logged_date", existing_type=sa.Date(), nullable=True
        )
        batch_op.create_index(
            batch_op.f("ix_contents_status"), ["status"], unique=False
        )


def downgrade():
    # 戻す前に、まだ見ていない行を消す（logged_date を NOT NULL に戻せないため）
    op.execute("DELETE FROM contents WHERE status = 'wish'")

    with op.batch_alter_table("contents", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_contents_status"))
        batch_op.alter_column(
            "logged_date", existing_type=sa.Date(), nullable=False
        )
        batch_op.drop_column("wished_at")
        batch_op.drop_column("status")
