import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { scopeName, scopeOf, useAuth } from "../auth";
import { STATUS, fmt, monthName, perTen, statusOf, useData, usePick, type Move } from "../data";
import { msg, tn, useLang, useT } from "../i18n";
import { Glyph, MISC } from "../ui/Icons";
import { Button, Download, Mark, TradeIcon } from "../ui/parts";

const LEVEL = [msg("far too few"), msg("a bit too few"), msg("about right"), msg("a bit too many"), msg("far too many")];

function Cable({ seats }: { seats: number }) {
  useT();
  return (
    <div className="cable" aria-hidden="true">
      <svg viewBox="0 0 220 70" preserveAspectRatio="none">
        <path className="cable-base" d="M4 14 C 70 70, 150 70, 216 14" />
        <path className="cable-flow" d="M4 14 C 70 70, 150 70, 216 14" />
        <circle cx="4" cy="14" r="4" className="cable-end from" />
        <circle cx="216" cy="14" r="4" className="cable-end to" />
      </svg>
      <span className="cable-label">{tn("{count} seats", { count: <b className="num">{fmt(seats)}</b> })}</span>
    </div>
  );
}

function Change({ before, after }: { before: number; after: number }) {
  const t = useT();
  const a = statusOf(before), b = statusOf(after);
  return (
    <span className="change">
      <span style={{ color: STATUS[a].color }}>{t(LEVEL[a])}</span>
      <span className="change-arrow">{MISC.arrow}</span>
      <span style={{ color: STATUS[b].color, fontWeight: 600 }}>{t(LEVEL[b])}</span>
    </span>
  );
}

