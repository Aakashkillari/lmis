import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { PILOT_STATES, homeFor, scopeName, useAuth, usePlace, useUser } from "../auth";
import { useData } from "../data";
import { LANGS, msg, useT } from "../i18n";
import { usePrefs } from "../prefs";
import { Glyph, NAV_ICONS } from "./Icons";
import { Cursor, Scroller, SmoothScroll, scrollToY, useScroll } from "./Motion";
import { Button } from "./parts";

const APP_LINKS = [
  { to: "/dashboard", label: msg("Dashboard"), icon: "map" },
  { to: "/explore", label: msg("Explore a trade"), icon: "explore" },
  { to: "/plan", label: msg("Plan seats"), icon: "plan" },
  { to: "/ask", label: msg("Ask Pramaan"), icon: "ask" },
];

export function Monogram({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#12161F" />
      <path d="M11 24V8h6.2a5 5 0 0 1 0 10H11" fill="none" stroke="#FFFFFF" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="22.5" cy="23.5" r="2" fill="#D9A21B" />
    </svg>
  );
}

function Sheet() {
  const data = useData();
  const t = useT();
  return (
    <div className="sheet" aria-hidden="true">
      <svg className="decal" viewBox={`0 0 ${data.geo.w} ${data.geo.h}`}>
        {data.geo.d.map((g) => <path key={g.n} d={g.d} />)}
      </svg>
      <span className="stamp">{t("Pramaan pilot: {states} states, {districts} districts, {trades} trades", { states: data.states.length, districts: data.states.length * data.districts.length, trades: data.trades.length })}</span>
    </div>
  );
}

/** Open/close behaviour shared by every drop-down: closes on outside click and Escape. */
function useMenu() {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (e: PointerEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false); };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", esc);
    return () => { window.removeEventListener("pointerdown", close); window.removeEventListener("keydown", esc); };
  }, [open]);
  return { open, setOpen, box };
}

function Picker({ label, button, children, className = "" }: { label: string; button: ReactNode; children: (close: () => void) => ReactNode; className?: string }) {
  const { open, setOpen, box } = useMenu();
  return (
    <div className={`picker ${className}`} ref={box}>
      <button className="picker-btn" aria-haspopup="menu" aria-expanded={open} aria-label={label} onClick={() => setOpen(!open)}>
        {button}<svg className="chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" /></svg>
      </button>
      {open ? <div className="menu" role="menu" aria-label={label}>{children(() => setOpen(false))}</div> : null}
    </div>
  );
}

function LangPicker() {
  const t = useT();
  const [prefs, setPrefs] = usePrefs();
  const now = LANGS.find((l) => l.code === prefs.lang) ?? LANGS[0];
  return (
    <Picker label={t("Language")} className="lang" button={<><Glyph name="lang" /><span>{now.short}</span></>}>
      {(close) => (
        <>
          <p className="label menu-title">{t("Language")}</p>
          {LANGS.map((l) => (
            <button key={l.code} role="menuitemradio" aria-checked={l.code === prefs.lang} lang={l.code} className={`menu-item ${l.code === prefs.lang ? "on" : ""}`} onClick={() => { setPrefs({ lang: l.code }); close(); }}>
              <span className="menu-mark" />{l.name}
            </button>
          ))}
        </>
      )}
    </Picker>
  );
}

function PlacePicker() {
  const t = useT();
  const [place, setPlace] = usePlace();
  const where = useLocation();
  const go = useNavigate();
  const national = where.pathname === "/india";
  return (
    <Picker label={t("Choose a state")} className="place" button={<><Glyph name="pin" /><span>{national ? t("All India") : t(place)}</span></>}>
      {(close) => (
        <>
          <button role="menuitemradio" aria-checked={national} className={`menu-item ${national ? "on" : ""}`} onClick={() => { close(); go("/india"); }}>
            <span className="menu-mark" /><span><b>{t("All India")}</b><small>{t("Compare the {count} pilot states", { count: PILOT_STATES.length })}</small></span>
          </button>
          <hr className="rule" />
          <p className="label menu-title">{t("Pilot states")}</p>
          {PILOT_STATES.map((s) => (
            <button key={s} role="menuitemradio" aria-checked={!national && s === place} className={`menu-item ${!national && s === place ? "on" : ""}`}
              onClick={() => { setPlace(s); close(); if (national) go("/dashboard"); }}>
              <span className="menu-mark" />{t(s)}
            </button>
          ))}
        </>
      )}
    </Picker>
  );
}

