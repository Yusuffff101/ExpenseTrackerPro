import asyncio
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from database import engine
from models import User

SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_user():
    async with SessionLocal() as session:
        password = "password123"

        hashed_password = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        user = User(
            email="yusuf@example.com",
            password=hashed_password
        )

        session.add(user)
        await session.commit()

        print("✅ User created!")


asyncio.run(create_user())