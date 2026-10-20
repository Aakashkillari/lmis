const C = ["#D70015", "#C93400", "#248A3D", "#0071A4", "#8944AB"];
const GLYPH = ["▼▼", "▼", "=", "▲", "▲▲"];
const RANGES = ["< 0.60", "0.60–0.80", "0.80–1.20", "1.20–1.50", "> 1.50"];
const esc = (text) => String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (n) => Math.round(n).toLocaleString("en-IN");
const tint = (s, a) => `color-mix(in srgb, ${C[s]} ${a}%, transparent)`;
const fill = (text, values) => text.replace(/\{(\w+)\}/g, (_, k) => values[k]);
const statusOf = (r) => (r < 0.6 ? 0 : r < 0.8 ? 1 : r < 1.2 ? 2 : r < 1.5 ? 3 : 4);

function compute(D, S) {
  const ks = D.trades.map((_, k) => k).filter((k) => S.sec === "all" || D.trades[k].sec === S.sec);
  const all = [];
  D.pairs.forEach((row, di) => ks.forEach((k) => all.push({ ...row[k], di, k })));
  let J = 0, T = 0, U = 0, SU = 0;
  all.forEach((p) => { J += p.j; T += p.t; U += Math.max(0, p.j - p.t); SU += Math.max(0, p.t - p.j); });
  const warns = D.warnings.filter((w) => ks.includes(w.k));
  const perDistrict = D.pairs.map((row) => {
    let sh = 0, ov = 0, u = 0, su = 0, j = 0, t = 0;
    ks.forEach((k) => { const p = row[k]; if (p.s === 0) sh++; if (p.s === 4) ov++; u += Math.max(0, p.j - p.t); su += Math.max(0, p.t - p.j); j += p.j; t += p.t; });
    return { sh, ov, u, su, j, t, r: t / j };
  });
  const shortCount = all.filter((p) => p.s === 0).length;
  const overCount = all.filter((p) => p.s === 4).length;
  return { ks, all, J, T, U, SU, warns, perDistrict, shortCount, overCount };
}

const toneOf = (m) => (m.sh > m.ov ? 0 : m.ov > m.sh ? 4 : m.sh === 0 ? 2 : 1);

function topBar(D, S) {
  const L = D.L;
  const segs = [["all", L.all], ["E", L.elec], ["A", L.auto]].map(([v, l]) => `<button class="${S.sec === v ? "on" : ""}" data-sec="${v}">${esc(l)}</button>`).join("");
  return `<div class="top">
    <div class="heading"><span class="eyebrow">${esc(L.statewide)} · ${esc(L.scope)}</span><span class="title">${esc(L.title)}</span></div>
    <div class="seg" role="group">${segs}</div>
    <span class="live"><i></i>${esc(fill(L.through, { month: D.through }))}</span>
    <button class="btn secondary" data-act="export">${esc(L.exportW)}</button>
  </div>`;
}

function kpis(D, X) {
  const L = D.L;
  const R = X.T / X.J;
  const rs = statusOf(R);
  const jw = X.J >= X.T ? 100 : (X.J / X.T) * 100;
  const tw = X.T >= X.J ? 100 : (X.T / X.J) * 100;
  const months = D.monthsShort.map((m, i) => {
    const glyphs = X.warns.filter((w) => w.mi === i).map((w) => `<span style="color:${C[w.to]}">${w.to === 0 ? "▼" : "▲"}</span>`).join("");
    return `<div><div class="stack">${glyphs}</div><span class="m">${esc(m)}</span></div>`;
  }).join("");
  return `<div class="kpis">
    <div class="card kpi"><span class="lab">${esc(L.kJobs)}</span><span class="val num">${fmt(X.J)}</span><span class="sub">${esc(L.kJobsSub)}</span></div>
    <div class="card kpi"><span class="lab">${esc(L.kTr)}</span><span class="val num">${fmt(X.T)}</span><span class="sub">${esc(L.kTrSub)}</span>
      <div class="pair"><div style="background:var(--g200);width:${jw.toFixed(1)}%"></div><div style="background:var(--g800);width:${tw.toFixed(1)}%"></div></div>
      <span class="ratio num"><span class="muted">${esc(L.stRatio)}</span> <b>${R.toFixed(2)}</b> <span style="color:${C[rs]};font-weight:600;white-space:nowrap">■ ${esc(L.fl[rs])}</span></span></div>
    <div class="card kpi"><span class="lab">${esc(L.kUnmet)}</span><span class="val num" style="color:${C[0]}">${fmt(X.U)}</span><span class="sub">${esc(fill(L.inS, { n: X.shortCount }))}</span></div>
    <div class="card kpi"><span class="lab">${esc(L.kSur)}</span><span class="val num" style="color:${C[4]}">${fmt(X.SU)}</span><span class="sub">${esc(fill(L.inO, { n: X.overCount }))}</span></div>
    <div class="card kpi"><div class="row"><span class="lab">${esc(L.kWarn)}</span><span class="val num" style="color:${C[1]}">${X.warns.length}</span></div>
      <span class="sub">${esc(L.kWarnSub)}</span><div class="months">${months}</div>
      <span class="legend-note">▼ → ${esc(L.sl[0])} · ▲ → ${esc(L.sl[4])}</span></div>
  </div>`;
}

