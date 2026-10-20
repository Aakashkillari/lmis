import { useState } from "react";
import { fmt, monthName, type Pair } from "../data";
import { useT } from "../i18n";

export function ForecastChart({ pair, historyMonths, futureMonths, traineesPerMonth }: { pair: Pair; historyMonths: string[]; futureMonths: string[]; traineesPerMonth: number }) {
  const t = useT();
  const [hover, setHover] = useState<number | null>(null);
  const W = 760, H = 300, L = 46, R = 16, T = 16, B = 34;
  const months = [...historyMonths, ...futureMonths];
  const values = [...pair.history, ...pair.forecast];
  const max = Math.max(...values, ...pair.forecastHigh, traineesPerMonth) * 1.1;
  const x = (i: number) => L + (i / (months.length - 1)) * (W - L - R);
  const y = (v: number) => T + (1 - v / max) * (H - T - B);
  const n = pair.history.length;
  const line = (arr: number[], offset: number) => arr.map((v, i) => `${i ? "L" : "M"}${x(i + offset).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const band = pair.forecastHigh.map((v, i) => `${i ? "L" : "M"}${x(i + n).toFixed(1)},${y(v).toFixed(1)}`).join("")
    + pair.forecastLow.map((_, i) => `L${x(n + pair.forecastLow.length - 1 - i).toFixed(1)},${y(pair.forecastLow[pair.forecastLow.length - 1 - i]).toFixed(1)}`).join("") + "Z";
  const ticks = [0, 0.5, 1].map((f) => Math.round((max / 1.1) * f));
  const joined = `M${x(n - 1).toFixed(1)},${y(pair.history[n - 1]).toFixed(1)}L${x(n).toFixed(1)},${y(pair.forecast[0]).toFixed(1)}`;
  const hoverValue = hover === null ? null : values[hover];
  return (
    <div>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const box = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
          const px = ((e.clientX - box.left) / box.width) * W;
          const i = Math.round(((px - L) / (W - L - R)) * (months.length - 1));
          setHover(Math.max(0, Math.min(months.length - 1, i)));
        }} role="img" aria-label={t("Job openings per month: last two years and the next twelve months")}>
        {ticks.map((v) => <g key={v}><line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="#EEF0F5" /><text x={L - 8} y={y(v) + 4} textAnchor="end">{fmt(v)}</text></g>)}
        <rect x={x(n)} y={T} width={W - R - x(n)} height={H - T - B} fill="#F7F9FC" />
        <text x={x(n) + 8} y={T + 14} style={{ fill: "#555B73", fontWeight: 600 }}>{t("Next 12 months")}</text>
        <path d={band} fill="rgba(11,110,105,0.14)" />
        <line x1={L} x2={W - R} y1={y(traineesPerMonth)} y2={y(traineesPerMonth)} stroke="#F2B630" strokeWidth="3" strokeLinecap="round" />
        <path d={line(pair.history, 0)} fill="none" stroke="#0B6E69" strokeWidth="2.6" strokeLinejoin="round" />
        <path d={joined + line(pair.forecast, n).replace("M", "L")} fill="none" stroke="#0B6E69" strokeWidth="2.6" strokeDasharray="6 5" strokeLinejoin="round" />
        {[0, Math.floor(n / 2), n, months.length - 1].map((i) => <text key={i} x={x(i)} y={H - 10} textAnchor="middle">{monthName(months[i])}</text>)}
        {hover !== null && hoverValue !== null ? (
          <g>
            <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} stroke="#1D2135" strokeDasharray="3 3" />
            <circle cx={x(hover)} cy={y(hoverValue)} r="5" fill="#0B6E69" stroke="#FFFFFF" strokeWidth="2" />
            <g transform={`translate(${Math.min(x(hover) + 10, W - 190)},${Math.max(T, y(hoverValue) - 52)})`}>
              <rect width="180" height="46" rx="10" fill="#1D2135" />
              <text x="12" y="19" style={{ fill: "#FFFFFF", fontWeight: 600 }}>{monthName(months[hover], true)}</text>
              <text x="12" y="36" style={{ fill: "#C9CEDC" }}>{t(hover >= n ? "{count} jobs expected" : "{count} jobs opened", { count: fmt(hoverValue) })}</text>
            </g>
          </g>
        ) : null}
      </svg>
      <div className="legend">
        <span><i style={{ background: "#0B6E69" }} />{t("Jobs opening each month")}</span>
        <span><i style={{ background: "repeating-linear-gradient(90deg,#0B6E69 0 6px,transparent 6px 10px)" }} />{t("Expected jobs")}</span>
        <span><i style={{ background: "rgba(11,110,105,0.3)", height: 10 }} />{t("Likely range")}</span>
        <span><i style={{ background: "#F2B630" }} />{t("Trainees finishing each month")}</span>
      </div>
    </div>
  );
}
