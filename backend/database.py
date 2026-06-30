from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://postgres:123456@localhost:5432/expense_tracker"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)