import os
import re
from datetime import date, datetime, timedelta

from sqlalchemy import desc, extract, func, select
from telegram import Bot, Update

from models import Budget, Expense, User
from session import SessionLocal


AMOUNT_PATTERN = re.compile(r"(?:spent|paid)?\s*(?:₹|rs\.?\s*)?(\d+(?:\.\d{1,2})?)\s+(?:on\s+)?(.+)", re.I)


def parse_expense_message(text: str) -> dict | None:
    clean = text.strip()
    match = AMOUNT_PATTERN.fullmatch(clean)
    if not match:
        return None
    amount = float(match.group(1))
    description = match.group(2).strip()
    expense_date = date.today()
    if description.lower().endswith(" yesterday"):
        description = description[:-10].strip()
        expense_date -= timedelta(days=1)
    elif description.lower().endswith(" today"):
        description = description[:-6].strip()
    keywords = {
        "Food": ("food", "lunch", "dinner", "breakfast", "grocery", "groceries", "coffee", "restaurant"),
        "Transport": ("uber", "ola", "taxi", "fuel", "petrol", "bus", "train"),
        "Shopping": ("shopping", "amazon", "clothes"),
        "Bills": ("bill", "rent", "electricity", "internet"),
        "Health": ("doctor", "medicine", "hospital", "gym"),
        "Entertainment": ("movie", "netflix", "game", "concert"),
    }
    lowered = description.lower()
    category = next((name for name, words in keywords.items() if any(word in lowered for word in words)), "Other")
    return {"amount": amount, "description": description.capitalize(), "category": category, "expense_date": expense_date}


async def send(chat_id: str, text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    async with Bot(token) as bot:
        await bot.send_message(chat_id=chat_id, text=text)


async def handle_update(payload: dict) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    bot = Bot(token)
    update = Update.de_json(payload, bot)
    if not update.message or not update.message.text:
        return
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()
    async with SessionLocal() as session:
        if text.startswith("/start"):
            await send(chat_id, "Welcome to ExpenseTracker Pro! Link your account with /link 123456, then send messages like: spent 250 on groceries yesterday")
            return
        if text.startswith("/link "):
            code = text.split(maxsplit=1)[1].strip()
            user = await session.scalar(select(User).where(User.telegram_link_code == code))
            if not user or not user.telegram_link_expires_at or user.telegram_link_expires_at < datetime.utcnow():
                await send(chat_id, "That link code is invalid or expired. Generate a new one in the web app.")
                return
            previously_linked = await session.scalar(
                select(User).where(User.telegram_chat_id == chat_id, User.id != user.id)
            )
            if previously_linked:
                previously_linked.telegram_chat_id = None
            user.telegram_chat_id = chat_id
            user.telegram_link_code = None
            user.telegram_link_expires_at = None
            await session.commit()
            await send(chat_id, "Account linked successfully. You can now log expenses here!")
            return
        user = await session.scalar(select(User).where(User.telegram_chat_id == chat_id))
        if not user:
            await send(chat_id, "Your Telegram is not linked. Generate a code in the web app, then use /link CODE.")
            return
        if text == "/list":
            rows = (await session.execute(select(Expense).where(Expense.user_id == user.id).order_by(desc(Expense.expense_date), desc(Expense.id)).limit(10))).scalars().all()
            message = "Recent expenses:\n" + "\n".join(f"• ₹{row.amount:g} · {row.description} · {row.expense_date:%d %b}" for row in rows) if rows else "No expenses yet."
            await send(chat_id, message)
            return
        if text == "/summary":
            now = date.today()
            total = await session.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.user_id == user.id, extract("month", Expense.expense_date) == now.month, extract("year", Expense.expense_date) == now.year))
            await send(chat_id, f"This month's spending: ₹{float(total):,.0f}")
            return
        if text == "/budget":
            now = date.today()
            budgets = (await session.execute(select(Budget).where(Budget.user_id == user.id, Budget.month == now.month, Budget.year == now.year))).scalars().all()
            await send(chat_id, "Budgets:\n" + "\n".join(f"• {item.category or 'Overall'}: ₹{item.limit_amount:g}" for item in budgets) if budgets else "No budgets set for this month.")
            return
        if text.startswith("/add "):
            parts = text.split(maxsplit=3)
            if len(parts) < 4:
                await send(chat_id, "Use: /add <amount> <category> <description>")
                return
            try:
                parsed = {"amount": float(parts[1]), "category": parts[2], "description": parts[3], "expense_date": date.today()}
            except ValueError:
                await send(chat_id, "The amount must be a number.")
                return
        else:
            parsed = parse_expense_message(text)
        if not parsed:
            await send(chat_id, "I couldn't read that. Try: spent 250 on groceries yesterday")
            return
        session.add(Expense(user_id=user.id, source="telegram", **parsed))
        await session.commit()
        await send(chat_id, f"Saved ₹{parsed['amount']:g} for {parsed['description']} ({parsed['category']}).")
