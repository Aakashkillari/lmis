import { useNavigate } from "react-router-dom";
import { PILOT_STATES, homeFor, scopeOf, seesLines, startPick, useAuth, usePlace, useUser } from "../auth";
import { SECTORS, useData, useNational, usePick, type SectorKey } from "../data";
import { LANGS, msg, useT } from "../i18n";
import { usePrefs, type Prefs } from "../prefs";
import { Glyph } from "../ui/Icons";
import { Button } from "../ui/parts";

type Switch = "smooth" | "motion" | "cursor" | "large";
const DISPLAY: { key: Switch; label: string; help: string }[] = [
  { key: "smooth", label: msg("Smooth scrolling"), help: msg("Pages glide when you scroll") },
  { key: "motion", label: msg("Animations"), help: msg("Sections fade in and icons redraw on hover") },
  { key: "cursor", label: msg("Pointer effect"), help: msg("A ring follows the mouse") },
  { key: "large", label: msg("Larger text"), help: msg("Easier to read on a projector") },
];

const clock = (seconds: number) => new Date(seconds * 1000).toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });

export default function Settings() {
  const t = useT();
  const data = useData();
  const user = useUser();
  const { signOut } = useAuth();
  const [prefs, setPrefs] = usePrefs();
  const [, setPlace] = usePlace();
  const [, setPick] = usePick();
  const { national } = useNational();
  const go = useNavigate();
  const startState = prefs.startState ?? user.scope.state ?? PILOT_STATES[0];
  const districts = national ? [...new Set(national.pairs.filter((p) => p.state === startState).map((p) => p.district))] : [];
  const sector: SectorKey = prefs.startSector ?? user.scope.sector ?? "all";
  const changed = prefs.startState !== null || prefs.startDistrict !== null || prefs.startSector !== null;
  const usualDistrict = user.scope.district && (!user.scope.state || user.scope.state === startState) ? user.scope.district : null;

  return (
    <div className="stack" style={{ gap: 24 }}>
      <div>
        <h1 className="h1">{t("Settings")}</h1>
        <p className="lede">{t("Saved for you on this computer. Anyone else who signs in here keeps their own settings.")}</p>
      </div>

      <div className="settings">
        <section className="panel" data-reveal>
          <div className="who-card">
            <span className="avatar xl">{user.initials}</span>
            <div><h2 className="h2">{t(user.name)}</h2><p>{t(user.title)}</p></div>
          </div>
          <dl className="facts">
            <div><dt>{t("User ID")}</dt><dd>{user.id}</dd></div>
            <div><dt>{t("Job")}</dt><dd>{t(user.summary)}</dd></div>
            <div><dt>{t("Signed in")}</dt><dd>{t("Since {start}. You stay signed in until {end}.", { start: clock(user.since), end: clock(user.until) })}</dd></div>
          </dl>
          <p className="label" style={{ margin: "18px 0 6px" }}>{t("What you see first")}</p>
          {seesLines(user, data).map((line) => (
            <span key={line} className="sees-line"><Glyph name="check" tone={{ ink: "#0B6E69", tile: "transparent" }} />{line}</span>
          ))}
          <p className="small" style={{ margin: "8px 0 0" }}>{t("You can still open any state, district or trade.")}</p>
          <div className="row" style={{ marginTop: 20 }}>
            <Button kind="quiet" icon="users" onClick={() => signOut("/login")}>{t("Switch account")}</Button>
            <Button kind="quiet" icon="out" onClick={() => signOut("/")}>{t("Sign out")}</Button>
          </div>
        </section>

        <div className="stack" style={{ gap: 20 }}>
          <section className="panel" data-reveal>
            <div className="panel-head"><div><h2 className="h2">{t("Language")}</h2><p>{t("Pramaan's screens and the assistant's answers use this language.")}</p></div></div>
            <div className="segment wrap" role="group" aria-label={t("Language")}>
              {LANGS.map((l) => <button key={l.code} lang={l.code} className={prefs.lang === l.code ? "on" : ""} onClick={() => setPrefs({ lang: l.code })}>{l.name}</button>)}
            </div>
          </section>

          <section className="panel" data-reveal>
            <div className="panel-head"><div><h2 className="h2">{t("Where Pramaan opens")}</h2><p>{t("The state, district and field you see after you sign in.")}</p></div></div>
            <label className="field">
              <span>{t("State")}</span>
              <select className="select" value={startState} onChange={(e) => setPrefs({ startState: e.target.value === (user.scope.state ?? PILOT_STATES[0]) ? null : e.target.value, startDistrict: null })}>
                {PILOT_STATES.map((s) => <option key={s} value={s}>{t(s)}</option>)}
              </select>
            </label>
            <label className="field">
              <span>{t("District")}</span>
              <select className="select" value={prefs.startDistrict ?? ""} onChange={(e) => setPrefs({ startDistrict: e.target.value || null })}>
                <option value="">{usualDistrict ? t("My district ({district})", { district: t(usualDistrict) }) : t("The one with the most unfilled jobs")}</option>
                {districts.filter((d) => d !== usualDistrict).map((d) => <option key={d} value={d}>{t(d)}</option>)}
              </select>
            </label>
            <div className="field">
              <span>{t("Field")}</span>
              <div className="segment wrap" role="group" aria-label={t("Field to open on")}>
                {(Object.keys(SECTORS) as SectorKey[]).map((key) => (
                  <button key={key} className={sector === key ? "on" : ""} onClick={() => setPrefs({ startSector: key === (user.scope.sector ?? "all") ? null : key })}>{t(SECTORS[key])}</button>
                ))}
              </div>
            </div>
            <div className="row" style={{ marginTop: 18 }}>
              <Button icon="map" onClick={() => {
                /* Same state: jump straight to the chosen view. Another state: its view starts fresh when it loads. */
                if (startState === data.state) setPick(startPick(scopeOf(user, data), prefs, data));
                else { try { sessionStorage.removeItem("pramaan-pick"); } catch { /* storage blocked */ } setPlace(startState); }
                go(homeFor(user) === "/india" && !changed ? "/india" : "/dashboard");
              }}>{t("Open Pramaan there")}</Button>
              {changed ? <Button kind="ghost" icon="reset" onClick={() => setPrefs({ startState: null, startDistrict: null, startSector: null })}>{t("Go back to my usual view")}</Button> : null}
            </div>
          </section>

          <section className="panel" data-reveal>
            <div className="panel-head"><div><h2 className="h2">{t("Display")}</h2><p>{t("Turn effects off if the screen feels slow or busy.")}</p></div></div>
            {DISPLAY.map((d) => (
              <button key={d.key} className="pref" role="switch" aria-checked={prefs[d.key]} onClick={() => setPrefs({ [d.key]: !prefs[d.key] } as Partial<Prefs>)}>
                <span><b>{t(d.label)}</b><small>{t(d.help)}</small></span>
                <i className={prefs[d.key] ? "on" : ""} />
              </button>
            ))}
          </section>
        </div>
      </div>
    </div>
  );
}
