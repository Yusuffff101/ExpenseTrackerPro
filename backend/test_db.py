from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:123456@localhost:5432/expense_tracker"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("✅ Connected to PostgreSQL successfully!")
except Exception as e:
    print("❌ Connection failed:")
    print(e)