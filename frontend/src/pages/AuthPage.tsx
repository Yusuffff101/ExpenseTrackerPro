import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Check, Eye, EyeOff, LockKeyhole, WalletCards } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import api, { getApiError, TOKEN_KEY } from "../api";

const schema = z.object({ email: z.string().email("Enter a valid email address"), password: z.string().min(6, "Use at least 6 characters") });
type FormValues = z.infer<typeof schema>;

export default function AuthPage({ mode }: { mode: "login" | "register" }) {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const isLogin = mode === "login";
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema) });
  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (!isLogin) await api.post("/register", values);
      const { data } = await api.post<{ access_token: string }>("/login", values);
      return data;
    },
    onSuccess: ({ access_token }) => { localStorage.setItem(TOKEN_KEY, access_token); navigate("/dashboard", { replace: true }); },
  });

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.05fr_.95fr]">
      <section className="relative hidden overflow-hidden bg-slate-950 p-12 text-white lg:flex lg:flex-col xl:p-16">
        <div className="absolute -left-40 bottom-[-22rem] h-[42rem] w-[42rem] rounded-full border border-white/5 ring-[90px] ring-white/[.025]" />
        <Brand light />
        <div className="relative my-auto max-w-xl">
          <p className="mb-5 text-xs font-bold tracking-[.24em] text-violet-300">MONEY, MADE CLEAR</p>
          <h1 className="text-5xl font-semibold leading-[1.08] tracking-[-.04em] xl:text-6xl">Know where it goes.<br /><span className="font-display italic text-violet-300">Own where you’re going.</span></h1>
          <p className="mt-7 max-w-lg text-base leading-7 text-slate-400">Track your expenses, understand your habits, and make more confident decisions with your money.</p>
          <div className="mt-9 grid gap-4 text-sm text-slate-300">
            {["Simple expense tracking", "A clear view of your spending", "Private and secure by design"].map((item) => <span className="flex items-center gap-3" key={item}><i className="grid h-6 w-6 place-items-center rounded-full bg-violet-400/15 text-violet-300"><Check size={14} /></i>{item}</span>)}
          </div>
        </div>
        <p className="relative text-xs text-slate-600">ExpenseTracker Pro · Your finances, without the noise.</p>
      </section>

      <section className="flex min-h-screen items-center justify-center bg-stone-50 px-5 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-14 lg:hidden"><Brand /></div>
          <div className="mb-8">
            <span className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand-100 text-brand-600"><LockKeyhole size={20} /></span>
            <h2 className="text-3xl font-bold tracking-tight text-slate-950">{isLogin ? "Welcome back" : "Create your account"}</h2>
            <p className="mt-2 text-sm text-slate-500">{isLogin ? "Sign in to continue to your dashboard." : "Start building a clearer picture of your money."}</p>
          </div>
          <form className="space-y-5" onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate>
            <div><label className="label" htmlFor="email">Email address</label><input id="email" className="field" type="email" placeholder="you@example.com" {...register("email")} />{errors.email && <p className="mt-1.5 text-xs font-medium text-red-600">{errors.email.message}</p>}</div>
            <div><label className="label" htmlFor="password">Password</label><div className="relative"><input id="password" className="field pr-12" type={showPassword ? "text" : "password"} placeholder="At least 6 characters" {...register("password")} /><button className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700" type="button" onClick={() => setShowPassword((v) => !v)} aria-label="Toggle password visibility">{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>{errors.password && <p className="mt-1.5 text-xs font-medium text-red-600">{errors.password.message}</p>}</div>
            {mutation.isError && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{getApiError(mutation.error)}</div>}
            <button className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-brand-500/20 transition hover:bg-brand-700" disabled={mutation.isPending}>{mutation.isPending ? "Please wait…" : isLogin ? "Sign in" : "Create account"}<ArrowRight size={17} /></button>
          </form>
          <p className="mt-7 text-center text-sm text-slate-500">{isLogin ? "New to ExpenseTracker?" : "Already have an account?"} <Link className="font-bold text-brand-600 hover:text-brand-700" to={isLogin ? "/register" : "/login"}>{isLogin ? "Create an account" : "Sign in"}</Link></p>
        </div>
      </section>
    </main>
  );
}

function Brand({ light = false }: { light?: boolean }) {
  return <div className={`flex items-center gap-3 font-bold tracking-tight ${light ? "text-white" : "text-slate-900"}`}><span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-600 text-white shadow-lg shadow-brand-500/20"><WalletCards size={21} /></span><span>ExpenseTracker <b className="text-brand-500">Pro</b></span></div>;
}
