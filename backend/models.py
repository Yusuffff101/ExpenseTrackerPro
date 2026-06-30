from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float


class Base(DeclarativeBase):
    pass


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
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