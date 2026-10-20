import { STATUS, districtTotals, statusOf, type Data } from "../data";
import { useT } from "../i18n";

const LABEL_OFFSET: Record<string, [number, number, "start" | "end" | "middle"]> = {
  Chennai: [-8, -14, "end"], Krishnagiri: [0, -16, "middle"], Salem: [0, -14, "middle"], Coimbatore: [0, 22, "middle"],
  Tiruppur: [10, 22, "start"], Tiruchirappalli: [0, -16, "middle"], Madurai: [0, -14, "middle"], Tirunelveli: [0, 22, "middle"],
  "Bengaluru Urban": [10, 4, "start"], Mysuru: [0, 22, "middle"], Belagavi: [0, -14, "middle"], Dharwad: [10, 4, "start"],
  "Dakshina Kannada": [8, 22, "start"], Kalaburagi: [0, -14, "middle"], Tumakuru: [-10, 4, "end"], Ballari: [0, -14, "middle"],
};

type MapProps = { data: Data; trades: number[]; selected?: number; onPick?: (d: number) => void; compact?: boolean; focus?: number | null; home?: number | null };

export function TNMap({ data, trades, selected, onPick, compact = false, focus = null, home = null }: MapProps) {
  const t = useT();
  const index: Record<string, number> = {};
  data.districts.forEach((d, i) => { index[d.name] = i; });
  const totals = data.districts.map((_, i) => districtTotals(data, i, trades));
  const tone = (i: number) => {
    const t = totals[i];
    if (t.short > t.many) return 0;
    if (t.many > t.short) return 4;
    return statusOf(t.ratio);
  };
  const strength = (i: number) => {
    const t = totals[i];
    const gap = t.unfilled + t.extra;
    const max = Math.max(...totals.map((x) => x.unfilled + x.extra));
    return 0.35 + 0.55 * Math.sqrt(gap / max);
  };
  return (
    <svg className="map-svg" viewBox={`-10 -10 ${data.geo.w + 20} ${data.geo.h + 20}`} role="group" aria-label={t("Map of {state} districts", { state: t(data.state) })}>
      {data.geo.d.map((g) => {
        const i = index[g.n];
        if (i === undefined) return <path key={g.n} d={g.d} fill="#E6E9F0"><title>{t(g.n)}</title></path>;
        const dim = focus !== null && i !== focus;
        const colour = dim ? "#C9CFD9" : STATUS[tone(i)].hex;
        return (
          <path key={g.n} d={g.d} className={`pilot ${i === selected ? "sel" : ""}`} fill={colour} fillOpacity={dim ? 0.6 : strength(i)}
            onClick={() => onPick?.(i)} tabIndex={onPick ? 0 : -1} onKeyDown={(e) => { if (e.key === "Enter") onPick?.(i); }}>
            <title>{t(g.n)}</title>
          </path>
        );
      })}
      {!compact && data.districts.map((d, i) => {
        const [dx, dy, anchor] = LABEL_OFFSET[d.name] || [0, -14, "middle"];
        return (
          <g key={d.name} style={{ pointerEvents: "none" }}>
            <circle cx={d.cx} cy={d.cy} r={i === selected ? 5 : 3.5} fill="#1D2135" stroke="#FFFFFF" strokeWidth="2" />
            <text className="map-label" x={d.cx + dx} y={d.cy + dy} textAnchor={anchor}>{t(d.name)}</text>
          </g>
        );
      })}
      {home !== null ? (
        <g className="home-pin" style={{ pointerEvents: "none" }}>
          <circle cx={data.districts[home].cx} cy={data.districts[home].cy} r="10" fill="none" stroke="#D9A21B" strokeWidth="2.2" />
          <circle cx={data.districts[home].cx} cy={data.districts[home].cy} r="4.5" fill="#D9A21B" stroke="#FFFFFF" strokeWidth="1.6" />
          {compact ? <text className="map-label" x={data.districts[home].cx} y={data.districts[home].cy + 26} textAnchor="middle">{t(data.districts[home].name)}</text> : null}
        </g>
      ) : null}
    </svg>
  );
}
