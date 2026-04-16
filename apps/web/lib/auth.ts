import { betterAuth } from "better-auth";
import { memoryAdapter } from "better-auth/adapters/memory";
import { getMigrations } from "better-auth/db/migration";
import { nextCookies } from "better-auth/next-js";
import { organization } from "better-auth/plugins";
import { kyselyAdapter } from "@better-auth/kysely-adapter";
import { Kysely, PostgresDialect } from "kysely";
import { headers } from "next/headers";
import { Pool } from "pg";
import { mapAuthSession, type AuthSession } from "@/lib/auth-shared";
import { getJudgeSession, isJudgeMode } from "@/lib/runtime";

type GlobalWithAuth = typeof globalThis & {
  __cmcAuthInstance?: ReturnType<typeof createAuthInstance>;
  __cmcAuthKysely?: Kysely<unknown>;
  __cmcAuthMemoryDb?: Record<string, unknown[]>;
  __cmcAuthMigrationPromise?: Promise<void>;
  __cmcAuthPool?: Pool;
};

const globalForAuth = globalThis as GlobalWithAuth;

function isTestEnvironment() {
  return process.env.NODE_ENV === "test" || process.env.BETTER_AUTH_USE_MEMORY === "true";
}

function getMemoryDb() {
  if (!globalForAuth.__cmcAuthMemoryDb) {
    globalForAuth.__cmcAuthMemoryDb = {
      user: [],
      session: [],
      account: [],
      verification: [],
      organization: [],
      member: [],
      invitation: [],
      team: [],
      teamMember: [],
    };
  }

  return globalForAuth.__cmcAuthMemoryDb;
}

function getDatabaseAdapter() {
  if (isTestEnvironment()) {
    return memoryAdapter(getMemoryDb());
  }

  const databaseUrl = process.env.BETTER_AUTH_DATABASE_URL ?? process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("BETTER_AUTH_DATABASE_URL or DATABASE_URL must be configured for Better Auth.");
  }

  if (!globalForAuth.__cmcAuthPool) {
    globalForAuth.__cmcAuthPool = new Pool({
      connectionString: databaseUrl,
    });
  }

  if (!globalForAuth.__cmcAuthKysely) {
    globalForAuth.__cmcAuthKysely = new Kysely({
      dialect: new PostgresDialect({
        pool: globalForAuth.__cmcAuthPool,
      }),
    });
  }

  return kyselyAdapter(globalForAuth.__cmcAuthKysely, {
    type: "postgres",
  });
}

function createAuthInstance() {
  return betterAuth({
    secret: process.env.BETTER_AUTH_SECRET ?? "dev-secret-change-me",
    baseURL: process.env.BETTER_AUTH_URL ?? process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
    database: getDatabaseAdapter(),
    emailAndPassword: {
      enabled: true,
      autoSignIn: true,
      minPasswordLength: 8,
      sendResetPassword: async ({ user, url }) => {
        console.info(`[better-auth] password reset requested for ${user.email}: ${url}`);
      },
    },
    plugins: [nextCookies(), organization()],
  });
}

export function getAuth(): ReturnType<typeof createAuthInstance> {
  if (!globalForAuth.__cmcAuthInstance) {
    globalForAuth.__cmcAuthInstance = createAuthInstance();
  }

  return globalForAuth.__cmcAuthInstance as ReturnType<typeof createAuthInstance>;
}

export async function ensureAuthSchema() {
  if (isTestEnvironment()) {
    return;
  }

  if (!globalForAuth.__cmcAuthMigrationPromise) {
    globalForAuth.__cmcAuthMigrationPromise = (async () => {
      const auth = getAuth();
      const migrations = await getMigrations(auth.options);
      await migrations.runMigrations();
    })();
  }

  await globalForAuth.__cmcAuthMigrationPromise;
}

export async function getServerSession() {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host") ?? "";
  if (isJudgeMode() && /^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host)) {
    return getJudgeSession();
  }

  try {
    await ensureAuthSchema();
    const payload = await getAuth().api.getSession({
      headers: requestHeaders,
    });

    return mapAuthSession(payload as Parameters<typeof mapAuthSession>[0]);
  } catch (error) {
    if (error instanceof Error && error.message.includes("BETTER_AUTH_DATABASE_URL")) {
      return null;
    }

    throw error;
  }
}

export function resetAuthStateForTests() {
  if (globalForAuth.__cmcAuthMemoryDb) {
    for (const key of Object.keys(globalForAuth.__cmcAuthMemoryDb)) {
      globalForAuth.__cmcAuthMemoryDb[key] = [];
    }
  }

  globalForAuth.__cmcAuthInstance = undefined;
  globalForAuth.__cmcAuthMigrationPromise = undefined;
}
