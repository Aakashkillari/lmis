import { useEffect, useState, type FormEvent } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import { homeFor, safeNext, scopeOf, seesLines, useAuth, type Account } from "../auth";
import { sectorTrades, useData } from "../data";
import { useT } from "../i18n";
import { Decal, Glyph, ROLE_ICON } from "../ui/Icons";
import { Button } from "../ui/parts";
import { TNMap } from "../ui/TNMap";

export default function Login() {
  const t = useT();
  const data = useData();
  const { user, notice, signIn, signInDemo } = useAuth();
  const [params] = useSearchParams();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/accounts").then((r) => r.json()).then((j) => setAccounts(j.accounts ?? [])).catch(() => setAccounts([]));
  }, []);

  if (user) return <Navigate to={safeNext(params.get("next")) ?? homeFor(user)} replace />;

  const run = async (key: string, action: () => Promise<void>) => {
    setBusy(key);
    setError("");
    try { await action(); } catch (e) { setError((e as Error).message); setBusy(null); }
  };
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) { setError(t("Enter your user ID and password.")); return; }
    run("form", () => signIn(username, password));
  };

  const list = accounts ?? [];
  const typed = list.find((a) => a.id === username.trim().toLowerCase());
  const shown = list.find((a) => a.id === hover) ?? typed ?? list[0];
  const scope = shown ? scopeOf(shown, data) : null;
  const elsewhere = shown?.scope.state && shown.scope.state !== data.state;

  return (
    <div className="login">
      <section className="login-copy" data-reveal>
        <h1 className="display">{t("Sign in to Pramaan")}</h1>
        <p className="lede">{t("Use the user ID and password from your department. Pramaan opens on the state, district or field you look after.")}</p>
        {notice ? <p className="notice" role="status"><Glyph name="bell" tone={{ ink: "#B86E12", tile: "transparent" }} />{notice}</p> : null}
        <form className="panel login-form" onSubmit={submit} noValidate>
          <Decal name="lock" />
          <label className="field">
            <span>{t("User ID")}</span>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" autoCapitalize="none" spellCheck={false} placeholder={t("For example, cbe.officer")} />
          </label>
          <label className="field">
            <span>{t("Password")}</span>
            <span className="pw">
              <input type={show ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
              <button type="button" className="pw-show" aria-pressed={show} onClick={() => setShow(!show)}>{show ? t("Hide") : t("Show")}</button>
            </span>
          </label>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          <Button type="submit" icon="lock" disabled={busy !== null}>{busy === "form" ? t("Signing in…") : t("Sign in")}</Button>
        </form>
        <p className="small" style={{ margin: "14px 0 0" }}>{t("Forgot your password? Ask your state skill planning cell to reset it.")}</p>
      </section>

      {list.length ? (
        <section className="panel login-demo" data-reveal>
          <div className="panel-head">
            <div><h2 className="h2">{t("Try a demo account")}</h2><p>{t("No password needed. Each one opens Pramaan the way that person would use it.")}</p></div>
          </div>
          <div className="login-demo-body">
            <div className="login-map">
              {scope ? <TNMap data={data} trades={sectorTrades(data, scope.sector ?? "all")} compact focus={elsewhere ? -1 : scope.district} home={elsewhere ? null : scope.district} /> : null}
              <p className="small" style={{ textAlign: "center", margin: "6px 0 0" }}>{t("Showing {state}", { state: t(data.state) })}</p>
            </div>
            <div className="accounts" onMouseLeave={() => setHover(null)}>
              {list.map((a) => (
                <button key={a.id} className={`account ${shown?.id === a.id ? "on" : ""}`} disabled={busy !== null}
                  onMouseEnter={() => setHover(a.id)} onFocus={() => setHover(a.id)} onClick={() => run(a.id, () => signInDemo(a.id))}>
                  <span className="account-icon"><Glyph name={ROLE_ICON[a.role]} /></span>
                  <span className="account-body"><b>{t(a.name)}</b><small>{t(a.title)}</small></span>
                  <span className="account-go">{busy === a.id ? t("Opening…") : t("Sign in")}</span>
                </button>
              ))}
              {shown ? (
                <div className="sees" aria-live="polite">
                  <p className="label" style={{ margin: "0 0 6px" }}>{t("What this person sees")}</p>
                  {seesLines(shown, data).map((line) => (
                    <span key={line} className="sees-line"><Glyph name="check" tone={{ ink: "#0B6E69", tile: "transparent" }} />{line}</span>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
