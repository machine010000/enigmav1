"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { languageCodes, locales, type LanguageCode, type Locale } from "./config";

type LocaleContextValue = { language: LanguageCode; locale: Locale; setLanguage: (language: LanguageCode) => void };
const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [restored, setRestored] = useState(false);
  useEffect(() => {
    const stored = window.localStorage.getItem("enigma-language") as LanguageCode | null;
    const restore = window.setTimeout(() => { if (stored && languageCodes.includes(stored)) setLanguage(stored); setRestored(true); }, 0);
    return () => window.clearTimeout(restore);
  }, []);
  useEffect(() => {
    if (!restored) return;
    document.documentElement.lang = language;
    document.documentElement.dir = locales[language].direction;
    window.localStorage.setItem("enigma-language", language);
  }, [language, restored]);
  return <LocaleContext.Provider value={{ language, locale: locales[language], setLanguage }}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) throw new Error("useLocale must be used inside LocaleProvider");
  return context;
}