function Profile() {
  const t = useT();
  const user = useUser();
  const { signOut } = useAuth();
  const { open, setOpen, box } = useMenu();
  const leave = (to: string) => { setOpen(false); signOut(to); };
  return (
    <div className="profile" ref={box}>
      <button className="avatar" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)} aria-label={t("{name}: account and settings", { name: t(user.name) })}>{user.initials}</button>
      {open ? (
        <div className="menu" role="menu" aria-label={t("Account and settings")}>
          <div className="who"><span className="avatar big">{user.initials}</span><span><b>{t(user.name)}</b><small>{t(user.title)}</small></span></div>
          <p className="menu-scope"><i />{t("Opens on {place}", { place: scopeName(user) })}</p>
          <hr className="rule" />
          <Link to="/settings" role="menuitem" className="menu-item" onClick={() => setOpen(false)}><Glyph name="sliders" />{t("Settings")}</Link>
          <Link to="/method" role="menuitem" className="menu-item" onClick={() => setOpen(false)}><Glyph name="question" />{t("How Pramaan works")}</Link>
          <button role="menuitem" className="menu-item" onClick={() => leave("/login")}><Glyph name="users" />{t("Switch account")}</button>
          <button role="menuitem" className="menu-item" onClick={() => leave("/")}><Glyph name="out" />{t("Sign out")}</button>
        </div>
      ) : null}
    </div>
  );
}

/** Scrolls to a section of the landing page, below the header. */
export function scrollToSection(id: string) {
  const el = document.getElementById(id);
  if (el) scrollToY(el.getBoundingClientRect().top + window.scrollY - 88);
}

function SiteNav() {
  const t = useT();
  const { user } = useAuth();
  const where = useLocation();
  const go = useNavigate();
  const section = (id: string) => (e: MouseEvent) => {
    e.preventDefault();
    if (where.pathname === "/") scrollToSection(id);
    else go(`/#${id}`);
  };
  return (
    <>
      <nav className="site-nav" aria-label={t("Main")}>
        <a href="/#what" onClick={section("what")}>{t("What it does")}</a>
        <NavLink to="/method" className={({ isActive }) => (isActive ? "active" : "")}>{t("How it works")}</NavLink>
        <a href="/#pilot" onClick={section("pilot")}>{t("Pilot states")}</a>
      </nav>
      <div className="topbar-end">
        <LangPicker />
        {user
          ? <Button icon="map" onClick={() => go(homeFor(user))}>{t("Open Pramaan")}</Button>
          : where.pathname === "/login" ? null : <Button kind="quiet" icon="lock" onClick={() => go("/login")}>{t("Sign in")}</Button>}
      </div>
    </>
  );
}

function AppNav() {
  const t = useT();
  const data = useData();
  return (
    <>
      <PlacePicker />
      <nav className="nav" aria-label={t("Main")}>
        {APP_LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} className={({ isActive }) => (isActive ? "active" : "")}>
            {NAV_ICONS[l.icon]}<span>{t(l.label)}</span>
          </NavLink>
        ))}
      </nav>
      <div className="topbar-end">
        <div className="where"><i className="pulse" />{t("Data to {month}", { month: data.updated })}</div>
        <LangPicker />
        <Profile />
      </div>
    </>
  );
}

export function Shell() {
  const t = useT();
  const { user } = useAuth();
  const where = useLocation();
  const { y } = useScroll();
  const site = !user || where.pathname === "/" || where.pathname === "/login";
  return (
    <>
      <Sheet />
      <SmoothScroll />
      <Cursor />
      <Scroller />
      <header className={`topbar ${site ? "site" : "app"} ${y > 12 ? "scrolled" : ""}`}>
        <div className="topbar-in">
          <NavLink to="/" className="brand" aria-label={t("Pramaan home")}><Monogram />Pramaan</NavLink>
          {site ? <SiteNav /> : <AppNav />}
        </div>
      </header>
      <main className={`page ${site ? "page-site" : ""}`}><Outlet /></main>
    </>
  );
}