export default function Plan() {
  const t = useT();
  const lang = useLang();
  const data = useData();
  const [, setPick] = usePick();
  const go = useNavigate();
  const { user } = useAuth();
  const scope = scopeOf(user, data);
  const scoped = scope.district !== null || scope.sector !== null;
  const [mine, setMine] = useState(true);
  const [anyField, setAnyField] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const all = useMemo(() => {
    const base = anyField ? data.moves.any : data.moves.same;
    if (!scoped || !mine) return base;
    return base.filter((m) => scope.district !== null
      ? m.from[0] === scope.district || m.to[0] === scope.district
      : data.trades[m.from[1]].sector === scope.sector || data.trades[m.to[1]].sector === scope.sector);
  }, [anyField, data, scoped, mine, scope.district, scope.sector]);
  const total = all.reduce((a, m) => a + m.seats, 0);
  const [budget, setBudget] = useState<number | null>(null);
  const limit = Math.min(budget ?? total, total);

  const moves = useMemo(() => {
    const out: Move[] = [];
    let left = limit;
    for (const m of all) {
      if (left <= 0) break;
      const seats = Math.min(m.seats, Math.floor(left / 10) * 10);
      if (seats <= 0) break;
      out.push({ ...m, seats });
      left -= seats;
    }
    return out;
  }, [all, limit]);

  const summary = useMemo(() => {
    const seats = data.pairs.map((row) => row.map((p) => p.seats));
    moves.forEach((m) => { seats[m.from[0]][m.from[1]] -= m.seats; seats[m.to[0]][m.to[1]] += m.seats; });
    const totals = { unfilledBefore: 0, unfilledAfter: 0, extraBefore: 0, extraAfter: 0 };
    data.pairs.forEach((row, d) => row.forEach((p, k) => {
      const after = seats[d][k] * (p.trainees / p.seats);
      totals.unfilledBefore += Math.max(0, p.jobs - p.trainees);
      totals.unfilledAfter += Math.max(0, p.jobs - after);
      totals.extraBefore += Math.max(0, p.trainees - p.jobs);
      totals.extraAfter += Math.max(0, after - p.jobs);
    }));
    return totals;
  }, [data, moves]);

  const growth = data.trades.map((x, k) => {
    const jobs = data.pairs.reduce((a, row) => a + row[k].jobs, 0);
    const last = data.pairs.reduce((a, row) => a + row[k].last, 0);
    const trainees = data.pairs.reduce((a, row) => a + row[k].trainees, 0);
    return { k, x, growth: jobs / last - 1, ratio: trainees / jobs };
  }).sort((a, b) => b.growth - a.growth);
  const maxGrowth = Math.max(...growth.map((g) => Math.abs(g.growth)));
  const months = data.futureMonths.slice(0, 6);
  const open = (d: number, k: number) => { setPick({ district: d, trade: k }); go("/explore"); };
  const visible = showAll ? moves : moves.slice(0, 5);
  const fixedJobs = summary.unfilledBefore - summary.unfilledAfter;
  const fixedPeople = summary.extraBefore - summary.extraAfter;

  /* The two clearest examples in this state: the most crowded course and the most short one. */
  const pairs = data.pairs.flatMap((row, d) => row.map((p, k) => ({ d, k, p })));
  const crowded = pairs.reduce((a, b) => (b.p.ratio > a.p.ratio ? b : a));
  const short = pairs.reduce((a, b) => (b.p.ratio < a.p.ratio ? b : a));
  const many = Math.round(crowded.p.ratio * 10), few = Math.round(short.p.ratio * 10);
  /* English needs lower case for a trade inside a sentence; other languages keep the name as written. */
  const inline = (name: string) => { const s = t(name); return lang === "en" && !/^[A-Z]{2}/.test(s) ? s.charAt(0).toLowerCase() + s.slice(1) : s; };
  const csv = new URLSearchParams({ state: data.state, mode: anyField ? "any" : "same", budget: String(limit) });
  if (scoped && mine && scope.district !== null) csv.set("district", data.districts[scope.district].name);
  if (scoped && mine && scope.sector) csv.set("sector", scope.sector);

  return (
    <div className="stack" style={{ gap: 24 }}>
      <div>
        <h1 className="h1">{t("Move seats to where the jobs are")}</h1>
        <p className="lede">{t("Some courses train more people than there are jobs. Others do not train enough. Pramaan suggests moving seats from the first kind to the second, so the same number of seats does more good.")}</p>
      </div>

      <section className="how" data-reveal>
        {[
          { icon: "up", tone: 4, title: t("Too many trainees"), text: t("{trade} courses in {district} train {n} people for every 10 jobs. About {extra} of them may not find work.", { trade: t(data.trades[crowded.k].name), district: t(data.districts[crowded.d].name), n: many, extra: Math.max(0, many - 10) }) },
          { icon: "down", tone: 0, title: t("Too few trainees"), text: t("{trade} courses in {district} train only {n} people for every 10 jobs. {gap} jobs stay empty.", { trade: t(data.trades[short.k].name), district: t(data.districts[short.d].name), n: few, gap: Math.max(0, 10 - few) }) },
          { icon: "plan", tone: 2, title: t("Move the seats"), text: t("Shift seats from the first course to the second. No new money and no new buildings. The total stays the same.") },
        ].map((s) => (
          <div key={s.icon} className="how-step">
            <span className="how-icon" style={{ background: STATUS[s.tone].bg }}><Glyph name={s.icon} tone={{ ink: STATUS[s.tone].hex, tile: "transparent" }} /></span>
            <div><h3 className="h3">{s.title}</h3><p>{s.text}</p></div>
          </div>
        ))}
      </section>

      <section className="panel" data-reveal>
        <div className="impact">
          <div>
            <p className="label" style={{ margin: 0 }}>{t("If you make the moves below")}</p>
            <p className="impact-line">{tn("{jobs} get a trained person, and {people} are left without work.", {
              jobs: <b className="num" style={{ color: STATUS[2].color }}>{t("{count} more jobs", { count: fmt(fixedJobs) })}</b>,
              people: <b className="num" style={{ color: STATUS[2].color }}>{t("{count} fewer trainees", { count: fmt(fixedPeople) })}</b>,
            })}</p>
            <p className="small" style={{ margin: "6px 0 0" }}>{t("Jobs left empty: {a} today, {b} after. Trainees without work: {c} today, {d} after.", { a: fmt(summary.unfilledBefore), b: fmt(summary.unfilledAfter), c: fmt(summary.extraBefore), d: fmt(summary.extraAfter) })}</p>
          </div>
          <div className="impact-controls">
            {scoped ? (
              <div className="segment" role="group" aria-label={t("Whose seat changes to show")}>
                <button className={mine ? "on mine" : "mine"} onClick={() => { setMine(true); setBudget(null); }}>{t("For {place}", { place: user ? scopeName(user) : "" })}</button>
                <button className={!mine ? "on" : ""} onClick={() => { setMine(false); setBudget(null); }}>{t("All of {state}", { state: t(data.state) })}</button>
              </div>
            ) : null}
            <div className="slider-row">
              <label htmlFor="budget">{t("How many seats can you move?")}</label><output className="num">{fmt(limit)}</output>
              <input id="budget" className="slider" type="range" min={0} max={total} step={10} value={limit} onChange={(e) => setBudget(Number(e.target.value))} style={{ gridColumn: "1 / -1" }} />
            </div>
            <div className="segment" role="group" aria-label={t("Which courses can swap seats")}>
              <button className={!anyField ? "on" : ""} onClick={() => { setAnyField(false); setBudget(null); }}>{t("Similar courses only")}</button>
              <button className={anyField ? "on" : ""} onClick={() => { setAnyField(true); setBudget(null); }}>{t("Any course")}</button>
            </div>
          </div>
        </div>
      </section>

      <section className="stack" style={{ gap: 14 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 className="h2">{t("What to change, biggest first")}</h2>
          <div className="row" style={{ gap: 14 }}>
            <span className="small">{t("{count} changes, {seats} seats", { count: moves.length, seats: fmt(moves.reduce((a, m) => a + m.seats, 0)) })}</span>
            {moves.length ? <Download href={`/api/export/moves.csv?${csv}`}>{t("Download this plan")}</Download> : null}
          </div>
        </div>
        {moves.length === 0 ? <div className="panel">{t("Slide \"How many seats can you move?\" to the right to see the changes.")}</div> : null}
        {visible.map((m, i) => {
          const fromTrade = data.trades[m.from[1]].name, toTrade = data.trades[m.to[1]].name;
          const fromPlace = t(data.districts[m.from[0]].name), toPlace = t(data.districts[m.to[0]].name);
          const same = m.from[0] === m.to[0];
          return (
            <article key={i} className="swap" data-reveal>
              <p className="swap-title">
                {same
                  ? tn("In {place}, move {seats} from {from} courses to {to} courses.", { place: <b>{fromPlace}</b>, seats: <b className="num">{t("{count} seats", { count: fmt(m.seats) })}</b>, from: inline(fromTrade), to: <b>{inline(toTrade)}</b> })
                  : tn("Move {seats} from {from} courses in {fromPlace} to {to} courses in {toPlace}.", { seats: <b className="num">{t("{count} seats", { count: fmt(m.seats) })}</b>, from: inline(fromTrade), fromPlace: <b>{fromPlace}</b>, to: inline(toTrade), toPlace: <b>{toPlace}</b> })}
              </p>
              <div className="swap-body">
                <button className="swap-side" onClick={() => open(m.from[0], m.from[1])}>
                  <span className="swap-tag">{t("Take seats from")}</span>
                  <span className="swap-who"><TradeIcon icon={data.trades[m.from[1]].icon} status={statusOf(m.fromBefore)} /><span><b>{t(fromTrade)}</b><small>{fromPlace}</small></span></span>
                  <Change before={m.fromBefore} after={m.fromAfter} />
                  <span className="small">{t("{before} trainees per 10 jobs today, {after} after", { before: perTen(m.fromBefore), after: perTen(m.fromAfter) })}</span>
                </button>
                <Cable seats={m.seats} />
                <button className="swap-side" onClick={() => open(m.to[0], m.to[1])}>
                  <span className="swap-tag">{t("Give seats to")}</span>
                  <span className="swap-who"><TradeIcon icon={data.trades[m.to[1]].icon} status={statusOf(m.toBefore)} /><span><b>{t(toTrade)}</b><small>{toPlace}</small></span></span>
                  <Change before={m.toBefore} after={m.toAfter} />
                  <span className="small">{t("{before} trainees per 10 jobs today, {after} after", { before: perTen(m.toBefore), after: perTen(m.toAfter) })}</span>
                </button>
              </div>
            </article>
          );
        })}
        {moves.length > 5 ? (
          <div><Button kind="quiet" icon={showAll ? "up" : "down"} onClick={() => setShowAll(!showAll)}>{showAll ? t("Show fewer") : t("Show all {count} changes", { count: moves.length })}</Button></div>
        ) : null}
      </section>

      <div className="two">
        <section className="panel" data-reveal>
          <div className="panel-head"><div><h2 className="h2">{t("Fastest growing jobs")}</h2><p>{t("Plan new seats and centres for these first.")}</p></div></div>
          {growth.map((g) => (
            <div key={g.k} className="li" style={{ gridTemplateColumns: "32px minmax(0,1fr) 140px auto" }}>
              <TradeIcon icon={g.x.icon} status={statusOf(g.ratio)} />
              <div><div className="t">{t(g.x.name)}</div><div className="s">{t("{n} trainees per 10 jobs", { n: perTen(g.ratio) })}</div></div>
              <div className="meter"><i style={{ width: `${(Math.abs(g.growth) / maxGrowth) * 100}%`, background: g.growth >= 0 ? "var(--accent)" : "#C3C8D6" }} /></div>
              <div className="v num" style={{ color: g.growth >= 0 ? "var(--accent)" : "var(--ink-3)" }}>{g.growth > 0 ? "+" : ""}{Math.round(g.growth * 100)}%</div>
            </div>
          ))}
        </section>

        <section className="panel" data-reveal>
          <div className="panel-head"><div><h2 className="h2">{t("Changing soon")}</h2><p>{t("These will tip into trouble in the next six months unless seats change.")}</p></div></div>
          <div className="stack" style={{ gap: 12 }}>
            {months.map((month) => {
              const items = data.warnings.filter((w) => w.month === month);
              if (!items.length) return null;
              return (
                <div key={month} style={{ display: "grid", gridTemplateColumns: "96px minmax(0,1fr)", gap: 12 }}>
                  <div style={{ fontWeight: 600 }}>{monthName(month)}</div>
                  <div className="stack" style={{ gap: 6 }}>
                    {items.map((w) => (
                      <div key={`${w.district}-${w.trade}`} className="row" role="button" tabIndex={0} onClick={() => open(w.district, w.trade)} style={{ cursor: "pointer", justifyContent: "space-between", padding: "6px 10px", borderRadius: 10, background: "#F6F7F9" }}>
                        <span>{t("{trade}, {district}", { trade: t(data.trades[w.trade].name), district: t(data.districts[w.district].name) })}</span>
                        <Mark status={w.next} short />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