function mapCard(D, S, X) {
  const L = D.L;
  const byName = {};
  D.districts.forEach((d, i) => { byName[d.n] = i; });
  const maxGap = Math.max(1, ...X.perDistrict.map((m) => m.u + m.su));
  const paths = D.geo.d.map((g) => {
    const di = byName[g.n];
    if (di === undefined) return { z: 0, html: `<path d="${g.d}" style="fill:#E5E5EA;stroke:#FFFFFF;stroke-width:1"></path>` };
    const m = X.perDistrict[di];
    const on = di === S.sel;
    const alpha = 22 + Math.round(34 * Math.sqrt((m.u + m.su) / maxGap));
    return { z: on ? 2 : 1, html: `<path class="pilot" data-dist="${di}" d="${g.d}" style="fill:${tint(toneOf(m), alpha)};stroke:${on ? "var(--accent)" : "#FFFFFF"};stroke-width:${on ? 2.5 : 1.2}"><title>${esc(g.n)}</title></path>` };
  }).sort((a, b) => a.z - b.z).map((p) => p.html).join("");
  const pins = D.districts.map((d, di) => {
    const m = X.perDistrict[di];
    const on = di === S.sel;
    const lines = [];
    if (m.sh) lines.push(`<span class="ln" style="color:${C[0]}">${m.sh} ${esc(L.sl[0])}</span>`);
    if (m.ov) lines.push(`<span class="ln" style="color:${C[4]}">${m.ov} ${esc(L.sl[4])}</span>`);
    if (!lines.length) lines.push(`<span class="ln" style="color:${C[2]}">${esc(L.sl[2])}</span>`);
    const dx = d.lx - d.cx, dy = d.ly - d.cy;
    const len = Math.hypot(dx, dy), ang = (Math.atan2(dy, dx) * 180) / Math.PI;
    const tf = d.side === "l" ? "translate(-100%,-50%)" : d.side === "b" ? "translate(-50%,0)" : "translate(0,-50%)";
    const ring = on ? "0 0 0 2px var(--accent), 0 4px 14px rgba(0,0,0,.16)" : "0 1px 2px rgba(0,0,0,.1), 0 4px 12px rgba(0,0,0,.08)";
    return `<div class="leader" style="left:${d.cx}px;top:${d.cy}px;width:${len.toFixed(1)}px;transform:rotate(${ang.toFixed(1)}deg)"></div>
      <div class="pin" style="left:${d.cx}px;top:${d.cy}px"></div>
      <button class="chip pick" data-dist="${di}" style="left:${d.lx}px;top:${d.ly}px;transform:${tf};box-shadow:${ring}">
        <span class="bar" style="background:${C[toneOf(m)]}"></span>
        <span class="body"><span class="line1"><b>${esc(d.n)}</b><span class="num">${m.r.toFixed(2)}</span></span>${lines.join("")}</span></button>`;
  }).join("");
  const keys = [[L.moreShort, tint(0, 44)], [L.moreOver, tint(4, 44)], [L.mixed, tint(1, 40)], [L.fl[2], tint(2, 40)], [L.notPilot, "#E5E5EA"]]
    .map(([lab, c]) => `<span class="key"><i style="background:${c}"></i>${esc(lab)}</span>`).join("");
  const R = X.T / X.J;
  const headline = statusOf(R) === 2 ? fill(L.head2, { r: R.toFixed(2), s: X.shortCount, o: X.overCount }) : fill(L.head, { s: X.shortCount, o: X.overCount });
  return `<section class="card section">
    <div class="section-head"><span class="section-title">${esc(L.map)}</span><span class="hint">${esc(L.clickHint)}</span></div>
    <div class="mapwrap">
      <div class="map"><svg viewBox="0 0 ${D.geo.w} ${D.geo.h}" width="${D.geo.w}" height="${D.geo.h}">${paths}</svg>
        <span class="sea">${esc(L.sea)}</span>${pins}</div>
      <div class="mapside">
        <div class="blk"><span class="h">${esc(L.mapRead)}</span>${keys}<span class="hint">${esc(L.darker)}</span></div>
        <div class="blk"><span class="h">${esc(L.insight)}</span><p class="insight">${esc(headline)}</p></div>
      </div>
    </div>
  </section>`;
}

