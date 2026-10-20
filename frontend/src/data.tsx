import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { locale, msg, t } from "./i18n";

export type Pair = {
  jobs: number; low: number; high: number; trainees: number; last: number; seats: number;
  completion: number; certification: number; ratio: number; status: number; growth: number;
  history: number[]; forecast: number[]; forecastLow: number[]; forecastHigh: number[];
};
export type Trade = { name: string; official: string; sector: "power" | "auto"; icon: string; nco: string; nsqf: number };
export type District = { name: string; note: string; cx: number; cy: number };
export type Warning = { district: number; trade: number; now: number; next: number; month: string; monthsAhead: number; people: number };
export type Move = { from: [number, number]; to: [number, number]; seats: number; fromBefore: number; fromAfter: number; toBefore: number; toAfter: number };
export type Method = {
  weights: Record<string, number>; duplication: number; coverage: number; bandLevel: number; historyMonths: number; forecastMonths: number;
  warningMonths: number; backtestMonths: number; bands: [number | null, number | null][]; donorKeep: number; receiverTarget: number; block: number;
};
export type Data = {
  state: string; states: string[]; method: Method;
  updated: string; historyMonths: string[]; futureMonths: string[]; districts: District[]; trades: Trade[]; pairs: Pair[][];
  warnings: Warning[]; moves: { same: Move[]; any: Move[] }; accuracy: { pramaan: number; simple: number };
  weights: Record<string, number>; geo: { w: number; h: number; d: { n: string; d: string; cx: number; cy: number }[] };
};

export const STATUS = [
  { name: msg("Not enough trainees"), short: msg("Too few"), color: "var(--s0)", bg: "var(--s0-bg)", hex: "#D1432F" },
  { name: msg("Running short"), short: msg("Running short"), color: "var(--s1)", bg: "var(--s1-bg)", hex: "#C97716" },
  { name: msg("Well matched"), short: msg("Matched"), color: "var(--s2)", bg: "var(--s2-bg)", hex: "#1F8A5B" },
  { name: msg("A few too many"), short: msg("A few extra"), color: "var(--s3)", bg: "var(--s3-bg)", hex: "#3B78BE" },
  { name: msg("Too many trainees"), short: msg("Too many"), color: "var(--s4)", bg: "var(--s4-bg)", hex: "#6A4FC4" },
];

export const BAND_WORDS = [msg("Below 6"), msg("6 to 8"), msg("8 to 12"), msg("12 to 15"), msg("Above 15")];

export const SECTORS = { all: msg("All fields"), power: msg("Electrical & power"), auto: msg("Vehicles") } as const;
export type SectorKey = keyof typeof SECTORS;

export const fmt = (n: number) => Math.round(n).toLocaleString("en-IN");
export const perTen = (ratio: number) => (Math.round(ratio * 100) / 10).toFixed(1).replace(/\.0$/, "");
export const statusOf = (r: number) => (r < 0.6 ? 0 : r < 0.8 ? 1 : r < 1.2 ? 2 : r < 1.5 ? 3 : 4);
export const monthName = (key: string, long = false, year = true) => {
  const [y, m] = key.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale(), { month: long ? "long" : "short", ...(year ? { year: "numeric" } : {}) });
};

const cache = new Map<string, Data>();
const DataContext = createContext<Data | null>(null);

