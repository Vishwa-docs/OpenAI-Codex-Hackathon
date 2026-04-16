export interface AuthSession {
  user: {
    id: string;
    email: string;
    name: string;
  };
  createdAt: string;
  activeOrganizationId?: string | null;
}

export interface SignInCredentials {
  email: string;
  password: string;
}

export interface SignUpCredentials extends SignInCredentials {
  name: string;
}

type BetterAuthSessionPayload =
  | {
      user: {
        id: string;
        email: string;
        name: string;
      };
      session: {
        createdAt: string | Date;
        activeOrganizationId?: string | null;
      };
    }
  | null
  | undefined;

export function mapAuthSession(payload: BetterAuthSessionPayload): AuthSession | null {
  if (!payload?.user || !payload.session) {
    return null;
  }

  return {
    user: {
      id: payload.user.id,
      email: payload.user.email,
      name: payload.user.name,
    },
    createdAt: String(payload.session.createdAt),
    activeOrganizationId: payload.session.activeOrganizationId ?? null,
  };
}
