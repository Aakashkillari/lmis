import type { ReactNode } from "react";
import { STATUS, fmt, perTen } from "../data";
import { t, tn, useT } from "../i18n";
import { Glyph, MISC, NAV_ICONS } from "./Icons";

export function Loader({ label }: { label?: string }) {
  const t = useT();
  return (
    <div className="loader" role="status" aria-live="polite">
      <div>
        <svg width="56" height="40" viewBox="0 0 56 40" aria-hidden="true">
          <rect x="2" y="4" width="9" height="34" rx="2" />
          <rect x="16" y="4" width="9" height="34" rx="2" />
          <rect x="30" y="4" width="9" height="34" rx="2" />
          <rect x="44" y="4" width="9" height="34" rx="2" />
        </svg>
        <p style={{ margin: "14px 0 0" }}>{label ?? t("Getting the latest numbers…")}</p>
      </div>
    </div>
  );
}

export function Button({ children, icon, kind = "primary", onClick, type = "button", disabled }: { children: ReactNode; icon?: string; kind?: "primary" | "accent" | "quiet" | "ghost"; onClick?: () => void; type?: "button" | "submit"; disabled?: boolean }) {
  const glyph = icon ? MISC[icon] ?? NAV_ICONS[icon] : null;
  return (
    <button className={`btn ${kind}`} type={type} onClick={onClick} disabled={disabled}>
      {glyph}{children}
    </button>
  );
}

export function Mark({ status, short = false, boxed = false }: { status: number; short?: boolean; boxed?: boolean }) {
  const s = STATUS[status];
  return (
    <span className={`mark ${boxed ? "boxed" : ""}`} style={{ color: s.color, background: boxed ? s.bg : undefined }}>
      <i style={{ background: s.hex }} />{t(short ? s.short : s.name)}
    </span>
  );
}

export function TradeIcon({ icon, status }: { icon: string; status?: number }) {
  const tone = status === undefined ? "idle" : { ink: STATUS[status].hex, tile: STATUS[status].bg.startsWith("var") ? STATUS_TILE[status] : STATUS[status].bg };
  return <span className="ticon"><Glyph name={icon} tone={tone} /></span>;
}

const STATUS_TILE = ["#FBE8E4", "#FBF0DF", "#E2F2E9", "#E5EEF8", "#ECE7FA"];

const Job = ({ filled, color }: { filled: boolean; color: string }) => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <rect x="3.5" y="7.5" width="17" height="12" rx="2.5" fill={filled ? color : "none"} stroke={filled ? color : "#C3C9D4"} strokeWidth="1.7" strokeDasharray={filled ? undefined : "2.4 2.4"} />
    <path d="M9 7.5V5.5h6v2" fill="none" stroke={filled ? color : "#C3C9D4"} strokeWidth="1.7" strokeLinecap="round" />
  </svg>
);
const Person = ({ color }: { color: string }) => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <circle cx="12" cy="7.5" r="3.4" fill={color} />
    <path d="M5.2 20.5c.6-4.2 3.2-6.7 6.8-6.7s6.2 2.5 6.8 6.7z" fill={color} />
  </svg>
);

export function JobsStrip({ ratio, status, small = false }: { ratio: number; status: number; small?: boolean }) {
  const filled = Math.min(10, Math.round(ratio * 10));
  const extra = Math.max(0, Math.min(12, Math.round(ratio * 10) - 10));
  const color = filled >= 10 ? STATUS[2].hex : STATUS[status].hex;
  return (
    <div className={`strip ${small ? "small" : ""}`} role="img" aria-label={t("{n} trainees for every 10 jobs", { n: perTen(ratio) })}>
      {Array.from({ length: 10 }, (_, i) => <Job key={i} filled={i < filled} color={color} />)}
      {extra > 0 ? <span className="sep" /> : null}
      {Array.from({ length: extra }, (_, i) => <Person key={`p${i}`} color={STATUS[4].hex} />)}
    </div>
  );
}

export function StripCaption({ ratio, jobs, trainees }: { ratio: number; jobs: number; trainees: number }) {
  const style = { margin: "8px 0 0", color: "var(--ink-2)" };
  if (ratio < 0.95) return <p className="small" style={style}>{tn("{bold} About {count} jobs may go unfilled.", { bold: <b>{t("{n} trainees for every 10 jobs.", { n: perTen(ratio) })}</b>, count: fmt(jobs - trainees) })}</p>;
  if (ratio > 1.05) return <p className="small" style={style}>{tn("{bold} About {count} people may not find a job.", { bold: <b>{t("{n} trainees for every 10 jobs.", { n: perTen(ratio) })}</b>, count: fmt(trainees - jobs) })}</p>;
  return <p className="small" style={style}>{tn("{bold} A healthy balance.", { bold: <b>{t("About one trainee for every job.")}</b> })}</p>;
}

export function Spark({ history, forecast, color }: { history: number[]; forecast: number[]; color: string }) {
  const values = [...history.slice(-12), ...forecast];
  const max = Math.max(...values), min = Math.min(...values);
  const x = (i: number) => (i / (values.length - 1)) * 84;
  const y = (v: number) => 26 - ((v - min) / (max - min || 1)) * 22;
  const split = Math.min(12, history.length) - 1;
  const path = (from: number, to: number) => values.slice(from, to + 1).map((v, i) => `${i ? "L" : "M"}${x(i + from).toFixed(1)},${y(v).toFixed(1)}`).join("");
  return (
    <svg className="spark" viewBox="0 0 84 28" aria-hidden="true">
      <path d={path(0, split)} fill="none" stroke="#A3ABBA" strokeWidth="1.6" strokeLinejoin="round" />
      <path d={path(split, values.length - 1)} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      <circle cx={x(values.length - 1)} cy={y(values[values.length - 1])} r="2.6" fill={color} />
    </svg>
  );
}

/** A plain link that downloads one of Pramaan's tables as a spreadsheet file. */
export function Download({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a className="btn ghost download" href={href} download>
      <Glyph name="download" />{children}
    </a>
  );
}
