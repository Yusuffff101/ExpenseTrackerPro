import secrets
import os
from datetime import date, datetime, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    RegisterRequest,
    LoginRequest,
    ExpenseCreate,
    ExpenseUpdate,
    CategoryCreate,
    BudgetUpsert,
    RecurringCreate,
    RecurringUpdate,
)

from fastapi import Depends
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM

import bcrypt

from session import SessionLocal
from models import Budget, Category, Expense, RecurringTransaction, User
from fastapi import HTTPException
from sqlalchemy import asc, desc, extract, func, or_, select, text

from auth import create_access_token
from fastapi.security import OAuth2PasswordBearer
from recurring_service import process_recurring
from telegram_service import handle_update

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

app = FastAPI()

DEFAULT_CATEGORIES = [
    ("Food", "#8b5cf6"),
    ("Transport", "#14b8a6"),
    ("Shopping", "#f59e0b"),
    ("Bills", "#f43f5e"),
    ("Health", "#3b82f6"),
    ("Entertainment", "#d946ef"),
    ("Other", "#64748b"),
]

origins = [origin.strip().rstrip("/") for origin in os.getenv(
    "FRONTEND_URLS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Expense Tracker API is running!"}


@app.get("/health")
async def health():
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "healthy"}


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
        await session.flush()
        session.add_all([
            Category(user_id=user.id, name=name, color=color)
            for name, color in DEFAULT_CATEGORIES
        ])
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
            category=data.category.strip(),
            expense_date=data.expense_date,
            source="web",
        )

        session.add(expense)
        await session.commit()

        return {
            "message": "Expense created successfully!"
        }

