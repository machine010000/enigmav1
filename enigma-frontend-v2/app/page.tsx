import { PublicHeader } from "./components/public-header";
import { LandingContent } from "./components/landing-content";

export default function LandingPage() {
  return <div className="app-shell"><PublicHeader /><main className="main"><LandingContent /></main><footer className="footer"><span>ENIGMA / FOUNDATION 058</span><span>Your next move, made clear.</span></footer></div>;
}
