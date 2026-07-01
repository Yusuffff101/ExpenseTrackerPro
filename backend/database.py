import os
from sqlalchemy.ext.asyncio import create_async_engine

# Read from the environment variable first. If it doesn't exist, use the local string.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:123456@localhost:5432/expense_tracker"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)