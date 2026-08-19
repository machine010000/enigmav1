"use client";

import { FormEvent, useState } from "react";
import { useLocale } from "../i18n/provider";
import { useAuth } from "../auth/provider";

export function AuthForm({ admin = false }: { admin?: boolean }) {
  const { locale } = useLocale();
  const { login, adminLogin, loading, error } = useAuth();
  const [identity, setIdentity] = useState("");
  const [password, setPassword] = useState("");
  const submit = async (event: FormEvent) => { event.preventDefault(); try { if (admin) await adminLogin(identity, password); else await login(identity, password); } catch { /* error is rendered from the auth layer */ } };
  return <form className="login-form" onSubmit={submit}><div className="eyebrow">{admin ? locale.shell.adminAccess : locale.shell.welcome}</div><h1>{admin ? locale.shell.adminLogin : locale.shell.signIn}</h1><p className="hero-copy">{admin ? locale.shell.adminAccess : locale.shell.welcome}</p><label htmlFor="identity">{admin ? locale.shell.username : locale.shell.email}</label><input id="identity" value={identity} onChange={(event) => setIdentity(event.target.value)} autoComplete={admin ? "username" : "email"} required /><label htmlFor="password">{locale.shell.password}</label><input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />{error && <p className="form-error" role="alert">{error}</p>}<button className="action primary" type="submit" disabled={loading}>{loading ? locale.shell.checking : locale.shell.continue}</button></form>;
}