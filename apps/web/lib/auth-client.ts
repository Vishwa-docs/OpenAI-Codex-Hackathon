import { createAuthClient } from "better-auth/client";
import { organizationClient } from "better-auth/client/plugins";
import { mapAuthSession, type AuthSession, type SignInCredentials, type SignUpCredentials } from "@/lib/auth-shared";

const client = createAuthClient({
  plugins: [organizationClient()],
});

function unwrap<T>(result: { data: T | null; error: { message?: string | null } | null }) {
  if (result.error) {
    throw new Error(result.error.message ?? "Authentication request failed.");
  }

  if (!result.data) {
    throw new Error("Authentication request returned no data.");
  }

  return result.data;
}

export const authClient = {
  async signInEmail(credentials: SignInCredentials): Promise<{ session: AuthSession }> {
    unwrap(
      await client.signIn.email({
        email: credentials.email,
        password: credentials.password,
        rememberMe: true,
      }),
    );

    const response = await this.getSession();
    if (!response.session) {
      throw new Error("Authentication succeeded but no session was established.");
    }

    return { session: response.session };
  },
  async signUpEmail(credentials: SignUpCredentials): Promise<{ session: AuthSession }> {
    unwrap(
      await client.signUp.email({
        name: credentials.name,
        email: credentials.email,
        password: credentials.password,
      }),
    );

    const response = await this.getSession();
    if (!response.session) {
      throw new Error("Account creation succeeded but no session was established.");
    }

    return { session: response.session };
  },
  async signOut(): Promise<void> {
    const result = await client.signOut();
    if (result.error) {
      throw new Error(result.error.message ?? "Unable to sign out.");
    }
  },
  async getSession(): Promise<{ session: AuthSession | null }> {
    const result = await client.getSession();
    if (result.error) {
      throw new Error(result.error.message ?? "Unable to fetch the current session.");
    }

    return {
      session: mapAuthSession((result.data ?? null) as Parameters<typeof mapAuthSession>[0]),
    };
  },
};
