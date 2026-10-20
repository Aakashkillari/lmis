import type { CSSProperties, ReactNode } from "react";

const GLYPHS: Record<string, string[]> = {
  home: ["M8 16.5 16 9.5l8 7", "M10.5 15v8.5h11V15"],
  map: ["M8 11.5 13 9.5l6 2 5-2v12l-5 2-6-2-5 2z", "M13 9.5v12M19 11.5v12"],
  explore: ["M9 23v-6M13 23V12M17 23v-4", "M21.2 9.2a3.2 3.2 0 1 1 0 6.4a3.2 3.2 0 1 1 0-6.4z", "M23.6 15.4l1.8 1.8"],
  plan: ["M8.5 12h11.5", "M17 9l3 3-3 3", "M23.5 20H12", "M15 17l-3 3 3 3"],
  ask: ["M8 9h16v10.5h-8.5L10.5 23.5v-4H8z", "M12 13.5h8M12 16.5h5"],
  bolt: ["M17.5 7 10 17.5h6.2L15 25l7.5-10.5h-6.2z"],
  plug: ["M13 7v4.5M19 7v4.5", "M10 11.5h12V14a6 6 0 0 1-12 0z", "M16 20v5"],
  solar: ["M8 22.5 10.5 13h11L24 22.5z", "M13.6 13l-1 9.5M18.4 13l1 9.5M9.3 17.8h13.4", "M16 7v2.5"],
  pole: ["M16 7v18", "M10 10.5h12M11.5 14.5h9", "M10 10.5 8.5 13M22 10.5l1.5 2.5", "M13 25h6"],
  panel: ["M10 7h12v18H10z", "M13 11h3.5M13 14.5h3.5M13 18h3.5", "M19.3 11.5h.01M19.3 16h.01"],
  bike: ["M7.2 21.5a2.8 2.8 0 1 0 5.6 0a2.8 2.8 0 1 0-5.6 0", "M19.6 21.5a2.8 2.8 0 1 0 5.6 0a2.8 2.8 0 1 0-5.6 0", "M10 21.5h7.6l3.6-9.5", "M7.6 16.2h6.2l1.6 5.3", "M19.4 12h4.2"],
  car: ["M8 20v-3.5L10.2 12h11.6l2.2 4.5V20z", "M10.5 22.2a1.4 1.4 0 0 0 2.8 0M18.7 22.2a1.4 1.4 0 0 0 2.8 0", "M10.5 16.2h11"],
  ev: ["M6.5 21v-3.4L8.7 13.4h9.6l2.2 4.2V21z", "M9 23.2a1.5 1.5 0 0 0 3 0M15 23.2a1.5 1.5 0 0 0 3 0", "M20.5 18.4h2.6a1.8 1.8 0 0 0 1.8-1.8v-4", "M23.3 12.6h3.3M23.9 12.6V9.9M26 12.6V9.9", "M13.7 14.8l-1.2 2.2h2l-1.2 2.2"],
  hammer: ["M18.5 10.5 14.6 7.2 12 9.8l3.8 3.8", "M15.8 13.6l7.6 7.6-1.9 1.9-7.6-7.6", "M18.5 10.5l2.3-2.3 2.4 2.4-2.3 2.3"],
  spray: ["M10 13.5h8v11.5h-8z", "M12 13.5v-3h4v3M16 10.5h2.6", "M21.5 8h.01M23.5 10.5h.01M21.5 12.5h.01"],
  arrow: ["M8 16h15", "M18 11l5 5-5 5"],
  send: ["M8 16.5 24 9l-5 16-3.5-6.5z", "M15.5 18.5 24 9"],
  down: ["M16 8v15", "M11 18l5 5 5-5"],
  up: ["M16 24V9", "M11 14l5-5 5 5"],
  equal: ["M10 13h12", "M10 19h12"],
  bell: ["M10.5 20.5V15a5.5 5.5 0 0 1 11 0v5.5l1.5 2H9z", "M14 25.2h4"],
  reset: ["M9 16a7 7 0 1 0 2.1-5", "M9.2 8.5V12h3.5"],
  download: ["M16 8v11", "M11 14.5l5 5 5-5", "M9 24h14"],
  question: ["M13 12.8a3 3 0 1 1 4.3 2.7c-.9.4-1.3 1-1.3 1.9v.5", "M16 21.3h.01"],
  pin: ["M16 25s-6.5-5.8-6.5-11a6.5 6.5 0 0 1 13 0c0 5.2-6.5 11-6.5 11z", "M16 11.6a2.2 2.2 0 1 0 0 4.4a2.2 2.2 0 1 0 0-4.4z"],
  lock: ["M10 15h12v9.5H10z", "M12.5 15v-2.8a3.5 3.5 0 0 1 7 0V15", "M16 18.6v2.4"],
  out: ["M14.5 9H9.5v14h5", "M18.5 12l4 4-4 4", "M22.5 16H13.5"],
  sliders: ["M8.5 11h7M19.5 11h4M8.5 16h3M15.5 16h8M8.5 21h9M21.5 21h2", "M17.5 9v4M13.5 14v4M19.5 19v4"],
  users: ["M13 15a3.2 3.2 0 1 0 0-6.4a3.2 3.2 0 1 0 0 6.4z", "M7.5 23.5a5.5 5.5 0 0 1 11 0", "M19.6 9a3.2 3.2 0 0 1 0 5.8", "M21.2 17.8a5.5 5.5 0 0 1 3.3 5"],
  check: ["M9.5 16.5l4.2 4.2 8.8-9.4"],
  lang: ["M7.5 22.5l4-11 4 11M9 18.6h5", "M17.5 10.5h7M21 8.5v2M18.6 14.2c1.4 2.4 3.4 3.9 5.9 4.6M24 10.5c-.7 3.6-2.8 6.6-6.2 8.6"],
  sheet: ["M10 7.5h8.5l4 4v13H10z", "M18.5 7.5v4h4", "M13 16h6.5M13 19.5h6.5"],
};

