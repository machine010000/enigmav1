import { PublicHeader } from "../components/public-header";
import { AuthForm } from "../components/auth-form";
import { LoginSwitch } from "../components/login-switch";

export default function LoginPage() { return <div className="app-shell"><PublicHeader /><main className="main"><AuthForm /><LoginSwitch admin /></main></div>; }