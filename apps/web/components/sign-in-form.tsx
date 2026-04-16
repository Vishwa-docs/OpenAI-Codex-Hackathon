"use client";

import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

export function SignInForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "sign-up") {
        await authClient.signUpEmail({ name, email, password });
      } else {
        await authClient.signInEmail({ email, password });
      }
      router.replace("/dashboard");
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to authenticate right now.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <h2 className="text-2xl font-semibold text-white">Sign in</h2>
      <div className="space-y-2">
        <label className="text-sm font-medium text-white" htmlFor="display-name">
          Full name
        </label>
        <input
          id="display-name"
          name="name"
          type="text"
          autoComplete="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-sky-400"
          placeholder="Your name"
        />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-white" htmlFor="work-email">
          Work email
        </label>
        <input
          id="work-email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-sky-400"
          placeholder="you@company.com"
        />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-white" htmlFor="work-password">
          Password
        </label>
        <input
          id="work-password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-sky-400"
          placeholder="Enter your password"
        />
      </div>
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
      <div className="grid gap-3 sm:grid-cols-2">
        <button
          type="submit"
          onClick={() => setMode("sign-in")}
          disabled={isSubmitting}
          className="inline-flex w-full items-center justify-center rounded-full bg-sky-400 px-5 py-3 text-sm font-medium text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting && mode === "sign-in" ? "Signing in..." : "Sign in"}
        </button>
        <button
          type="submit"
          onClick={() => setMode("sign-up")}
          disabled={isSubmitting}
          className="inline-flex w-full items-center justify-center rounded-full border border-white/10 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting && mode === "sign-up" ? "Creating account..." : "Create account"}
        </button>
      </div>
    </form>
  );
}
