"use client";

import Link from "next/link";
import { useLocale } from "../i18n/provider";
import { FreelancingControlCenter } from "./freelancing-control-center";

export function FreelancingShell() {
  return <FreelancingControlCenter />;
}

export function SimpleModuleShell({ kind }: { kind: "academy" | "creativity" }) {
  const { locale } = useLocale();
  const title = locale.modules[kind];
  const copy = locale.modules[`${kind}Copy` as keyof typeof locale.modules];
  return <section className="workspace"><Link className="action secondary" href="/app/freelancing">← {locale.shell.back}</Link><div className="workspace-header"><div><div className="eyebrow">{locale.shell.ready}</div><h1>{title}</h1></div><p>{copy}</p></div><div className="workspace-panel"><span className="status">Foundation ready</span><h3>{title}</h3><p>{locale.shell.placeholder}</p></div></section>;
}

export function BrandingShell() {
  const { locale } = useLocale();
  return <section className="workspace"><div className="eyebrow">{locale.shell.reserved}</div><div className="workspace-header"><div><h1>{locale.modules.branding}</h1><p>{locale.modules.brandingCopy}</p></div><span className="status">Reserved</span></div><div className="workspace-panel"><h3>Workspace reserved</h3><p>This area is intentionally inactive. Branding & Selling workflow implementation is not part of this task.</p></div></section>;
}