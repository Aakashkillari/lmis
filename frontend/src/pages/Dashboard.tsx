import { useNavigate } from "react-router-dom";
import { scopeOf, useAuth } from "../auth";
import { BAND_WORDS, SECTORS, STATUS, districtTotals, fmt, monthName, perTen, sectorTrades, statusOf, useData, usePick, type SectorKey } from "../data";
import { tn, useT } from "../i18n";
import { TRADE_ICONS } from "../ui/Icons";
import { Button, Download, JobsStrip, Mark, Spark, StripCaption, TradeIcon } from "../ui/parts";
import { TNMap } from "../ui/TNMap";

function FieldBalance({ label, unfilled, extra, max }: { label: string; unfilled: number; extra: number; max: number }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "150px 1fr 1fr", alignItems: "center", gap: 0 }}>
      <span style={{ fontSize: 14, color: "#C9D1DE", fontWeight: 500 }}>{label}</span>
      <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 8, paddingRight: 6, borderRight: "1px solid rgba(255,255,255,.25)" }}>
        <span className="num" style={{ fontSize: 13, color: "#FF8A73", fontWeight: 600 }}>{fmt(unfilled)}</span>
        <div style={{ height: 14, width: `${(unfilled / max) * 100}%`, background: "#E5543D", borderRadius: "4px 0 0 4px", minWidth: 2 }} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 6 }}>
        <div style={{ height: 14, width: `${(extra / max) * 100}%`, background: "#8C70E0", borderRadius: "0 4px 4px 0", minWidth: 2 }} />
        <span className="num" style={{ fontSize: 13, color: "#B9A6FF", fontWeight: 600 }}>{fmt(extra)}</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const t = useT();
  const data = useData();
  const [pick, setPick] = usePick();
  const { user } = useAuth();
  const scope = scopeOf(user, data);
  const go = useNavigate();
  const trades = sectorTrades(data, pick.sector);
  const all = data.districts.flatMap((_, d) => trades.map((k) => ({ d, k, p: data.pairs[d][k] })));
  const sum = (f: (x: (typeof all)[number]) => number) => all.reduce((a, x) => a + f(x), 0);
  const jobs = sum((x) => x.p.jobs), trainees = sum((x) => x.p.trainees);
  const unfilled = sum((x) => Math.max(0, x.p.jobs - x.p.trainees)), extra = sum((x) => Math.max(0, x.p.trainees - x.p.jobs));
  const fields = (["power", "auto"] as const).map((f) => {
    const list = data.districts.flatMap((_, d) => sectorTrades(data, f).map((k) => data.pairs[d][k]));
    return { f, unfilled: list.reduce((a, p) => a + Math.max(0, p.jobs - p.trainees), 0), extra: list.reduce((a, p) => a + Math.max(0, p.trainees - p.jobs), 0) };
  });
  const fieldMax = Math.max(...fields.flatMap((x) => [x.unfilled, x.extra]));
  const district = data.districts[pick.district];
  const totals = districtTotals(data, pick.district, trades);
  const rows = trades.map((k) => ({ k, p: data.pairs[pick.district][k] })).sort((a, b) => (b.p.jobs - b.p.trainees) - (a.p.jobs - a.p.trainees));
  const needed = all.filter((x) => x.p.status <= 1).sort((a, b) => (b.p.jobs - b.p.trainees) - (a.p.jobs - a.p.trainees)).slice(0, 5);
  const crowded = all.filter((x) => x.p.status >= 3).sort((a, b) => (b.p.trainees - b.p.jobs) - (a.p.trainees - a.p.jobs)).slice(0, 5);
  const soon = data.warnings.filter((w) => trades.includes(w.trade));
  const shortPlaces = all.filter((x) => x.p.status === 0).length;
  const open = (d: number, k: number) => { setPick({ district: d, trade: k }); go("/explore"); };
  const ratioAll = trainees / jobs;
  const query = `state=${encodeURIComponent(data.state)}&sector=${pick.sector}`;

  return (
    <div className="stack" style={{ gap: 24 }}>
      <section className="night" data-reveal>
        <div className="night-grid">
          <div>
            <p className="label" style={{ color: "#8E99AC", margin: "0 0 12px" }}>{t("{state}: the next 12 months", { state: t(data.state) })}</p>
            <h1 className="display">
              {tn("{jobs} may go unfilled while {people} may not find work.", {
                jobs: <span className="hi-red">{t("{count} jobs", { count: fmt(unfilled) })}</span>,
                people: <span className="hi-violet">{t("{count} trainees", { count: fmt(extra) })}</span>,
              })}
            </h1>
            <p className="lede">{t("Across the state the numbers almost balance. The problem is where the seats are: {count} district and trade pairs have too few trainees.", { count: shortPlaces })}</p>
            <div className="row" style={{ marginTop: 22 }}>
              <div className="segment" role="group" aria-label={t("Choose a field")}>
                {(Object.keys(SECTORS) as SectorKey[]).map((key) => (
                  <button key={key} className={`${pick.sector === key ? "on" : ""} ${scope.sector === key ? "mine" : ""}`} title={scope.sector === key ? t("Your field") : undefined} onClick={() => setPick({ sector: key })}>{t(SECTORS[key])}</button>
                ))}
              </div>
              <Button kind="quiet" icon="plan" onClick={() => go("/plan")}>{t("See the seat plan")}</Button>
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingBottom: 6 }}>
            <div style={{ display: "grid", gridTemplateColumns: "150px 1fr 1fr", fontSize: 12.5, color: "#8E99AC" }}>
              <span>{t("Field")}</span><span style={{ textAlign: "right", paddingRight: 6 }}>{t("Jobs unfilled")}</span><span style={{ paddingLeft: 6 }}>{t("Extra trainees")}</span>
            </div>
            {fields.map((x) => <FieldBalance key={x.f} label={t(SECTORS[x.f])} unfilled={x.unfilled} extra={x.extra} max={fieldMax} />)}
          </div>
        </div>
      </section>

      <section className="ledger" data-reveal>
        <div className="lead"><span className="label">{t("Jobs coming next year")}</span><span className="figure num">{fmt(jobs)}</span><span className="help">{t("{districts} districts, {trades} trades", { districts: data.districts.length, trades: trades.length })}</span></div>
        <div><span className="label">{t("Trainees ready each year")}</span><span className="figure num">{fmt(trainees)}</span><span className="help">{t("People who finish and pass")}</span></div>
        <div><span className="label">{t("Trainees for every 10 jobs")}</span><span className="figure num" style={{ color: STATUS[statusOf(ratioAll)].color }}>{perTen(ratioAll)}</span><span className="help">{t("Statewide average")}</span></div>
        <div><span className="label">{t("Changing in 6 months")}</span><span className="figure num" style={{ color: "var(--s1)" }}>{soon.length}</span><span className="help">{t("Trades about to tip over")}</span></div>
      </section>

      <div className="mapgrid">
        <section className="panel" data-reveal>
          <div className="panel-head"><div><h2 className="h2">{t("Where the mismatch is")}</h2><p>{t("Click a district. Darker means a bigger mismatch.")}</p></div></div>
          <TNMap data={data} trades={trades} selected={pick.district} onPick={(d) => setPick({ district: d })} home={scope.district} />
          <div className="keyrow" style={{ marginTop: 10 }}>
            <span><i style={{ background: STATUS[0].hex }} />{t("Mostly too few trainees")}</span>
            <span><i style={{ background: STATUS[4].hex }} />{t("Mostly too many")}</span>
            <span><i style={{ background: STATUS[2].hex }} />{t("Well matched")}</span>
            <span><i style={{ background: "#DFE3EA" }} />{t("Not in pilot yet")}</span>
            {scope.district !== null ? <span><i className="gold" />{t("Your district")}</span> : null}
          </div>
        </section>

        <section className="panel" data-reveal>
          <div className="panel-head">
            <div>
              <h2 className="h1" style={{ fontSize: 30 }}>{t(district.name)}</h2>
              <p>{t(district.note)}{scope.district === pick.district ? <span className="yours"><i />{t("Your district")}</span> : null}</p>
            </div>
            <div className="stack" style={{ gap: 8, alignItems: "flex-end" }}>
              <Mark status={statusOf(totals.ratio)} boxed />
              {scope.district !== null && scope.district !== pick.district ? <Button kind="ghost" icon="pin" onClick={() => setPick({ district: scope.district! })}>{t("Back to {district}", { district: t(data.districts[scope.district].name) })}</Button> : null}
            </div>
          </div>
          <JobsStrip ratio={totals.ratio} status={statusOf(totals.ratio)} />
          <StripCaption ratio={totals.ratio} jobs={totals.jobs} trainees={totals.trainees} />
          <div style={{ marginTop: 18 }}>
            <div style={{ display: "grid", gridTemplateColumns: "30px minmax(0,1fr) 84px 92px", gap: 12, fontSize: 12, color: "var(--ink-3)", padding: "0 4px 6px" }}>
              <span /><span>{t("Trade")}</span><span>{t("Jobs trend")}</span><span style={{ textAlign: "right" }}>{t("Per 10 jobs")}</span>
            </div>
            {rows.map(({ k, p }) => (
              <div key={k} className="trow" role="button" tabIndex={0} onClick={() => open(pick.district, k)} onKeyDown={(e) => { if (e.key === "Enter") open(pick.district, k); }}>
                <TradeIcon icon={data.trades[k].icon} status={p.status} />
                <div><div className="nm">{t(data.trades[k].name)}</div><div className="sub">{t("{jobs} jobs, {trainees} trainees", { jobs: fmt(p.jobs), trainees: fmt(p.trainees) })}</div></div>
                <Spark history={p.history} forecast={p.forecast} color={STATUS[p.status].hex} />
                <div className="pt"><b className="num" style={{ color: STATUS[p.status].color }}>{perTen(p.ratio)}</b><Mark status={p.status} short /></div>
              </div>
            ))}
          </div>
          <div className="row" style={{ marginTop: 18 }}>
            <Button onClick={() => open(pick.district, rows[0].k)} icon="explore">{t("Open {district}", { district: t(district.name) })}</Button>
            <Button kind="quiet" icon="plan" onClick={() => go("/plan")}>{t("Plan seat changes")}</Button>
          </div>
        </section>
      </div>

      <section className="panel" data-reveal>
        <div className="panel-head">
          <div><h2 className="h2">{t("Every district, every trade")}</h2><p>{t("Each box is the number of trainees for every 10 jobs. Click a box to see the story behind it.")}</p></div>
          <div className="stack" style={{ gap: 10, alignItems: "flex-end" }}>
            <div className="keyrow" style={{ maxWidth: 420, justifyContent: "flex-end" }}>
              {STATUS.map((s, i) => <span key={s.name}><i style={{ background: s.hex }} />{t(BAND_WORDS[i])}</span>)}
            </div>
            <Download href={`/api/export/gaps.csv?${query}`}>{t("Download this table")}</Download>
          </div>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="matrix">
            <thead><tr><th />{trades.map((k) => <th key={k}>{TRADE_ICONS[data.trades[k].icon]}{t(data.trades[k].name)}</th>)}</tr></thead>
            <tbody>
              {data.districts.map((d, di) => (
                <tr key={d.name}>
                  <th className="dn" scope="row" style={{ fontWeight: di === pick.district ? 600 : 400 }}>{t(d.name)}</th>
                  {trades.map((k) => {
                    const p = data.pairs[di][k];
                    const strong = p.status === 0 || p.status === 4;
                    return (
                      <td key={k}>
                        <button className="cell num" onClick={() => open(di, k)} title={t("{trade} in {district}: {status}", { trade: t(data.trades[k].name), district: t(d.name), status: t(STATUS[p.status].name) })}
                          style={{ background: strong ? STATUS[p.status].hex : STATUS[p.status].bg, color: strong ? "#FFFFFF" : STATUS[p.status].color }}>{perTen(p.ratio)}</button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="three">
        <section className="plate" data-reveal>
          <h2 className="h3" style={{ marginBottom: 8 }}>{t("Needs more trainees")}</h2>
          {needed.map(({ d, k, p }) => (
            <div key={`${d}-${k}`} className="li" role="button" tabIndex={0} onClick={() => open(d, k)}>
              <TradeIcon icon={data.trades[k].icon} status={p.status} />
              <div><div className="t">{t(data.trades[k].name)}</div><div className="s">{t(data.districts[d].name)}</div></div>
              <div className="v num" style={{ color: STATUS[0].color }}>{fmt(p.jobs - p.trainees)}<small>{t("jobs unfilled")}</small></div>
            </div>
          ))}
        </section>
        <section className="plate" data-reveal>
          <h2 className="h3" style={{ marginBottom: 8 }}>{t("Too many trainees")}</h2>
          {crowded.map(({ d, k, p }) => (
            <div key={`${d}-${k}`} className="li" role="button" tabIndex={0} onClick={() => open(d, k)}>
              <TradeIcon icon={data.trades[k].icon} status={p.status} />
              <div><div className="t">{t(data.trades[k].name)}</div><div className="s">{t(data.districts[d].name)}</div></div>
              <div className="v num" style={{ color: STATUS[4].color }}>{fmt(p.trainees - p.jobs)}<small>{t("without a job")}</small></div>
            </div>
          ))}
        </section>
        <section className="plate" data-reveal>
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
            <h2 className="h3">{t("Changing soon")}</h2>
            <Download href={`/api/export/warnings.csv?${query}`}>{t("Download")}</Download>
          </div>
          {soon.slice(0, 5).map((w) => (
            <div key={`${w.district}-${w.trade}`} className="li" role="button" tabIndex={0} onClick={() => open(w.district, w.trade)}>
              <TradeIcon icon={data.trades[w.trade].icon} status={w.next} />
              <div><div className="t">{t(data.trades[w.trade].name)}</div><div className="s">{t(data.districts[w.district].name)}</div></div>
              <div className="v" style={{ color: STATUS[w.next].color }}>{monthName(w.month)}<small>{t(w.next === 0 ? "becomes too few" : "becomes too many")}</small></div>
            </div>
          ))}
          {soon.length > 5 ? <Button kind="ghost" onClick={() => go("/plan")}>{t("See all {count}", { count: soon.length })}</Button> : null}
        </section>
      </div>
    </div>
  );
}
