import en from "./locales/en.json";
import ar from "./locales/ar.json";
import es from "./locales/es.json";
import fr from "./locales/fr.json";

export type Locale = typeof en;
export type LanguageCode = "en" | "ar" | "es" | "fr";
export const locales: Record<LanguageCode, Locale> = { en, ar, es, fr };
export const languageCodes = Object.keys(locales) as LanguageCode[];