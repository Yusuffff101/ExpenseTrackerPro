import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from database import engine
from models import Expense

SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_expenses():
    async with SessionLocal() as session:
        result = await session.execute(
            select(Expense)
        )

        expenses = result.scalars().all()

        for expense in expenses:
            print(
                f"ID: {expense.id}, "
                f"Description: {expense.description}, "
                f"Amount: {expense.amount}, "
                f"Category: {expense.category}"
            )


asyncio.run(get_expenses())