function detailCard(D, S, X) {
  const L = D.L;
  const d = D.districts[S.sel];
  const rows = X.ks.map((k) => ({ ...D.pairs[S.sel][k], k }));
  const vmax = Math.max(1, ...rows.map((p) => Math.max(p.j, p.t)));
  let dj = 0, dt = 0;
  rows.forEach((p) => { dj += p.j; dt += p.t; });
  const dr = dt / dj, ds = statusOf(dr);
  const worstShort = rows.filter((p) => p.s <= 1).sort((a, b) => (b.j - b.t) - (a.j - a.t))[0];
  const worstOver = rows.filter((p) => p.s >= 3).sort((a, b) => (b.t - b.j) - (a.t - a.j))[0];
  const rec = [];
  if (worstShort) rec.push(`<div class="line" data-trade="${worstShort.k}"><span class="act" style="color:${C[0]}">▼ ${esc(L.add)}</span><span class="tr">${esc(D.trades[worstShort.k].n)}</span><span class="v num" style="color:${C[worstShort.s]}">+${fmt(worstShort.j - worstShort.t)} ${esc(L.unfilled)}</span></div>`);
  if (worstOver) rec.push(`<div class="line" data-trade="${worstOver.k}"><span class="act" style="color:${C[4]}">▲ ${esc(L.cut)}</span><span class="tr">${esc(D.trades[worstOver.k].n)}</span><span class="v num" style="color:${C[worstOver.s]}">−${fmt(worstOver.t - worstOver.j)} ${esc(L.surplusW)}</span></div>`);
  const body = rows.map((p) => `<div class="trow ${p.k === S.tr ? "on" : ""}" data-trade="${p.k}">
      <div class="tname"><span title="${esc(D.trades[p.k].n)}">${esc(D.trades[p.k].s)}</span><div class="minibar"><i class="j" style="width:${((p.j / vmax) * 100).toFixed(1)}%"></i><i class="t" style="width:${((p.t / vmax) * 100).toFixed(1)}%"></i></div></div>
      <span class="tcell num">${fmt(p.j)}</span><span class="tcell num">${fmt(p.t)}</span><span class="tcell b num">${p.r.toFixed(2)}</span>
      <span class="tstat" style="color:${C[p.s]}">■ ${esc(L.fl[p.s])}</span></div>`).join("");
  return `<section class="card detail">
    <div class="who"><div style="display:flex;flex-direction:column;gap:2px;min-width:0"><span class="name">${esc(d.n)}</span><span class="hint">${esc(d.note)} · ${esc(L.detail)}</span></div>
      <span class="pill" style="color:${C[ds]};background:${tint(ds, 13)}">■ ${esc(L.fl[ds])}</span></div>
    <div class="stats"><div><span class="k">${esc(L.jobs12)}</span><span class="v num">${fmt(dj)}</span></div><div><span class="k">${esc(L.trYr)}</span><span class="v num">${fmt(dt)}</span></div><div><span class="k">${esc(L.ratioW)}</span><span class="v num">${dr.toFixed(2)}</span></div></div>
    ${rec.length ? `<div class="rec"><span class="k">${esc(L.recFor)}</span>${rec.join("")}</div>` : ""}
    <div class="trow thead"><span>${esc(L.trade)}</span><span>${esc(L.jobs12)}</span><span>${esc(L.trYr)}</span><span>${esc(L.ratioW)}</span><span>${esc(L.status)}</span></div>
    <div class="tbody">${body}</div>
    <div class="foot"><button class="btn primary" data-open="explore">${esc(L.explore)}</button><button class="btn secondary" data-open="plan">${esc(L.planBtn)}</button>
      <span class="keys"><span><i style="width:12px;height:8px;background:var(--g200);border-radius:2px;display:inline-block"></i>${esc(L.jobsW)}</span><span><i style="width:12px;height:3px;background:var(--g800);border-radius:2px;display:inline-block"></i>${esc(L.trW)}</span></span></div>
  </section>`;
}

