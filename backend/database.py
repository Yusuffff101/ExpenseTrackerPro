import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

raw_database_url = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:123456@localhost:5432/expense_tracker"
)


def async_database_url(value: str) -> str:
    """Normalize provider connection strings for SQLAlchemy's asyncpg driver."""
    if value.startswith("postgres://"):
        value = value.replace("postgres://", "postgresql://", 1)
    if value.startswith("postgresql://"):
        value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
    parts = urlsplit(value)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.pop("channel_binding", None)  # libpq-only option from Neon connection strings
    if "sslmode" in query:
        query["ssl"] = query.pop("sslmode")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


DATABASE_URL = async_database_url(raw_database_url)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
)
