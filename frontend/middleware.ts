import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const tenantMode = process.env.TENANT_MODE === "true";
  const pathname = request.nextUrl.pathname;

  // Tenant mode: landing page (/) ko /login pe redirect karo
  if (tenantMode && pathname === "/") {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/"],
};
