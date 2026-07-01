import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from database import engine
from models import Expense

SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def add_expense():
    async with SessionLocal() as session:
        expense = Expense(
        user_id=2,
        amount=250,
        description="Lunch",
        category="Food"
    )

        session.add(expense)
        await session.commit()

        print("✅ Expense added!")


asyncio.run(add_expense())