"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "../i18n/provider";
import { useAuth } from "../auth/provider";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { language, locale, setLanguage } = useLocale();
  const { user, logout } = useAuth();
  const links = [["/app", locale.nav.home], ["/app/freelancing", locale.nav.freelancing], ["/app/freelancing/academy", locale.nav.academy], ["/app/freelancing/creativity", locale.nav.creativity], ["/app/branding-selling", locale.nav.branding]];
  return <div className="app-shell"><header className="topbar"><Link className="brand" href="/app"><span className="brand-mark">E</span> ENIGMA</Link><nav className="nav" aria-label="Application navigation">{links.map(([href, label]) => <Link key={href} className={`nav-button ${pathname === href ? "active" : ""}`} href={href}>{label}</Link>)}</nav><div className="top-actions"><select className="language-button" value={language} onChange={(event) => setLanguage(event.target.value as typeof language)} aria-label="Language">{(["en", "ar", "es", "fr"] as const).map((code) => <option key={code} value={code}>{code.toUpperCase()}</option>)}</select><button className="auth-button" onClick={logout}>{locale.shell.signOut}</button></div></header><div className="app-user">{user?.name} <span>{user?.email}</span></div><main className="main">{children}</main><footer className="footer"><span>ENIGMA / WORKSPACE</span><span>{user?.plan}</span></footer></div>;
}