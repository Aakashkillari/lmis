import { useNavigate } from "react-router-dom";
import { homeFor, useAuth } from "../auth";
import { BAND_WORDS, STATUS, busiestDistrict, fmt, useData, useNational } from "../data";
import { msg, tn, useT } from "../i18n";
import { ForecastChart } from "../ui/ForecastChart";
import { Glyph } from "../ui/Icons";
import { Button } from "../ui/parts";
import { scrollToSection } from "../ui/Shell";

const STEPS = [
  { id: "collect", title: msg("Collect job signals"), icon: "download" },
  { id: "combine", title: msg("Combine into one number"), icon: "equal" },
  { id: "forecast", title: msg("Forecast 12 months"), icon: "explore" },
  { id: "supply", title: msg("Count trainees"), icon: "users" },
  { id: "compare", title: msg("Compare"), icon: "map" },
  { id: "warn", title: msg("Warn early"), icon: "bell" },
  { id: "moves", title: msg("Suggest seat moves"), icon: "plan" },
];

const SOURCES = [
  { key: "portal", name: msg("Online job portals"), what: msg("Live job ads. The same job is often posted on several sites, so Pramaan divides the count by {n}.") },
  { key: "ncs", name: msg("National Career Service (NCS)"), what: msg("Government job portal vacancies. It sees about {n}% of real jobs, so its count is scaled up.") },
  { key: "industry", name: msg("Industry and Sector Skill Council hiring plans"), what: msg("What employers plan to hire in the next three months: the earliest signal.") },
  { key: "eshram", name: msg("e-Shram registrations"), what: msg("Workers registering in a trade. Shows where informal work is growing.") },
];

const ACTIONS = [msg("Add seats or open centres"), msg("Get ready to add seats"), msg("Keep as it is"), msg("Hold seats"), msg("Cut seats or retrain")];

const API = [
  { path: "GET /api/national", what: msg("Every pilot state compared, with all district and trade gaps") },
  { path: "GET /api/data?state=", what: msg("One state's forecasts, warnings and seat moves") },
  { path: "GET /api/gaps?state=&district=&trade=", what: msg("Current gaps with NCO codes and NSQF levels, for scheme systems") },
  { path: "GET /api/export/{table}.csv", what: msg("Spreadsheets: gaps, forecast, warnings or moves. Filter by state, district, field and trade") },
  { path: "GET /api/match?q=", what: msg("Matches a job title to its official NCO trade") },
];

