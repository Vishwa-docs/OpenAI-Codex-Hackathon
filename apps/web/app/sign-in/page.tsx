import { SignInForm } from "@/components/sign-in-form";
import { getServerSession } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function SignInPage() {
  const session = await getServerSession();

  if (session) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-screen bg-ink-950 text-slate-100">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.18),transparent_30%),linear-gradient(to_bottom,rgba(255,255,255,0.03),transparent_20%)]" />
      <div className="mx-auto flex min-h-screen max-w-7xl items-center px-6 py-16 lg:px-8">
        <div className="grid w-full gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="space-y-6">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Cloud Migration Cockpit</p>
            <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-white md:text-6xl">
              Sign in to the cockpit and continue the migration workflow.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-300">
              This workspace is the authenticated app surface. It connects to live APIs and shows explicit
              configuration errors when required services are unavailable.
            </p>
          </section>
          <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur">
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Session gate</p>
              <h2 className="text-2xl font-semibold text-white">Sign in</h2>
              <p className="text-sm leading-6 text-slate-300">
                Use your work credentials to sign in, or create a new workspace account to enter the authenticated migration workspace.
              </p>
            </div>
            <div className="mt-6">
              <SignInForm />
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
