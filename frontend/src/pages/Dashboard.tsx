import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Bot, CalendarDays, CalendarClock, ChevronLeft, ChevronRight, Edit3, LayoutDashboard, LogOut, Menu, PiggyBank, Plus, Search, Tag, Trash2, WalletCards, X } from "lucide-react";
import { useDeferredValue, useState } from "react";
import toast from "react-hot-toast";
import api, { getApiError, TOKEN_KEY } from "../api";
import type { Category, Expense, ExpenseInput, ExpensePage, User } from "../types";
import { AnalyticsView, BudgetsView, RecurringView, TelegramView } from "../components/AdvancedViews";

const fallbackCategories = ["Food", "Transport", "Shopping", "Bills", "Health", "Entertainment", "Other"];
const categoryColors = ["bg-violet-500", "bg-teal-500", "bg-amber-500", "bg-rose-500", "bg-blue-500", "bg-fuchsia-500", "bg-slate-500"];
const categoryTint = ["bg-violet-50 text-violet-700", "bg-teal-50 text-teal-700", "bg-amber-50 text-amber-700", "bg-rose-50 text-rose-700", "bg-blue-50 text-blue-700", "bg-fuchsia-50 text-fuchsia-700", "bg-slate-100 text-slate-700"];
const currency = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const formatDate = (value: string) => new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`));
const today = () => new Date().toISOString().slice(0, 10);

export default function Dashboard() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [category, setCategory] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [modal, setModal] = useState(false);
  const [categoryModal, setCategoryModal] = useState(false);
  const [editing, setEditing] = useState<Expense | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Expense | null>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [view, setView] = useState<"overview" | "analytics" | "budgets" | "recurring" | "telegram">("overview");

  const filterKey = { search: deferredSearch, category, startDate, endDate, page, pageSize };
  const expensesQuery = useQuery({
    queryKey: ["expenses", filterKey],
    queryFn: async () => (await api.get<ExpensePage>("/expenses", { params: { search: deferredSearch || undefined, category: category || undefined, start_date: startDate || undefined, end_date: endDate || undefined, page, page_size: pageSize } })).data,
  });
  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: async () => (await api.get<Category[]>("/categories")).data });
  const userQuery = useQuery({ queryKey: ["me"], queryFn: async () => (await api.get<User>("/me")).data });
  const categoryNames = categoriesQuery.data?.map((item) => item.name) ?? fallbackCategories;
  const data = expensesQuery.data;
  const expenses = data?.items ?? [];
  const grouped = data?.category_totals ?? {};
  const top = Object.entries(grouped).sort((a, b) => b[1] - a[1])[0];

  const save = useMutation({ mutationFn: (input: ExpenseInput) => editing ? api.put(`/expenses/${editing.id}`, input) : api.post("/expenses", input), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["expenses"] }); toast.success(editing ? "Expense updated" : "Expense added"); closeModal(); }, onError: (error) => toast.error(getApiError(error)) });
  const remove = useMutation({ mutationFn: (id: number) => api.delete(`/expenses/${id}`), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["expenses"] }); toast.success("Expense deleted"); setDeleteTarget(null); }, onError: (error) => toast.error(getApiError(error)) });
  const createCategory = useMutation({ mutationFn: (input: { name: string; color: string }) => api.post("/categories", input), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["categories"] }); toast.success("Category created"); setCategoryModal(false); }, onError: (error) => toast.error(getApiError(error)) });

  const closeModal = () => { setModal(false); setEditing(null); };
  const resetFilters = () => { setSearch(""); setCategory(""); setStartDate(""); setEndDate(""); setPage(1); };
  const hasFilters = Boolean(search || category || startDate || endDate);
  const changeFilter = (setter: (value: string) => void, value: string) => { setter(value); setPage(1); };
  const logout = () => { localStorage.removeItem(TOKEN_KEY); window.location.assign("/login"); };

  return <div className="min-h-screen bg-stone-50 lg:grid lg:grid-cols-[240px_1fr]">
    {navOpen && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/40 backdrop-blur-sm lg:hidden" onClick={() => setNavOpen(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-60 flex-col bg-slate-950 px-4 py-6 text-white transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${navOpen ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex items-center justify-between px-2"><div className="flex items-center gap-2.5 text-sm font-bold"><span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-600"><WalletCards size={19} /></span>ExpenseTracker <b className="text-violet-300">Pro</b></div><button className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 lg:hidden" onClick={() => setNavOpen(false)}><X size={19} /></button></div>
      <nav className="mt-10 space-y-1">{[
        ["overview", "Overview", LayoutDashboard], ["analytics", "Analytics", BarChart3], ["budgets", "Budgets", PiggyBank], ["recurring", "Recurring", CalendarClock], ["telegram", "Telegram", Bot],
      ].map(([id, label, Icon]) => <button key={id as string} onClick={() => { setView(id as typeof view); setNavOpen(false); }} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${view === id ? "bg-white/10 text-white" : "text-slate-500 hover:bg-white/5 hover:text-slate-300"}`}><Icon size={18} />{label as string}</button>)}</nav>
      <div className="mt-auto border-t border-white/10 pt-4"><div className="flex items-center gap-3 rounded-xl p-2"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand-600 text-sm font-bold">{userQuery.data?.email.slice(0, 1).toUpperCase() ?? "U"}</div><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold">{userQuery.data?.email.split("@")[0] ?? "Account"}</p><p className="truncate text-[10px] text-slate-500">{userQuery.data?.email}</p></div><button className="rounded-lg p-2 text-slate-500 hover:bg-white/10 hover:text-white" onClick={logout} aria-label="Sign out"><LogOut size={17} /></button></div></div>
    </aside>

    <main className="min-w-0 px-4 py-6 sm:px-7 lg:px-10 lg:py-9 xl:px-14">
      {view !== "overview" && <button className="mb-5 rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 shadow-sm lg:hidden" onClick={() => setNavOpen(true)}><Menu size={20} /></button>}
      {view === "overview" ? <>
      <header className="mb-8 flex items-center gap-4"><button className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 shadow-sm lg:hidden" onClick={() => setNavOpen(true)}><Menu size={20} /></button><div className="mr-auto"><p className="text-xs font-bold tracking-[.18em] text-brand-600">OVERVIEW</p><h1 className="mt-1 text-xl font-bold tracking-tight sm:text-2xl">Your spending at a glance</h1></div><button className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50" onClick={() => setCategoryModal(true)}><Tag size={17} /><span className="hidden md:inline">New category</span></button><button className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-brand-500/20 hover:bg-brand-700" onClick={() => setModal(true)}><Plus size={18} /><span className="hidden sm:inline">Add expense</span></button></header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><SummaryCard label="Filtered total" value={currency.format(Number(data?.total_amount ?? 0))} note={`${data?.total ?? 0} ${(data?.total ?? 0) === 1 ? "transaction" : "transactions"}`} featured /><SummaryCard label="Top category" value={top?.[0] ?? "No data"} note={top ? currency.format(top[1]) : "No expenses in this view"} /><SummaryCard label="Average expense" value={currency.format(data?.total ? Number(data.total_amount) / data.total : 0)} note="In the current view" className="sm:col-span-2 xl:col-span-1" /></section>

      <section className="surface mt-5 p-4 sm:p-5">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(220px,1fr)_180px_160px_160px_auto]">
          <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-400 focus-within:border-brand-500 focus-within:bg-white"><Search size={17} /><input className="min-w-0 flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400" value={search} onChange={(e) => changeFilter(setSearch, e.target.value)} placeholder="Search description" /></label>
          <select className="field py-2.5" value={category} onChange={(e) => changeFilter(setCategory, e.target.value)}><option value="">All categories</option>{categoryNames.map((name) => <option key={name}>{name}</option>)}</select>
          <label className="relative"><span className="absolute -top-2 left-3 bg-white px-1 text-[9px] font-bold text-slate-400">FROM</span><input className="field py-2.5" type="date" value={startDate} max={endDate || undefined} onChange={(e) => changeFilter(setStartDate, e.target.value)} /></label>
          <label className="relative"><span className="absolute -top-2 left-3 bg-white px-1 text-[9px] font-bold text-slate-400">TO</span><input className="field py-2.5" type="date" value={endDate} min={startDate || undefined} onChange={(e) => changeFilter(setEndDate, e.target.value)} /></label>
          {hasFilters && <button className="rounded-xl px-3 py-2 text-sm font-bold text-brand-600 hover:bg-brand-50" onClick={resetFilters}>Clear filters</button>}
        </div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(270px,.72fr)_minmax(500px,1.28fr)]">
        <article className="surface p-5 sm:p-6"><SectionHeading eyebrow="BREAKDOWN" title="By category" />{Object.keys(grouped).length ? <div className="mt-7 space-y-6">{Object.entries(grouped).sort((a, b) => b[1] - a[1]).map(([name, value], index) => <div key={name}><div className="mb-2 flex items-center justify-between text-sm"><span className="flex items-center gap-2.5 font-medium"><i className={`h-2.5 w-2.5 rounded-full ${categoryColors[index % categoryColors.length]}`} />{name}</span><b>{currency.format(value)}</b></div><div className="h-1.5 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${categoryColors[index % categoryColors.length]}`} style={{ width: `${(value / Number(data?.total_amount || 1)) * 100}%` }} /></div></div>)}</div> : <EmptyState />}</article>
        <article className="surface min-w-0 p-5 sm:p-6">
          <div className="flex items-center justify-between"><SectionHeading eyebrow="ACTIVITY" title="Expenses" /><span className="text-xs text-slate-400">{data?.total ?? 0} total</span></div>
          <div className="mt-5">{expensesQuery.isLoading ? <div className="space-y-3">{[1, 2, 3].map((item) => <div className="h-16 animate-pulse rounded-xl bg-slate-100" key={item} />)}</div> : expensesQuery.isError ? <div className="py-16 text-center text-sm text-red-600">Couldn’t load expenses. <button className="font-bold underline" onClick={() => expensesQuery.refetch()}>Try again</button></div> : expenses.length ? <div>{expenses.map((expense, index) => <div className="group grid grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-3 border-b border-slate-100 py-3.5 last:border-0 sm:grid-cols-[40px_minmax(0,1fr)_auto_64px]" key={expense.id}><span className={`grid h-10 w-10 place-items-center rounded-xl text-sm font-bold ${categoryTint[index % categoryTint.length]}`}>{expense.category.slice(0, 1).toUpperCase()}</span><div className="min-w-0"><p className="truncate text-sm font-semibold">{expense.description}</p><p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-400"><span>{expense.category}</span><span>·</span><CalendarDays size={12} />{formatDate(expense.expense_date)}</p></div><strong className="text-sm">−{currency.format(Number(expense.amount))}</strong><div className="col-start-2 col-end-4 flex justify-end sm:col-auto sm:opacity-0 sm:transition sm:group-hover:opacity-100"><button className="rounded-lg p-2 text-slate-400 hover:bg-brand-50 hover:text-brand-600" onClick={() => { setEditing(expense); setModal(true); }} aria-label="Edit"><Edit3 size={16} /></button><button className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600" onClick={() => setDeleteTarget(expense)} aria-label="Delete"><Trash2 size={16} /></button></div></div>)}</div> : <EmptyState search={hasFilters} />}</div>
          {data && data.total > 0 && <div className="mt-5 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between"><label className="text-xs text-slate-500">Rows <select className="ml-2 rounded-lg border border-slate-200 bg-white px-2 py-1.5" value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}><option>5</option><option>10</option><option>20</option></select></label><div className="flex items-center justify-between gap-3"><span className="text-xs text-slate-500">Page {data.page} of {data.pages}</span><div className="flex gap-1"><button className="rounded-lg border border-slate-200 p-2 hover:bg-slate-50" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}><ChevronLeft size={16} /></button><button className="rounded-lg border border-slate-200 p-2 hover:bg-slate-50" disabled={page >= data.pages} onClick={() => setPage((value) => value + 1)}><ChevronRight size={16} /></button></div></div></div>}
        </article>
      </section>
      </> : view === "analytics" ? <AnalyticsView /> : view === "budgets" ? <BudgetsView categories={categoriesQuery.data ?? []} /> : view === "recurring" ? <RecurringView categories={categoriesQuery.data ?? []} /> : <TelegramView />}
    </main>

    {modal && <ExpenseModal expense={editing} categories={categoryNames} busy={save.isPending} onClose={closeModal} onSave={(input) => save.mutate(input)} />}
    {categoryModal && <CategoryModal busy={createCategory.isPending} onClose={() => setCategoryModal(false)} onSave={(input) => createCategory.mutate(input)} />}
    {deleteTarget && <ConfirmDelete expense={deleteTarget} busy={remove.isPending} onCancel={() => setDeleteTarget(null)} onConfirm={() => remove.mutate(deleteTarget.id)} />}
  </div>;
}