function matrixCard(D, S, X) {
  const L = D.L;
  const cols = `148px repeat(${X.ks.length}, minmax(0,1fr)) 108px`;
  const groups = S.sec === "all" ? [[L.elec, 5], [L.auto, 5]] : [[S.sec === "E" ? L.elec : L.auto, 5]];
  const legend = L.fl.map((lab, s) => `<span style="color:${C[s]}">■ ${esc(lab)} <em>${RANGES[s]}</em></span>`).join("");
  const head = `<div class="mgrid" style="grid-template-columns:${cols}"><div class="mrule"></div>${groups.map(([n, span]) => `<span class="mgroup" style="grid-column:span ${span}">${esc(n)}</span>`).join("")}<div class="mrule"></div>
    <div class="mhead"></div>${X.ks.map((k) => `<span class="mhead" title="${esc(D.trades[k].n)}">${esc(D.trades[k].s)}</span>`).join("")}<span class="mhead last">${esc(L.ratioW)}</span></div>`;
  const rows = D.districts.map((d, di) => {
    const on = di === S.sel;
    const m = X.perDistrict[di];
    const dsx = statusOf(m.r);
    const cells = X.ks.map((k) => {
      const p = D.pairs[di][k];
      const sel = on && k === S.tr;
      const bg = sel ? "var(--sel)" : p.s === 0 || p.s === 4 ? tint(p.s, 9) : p.s === 2 ? "transparent" : tint(p.s, 5);
      return `<button class="mcell" data-cell="${di},${k}" style="background:${bg};box-shadow:inset 0 0 0 1.5px ${sel ? "var(--accent)" : "transparent"}"><b class="num">${p.r.toFixed(2)}</b><em style="color:${C[p.s]}">■ ${esc(L.sl[p.s])}</em></button>`;
    }).join("");
    return `<div class="mrow ${on ? "on" : ""}" style="grid-template-columns:${cols}">
      <div class="mname" data-dist="${di}" style="font-weight:${on ? 700 : 500}"><i style="background:${on ? "var(--accent)" : "transparent"}"></i>${esc(d.n)}</div>${cells}
      <div class="mdist" data-dist="${di}"><b class="num">${m.r.toFixed(2)}</b><em style="color:${C[dsx]}">■ ${esc(L.sl[dsx])}</em></div></div>`;
  }).join("");
  return `<div class="wide"><section class="card matrix">
    <div class="section-head" style="flex-wrap:wrap"><div style="display:flex;flex-direction:column;gap:2px"><span class="section-title">${esc(L.matrix)}</span><span class="hint">${esc(L.explain)}</span></div><div class="mlegend">${legend}</div></div>
    <div>${head}${rows}</div></section></div>`;
}

