import calendar
from datetime import date, timedelta

from sqlalchemy import select

from models import Expense, RecurringTransaction


def next_occurrence(value: date, frequency: str) -> date:
    if frequency == "weekly":
        return value + timedelta(days=7)
    month = 1 if value.month == 12 else value.month + 1
    year = value.year + 1 if value.month == 12 else value.year
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


async def process_recurring(session, user_id: int, through: date | None = None) -> int:
    through = through or date.today()
    result = await session.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.active.is_(True),
            RecurringTransaction.next_run_date <= through,
        )
    )
    generated = 0
    for item in result.scalars().all():
        while item.next_run_date <= through:
            session.add(Expense(
                user_id=user_id,
                description=item.description,
                amount=item.amount,
                category=item.category,
                expense_date=item.next_run_date,
                source="recurring",
            ))
            item.last_generated_date = item.next_run_date
            item.next_run_date = next_occurrence(item.next_run_date, item.frequency)
            generated += 1
    if generated:
        await session.commit()
    return generated