function SummaryCard({ label, value, note, featured = false, className = "" }: { label: string; value: string; note: string; featured?: boolean; className?: string }) { return <article className={`rounded-2xl border p-5 shadow-sm sm:p-6 ${featured ? "border-brand-600 bg-brand-600 text-white shadow-brand-500/20" : "border-slate-200/80 bg-white"} ${className}`}><p className={`text-[11px] font-bold tracking-[.15em] ${featured ? "text-violet-200" : "text-slate-400"}`}>{label.toUpperCase()}</p><strong className="mt-3 block text-2xl tracking-tight">{value}</strong><p className={`mt-1 text-xs ${featured ? "text-violet-200" : "text-slate-400"}`}>{note}</p></article>; }
function SectionHeading({ eyebrow, title }: { eyebrow: string; title: string }) { return <div><p className="text-[10px] font-bold tracking-[.18em] text-brand-600">{eyebrow}</p><h2 className="mt-1 text-lg font-bold tracking-tight">{title}</h2></div>; }
function EmptyState({ search = false }: { search?: boolean }) { return <div className="grid min-h-60 place-content-center text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-brand-50 text-brand-600"><WalletCards size={21} /></span><h3 className="mt-4 text-sm font-bold">{search ? "No matching expenses" : "No expenses yet"}</h3><p className="mt-1 text-xs text-slate-400">{search ? "Change or clear your filters." : "Add an expense to get started."}</p></div>; }

