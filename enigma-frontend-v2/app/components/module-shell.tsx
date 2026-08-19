"use client";

import Link from "next/link";
import { useLocale } from "../i18n/provider";

const areas = ["Marketplace / Jobs", "Opportunity Verification", "Academy", "Creativity", "Applications", "Active Work"];

export function FreelancingShell() {
  const { locale } = useLocale();
  return <section className="workspace"><div className="eyebrow">{locale.shell.ready}</div><div className="workspace-header"><div><h1>{locale.modules.freelancing}</h1><p>{locale.modules.freelancingCopy}</p></div><span className="status">Backend integration pending</span></div><div className="module-grid">{areas.map((area) => <div className="workspace-panel" key={area}><span className="status">Not available yet</span><h3>{area}</h3><p>No marketplace connected. This shell does not simulate data or submit applications.</p></div>)}</div></section>;
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