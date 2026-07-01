from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    telegram_link_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    telegram_link_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id")
    )
    
    description: Mapped[str] = mapped_column(
        String(255)
    )

    amount: Mapped[float] = mapped_column(
        Float
    )

    category: Mapped[str] = mapped_column(
        String(100)
    )

    expense_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        index=True
    )

    source: Mapped[str] = mapped_column(String(20), default="web")

    __table_args__ = (
        Index("ix_expenses_user_date", "user_id", "expense_date"),
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(20), default="#7559e8")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    limit_amount: Mapped[float] = mapped_column(Float)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("user_id", "category", "month", "year", name="uq_budget_period_category"),
        Index("ix_budgets_user_period", "user_id", "year", "month"),
    )


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(100))
    frequency: Mapped[str] = mapped_column(String(20))
    next_run_date: Mapped[date] = mapped_column(Date, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_generated_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    