/** Loads one state's numbers. Each state is fetched once and kept, so switching back is instant. */
export function DataProvider({ state, children, fallback }: { state: string; children: ReactNode; fallback: ReactNode }) {
  const [data, setData] = useState<Data | null>(() => cache.get(state) ?? null);
  const [error, setError] = useState("");
  useEffect(() => {
    const known = cache.get(state);
    if (known) { setData(known); return; }
    let live = true;
    setError("");
    fetch(`/api/data?state=${encodeURIComponent(state)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(t("Server answered with error {code}", { code: r.status })))))
      .then((d: Data) => { cache.set(state, d); if (live) setData(d); })
      .catch((e) => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [state]);
  if (error) {
    return (
      <div className="loader"><div><h2 className="h2">{t("Pramaan could not load its data")}</h2><p className="lede">{t("Start the Pramaan server, then refresh this page. Details: {error}", { error })}</p></div></div>
    );
  }
  if (!data || data.state !== state) return <>{fallback}</>;
  return <DataContext.Provider value={data}>{children}</DataContext.Provider>;
}

export function useData() {
  const data = useContext(DataContext);
  if (!data) throw new Error("useData must be used inside DataProvider");
  return data;
}

export type National = {
  states: {
    name: string; districts: number; updated: string; jobs: number; trainees: number; unfilled: number; extra: number;
    short: number; many: number; warnings: number; accuracy: { pramaan: number; simple: number };
    sectors: Record<"power" | "auto", { jobs: number; trainees: number; unfilled: number; extra: number }>;
    trades: { jobs: number; trainees: number; unfilled: number; extra: number }[];
  }[];
  pairs: { state: string; district: string; trade: number; jobs: number; trainees: number; ratio: number; status: number }[];
  trades: { name: string; sector: "power" | "auto"; icon: string }[];
  method: Method;
};

let nationalCache: National | null = null;

/** Summary of every pilot state, for the India page, the landing page and settings. */
export function useNational() {
  const [value, setValue] = useState<National | null>(nationalCache);
  const [error, setError] = useState("");
  useEffect(() => {
    if (nationalCache) return;
    let live = true;
    fetch("/api/national")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(t("Server answered with error {code}", { code: r.status })))))
      .then((d: National) => { nationalCache = d; if (live) setValue(d); })
      .catch((e) => { if (live) setError(e.message); });
    return () => { live = false; };
  }, []);
  return { national: value, error };
}

const PICK_KEY = "pramaan-pick";
export type PickState = { district: number; trade: number; sector: SectorKey };
const initialPick = (owner: string, start: PickState): PickState => {
  try {
    const saved = JSON.parse(sessionStorage.getItem(PICK_KEY) || "null");
    if (saved && saved.owner === owner && typeof saved.district === "number") return { district: saved.district, trade: saved.trade, sector: saved.sector };
  } catch {
    return start;
  }
  return start;
};
const PickContext = createContext<[PickState, (next: Partial<PickState>) => void] | null>(null);

/** owner is the person and state together, so each state keeps its own district and trade choice. */
export function PickProvider({ children, owner, start }: { children: ReactNode; owner: string; start: PickState }) {
  const [pick, setPick] = useState<PickState>(() => initialPick(owner, start));
  const update = (next: Partial<PickState>) =>
    setPick((current) => {
      const merged = { ...current, ...next };
      try { sessionStorage.setItem(PICK_KEY, JSON.stringify({ ...merged, owner })); } catch { return merged; }
      return merged;
    });
  return <PickContext.Provider value={[pick, update]}>{children}</PickContext.Provider>;
}

export function usePick() {
  const value = useContext(PickContext);
  if (!value) throw new Error("usePick must be used inside PickProvider");
  return value;
}

export function sectorTrades(data: Data, sector: SectorKey) {
  return data.trades.map((_, i) => i).filter((i) => sector === "all" || data.trades[i].sector === sector);
}

export function districtTotals(data: Data, d: number, trades: number[]) {
  let jobs = 0, trainees = 0, unfilled = 0, extra = 0, short = 0, many = 0;
  trades.forEach((k) => {
    const p = data.pairs[d][k];
    jobs += p.jobs; trainees += p.trainees;
    unfilled += Math.max(0, p.jobs - p.trainees); extra += Math.max(0, p.trainees - p.jobs);
    if (p.status === 0) short++;
    if (p.status === 4) many++;
  });
  return { jobs, trainees, unfilled, extra, short, many, ratio: trainees / jobs };
}

/** The district with the most jobs left unfilled: a sensible place to start looking. */
export function busiestDistrict(data: Data) {
  const all = sectorTrades(data, "all");
  let best = 0, most = -1;
  data.districts.forEach((_, d) => { const u = districtTotals(data, d, all).unfilled; if (u > most) { most = u; best = d; } });
  return best;
}
