import { AppShell } from "../components/app-shell";
import { ProtectedRoute } from "../components/protected-route";

export default function ApplicationLayout({ children }: { children: React.ReactNode }) { return <ProtectedRoute><AppShell>{children}</AppShell></ProtectedRoute>; }