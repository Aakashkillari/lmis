import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { PickProvider, SECTORS, busiestDistrict, sectorTrades, useData, type Data, type PickState } from "./data";
import { t } from "./i18n";
import { usePrefs, type Prefs } from "./prefs";

export type Role = "national" | "state" | "district" | "sector";
export type Account = {
  id: string; name: string; title: string; role: Role; initials: string; summary: string;
  scope: { state: string | null; district: string | null; sector: "power" | "auto" | null };
};
export type User = Account & { since: number; until: number };

type Auth = {
  user: User | null;
  notice: string;
  /** Where to send someone who just signed out, so page guards don't bounce them through the sign-in page. */
  after: string | null;
  signIn: (username: string, password: string) => Promise<void>;
  signInDemo: (id: string) => Promise<void>;
  signOut: (to?: string) => Promise<void>;
  lost: () => void;
};

const AuthContext = createContext<Auth | null>(null);

async function post(url: string, body?: unknown) {
  let response: Response;
  try {
    response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}) });
  } catch {
    throw new Error(t("Pramaan could not reach its server. Check that it is running and try again."));
  }
  const json = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof json.detail === "string" ? t(json.detail) : t("Pramaan answered with error {code}. Try again.", { code: response.status }));
  return json;
}

export function AuthProvider({ children, fallback }: { children: ReactNode; fallback: ReactNode }) {
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [notice, setNotice] = useState("");
  const [after, setAfter] = useState<string | null>(null);
  const navigate = useNavigate();
  useEffect(() => {
    fetch("/api/me").then((r) => r.json()).then((j) => setUser(j.user ?? null)).catch(() => setUser(null));
  }, []);
  const value = useMemo<Auth>(() => ({
    user: user ?? null,
    notice,
    after,
    signIn: async (username, password) => { setUser(await post("/api/login", { username, password })); setNotice(""); setAfter(null); },
    signInDemo: async (id) => { setUser(await post("/api/login/demo", { username: id })); setNotice(""); setAfter(null); },
    signOut: async (to = "/") => {
      await post("/api/logout").catch(() => null);
      try { sessionStorage.removeItem("pramaan-pick"); sessionStorage.removeItem("pramaan-place"); } catch { /* storage blocked */ }
      setAfter(to);
      setUser(null);
      navigate(to, { replace: true });
    },
    lost: () => { setNotice(t("Your session ended. Sign in again to keep going.")); setAfter(null); setUser(null); },
  }), [user, notice, after, navigate]);
  if (user === undefined) return <>{fallback}</>;
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

export function useUser() {
  const { user } = useAuth();
  if (!user) throw new Error("useUser needs a signed-in user");
  return user;
}

/* ---- which state is open ---- */

export const PILOT_STATES = ["Tamil Nadu", "Karnataka"];
const PLACE_KEY = "pramaan-place";
const PlaceContext = createContext<[string, (state: string) => void] | null>(null);

function firstPlace(owner: string, account: Account | null, prefs: Prefs) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(PLACE_KEY) || "null");
    if (saved && saved.owner === owner && PILOT_STATES.includes(saved.state)) return saved.state as string;
  } catch { /* storage blocked */ }
  const wanted = prefs.startState ?? account?.scope.state;
  return wanted && PILOT_STATES.includes(wanted) ? wanted : PILOT_STATES[0];
}

/** The state whose numbers are on screen. Each person starts on their own state. */
export function PlaceProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [prefs] = usePrefs();
  const owner = user?.id ?? "guest";
  const [state, setState] = useState(() => ({ owner, place: firstPlace(owner, user, prefs) }));
  let current = state;
  if (state.owner !== owner) {
    current = { owner, place: firstPlace(owner, user, prefs) };
    setState(current);
  }
  const setPlace = (place: string) => {
    setState({ owner, place });
    try { sessionStorage.setItem(PLACE_KEY, JSON.stringify({ owner, state: place })); } catch { /* storage blocked */ }
  };
  return <PlaceContext.Provider value={[current.place, setPlace]}>{children}</PlaceContext.Provider>;
}

