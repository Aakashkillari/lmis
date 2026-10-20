import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { PILOT_STATES, homeFor, useAuth, usePlace } from "../auth";
import { STATUS, fmt, perTen, sectorTrades, statusOf, useData, useNational, usePick } from "../data";
import { msg, useT } from "../i18n";
import { Decal, Glyph } from "../ui/Icons";
import { Button, JobsStrip, Mark, TradeIcon } from "../ui/parts";
import { scrollToSection } from "../ui/Shell";
import { TNMap } from "../ui/TNMap";

const STEPS = [
  { title: msg("See where jobs are coming"), text: msg("A map of every district shows which trades will hire more people next year, and which will hire fewer.") },
  { title: msg("Spot the mismatch early"), text: msg("Pramaan warns you months ahead when a trade is about to have too few or too many trainees.") },
  { title: msg("Move seats before it is too late"), text: msg("It suggests how many training seats to shift, and from where, without adding new budget.") },
];

const ROLES = [
  { icon: "explore", title: msg("National skill planners"), text: msg("Compare states and set yearly training targets.") },
  { icon: "map", title: msg("State skill planning cells"), text: msg("Plan seats for every district and trade in the state.") },
  { icon: "pin", title: msg("District skill officers"), text: msg("See their own district first and ask for seat changes.") },
  { icon: "car", title: msg("Sector Skill Councils"), text: msg("Follow their trades across every pilot state.") },
];

