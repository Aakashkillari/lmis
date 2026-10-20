import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { SectorKey } from "./data";
import type { Lang } from "./i18n";

export type Prefs = {
  smooth: boolean; cursor: boolean; motion: boolean; large: boolean; lang: Lang;
  startState: string | null; startDistrict: string | null; startSector: SectorKey | null;
};
const DEFAULTS: Prefs = { smooth: true, cursor: true, motion: true, large: false, lang: "en", startState: null, startDistrict: null, startSector: null };
const keyFor = (owner: string) => `pramaan-prefs:${owner}`;

const load = (owner: string, carry?: Prefs): Prefs => {
  try {
    const saved = JSON.parse(localStorage.getItem(keyFor(owner)) || "null");
    if (saved) return { ...DEFAULTS, ...saved, startDistrict: typeof saved.startDistrict === "string" ? saved.startDistrict : null };
  } catch {
    return DEFAULTS;
  }
  /* First time this person signs in here: keep the language they were already reading in. */
  return carry ? { ...DEFAULTS, lang: carry.lang } : DEFAULTS;
};

const PrefsContext = createContext<[Prefs, (next: Partial<Prefs>) => void] | null>(null);

/** Settings live per person: whoever signs in on this computer gets their own. */
export function PrefsProvider({ owner, children }: { owner: string; children: ReactNode }) {
  const [state, setState] = useState(() => ({ owner, prefs: load(owner) }));
  let current = state;
  if (state.owner !== owner) {
    current = { owner, prefs: load(owner, state.prefs) };
    setState(current);
  }
  const { prefs } = current;
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("text-large", prefs.large);
    root.classList.toggle("no-motion", !prefs.motion);
    try { localStorage.setItem(keyFor(current.owner), JSON.stringify(prefs)); } catch { return; }
  }, [current.owner, prefs]);
  const update = (next: Partial<Prefs>) => setState((s) => ({ owner: s.owner, prefs: { ...s.prefs, ...next } }));
  return <PrefsContext.Provider value={[prefs, update]}>{children}</PrefsContext.Provider>;
}

export function usePrefs() {
  const value = useContext(PrefsContext);
  if (!value) throw new Error("usePrefs must be used inside PrefsProvider");
  return value;
}
