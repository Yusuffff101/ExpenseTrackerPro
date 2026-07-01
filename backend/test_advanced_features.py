import unittest
from datetime import date, timedelta

from recurring_service import next_occurrence
from telegram_service import parse_expense_message


class TelegramParserTests(unittest.TestCase):
    def test_natural_expense(self):
        parsed = parse_expense_message("spent 500 on groceries yesterday")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["amount"], 500)
        self.assertEqual(parsed["category"], "Food")
        self.assertEqual(parsed["expense_date"], date.today() - timedelta(days=1))

    def test_rejects_unstructured_message(self):
        self.assertIsNone(parse_expense_message("hello bot"))


class RecurringDateTests(unittest.TestCase):
    def test_month_end_is_clamped(self):
        self.assertEqual(next_occurrence(date(2026, 1, 31), "monthly"), date(2026, 2, 28))

    def test_weekly_schedule(self):
        self.assertEqual(next_occurrence(date(2026, 7, 1), "weekly"), date(2026, 7, 8))


if __name__ == "__main__":
    unittest.main()