export default function Landing() {
  const t = useT();
  const data = useData();
  const [, setPick] = usePick();
  const [place, setPlace] = usePlace();
  const { user } = useAuth();
  const { national } = useNational();
  const where = useLocation();
  const go = useNavigate();

  useEffect(() => {
    if (!where.hash) return;
    const timer = window.setTimeout(() => scrollToSection(where.hash.slice(1)), 350);
    return () => window.clearTimeout(timer);
  }, [where.hash]);

  const states = national?.states ?? [];
  const jobs = states.reduce((a, s) => a + s.jobs, 0);
  const unfilled = states.reduce((a, s) => a + s.unfilled, 0);
  const districts = states.reduce((a, s) => a + s.districts, 0);
  const pairs = data.pairs.flatMap((row, d) => row.map((p, k) => ({ d, k, p })));
  const short = [...pairs].sort((a, b) => (b.p.jobs - b.p.trainees) - (a.p.jobs - a.p.trainees)).slice(0, 2);
  const crowded = [...pairs].sort((a, b) => (b.p.trainees - b.p.jobs) - (a.p.trainees - a.p.jobs))[0];
  const cases = [...short, crowded];
  const enter = (to: string) => go(user ? to : `/login?next=${encodeURIComponent(to)}`);

  return (
    <div className="landing">
      <section className="landing-hero">
        <div className="landing-copy" data-reveal>
          <h1 className="display">{t("Train people for the jobs that are coming")}</h1>
          <p className="lede">{t("Pramaan shows skill planners where jobs will open in the next 12 months, whether enough people are being trained for them, and where training seats should move.")}</p>
          <div className="row" style={{ marginTop: 28 }}>
            {user
              ? <Button icon="map" onClick={() => go(homeFor(user))}>{t("Open Pramaan")}</Button>
              : <Button icon="lock" onClick={() => go("/login")}>{t("Sign in")}</Button>}
            <Button kind="quiet" icon="question" onClick={() => go("/method")}>{t("See how it works")}</Button>
          </div>
          <dl className="landing-facts">
            <div><dt>{t("Jobs expected next year")}</dt><dd className="num">{states.length ? fmt(jobs) : "…"}</dd></div>
            <div><dt>{t("Jobs at risk of going unfilled")}</dt><dd className="num" style={{ color: STATUS[0].color }}>{states.length ? fmt(unfilled) : "…"}</dd></div>
            <div><dt>{t("Pilot states and districts")}</dt><dd className="num">{states.length ? t("{states} states, {districts} districts", { states: states.length, districts }) : "…"}</dd></div>
          </dl>
        </div>

        <div className="panel landing-preview" data-reveal>
          <div className="landing-map">
            <TNMap data={data} trades={sectorTrades(data, "all")} compact />
            <div className="segment state-switch" role="group" aria-label={t("Choose a state")}>
              {PILOT_STATES.map((s) => <button key={s} className={s === place ? "on" : ""} onClick={() => setPlace(s)}>{t(s)}</button>)}
            </div>
          </div>
          <div className="landing-cases">
            <p className="label" style={{ margin: 0 }}>{t("Right now in {state}", { state: t(data.state) })}</p>
            {cases.map(({ d, k, p }) => (
              <button key={`${d}-${k}`} className="case" onClick={() => { setPick({ district: d, trade: k }); enter("/explore"); }}>
                <TradeIcon icon={data.trades[k].icon} status={p.status} />
                <span className="case-body">
                  <span className="case-title">{t("{trade}, {district}", { trade: t(data.trades[k].name), district: t(data.districts[d].name) })}</span>
                  <JobsStrip ratio={p.ratio} status={p.status} small />
                  <span className="case-foot"><b className="num" style={{ color: STATUS[p.status].color }}>{t("{n} per 10 jobs", { n: perTen(p.ratio) })}</b><Mark status={p.status} short /></span>
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section id="what" className="landing-section">
        <h2 className="h1">{t("What Pramaan does")}</h2>
        <div className="landing-steps">
          {STEPS.map((s, i) => (
            <div key={s.title} className="step3" data-reveal>
              <span className="no">{t("Step {n}", { n: i + 1 })}</span>
              <h3>{t(s.title)}</h3>
              <p>{t(s.text)}</p>
            </div>
          ))}
        </div>
        <div className="roles" data-reveal>
          {ROLES.map((r) => (
            <div key={r.title} className="role">
              <Glyph name={r.icon} />
              <div><b>{t(r.title)}</b><p>{t(r.text)}</p></div>
            </div>
          ))}
        </div>
      </section>

      <section id="pilot" className="landing-section">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-end" }}>
          <div><h2 className="h1">{t("Pilot states")}</h2><p className="lede">{t("Two states are live, with 8 districts each, in two fields: electrical and power, and vehicles. More states can join without changing the method.")}</p></div>
          <Button kind="quiet" icon="question" onClick={() => go("/method")}>{t("How the numbers are made")}</Button>
        </div>
        <div className="pilot-grid">
          {states.map((s) => {
            const ratio = s.trainees / s.jobs;
            return (
              <article key={s.name} className="panel pilot" data-reveal>
                <Decal name="map" />
                <div className="panel-head">
                  <div><h3 className="h2">{t(s.name)}</h3><p>{t("{count} districts, data to {month}", { count: s.districts, month: s.updated })}</p></div>
                  <Mark status={statusOf(ratio)} boxed />
                </div>
                <dl className="pilot-facts">
                  <div><dt>{t("Jobs next year")}</dt><dd className="num">{fmt(s.jobs)}</dd></div>
                  <div><dt>{t("Jobs at risk")}</dt><dd className="num" style={{ color: STATUS[0].color }}>{fmt(s.unfilled)}</dd></div>
                  <div><dt>{t("Early warnings")}</dt><dd className="num" style={{ color: STATUS[1].color }}>{s.warnings}</dd></div>
                </dl>
                <div className="row" style={{ marginTop: 16 }}>
                  <Button kind="quiet" icon="map" onClick={() => { setPlace(s.name); enter("/dashboard"); }}>{t("Open {state}", { state: t(s.name) })}</Button>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <p className="small landing-note">{t("Pilot for Smart India Hackathon 2026, problem statement 26246. Runs on a demo dataset that follows the structure of NCS, e-Shram, PLFS and NCVT.")}</p>
    </div>
  );
}
