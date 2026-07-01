"""One-time migration for expense dates and user categories.

Run from the backend folder: python migrate_expense_features.py
"""

import asyncio

from sqlalchemy import text

from database import engine
from models import Base


async def migrate() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS expense_date DATE"))
        await connection.execute(text("UPDATE expenses SET expense_date = CURRENT_DATE WHERE expense_date IS NULL"))
        await connection.execute(text("ALTER TABLE expenses ALTER COLUMN expense_date SET NOT NULL"))
        await connection.execute(text("CREATE INDEX IF NOT EXISTS ix_expenses_user_date ON expenses (user_id, expense_date)"))
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
