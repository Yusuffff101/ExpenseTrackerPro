from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    RegisterRequest,
    LoginRequest,
    ExpenseCreate,
    ExpenseUpdate
)

from fastapi import Depends
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM

import bcrypt

from session import SessionLocal
from models import User, Expense
from fastapi import HTTPException
from sqlalchemy import select

from auth import create_access_token
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Expense Tracker API is running!"}


@app.post("/register")
async def register(data: RegisterRequest):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == data.email)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        hashed_password = bcrypt.hashpw(
            data.password.encode(),
            bcrypt.gensalt()
        ).decode()

        user = User(
            email=data.email,
            password=hashed_password
        )

        session.add(user)
        await session.commit()

        return {
            "message": "User registered successfully!"
        }

@app.post("/login")
async def login(data: LoginRequest):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == data.email)
        )

        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not bcrypt.checkpw(
            data.password.encode(),
            user.password.encode()
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        access_token = create_access_token(
            {"sub": user.email}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
async def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )

        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return user
    
@app.get("/me")
async def me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email
    }

# @app.post("/test-token")
# async def test_token(token: str):
#     return await get_current_user(token)

@app.post("/expenses")
async def create_expense(
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user)
):
    async with SessionLocal() as session:
        expense = Expense(
            user_id=current_user.id,
            description=data.description,
            amount=data.amount,
            category=data.category
        )

        session.add(expense)
        await session.commit()

        return {
            "message": "Expense created successfully!"
        }

@app.get("/expenses")
async def get_expenses(
    current_user: User = Depends(get_current_user)
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Expense).where(
                Expense.user_id == current_user.id
            )
        )

        expenses = result.scalars().all()

        return expenses
    
@app.put("/expenses/{expense_id}")
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_user)
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.user_id == current_user.id
            )
        )

        expense = result.scalar_one_or_none()

        if expense is None:
            raise HTTPException(
                status_code=404,
                detail="Expense not found"
            )

        expense.description = data.description
        expense.amount = data.amount
        expense.category = data.category

        await session.commit()

        return {
            "message": "Expense updated successfully!"
        }
    
@app.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user)
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.user_id == current_user.id
            )
        )

        expense = result.scalar_one_or_none()

        if expense is None:
            raise HTTPException(
                status_code=404,
                detail="Expense not found"
            )

        await session.delete(expense)
        await session.commit()

        return {
            "message": "Expense deleted successfully!"
        }