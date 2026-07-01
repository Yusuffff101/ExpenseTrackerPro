from datetime import date

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ExpenseCreate(BaseModel):
    description: str
    amount: float = Field(gt=0)
    category: str
    expense_date: date = Field(default_factory=date.today)

class ExpenseUpdate(BaseModel):
    description: str
    amount: float = Field(gt=0)
    category: str
    expense_date: date


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#7559e8", pattern=r"^#[0-9a-fA-F]{6}$")


class BudgetUpsert(BaseModel):
    category: str | None = None
    limit_amount: float = Field(gt=0)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020, le=2100)


class RecurringCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=100)
    frequency: str = Field(pattern="^(weekly|monthly)$")
    next_run_date: date


class RecurringUpdate(RecurringCreate):
    active: bool = True
