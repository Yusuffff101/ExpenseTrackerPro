"""Idempotent production migration for fresh and existing databases."""

import asyncio

from sqlalchemy import text

from database import engine
from models import Base


async def migrate() -> None:
    async with engine.begin() as connection:
        # Creates every table on a fresh database. Existing tables are left untouched.
        await connection.run_sync(Base.metadata.create_all)

        # Brings databases created by older project versions up to the current schema.
        await connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR(50)"))
        await connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_link_code VARCHAR(6)"))
        await connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_link_expires_at TIMESTAMP"))
        await connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_telegram_chat_id ON users (telegram_chat_id) WHERE telegram_chat_id IS NOT NULL"))
        await connection.execute(text("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS expense_date DATE"))
        await connection.execute(text("UPDATE expenses SET expense_date = CURRENT_DATE WHERE expense_date IS NULL"))
        await connection.execute(text("ALTER TABLE expenses ALTER COLUMN expense_date SET NOT NULL"))
        await connection.execute(text("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'web'"))
        await connection.execute(text("UPDATE expenses SET source = 'web' WHERE source IS NULL"))
        await connection.execute(text("ALTER TABLE expenses ALTER COLUMN source SET NOT NULL"))
        await connection.execute(text("CREATE INDEX IF NOT EXISTS ix_expenses_user_date ON expenses (user_id, expense_date)"))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
