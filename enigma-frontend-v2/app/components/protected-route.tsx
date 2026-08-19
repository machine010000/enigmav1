"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../auth/provider";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { authenticated, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => { if (!loading && !authenticated) router.replace(`/login?next=${encodeURIComponent(pathname)}`); }, [authenticated, loading, pathname, router]);
  if (loading || !authenticated) return <main className="main"><section className="workspace"><div className="eyebrow">ENIGMA</div><h1>Checking your session.</h1></section></main>;
  return <>{children}</>;
}