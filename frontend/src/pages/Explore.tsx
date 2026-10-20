import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { STATUS, fmt, monthName, perTen, statusOf, useData, usePick } from "../data";
import { tn, useT } from "../i18n";
import { Decal, TRADE_ICONS } from "../ui/Icons";
import { Button, Download, JobsStrip, Mark, StripCaption } from "../ui/parts";
import { ForecastChart } from "../ui/ForecastChart";

export default function Explore() {
  const t = useT();
  const data = useData();
  const [pick, setPick] = usePick();
  const go = useNavigate();
  const trade = data.trades[pick.trade];
  const district = data.districts[pick.district];
  const pair = data.pairs[pick.district][pick.trade];
  const [seats, setSeats] = useState(pair.seats);
  const [pass, setPass] = useState(Math.round(pair.completion * pair.certification * 100));
  useEffect(() => { setSeats(pair.seats); setPass(Math.round(pair.completion * pair.certification * 100)); }, [pick.district, pick.trade, pair.seats, pair.completion, pair.certification]);

  const newTrainees = seats * (pass / 100);
  const newRatio = newTrainees / pair.jobs;
  const newStatus = statusOf(newRatio);
  const balanceSeats = Math.round(pair.jobs / (pass / 100) / 10) * 10;
  const past12 = pair.history.slice(-12);
  const outlook = pair.forecast.map((_, i) => {
    const window = [...past12.slice(i + 1), ...pair.forecast.slice(0, i + 1)];
    const ratio = pair.trainees / window.reduce((a, v) => a + v, 0);
    return { month: data.futureMonths[i], ratio, status: statusOf(ratio) };
  });
  const growth = Math.round(pair.growth * 100);
  const names = { trade: t(trade.name), district: t(district.name) };

  return (
    <div className="stack">
      <div>
        <h1 className="h1" style={{ maxWidth: "none" }}>{t("{trade} in {district}", names)}</h1>
        <p className="lede">
          {tn("Next year {district} expects about {jobs}. Training will produce about {trainees}.", {
            district: names.district,
            jobs: <b>{t("{count} jobs for this trade", { count: fmt(pair.jobs) })}</b>,
            trainees: <b>{fmt(pair.trainees)}</b>,
          })}{" "}
          {growth > 0 ? t("Demand is growing {n}% a year.", { n: growth }) : growth < 0 ? t("Demand is falling {n}% a year.", { n: Math.abs(growth) }) : t("Demand is steady.")}
        </p>
      </div>

      <section className="plate" data-reveal>
        <div className="stack" style={{ gap: 12 }}>
          <div className="choices" role="group" aria-label={t("Choose a district")}>
            {data.districts.map((d, i) => <button key={d.name} className={`choice ${i === pick.district ? "on" : ""}`} onClick={() => setPick({ district: i })}>{t(d.name)}</button>)}
          </div>
          <div className="choices" role="group" aria-label={t("Choose a trade")}>
            {data.trades.map((x, i) => (
              <button key={x.official} className={`choice ${i === pick.trade ? "on" : ""}`} onClick={() => setPick({ trade: i })} title={x.official}>
                {TRADE_ICONS[x.icon]}{t(x.name)}
              </button>
            ))}
          </div>
        </div>
      </section>

      <div className="two">
        <section className="panel" data-reveal style={{ ["--tc" as string]: STATUS[pair.status].hex }}>
          <div className="panel-head"><h2 className="h2">{t("Today's picture")}</h2><Mark status={pair.status} boxed /></div>
          <JobsStrip ratio={pair.ratio} status={pair.status} />
          <StripCaption ratio={pair.ratio} jobs={pair.jobs} trainees={pair.trainees} />
          <div className="ledger" style={{ gridTemplateColumns: "repeat(3, minmax(0,1fr))", marginTop: 18 }}>
            <div><span className="label">{t("Jobs next year")}</span><span className="figure num">{fmt(pair.jobs)}</span><span className="help">{t("Likely {low} to {high}", { low: fmt(pair.low), high: fmt(pair.high) })}</span></div>
            <div><span className="label">{t("Trainees each year")}</span><span className="figure num">{fmt(pair.trainees)}</span><span className="help">{t("From {count} training seats", { count: fmt(pair.seats) })}</span></div>
            <div><span className="label">{t("Change in jobs")}</span><span className="figure num" style={{ color: growth >= 0 ? "var(--s2)" : "var(--s0)" }}>{growth > 0 ? "+" : ""}{growth}%</span><span className="help">{t("Compared with last year")}</span></div>
          </div>
          <p className="small" style={{ marginTop: 12 }}>{t("Official name: {name}. NCO code {nco}. Skill level {level}.", { name: trade.official, nco: trade.nco, level: trade.nsqf })}</p>
        </section>

        <section className="panel" data-reveal>
          <Decal name="sliders" />
          <div className="panel-head"><div><h2 className="h2">{t("Try a change")}</h2><p>{t("Move the sliders to see what happens before you decide.")}</p></div>
            <Button kind="quiet" icon="reset" onClick={() => { setSeats(pair.seats); setPass(Math.round(pair.completion * pair.certification * 100)); }}>{t("Reset")}</Button></div>
          <div className="stack" style={{ gap: 14 }}>
            <div className="slider-row">
              <label htmlFor="seats">{t("Training seats")}</label><output className="num">{fmt(seats)}</output>
              <input id="seats" className="slider" type="range" min={0} max={Math.max(pair.seats * 3, balanceSeats + 200)} step={10} value={seats} onChange={(e) => setSeats(Number(e.target.value))} style={{ gridColumn: "1 / -1" }} />
            </div>
            <div className="slider-row">
              <label htmlFor="pass">{t("Trainees who finish and pass")}</label><output className="num">{pass}%</output>
              <input id="pass" className="slider" type="range" min={30} max={100} step={1} value={pass} onChange={(e) => setPass(Number(e.target.value))} style={{ gridColumn: "1 / -1" }} />
            </div>
            <div style={{ background: STATUS[newStatus].bg, borderRadius: 14, padding: 14 }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <b style={{ fontSize: 18 }}>{t("{n} trainees for every 10 jobs", { n: perTen(newRatio) })}</b><Mark status={newStatus} boxed />
              </div>
              <div style={{ marginTop: 10 }}><JobsStrip ratio={newRatio} status={newStatus} small /></div>
              <p className="small" style={{ margin: "8px 0 0", color: "var(--ink-2)" }}>
                {newRatio < 0.95 ? t("Still about {count} jobs short.", { count: fmt(pair.jobs - newTrainees) }) : newRatio > 1.05 ? t("About {count} trainees may not find a job.", { count: fmt(newTrainees - pair.jobs) }) : t("This closely matches the jobs coming.")}
                {" "}{tn("To match the jobs exactly, plan about {seats}.", { seats: <b>{t("{count} seats", { count: fmt(balanceSeats) })}</b> })}
              </p>
            </div>
          </div>
        </section>
      </div>

      <section className="panel" data-reveal>
        <div className="panel-head">
          <div><h2 className="h2">{t("Jobs over time")}</h2><p>{t("The green line is jobs opening each month. The yellow line is how many trainees finish each month. When green rises above yellow, there are not enough trainees.")}</p></div>
          <Download href={`/api/export/forecast.csv?state=${encodeURIComponent(data.state)}&district=${encodeURIComponent(district.name)}&trade=${encodeURIComponent(trade.official)}`}>{t("Download the forecast")}</Download>
        </div>
        <ForecastChart pair={pair} historyMonths={data.historyMonths} futureMonths={data.futureMonths} traineesPerMonth={pair.trainees / 12} />
      </section>

      <section className="panel" data-reveal>
        <div className="panel-head"><div><h2 className="h2">{t("Month by month")}</h2><p>{t("How the balance changes over the next year if nothing changes.")}</p></div>
          <Button kind="quiet" icon="plan" onClick={() => go("/plan")}>{t("Plan seat changes")}</Button></div>
        <div className="months">
          {outlook.map((o) => (
            <div key={o.month} title={t(STATUS[o.status].name)} style={{ background: STATUS[o.status].bg, borderRadius: 12, padding: "10px 6px", textAlign: "center" }}>
              <div className="small" style={{ color: "var(--ink-2)" }}>{monthName(o.month, false, false)}</div>
              <div className="num" style={{ fontWeight: 700, fontSize: 18, color: STATUS[o.status].color }}>{perTen(o.ratio)}</div>
              <div style={{ fontSize: 11, color: STATUS[o.status].color, fontWeight: 600 }}>{t(STATUS[o.status].short)}</div>
            </div>
          ))}
        </div>
        <p className="small" style={{ marginTop: 10 }}>{t("Numbers show trainees for every 10 jobs.")}</p>
      </section>
    </div>
  );
}
