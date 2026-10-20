import { Fragment, createContext, createElement, useContext, useEffect, type ReactNode } from "react";
import { usePrefs } from "./prefs";
import hi from "./locales/hi.json";
import kn from "./locales/kn.json";
import ta from "./locales/ta.json";

export type Lang = "en" | "ta" | "hi" | "kn";
export const LANGS: { code: Lang; name: string; short: string; locale: string }[] = [
  { code: "en", name: "English", short: "EN", locale: "en-IN" },
  { code: "ta", name: "தமிழ்", short: "தமிழ்", locale: "ta-IN" },
  { code: "hi", name: "हिन्दी", short: "हिन्दी", locale: "hi-IN" },
  { code: "kn", name: "ಕನ್ನಡ", short: "ಕನ್ನಡ", locale: "kn-IN" },
];

/* English text is the key. Each language file maps it to the translation; anything missing falls back to English. */
const DICTS: Record<Lang, Record<string, string>> = { en: {}, ta, hi, kn };
let current: Lang = "en";

/** Marks text for translation where it is defined, for text that is translated later with t(). */
export const msg = (text: string) => text;

export function t(text: string, vars?: Record<string, string | number>) {
  const base = DICTS[current][text] || text;
  return vars ? base.replace(/\{(\w+)\}/g, (all, key: string) => (key in vars ? String(vars[key]) : all)) : base;
}

/** Like t(), but placeholders can be React nodes, so a translated sentence can keep its bold numbers. */
export function tn(text: string, parts: Record<string, ReactNode>) {
  const base = DICTS[current][text] || text;
  return base.split(/(\{\w+\})/g).map((piece, i) => {
    const name = /^\{(\w+)\}$/.exec(piece)?.[1];
    return createElement(Fragment, { key: i }, name && name in parts ? parts[name] : piece);
  });
}

export const locale = () => LANGS.find((l) => l.code === current)?.locale ?? "en-IN";

const LangContext = createContext<Lang>("en");

export function I18nProvider({ children }: { children: ReactNode }) {
  const [prefs] = usePrefs();
  current = prefs.lang;
  useEffect(() => { document.documentElement.lang = prefs.lang; }, [prefs.lang]);
  return <LangContext.Provider value={prefs.lang}>{children}</LangContext.Provider>;
}

/** Call in any component that shows text, so it redraws when the language changes. */
export function useT() {
  useContext(LangContext);
  return t;
}

export function useLang() {
  return useContext(LangContext);
}
