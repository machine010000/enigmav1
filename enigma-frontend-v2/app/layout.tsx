import type { Metadata } from "next";
import "./globals.css";
import { LocaleProvider } from "./i18n/provider";
import { AuthProvider } from "./auth/provider";

export const metadata: Metadata = {
  title: "ENIGMA | Your next move, made clear",
  description: "The ENIGMA workspace for turning intent into useful momentum.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return <html lang="en" dir="ltr"><body><LocaleProvider><AuthProvider>{children}</AuthProvider></LocaleProvider></body></html>;
}