export function usePlace() {
  const value = useContext(PlaceContext);
  if (!value) throw new Error("usePlace must be used inside PlaceProvider");
  return value;
}

/* ---- what each person sees first ---- */

export type Scope = { state: string | null; district: number | null; sector: "power" | "auto" | null };

export function scopeOf(account: Account | null, data: Data): Scope {
  if (!account) return { state: null, district: null, sector: null };
  const here = !account.scope.state || account.scope.state === data.state;
  const d = here && account.scope.district ? data.districts.findIndex((x) => x.name === account.scope.district) : -1;
  return { state: account.scope.state, district: d >= 0 ? d : null, sector: account.scope.sector };
}

export function seesLines(account: Account, data: Data) {
  const { scope } = account;
  const states = data.states.length;
  if (scope.district) {
    return [t("Opens on {district}, with all {count} trades", { district: t(scope.district), count: data.trades.length }), t("Seat changes that involve {district}", { district: t(scope.district) }), t("Answers about {district} first", { district: t(scope.district) })];
  }
  if (scope.sector === "auto") {
    return [t("Vehicle trades in all {count} pilot states", { count: states }), t("Seat changes for vehicle courses"), t("Answers about vehicle trades first")];
  }
  if (scope.sector === "power") {
    return [t("Electrical and power trades in all {count} pilot states", { count: states }), t("Seat changes for electrical and power courses"), t("Answers about electrical and power trades first")];
  }
  if (scope.state) {
    return [t("All districts and all {count} trades in {state}", { count: data.trades.length, state: t(scope.state) }), t("Every suggested seat change in {state}", { state: t(scope.state) }), t("Answers about {state} first", { state: t(scope.state) })];
  }
  return [t("All {count} pilot states, side by side", { count: states }), t("Every district and trade in each state"), t("The worst gaps across the country, ranked")];
}

export function scopeName(account: Account) {
  const { scope } = account;
  if (scope.district) return t(scope.district);
  if (scope.sector) return t(SECTORS[scope.sector]);
  if (scope.state) return t(scope.state);
  return t("All India");
}

/** National and sector roles start on the India page; state and district roles on their dashboard. */
export function homeFor(account: Account | null) {
  return account && (account.role === "national" || account.role === "sector") ? "/india" : "/dashboard";
}

export function startPick(scope: Scope, prefs: Prefs, data: Data): PickState {
  const chosen = prefs.startDistrict && (!prefs.startState || prefs.startState === data.state) ? data.districts.findIndex((d) => d.name === prefs.startDistrict) : -1;
  const district = chosen >= 0 ? chosen : scope.district ?? busiestDistrict(data);
  const sector = prefs.startSector ?? scope.sector ?? "all";
  const trades = sectorTrades(data, sector);
  const trade = trades.reduce((best, k) => (data.pairs[district][k].ratio < data.pairs[district][best].ratio ? k : best), trades[0]);
  return { district, sector, trade };
}

/** Gives each person, in each state, their own starting view and remembered choices. */
export function ScopedPick({ children }: { children: ReactNode }) {
  const data = useData();
  const { user } = useAuth();
  const [prefs] = usePrefs();
  const owner = `${user?.id ?? "guest"}:${data.state}`;
  const start = startPick(scopeOf(user, data), prefs, data);
  return <PickProvider key={owner} owner={owner} start={start}>{children}</PickProvider>;
}

export function RequireUser() {
  const { user, after } = useAuth();
  const where = useLocation();
  if (!user) return <Navigate to={after ?? `/login?next=${encodeURIComponent(where.pathname)}`} replace />;
  return <Outlet />;
}

export function safeNext(next: string | null) {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/login")) return null;
  return next;
}
