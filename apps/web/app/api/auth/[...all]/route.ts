import { toNextJsHandler } from "better-auth/next-js";
import { ensureAuthSchema, getAuth } from "@/lib/auth";

const handler = toNextJsHandler(async (request: Request) => {
  await ensureAuthSchema();
  return getAuth().handler(request);
});

export const { GET, POST, DELETE, PATCH, PUT } = handler;