export type Tone = "idle" | "ink" | "light" | { ink: string; tile: string };

export function Glyph({ name, tone = "idle", size, title, className = "" }: { name: string; tone?: Tone; size?: number; title?: string; className?: string }) {
  const paths = GLYPHS[name] ?? GLYPHS.question;
  const style: CSSProperties = typeof tone === "object" ? ({ ["--g-ink" as string]: tone.ink, ["--g-tile" as string]: tone.tile } as CSSProperties) : {};
  const toneClass = typeof tone === "string" ? `g-${tone}` : "";
  return (
    <svg className={`glyph ${toneClass} ${className}`} viewBox="0 0 32 32" width={size} height={size} style={style} role={title ? "img" : undefined} aria-label={title} aria-hidden={title ? undefined : true}>
      <rect className="tile" width="32" height="32" rx="8.5" />
      {paths.map((d, i) => <path key={i} className="g" d={d} pathLength={1} />)}
      <circle className="dot" cx="25.2" cy="25.2" r="1.9" />
    </svg>
  );
}

const make = (names: string[]) => Object.fromEntries(names.map((n) => [n, <Glyph key={n} name={n} />])) as Record<string, ReactNode>;

export const NAV_ICONS = make(["home", "map", "explore", "plan", "ask"]);
export const TRADE_ICONS = make(["bolt", "plug", "solar", "pole", "panel", "bike", "car", "ev", "hammer", "spray"]);
export const MISC = make(["arrow", "send", "down", "up", "equal", "bell", "reset", "download", "question", "pin", "lock", "out", "sliders", "users", "check", "lang", "sheet"]);
export const ROLE_ICON: Record<string, string> = { national: "explore", state: "map", district: "pin", sector: "car" };

export function StatusGlyph({ status }: { status: number }) {
  return <Glyph name={status <= 1 ? "down" : status >= 3 ? "up" : "equal"} />;
}

/** A large, faint outline of an icon that sits behind a card's content as a decal. */
export function Decal({ name }: { name: string }) {
  const paths = GLYPHS[name] ?? GLYPHS.question;
  return (
    <svg className="decal-glyph" viewBox="0 0 32 32" aria-hidden="true">
      {paths.map((d, i) => <path key={i} d={d} />)}
    </svg>
  );
}
