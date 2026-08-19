"use client";

import Link from "next/link";
import { useLocale } from "../i18n/provider";

export function LoginSwitch({ admin = false }: { admin?: boolean }) {
  const { locale } = useLocale();
  return <p className="auth-switch"><Link href={admin ? "/admin-login" : "/login"}>{admin ? locale.shell.adminLogin : locale.shell.signIn}</Link></p>;
}