@app.get("/expenses")
async def get_expenses(
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="expense_date", pattern="^(expense_date|amount|description|category)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user)
):
    async with SessionLocal() as session:
        await process_recurring(session, current_user.id)
        filters = [Expense.user_id == current_user.id]
        if category:
            filters.append(Expense.category == category)
        if start_date:
            filters.append(Expense.expense_date >= start_date)
        if end_date:
            filters.append(Expense.expense_date <= end_date)
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(Expense.description.ilike(term), Expense.category.ilike(term)))

        total = await session.scalar(select(func.count(Expense.id)).where(*filters))
        total_amount = await session.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(*filters))
        category_result = await session.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(*filters)
            .group_by(Expense.category)
            .order_by(desc(func.sum(Expense.amount)))
        )
        sort_column = getattr(Expense, sort_by)
        sort_direction = asc if order == "asc" else desc
        result = await session.execute(
            select(Expense)
            .where(*filters)
            .order_by(sort_direction(sort_column), desc(Expense.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return {
            "items": result.scalars().all(),
            "total": total or 0,
            "page": page,
            "page_size": page_size,
            "pages": max(1, ((total or 0) + page_size - 1) // page_size),
            "total_amount": total_amount or 0,
            "category_totals": {name: amount for name, amount in category_result.all()},
        }
    
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
        expense.expense_date = data.expense_date

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


@app.get("/categories")
async def get_categories(current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Category)
            .where(Category.user_id == current_user.id)
            .order_by(Category.name)
        )
        categories = result.scalars().all()
        if not categories:
            categories = [
                Category(user_id=current_user.id, name=name, color=color)
                for name, color in DEFAULT_CATEGORIES
            ]
            session.add_all(categories)
            await session.commit()
        return categories


@app.post("/categories", status_code=201)
async def create_category(data: CategoryCreate, current_user: User = Depends(get_current_user)):
    name = data.name.strip()
    async with SessionLocal() as session:
        existing = await session.scalar(
            select(Category).where(
                Category.user_id == current_user.id,
                func.lower(Category.name) == name.lower(),
            )
        )
        if existing:
            raise HTTPException(status_code=409, detail="Category already exists")
        category = Category(user_id=current_user.id, name=name, color=data.color)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


@app.delete("/categories/{category_id}")
async def delete_category(category_id: int, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        category = await session.scalar(
            select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        usage_count = await session.scalar(
            select(func.count(Expense.id)).where(
                Expense.user_id == current_user.id,
                Expense.category == category.name,
            )
        )
        if usage_count:
            raise HTTPException(status_code=409, detail="Category is used by existing expenses")
        await session.delete(category)
        await session.commit()
        return {"message": "Category deleted successfully!"}


@app.get("/analytics")
async def get_analytics(
    months: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    start_month = today.month - months + 1
    start_year = today.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = date(start_year, start_month, 1)
    async with SessionLocal() as session:
        trend_rows = (await session.execute(
            select(
                extract("year", Expense.expense_date).label("year"),
                extract("month", Expense.expense_date).label("month"),
                func.sum(Expense.amount).label("total"),
            )
            .where(Expense.user_id == current_user.id, Expense.expense_date >= start_date)
            .group_by("year", "month")
            .order_by("year", "month")
        )).all()
        category_rows = (await session.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == current_user.id, Expense.expense_date >= start_date)
            .group_by(Expense.category)
            .order_by(desc(func.sum(Expense.amount)))
        )).all()
        daily_rows = (await session.execute(
            select(Expense.expense_date, func.sum(Expense.amount))
            .where(Expense.user_id == current_user.id, Expense.expense_date >= today.replace(day=1))
            .group_by(Expense.expense_date)
            .order_by(Expense.expense_date)
        )).all()
        month_lookup = {(int(year), int(month)): float(total) for year, month, total in trend_rows}
        trend = []
        year, month = start_year, start_month
        for _ in range(months):
            trend.append({"year": year, "month": month, "label": date(year, month, 1).strftime("%b %Y"), "total": month_lookup.get((year, month), 0)})
            month += 1
            if month == 13:
                month, year = 1, year + 1
        current_total = month_lookup.get((today.year, today.month), 0)
        previous_month = 12 if today.month == 1 else today.month - 1
        previous_year = today.year - 1 if today.month == 1 else today.year
        previous_total = month_lookup.get((previous_year, previous_month), 0)
        change = ((current_total - previous_total) / previous_total * 100) if previous_total else None
        return {
            "trend": trend,
            "categories": [{"category": name, "total": float(total)} for name, total in category_rows],
            "daily": [{"date": row_date, "total": float(total)} for row_date, total in daily_rows],
            "current_month": current_total,
            "previous_month": previous_total,
            "month_change_percent": change,
        }


@app.post("/budgets")
async def set_budget(data: BudgetUpsert, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        conditions = [Budget.user_id == current_user.id, Budget.month == data.month, Budget.year == data.year]
        conditions.append(Budget.category.is_(None) if data.category is None else Budget.category == data.category)
        budget = await session.scalar(select(Budget).where(*conditions))
        if budget:
            budget.limit_amount = data.limit_amount
        else:
            budget = Budget(user_id=current_user.id, **data.model_dump())
            session.add(budget)
        await session.commit()
        await session.refresh(budget)
        return budget


@app.get("/budgets/status")
async def budget_status(
    month: int = Query(default_factory=lambda: date.today().month, ge=1, le=12),
    year: int = Query(default_factory=lambda: date.today().year, ge=2020, le=2100),
    current_user: User = Depends(get_current_user),
):
    async with SessionLocal() as session:
        budgets = (await session.execute(select(Budget).where(Budget.user_id == current_user.id, Budget.month == month, Budget.year == year).order_by(Budget.category))).scalars().all()
        spending = dict((await session.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == current_user.id, extract("month", Expense.expense_date) == month, extract("year", Expense.expense_date) == year)
            .group_by(Expense.category)
        )).all())
        total_spent = sum(float(value) for value in spending.values())
        return [{
            "id": item.id,
            "category": item.category,
            "limit_amount": item.limit_amount,
            "spent": total_spent if item.category is None else float(spending.get(item.category, 0)),
            "remaining": item.limit_amount - (total_spent if item.category is None else float(spending.get(item.category, 0))),
            "percentage": round((total_spent if item.category is None else float(spending.get(item.category, 0))) / item.limit_amount * 100, 1),
            "month": month,
            "year": year,
        } for item in budgets]


@app.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: int, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        budget = await session.scalar(select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id))
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        await session.delete(budget)
        await session.commit()
        return {"message": "Budget deleted"}


@app.get("/recurring")
async def list_recurring(current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        await process_recurring(session, current_user.id)
        result = await session.execute(select(RecurringTransaction).where(RecurringTransaction.user_id == current_user.id).order_by(RecurringTransaction.next_run_date))
        return result.scalars().all()


@app.post("/recurring", status_code=201)
async def create_recurring(data: RecurringCreate, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        item = RecurringTransaction(user_id=current_user.id, active=True, **data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        await process_recurring(session, current_user.id)
        return item


@app.put("/recurring/{recurring_id}")
async def update_recurring(recurring_id: int, data: RecurringUpdate, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        item = await session.scalar(select(RecurringTransaction).where(RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == current_user.id))
        if not item:
            raise HTTPException(status_code=404, detail="Recurring transaction not found")
        for field, value in data.model_dump().items():
            setattr(item, field, value)
        await session.commit()
        return item


@app.delete("/recurring/{recurring_id}")
async def delete_recurring(recurring_id: int, current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        item = await session.scalar(select(RecurringTransaction).where(RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == current_user.id))
        if not item:
            raise HTTPException(status_code=404, detail="Recurring transaction not found")
        await session.delete(item)
        await session.commit()
        return {"message": "Recurring transaction deleted"}


@app.post("/recurring/process")
async def run_recurring(current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        return {"generated": await process_recurring(session, current_user.id)}


@app.get("/telegram/status")
async def telegram_status(current_user: User = Depends(get_current_user)):
    return {"linked": bool(current_user.telegram_chat_id), "chat_id": current_user.telegram_chat_id}


@app.post("/telegram/generate-link-code")
async def generate_telegram_code(current_user: User = Depends(get_current_user)):
    code = f"{secrets.randbelow(1_000_000):06d}"
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.id == current_user.id))
        user.telegram_link_code = code
        user.telegram_link_expires_at = datetime.utcnow().replace(microsecond=0) + timedelta(minutes=10)
        await session.commit()
    return {"code": code, "expires_in_minutes": 10}


@app.delete("/telegram/unlink")
async def unlink_telegram(current_user: User = Depends(get_current_user)):
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.id == current_user.id))
        user.telegram_chat_id = None
        user.telegram_link_code = None
        user.telegram_link_expires_at = None
        await session.commit()
    return {"message": "Telegram account unlinked"}


@app.post("/telegram/webhook", include_in_schema=False)
async def telegram_webhook(payload: dict):
    try:
        await handle_update(payload)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"ok": True}
