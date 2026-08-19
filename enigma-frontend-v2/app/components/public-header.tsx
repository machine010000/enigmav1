"use client";

import Link from "next/link";
import { useLocale } from "../i18n/provider";

export function PublicHeader() {
  const { language, locale, setLanguage } = useLocale();
  return <header className="topbar"><Link className="brand" href="/"><span className="brand-mark">E</span> ENIGMA</Link><nav className="nav" aria-label="Main navigation"><Link className="nav-button" href="/">{locale.nav.home}</Link><Link className="nav-button" href="/login">{locale.shell.signIn}</Link><Link className="nav-button" href="/admin-login">{locale.shell.admin}</Link></nav><div className="top-actions"><select className="language-button" value={language} onChange={(event) => setLanguage(event.target.value as typeof language)} aria-label="Language">{(["en", "ar", "es", "fr"] as const).map((code) => <option key={code} value={code}>{code.toUpperCase()}</option>)}</select></div></header>;
}