function ExpenseModal({ expense, categories, busy, onClose, onSave }: { expense: Expense | null; categories: string[]; busy: boolean; onClose: () => void; onSave: (data: ExpenseInput) => void }) {
  const [description, setDescription] = useState(expense?.description ?? ""); const [amount, setAmount] = useState(expense?.amount.toString() ?? ""); const [category, setCategory] = useState(expense?.category ?? categories[0] ?? "Other"); const [expenseDate, setExpenseDate] = useState(expense?.expense_date ?? today());
  const submit = (event: React.FormEvent) => { event.preventDefault(); if (!description.trim() || !amount || Number(amount) <= 0) return; onSave({ description: description.trim(), amount: Number(amount), category, expense_date: expenseDate }); };
  return <ModalShell onClose={onClose}><form onSubmit={submit}><p className="text-[10px] font-bold tracking-[.18em] text-brand-600">{expense ? "EDIT EXPENSE" : "NEW EXPENSE"}</p><h2 className="mb-7 mt-1 text-2xl font-bold tracking-tight">{expense ? "Update the details" : "Add an expense"}</h2><div className="space-y-5"><div><label className="label">Description</label><input className="field" autoFocus value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Lunch with friends" required /></div><div className="grid gap-5 sm:grid-cols-2"><div><label className="label">Amount (₹)</label><input className="field" type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" required /></div><div><label className="label">Date</label><input className="field" type="date" value={expenseDate} onChange={(e) => setExpenseDate(e.target.value)} required /></div></div><div><label className="label">Category</label><select className="field" value={category} onChange={(e) => setCategory(e.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select></div></div><ModalActions busy={busy} onClose={onClose} submitText={expense ? "Save changes" : "Add expense"} /></form></ModalShell>;
}

function CategoryModal({ busy, onClose, onSave }: { busy: boolean; onClose: () => void; onSave: (data: { name: string; color: string }) => void }) { const [name, setName] = useState(""); const [color, setColor] = useState("#7559e8"); return <ModalShell onClose={onClose}><form onSubmit={(event) => { event.preventDefault(); if (name.trim()) onSave({ name: name.trim(), color }); }}><p className="text-[10px] font-bold tracking-[.18em] text-brand-600">CUSTOM CATEGORY</p><h2 className="mb-7 mt-1 text-2xl font-bold tracking-tight">Create a category</h2><label className="label">Category name</label><input className="field" autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Education" required maxLength={100} /><label className="label mt-5">Color</label><div className="flex items-center gap-3"><input className="h-11 w-14 rounded-lg border border-slate-200 bg-white p-1" type="color" value={color} onChange={(e) => setColor(e.target.value)} /><span className="text-sm text-slate-500">{color}</span></div><ModalActions busy={busy} onClose={onClose} submitText="Create category" /></form></ModalShell>; }

function ModalShell({ children, onClose }: { children: React.ReactNode; onClose: () => void }) { return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4 backdrop-blur-sm"><div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl sm:p-8"><button className="absolute right-4 top-4 rounded-lg p-2 text-slate-400 hover:bg-slate-100" onClick={onClose} type="button"><X size={19} /></button>{children}</div></div>; }
function ModalActions({ busy, onClose, submitText }: { busy: boolean; onClose: () => void; submitText: string }) { return <div className="mt-7 flex justify-end gap-3"><button type="button" className="rounded-xl bg-slate-100 px-4 py-3 text-sm font-bold text-slate-700 hover:bg-slate-200" onClick={onClose}>Cancel</button><button className="rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white hover:bg-brand-700" disabled={busy}>{busy ? "Saving…" : submitText}</button></div>; }
function ConfirmDelete({ expense, busy, onCancel, onConfirm }: { expense: Expense; busy: boolean; onCancel: () => void; onConfirm: () => void }) { return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4 backdrop-blur-sm"><div className="w-full max-w-sm rounded-2xl bg-white p-7 text-center shadow-2xl"><span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-600"><Trash2 size={21} /></span><h2 className="mt-4 text-xl font-bold">Delete this expense?</h2><p className="mt-2 text-sm text-slate-500">“{expense.description}” will be permanently removed.</p><div className="mt-7 flex justify-center gap-3"><button className="rounded-xl bg-slate-100 px-4 py-3 text-sm font-bold text-slate-700" onClick={onCancel}>Cancel</button><button className="rounded-xl bg-red-600 px-4 py-3 text-sm font-bold text-white hover:bg-red-700" disabled={busy} onClick={onConfirm}>{busy ? "Deleting…" : "Delete expense"}</button></div></div></div>; }
