import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { usePlace, useUser } from "../auth";
import { SECTORS, STATUS, fmt, perTen, statusOf, useNational, usePick, type National, type SectorKey } from "../data";
import { tn, useT } from "../i18n";
import { TRADE_ICONS } from "../ui/Icons";
import { Button, Download, JobsStrip, Loader, Mark, TradeIcon } from "../ui/parts";

type Pair = National["pairs"][number];

export default function India() {
  const t = useT();
  const user = useUser();
  const [place, setPlace] = usePlace();
  const [, setPick] = usePick();
  const go = useNavigate();
  const { national, error } = useNational();
  const [sector, setSector] = useState<SectorKey>(user.scope.sector ?? "all");
  const [side, setSide] = useState<"short" | "many">("short");
  const [showAll, setShowAll] = useState(false);
  if (error) return <div className="panel">{t("Pramaan could not load the national summary. Details: {error}", { error })}</div>;
  if (!national) return <Loader />;

  const inField = (k: number) => sector === "all" || national.trades[k].sector === sector;
  const totals = (state: string) => {
    const s = national.states.find((x) => x.name === state)!;
    return sector === "all" ? s : { ...s, ...s.sectors[sector] };
  };
  const all = national.states.map((s) => totals(s.name));
  const unfilled = all.reduce((a, s) => a + s.unfilled, 0), extra = all.reduce((a, s) => a + s.extra, 0);
  const max = Math.max(...all.flatMap((s) => [s.unfilled, s.extra]));
  const pairs = national.pairs.filter((p) => inField(p.trade));
  const ranked = [...pairs].sort((a, b) => side === "short" ? (b.jobs - b.trainees) - (a.jobs - a.trainees) : (b.trainees - b.jobs) - (a.trainees - a.jobs))
    .filter((p) => (side === "short" ? p.jobs > p.trainees : p.trainees > p.jobs));
  const shown = showAll ? ranked : ranked.slice(0, 10);

  /* Opening a pair in another state: remember the pick for that state, then switch to it. */
  const openState = (state: string) => { setPlace(state); go("/dashboard"); };
  const openPair = (p: Pair) => {
    const districts = [...new Set(national.pairs.filter((x) => x.state === p.state).map((x) => x.district))];
    const pick = { district: districts.indexOf(p.district), trade: p.trade, sector: "all" as SectorKey };
    if (p.state === place) setPick(pick);
    else {
      try { sessionStorage.setItem("pramaan-pick", JSON.stringify({ ...pick, owner: `${user.id}:${p.state}` })); } catch { /* storage blocked */ }
      setPlace(p.state);
    }
    go("/explore");
  };
  const worst = (state: string, how: "short" | "many") => pairs.filter((p) => p.state === state)
    .sort((a, b) => how === "short" ? (b.jobs - b.trainees) - (a.jobs - a.trainees) : (b.trainees - b.jobs) - (a.trainees - a.jobs))[0];

  return (
    <div className="stack" style={{ gap: 24 }}>
      <section className="night" data-reveal>
        <div className="night-grid">
          <div>
            <p className="label" style={{ color: "#8E99AC", margin: "0 0 12px" }}>{t("All India: the next 12 months")}</p>
            <h1 className="display">
              {tn("{jobs} may go unfilled across {count} pilot states, while {people} may not find work.", {
                jobs: <span className="hi-red">{t("{count} jobs", { count: fmt(unfilled) })}</span>,
                count: national.states.length,
                people: <span className="hi-violet">{t("{count} trainees", { count: fmt(extra) })}</span>,
              })}
            </h1>
            <p className="lede">{t("Pick a state to see its districts. More states join as their job and training data is connected.")}</p>
            <div className="row" style={{ marginTop: 22 }}>
              <div className="segment" role="group" aria-label={t("Choose a field")}>
                {(Object.keys(SECTORS) as SectorKey[]).map((key) => (
                  <button key={key} className={`${sector === key ? "on" : ""} ${user.scope.sector === key ? "mine" : ""}`} onClick={() => setSector(key)}>{t(SECTORS[key])}</button>
                ))}
              </div>
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingBottom: 6 }}>
            <div style={{ display: "grid", gridTemplateColumns: "150px 1fr 1fr", fontSize: 12.5, color: "#8E99AC" }}>
              <span>{t("State")}</span><span style={{ textAlign: "right", paddingRight: 6 }}>{t("Jobs unfilled")}</span><span style={{ paddingLeft: 6 }}>{t("Extra trainees")}</span>
            </div>
            {all.map((s) => (
              <div key={s.name} className="balance-row">
                <span>{t(s.name)}</span>
                <div className="bal-left"><span className="num">{fmt(s.unfilled)}</span><i style={{ width: `${(s.unfilled / max) * 100}%` }} /></div>
                <div className="bal-right"><i style={{ width: `${(s.extra / max) * 100}%` }} /><span className="num">{fmt(s.extra)}</span></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="two">
        {national.states.map((s) => {
          const v = totals(s.name);
          const ratio = v.trainees / v.jobs;
          const short = worst(s.name, "short"), many = worst(s.name, "many");
          return (
            <article key={s.name} className="panel state-card" data-reveal>
              <div className="panel-head">
                <div><h2 className="h1" style={{ fontSize: 30 }}>{t(s.name)}</h2><p>{t("{count} pilot districts, data to {month}", { count: s.districts, month: s.updated })}</p></div>
                <Mark status={statusOf(ratio)} boxed />
              </div>
              <JobsStrip ratio={ratio} status={statusOf(ratio)} />
              <div className="ledger" style={{ gridTemplateColumns: "repeat(3, minmax(0,1fr))", marginTop: 16 }}>
                <div><span className="label">{t("Jobs next year")}</span><span className="figure num">{fmt(v.jobs)}</span></div>
                <div><span className="label">{t("Trainees for every 10 jobs")}</span><span className="figure num" style={{ color: STATUS[statusOf(ratio)].color }}>{perTen(ratio)}</span></div>
                <div><span className="label">{t("Changing in 6 months")}</span><span className="figure num" style={{ color: "var(--s1)" }}>{s.warnings}</span></div>
              </div>
              <div className="stack" style={{ gap: 8, marginTop: 16 }}>
                {short ? (
                  <button className="case" onClick={() => openPair(short)}>
                    <TradeIcon icon={national.trades[short.trade].icon} status={short.status} />
                    <span className="case-body"><span className="small">{t("Biggest shortage")}</span><span className="case-title">{t("{trade} in {district}", { trade: t(national.trades[short.trade].name), district: t(short.district) })}</span><span className="small" style={{ color: STATUS[0].color }}>{t("{count} jobs may go unfilled", { count: fmt(short.jobs - short.trainees) })}</span></span>
                  </button>
                ) : null}
                {many ? (
                  <button className="case" onClick={() => openPair(many)}>
                    <TradeIcon icon={national.trades[many.trade].icon} status={many.status} />
                    <span className="case-body"><span className="small">{t("Most crowded")}</span><span className="case-title">{t("{trade} in {district}", { trade: t(national.trades[many.trade].name), district: t(many.district) })}</span><span className="small" style={{ color: STATUS[4].color }}>{t("{count} trainees may not find work", { count: fmt(many.trainees - many.jobs) })}</span></span>
                  </button>
                ) : null}
              </div>
              <div className="row" style={{ marginTop: 18 }}>
                <Button icon="map" onClick={() => openState(s.name)}>{t("Open {state}", { state: t(s.name) })}</Button>
                <Download href={`/api/export/gaps.csv?state=${encodeURIComponent(s.name)}&sector=${sector}`}>{t("Download")}</Download>
              </div>
            </article>
          );
        })}
      </div>

      <section className="panel" data-reveal>
        <div className="panel-head">
          <div><h2 className="h2">{t("Every trade, state by state")}</h2><p>{t("Trainees for every 10 jobs in each state. Click a state's column to open it.")}</p></div>
          <Download href={`/api/export/gaps.csv?state=all&sector=${sector}`}>{t("Download all states")}</Download>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="matrix compare">
            <thead><tr><th />{national.states.map((s) => <th key={s.name}><button className="link" onClick={() => openState(s.name)}>{t(s.name)}</button></th>)}<th>{t("All pilot states")}</th></tr></thead>
            <tbody>
              {national.trades.map((tr, k) => {
                if (!inField(k)) return null;
                const cells = national.states.map((s) => s.trades[k]);
                const sum = cells.reduce((a, c) => ({ jobs: a.jobs + c.jobs, trainees: a.trainees + c.trainees }), { jobs: 0, trainees: 0 });
                return (
                  <tr key={tr.name}>
                    <th className="dn" scope="row">{TRADE_ICONS[tr.icon]}{t(tr.name)}</th>
                    {[...cells, sum].map((c, i) => {
                      const r = c.trainees / c.jobs, st = statusOf(r), strong = st === 0 || st === 4;
                      return <td key={i}><span className="cell num" style={{ background: strong ? STATUS[st].hex : STATUS[st].bg, color: strong ? "#FFFFFF" : STATUS[st].color }}>{perTen(r)}</span></td>;
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel" data-reveal>
        <div className="panel-head">
          <div><h2 className="h2">{t("The worst gaps in the country, ranked")}</h2><p>{t("Every district and trade in the pilot, worst first. Use this to set next year's training targets.")}</p></div>
          <div className="segment" role="group" aria-label={t("Which gaps to rank")}>
            <button className={side === "short" ? "on" : ""} onClick={() => { setSide("short"); setShowAll(false); }}>{t("Too few trainees")}</button>
            <button className={side === "many" ? "on" : ""} onClick={() => { setSide("many"); setShowAll(false); }}>{t("Too many trainees")}</button>
          </div>
        </div>
        <ol className="rank">
          {shown.map((p, i) => (
            <li key={`${p.state}-${p.district}-${p.trade}`}>
              <button onClick={() => openPair(p)}>
                <span className="rank-no num">{i + 1}</span>
                <TradeIcon icon={national.trades[p.trade].icon} status={p.status} />
                <span className="rank-name"><b>{t(national.trades[p.trade].name)}</b><small>{t("{district}, {state}", { district: t(p.district), state: t(p.state) })}</small></span>
                <span className="rank-ratio num" style={{ color: STATUS[p.status].color }}>{t("{n} per 10 jobs", { n: perTen(p.ratio) })}</span>
                <span className="rank-gap num" style={{ color: side === "short" ? STATUS[0].color : STATUS[4].color }}>{fmt(Math.abs(p.jobs - p.trainees))}<small>{t(side === "short" ? "jobs unfilled" : "without a job")}</small></span>
              </button>
            </li>
          ))}
        </ol>
        {ranked.length > 10 ? <div style={{ marginTop: 12 }}><Button kind="quiet" icon={showAll ? "up" : "down"} onClick={() => setShowAll(!showAll)}>{showAll ? t("Show fewer") : t("Show all {count}", { count: ranked.length })}</Button></div> : null}
      </section>

      <p className="small">{t("Pramaan is built so any state can join. Each new state needs its job signals and training seat data connected; the forecasts, warnings and seat plans then work the same way.")}</p>
    </div>
  );
}
