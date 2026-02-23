"""Creacion inicial

Revision ID: d646c3e28b84
Revises:
Create Date: 2026-02-20 17:04:04.404542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d646c3e28b84"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "category",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_category_id"), "category", ["id"], unique=False)
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=True),
        sa.Column("verification_token", sa.String(), nullable=True),
        sa.Column("verification_token_expires", sa.DateTime(), nullable=True),
        sa.Column("recovery_token", sa.String(), nullable=True),
        sa.Column("recovery_token_expires", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("full_name"),
        sa.UniqueConstraint("password_hash"),
        sa.UniqueConstraint("recovery_token"),
        sa.UniqueConstraint("verification_token"),
    )
    op.create_index(op.f("ix_user_id"), "user", ["id"], unique=False)
    op.create_table(
        "access_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_log_id"), "access_log", ["id"], unique=False)
    op.create_table(
        "budget",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("amount_limit", sa.Double(), nullable=True),
        sa.Column("month", sa.String(), nullable=True),
        sa.Column("year", sa.String(), nullable=True),
        sa.Column("alert_treshold", sa.Double(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_budget_id"), "budget", ["id"], unique=False)
    op.create_table(
        "expense",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Double(), nullable=True),
        sa.Column("expense_date", sa.DateTime(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expense_id"), "expense", ["id"], unique=False)
    op.create_table(
        "alert",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("alert_type", sa.String(), nullable=True),
        sa.Column("percentage_reached", sa.Double(), nullable=True),
        sa.Column("amount_spent", sa.Double(), nullable=True),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("budget_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["budget_id"], ["budget.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("budget_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_alert_id"), "alert", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_alert_id"), table_name="alert")
    op.drop_table("alert")
    op.drop_index(op.f("ix_expense_id"), table_name="expense")
    op.drop_table("expense")
    op.drop_index(op.f("ix_budget_id"), table_name="budget")
    op.drop_table("budget")
    op.drop_index(op.f("ix_access_log_id"), table_name="access_log")
    op.drop_table("access_log")
    op.drop_index(op.f("ix_user_id"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_category_id"), table_name="category")
    op.drop_table("category")