function listsRow(D, X) {
  const L = D.L;
  const item = (p, value, label) => ({ p, value, label });
  const shorts = X.all.filter((p) => p.s === 0).sort((a, b) => (b.j - b.t) - (a.j - a.t)).slice(0, 5).map((p) => item(p, p.j - p.t, L.unfilled));
  const surs = X.all.filter((p) => p.s === 4).sort((a, b) => (b.t - b.j) - (a.t - a.j)).slice(0, 5).map((p) => item(p, p.t - p.j, L.surplusW));
  const render = (list) => {
    const max = Math.max(1, ...list.map((x) => x.value));
    return list.map(({ p, value, label }) => `<div class="item" data-cell="${p.di},${p.k}">
      <div class="top2"><div style="display:flex;flex-direction:column;gap:2px;min-width:0"><span class="t">${esc(D.trades[p.k].n)}</span><span class="s">${esc(D.districts[p.di].n)} · ${fmt(p.j)} ${esc(L.jobsW)} · ${fmt(p.t)} ${esc(L.trW)}</span></div>
      <span class="p num" style="color:${C[p.s]};background:${tint(p.s, 13)}">${fmt(value)} ${esc(label)}</span></div>
      <div class="track"><i style="background:${C[p.s]};width:${((value / max) * 100).toFixed(0)}%"></i></div></div>`).join("");
  };
  const warns = X.warns.slice(0, 5).map((w) => `<div class="item" data-cell="${w.di},${w.k}"><div class="top2">
      <div style="display:flex;flex-direction:column;gap:2px;min-width:0"><span class="t">${esc(D.trades[w.k].n)}</span><span class="s">${esc(D.districts[w.di].n)} · ${esc(L.now)} ${w.now.toFixed(2)} ${esc(L.fl[w.nowS])}</span></div>
      <div class="rt"><b>${esc(D.months[w.mi])}</b><span class="p" style="color:${C[w.to]};background:${tint(w.to, 13)}">→ ${esc(L.fl[w.to])}</span></div></div></div>`).join("");
  return `<div class="lists">
    <section class="card list"><div class="lh"><span class="section-title">${esc(L.short)}</span><button class="btn ghost" data-open="plan" data-tab="moves">${esc(L.viewAll)}</button></div>${render(shorts)}</section>
    <section class="card list"><div class="lh"><span class="section-title">${esc(L.sur)}</span><button class="btn ghost" data-open="plan" data-tab="moves">${esc(L.viewAll)}</button></div>${render(surs)}</section>
    <section class="card list"><div class="lh"><span class="section-title">${esc(L.warn)}</span><button class="btn ghost" data-open="plan" data-tab="warnings">${esc(L.viewAll)} · ${X.warns.length}</button></div>${warns}</section>
  </div>`;
}

function footer(D) {
  const L = D.L;
  return `<footer><span><b>${esc(L.sources)}</b> · ${esc(L.signals)}</span><span><b>${esc(L.accuracy)}</b> · ${D.accuracy.model.toFixed(0)}% (${esc(L.baseline)}: ${D.accuracy.naive.toFixed(0)}%)</span><span class="end">${esc(L.boundaries)}</span></footer>`;
}

function exportCsv(D, X) {
  const lines = [["district", "trade", "sector", "jobs_12m", "trainees_per_year", "gap_ratio", "status"].join(",")];
  X.all.forEach((p) => lines.push([D.districts[p.di].n, `"${D.trades[p.k].n}"`, D.trades[p.k].sec === "E" ? "Electrical and Power" : "Automotive", Math.round(p.j), Math.round(p.t), p.r.toFixed(3), D.statusNames[p.s]].join(",")));
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "pramaan_skill_gap.csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let root = parentElement.querySelector(".pramaan-dash");
  if (!root) {
    root = document.createElement("div");
    root.className = "pramaan-dash";
    parentElement.appendChild(root);
  }
  if (!root.__state || root.__stamp !== data.stamp) {
    root.__state = { sel: data.start.sel, tr: data.start.tr, sec: data.start.sec };
    root.__stamp = data.stamp;
  }
  const S = root.__state;

  const render = () => {
    const X = compute(data, S);
    if (!X.ks.includes(S.tr)) S.tr = X.ks[0];
    root.innerHTML = topBar(data, S)
      + `<div class="grid">${kpis(data, X)}${mapCard(data, S, X)}${detailCard(data, S, X)}</div>`
      + matrixCard(data, S, X) + listsRow(data, X) + footer(data);
    root.__x = X;
  };

  root.onclick = (event) => {
    const target = event.target.closest("[data-sec],[data-dist],[data-cell],[data-trade],[data-open],[data-act]");
    if (!target || !root.contains(target)) return;
    const ds = target.dataset;
    if (ds.sec) { S.sec = ds.sec; render(); return; }
    if (ds.act === "export") { exportCsv(data, root.__x); return; }
    if (ds.open) {
      setTriggerValue("open", { page: ds.open, tab: ds.tab || "", district: data.districts[S.sel].n, trade: data.trades[S.tr].n, sector: S.sec });
      return;
    }
    if (ds.cell) { const [di, k] = ds.cell.split(",").map(Number); S.sel = di; S.tr = k; render(); return; }
    if (ds.dist !== undefined) { S.sel = Number(ds.dist); render(); return; }
    if (ds.trade !== undefined) { S.tr = Number(ds.trade); render(); }
  };
  render();
}
