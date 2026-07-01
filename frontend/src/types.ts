export interface Expense { id: number; description: string; amount: number; category: string; expense_date: string }
export interface User { id: number; email: string }
export interface ExpenseInput { description: string; amount: number; category: string; expense_date: string }
export interface Category { id: number; name: string; color: string }
export interface ExpensePage {
  items: Expense[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  total_amount: number;
  category_totals: Record<string, number>;
}
export interface BudgetStatus { id: number; category: string | null; limit_amount: number; spent: number; remaining: number; percentage: number; month: number; year: number }
export interface AnalyticsData {
  trend: { year: number; month: number; label: string; total: number }[];
  categories: { category: string; total: number }[];
  daily: { date: string; total: number }[];
  current_month: number;
  previous_month: number;
  month_change_percent: number | null;
}
export interface RecurringTransaction { id: number; description: string; amount: number; category: string; frequency: "weekly" | "monthly"; next_run_date: string; active: boolean; last_generated_date: string | null }
export interface TelegramStatus { linked: boolean; chat_id: string | null }
