import { beforeEach, describe, expect, it } from "vitest";
import { GET, POST } from "@/app/api/auth/[...all]/route";
import { resetAuthStateForTests } from "@/lib/auth";

describe("auth route", () => {
  beforeEach(() => {
    resetAuthStateForTests();
  });

  it("creates an account, issues a session cookie, and returns the current session", async () => {
    const signUpResponse = await POST(
      new Request("http://localhost/api/auth/sign-up/email", {
        method: "POST",
        headers: {
          "content-type": "application/json"
        },
        body: JSON.stringify({
          name: "Mia Chen",
          email: "mia.chen@northwind.example",
          password: "demo-password"
        })
      })
    );

    expect(signUpResponse.status).toBe(200);

    const cookie = signUpResponse.headers.get("set-cookie");
    expect(cookie).toContain("better-auth");

    const sessionResponse = await GET(
      new Request("http://localhost/api/auth/get-session", {
        headers: {
          cookie: cookie ?? ""
        }
      })
    );

    expect(sessionResponse.status).toBe(200);
    await expect(sessionResponse.json()).resolves.toMatchObject({
      user: {
        email: "mia.chen@northwind.example"
      }
    });
  });

  it("clears the session cookie on sign out", async () => {
    const signUpResponse = await POST(
      new Request("http://localhost/api/auth/sign-up/email", {
        method: "POST",
        headers: {
          "content-type": "application/json"
        },
        body: JSON.stringify({
          name: "Mia Chen",
          email: "mia.chen@northwind.example",
          password: "demo-password"
        })
      })
    );
    const cookie = signUpResponse.headers.get("set-cookie") ?? "";

    const signOutResponse = await POST(
      new Request("http://localhost/api/auth/sign-out", {
        method: "POST",
        headers: {
          cookie
        }
      })
    );

    expect(signOutResponse.status).toBe(200);
    expect(signOutResponse.headers.get("set-cookie")).toContain("Max-Age=0");
  });
});