export default function Method() {
  const t = useT();
  const data = useData();
  const { user } = useAuth();
  const go = useNavigate();
  const { national } = useNational();
  const m = data.method;
  const d = busiestDistrict(data);
  const k = data.trades.findIndex((x) => x.icon === "ev");
  const pair = data.pairs[d][k];
  const accuracy = national?.states ?? [{ name: data.state, accuracy: data.accuracy }];
  const worst = Math.max(...accuracy.flatMap((s) => [s.accuracy.pramaan, s.accuracy.simple]));
  const sample = data.trades.find((x) => x.icon === "bike")!;

  return (
    <div className="method">
      <section className="method-hero" data-reveal>
        <h1 className="display">{t("How Pramaan works")}</h1>
        <p className="lede">{t("Pramaan turns scattered job signals into a plan for training seats. Here is every step, with the exact numbers it uses.")}</p>
        <p className="note">{t("The pilot runs on a demo dataset that follows the structure of NCS, e-Shram, PLFS and NCVT data. The method is the same for live data.")}</p>
      </section>

      <ol className="flow" data-reveal aria-label={t("The seven steps")}>
        {STEPS.map((s, i) => (
          <li key={s.id}>
            <a href={`#${s.id}`} onClick={(e) => { e.preventDefault(); scrollToSection(s.id); }}>
              <span className="flow-no num">{i + 1}</span><Glyph name={s.icon} /><span>{t(s.title)}</span>
            </a>
          </li>
        ))}
      </ol>

      <section id="collect" className="mstep" data-reveal>
        <div className="mstep-head"><span className="flow-no num">1</span><div><h2 className="h2">{t("Collect job signals")}</h2><p>{t("Four sources, read every month for each district and trade. Each one sees part of the picture, so Pramaan weighs them.")}</p></div></div>
        <div className="sources">
          {SOURCES.map((s) => (
            <div key={s.key} className="source">
              <div className="source-top"><b>{t(s.name)}</b><span className="num">{Math.round(m.weights[s.key] * 100)}%</span></div>
              <div className="weight"><i style={{ width: `${(m.weights[s.key] / 0.35) * 100}%` }} /></div>
              <p>{t(s.what, { n: s.key === "portal" ? m.duplication : Math.round(m.coverage * 100) })}</p>
            </div>
          ))}
        </div>
        <p className="small">{t("Also used: PLFS to check state totals, and NCVT MIS and Skill India Digital Hub for training seats, completion and certification.")}</p>
      </section>

      <section id="combine" className="mstep" data-reveal>
        <div className="mstep-head"><span className="flow-no num">2</span><div><h2 className="h2">{t("Combine into one demand index")}</h2><p>{t("Each signal is put on the same scale: how far above or below its own usual level it is this month. The four are then blended with the weights above, and turned back into a number of job openings using NCS and job portal counts.")}</p></div></div>
        <div className="formula" aria-label={t("Demand index formula")}>
          <span>{t("Demand index")}</span><i>=</i>
          {SOURCES.map((s, i) => <span key={s.key} className="term">{i ? <i>+</i> : null}<b className="num">{m.weights[s.key].toFixed(2)}</b> × {t(s.name).split(" (")[0]}</span>)}
        </div>
        <div className="match-demo">
          <span className="small">{t("Messy job titles are matched to official trade codes first:")}</span>
          <span className="chip">“Bike Mechanic”</span><span className="chip">“Two Wheeler Mechanic”</span><span className="chip">“Scooter Mechanic”</span>
          <Glyph name="arrow" /><span className="chip strong">{t(sample.name)}, NCO {sample.nco}</span>
        </div>
      </section>

      <section id="forecast" className="mstep" data-reveal>
        <div className="mstep-head"><span className="flow-no num">3</span><div><h2 className="h2">{t("Forecast the next 12 months")}</h2><p>{t("The Holt-Winters method learns two things from {months} months of history: the trend (growing or shrinking) and the yearly pattern (busy and quiet months). It then projects {ahead} months ahead. The shaded band is the likely range: {level}% of outcomes fall inside it.", { months: m.historyMonths, ahead: m.forecastMonths, level: Math.round(m.bandLevel * 100) })}</p></div></div>
        <div className="panel">
          <p className="label" style={{ margin: "0 0 8px" }}>{t("Example: {trade} in {district}", { trade: t(data.trades[k].name), district: t(data.districts[d].name) })}</p>
          <ForecastChart pair={pair} historyMonths={data.historyMonths} futureMonths={data.futureMonths} traineesPerMonth={pair.trainees / 12} />
        </div>
      </section>

      <section id="supply" className="mstep" data-reveal>
        <div className="mstep-head"><span className="flow-no num">4</span><div><h2 className="h2">{t("Count the trainees who will be ready")}</h2><p>{t("Not everyone who takes a seat finishes, and not everyone who finishes passes. Pramaan counts only people who are ready for the job.")}</p></div></div>
        <div className="formula big">
          <span className="term"><b className="num">{fmt(pair.seats)}</b> {t("seats")}</span><i>×</i>
          <span className="term"><b className="num">{Math.round(pair.completion * 100)}%</b> {t("finish")}</span><i>×</i>
          <span className="term"><b className="num">{Math.round(pair.certification * 100)}%</b> {t("pass")}</span><i>=</i>
          <span className="term result"><b className="num">{fmt(pair.trainees)}</b> {t("trainees ready each year")}</span>
        </div>
      </section>

      <section id="compare" className="mstep" data-reveal>
        <div className="mstep-head"><span className="flow-no num">5</span><div><h2 className="h2">{t("Compare jobs and trainees")}</h2><p>{t("Pramaan divides trainees by jobs and shows it as trainees for every 10 jobs. Ten means one trainee for every job.")}</p></div></div>
        <div className="scale">
          {STATUS.map((s, i) => (
            <div key={s.name} className="scale-band" style={{ background: s.bg, color: s.color }}>
              <span className="scale-range num">{t(BAND_WORDS[i])}</span>
              <b>{t(s.name)}</b>
              <span className="scale-do">{t(ACTIONS[i])}</span>
            </div>
          ))}
        </div>
      </section>

      <section id="warn" className="mstep" data-reveal>
        <div className="mstep-head"><span className="flow-no num">6</span><div><h2 className="h2">{t("Warn early")}</h2><p>{t("Every month Pramaan looks {months} months ahead. If a course is about to cross into not enough trainees or too many trainees, it is flagged with the month it will happen, so seats can change before the problem shows up in placements.", { months: m.warningMonths })}</p></div></div>
        <p className="callout">{tn("Right now: {count} warnings in {state}.", { count: <b className="num">{data.warnings.length}</b>, state: t(data.state) })}</p>
      </section>

      <section id="moves" className="mstep" data-reveal>
        <div className="mstep-head"><span className="flow-no num">7</span><div><h2 className="h2">{t("Suggest seat moves")}</h2><p>{t("Seats move from courses with too many trainees to courses with too few, biggest gaps first. The total number of seats never changes, so no new money is needed.")}</p></div></div>
        <ul className="rules">
          <li><Glyph name="check" tone={{ ink: "#0B6E69", tile: "transparent" }} />{t("A course giving seats keeps enough for {n}% of its jobs.", { n: Math.round(m.donorKeep * 100) })}</li>
          <li><Glyph name="check" tone={{ ink: "#0B6E69", tile: "transparent" }} />{t("A course receiving seats gets enough for {n}% of its jobs.", { n: Math.round(m.receiverTarget * 100) })}</li>
          <li><Glyph name="check" tone={{ ink: "#0B6E69", tile: "transparent" }} />{t("Seats move in blocks of {n}, the size of one batch.", { n: m.block })}</li>
          <li><Glyph name="check" tone={{ ink: "#0B6E69", tile: "transparent" }} />{t("Planners choose: swap only between similar courses, or between any courses.")}</li>
        </ul>
      </section>

      <section className="mstep" data-reveal>
        <div className="mstep-head"><Glyph name="question" /><div><h2 className="h2">{t("How accurate is it?")}</h2><p>{t("Pramaan hid the last {months} months of data, forecast them, and compared with what really happened. Smaller is better.", { months: m.backtestMonths })}</p></div></div>
        <div className="accuracy">
          {accuracy.map((s) => (
            <div key={s.name} className="acc-state">
              <b>{t(s.name)}</b>
              <div className="acc-row"><span>{t("Pramaan")}</span><div className="acc-bar"><i style={{ width: `${(s.accuracy.pramaan / worst) * 100}%`, background: "var(--accent)" }} /></div><span className="num">{s.accuracy.pramaan.toFixed(1)}%</span></div>
              <div className="acc-row"><span>{t("Simple average")}</span><div className="acc-bar"><i style={{ width: `${(s.accuracy.simple / worst) * 100}%`, background: "#C3C8D6" }} /></div><span className="num">{s.accuracy.simple.toFixed(1)}%</span></div>
            </div>
          ))}
        </div>
        <p className="small">{t("Median forecast error across all district and trade pairs. The simple average repeats the last 12 months.")}</p>
      </section>

      <section className="mstep" data-reveal>
        <div className="mstep-head"><Glyph name="sheet" /><div><h2 className="h2">{t("Use Pramaan's numbers in other systems")}</h2><p>{t("Every forecast can feed scheme target-setting directly, as data or as a spreadsheet. Downloads need a signed-in account.")}</p></div></div>
        <dl className="api">
          {API.map((a) => <div key={a.path}><dt><code>{a.path}</code></dt><dd>{t(a.what)}</dd></div>)}
        </dl>
        <div className="row" style={{ marginTop: 16 }}>
          <a className="btn quiet" href="/docs" target="_blank" rel="noreferrer"><Glyph name="sheet" />{t("Open the API reference")}</a>
          <Button kind="ghost" icon="map" onClick={() => go(user ? homeFor(user) : "/login")}>{user ? t("Back to Pramaan") : t("Sign in to try it")}</Button>
        </div>
      </section>
    </div>
  );
}
