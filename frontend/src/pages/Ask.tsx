import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useNavigate } from "react-router-dom";
import { scopeOf, useAuth, type Scope } from "../auth";
import { useData, usePick, type Data } from "../data";
import { t, useLang, useT } from "../i18n";
import { Decal, NAV_ICONS } from "../ui/Icons";
import { Button } from "../ui/parts";

type Turn = { role: "user" | "assistant"; content: string };

function suggestionsFor(scope: Scope, data: Data) {
  const state = t(data.state);
  if (scope.district !== null) {
    const d = t(data.districts[scope.district].name);
    return [t("What should {district} plan for next year?", { district: d }), t("Which trades need more trainees in {district}?", { district: d }), t("Which trades have too many trainees in {district}?", { district: d }), t("Where can {district} move training seats?", { district: d }), t("What will change in {district} in the next 6 months?", { district: d }), t("How does Pramaan predict jobs?")];
  }
  if (scope.sector === "auto") {
    return [t("Where should we add EV mechanic seats in {state}?", { state }), t("Which districts have too many bike mechanic trainees?"), t("Which vehicle trades are growing fastest?"), t("Which vehicle courses should get fewer seats?"), t("Which vehicle trades will run into trouble in the next 6 months?"), t("How does Pramaan predict jobs?")];
  }
  const first = t(data.districts[0].name), second = t(data.districts[1].name), third = t(data.districts[data.districts.length - 2].name);
  return [t("Which field needs more trainees in {district}?", { district: first }), t("Where should we add EV mechanic seats in {state}?", { state }), t("Which trades have too many trainees in {district}?", { district: third }), t("What should {district} plan for next year?", { district: second }), t("Which trades will run into trouble in the next 6 months?"), t("How does Pramaan predict jobs?")];
}

export default function Ask() {
  const t = useT();
  const lang = useLang();
  const data = useData();
  const [, setPick] = usePick();
  const { user, lost } = useAuth();
  const suggestions = suggestionsFor(scopeOf(user, data), data);
  const go = useNavigate();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [ai, setAi] = useState<{ ai: boolean; model: string } | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => { fetch("/api/status").then((r) => r.json()).then(setAi).catch(() => setAi({ ai: false, model: "" })); }, []);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [turns, busy]);
  useEffect(() => { setTurns([]); }, [data.state]);

  const ask = async (question: string) => {
    const q = question.trim();
    if (!q || busy) return;
    const history = turns.slice(-6);
    setTurns((all) => [...all, { role: "user", content: q }, { role: "assistant", content: "" }]);
    setText("");
    setBusy(true);
    try {
      const response = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q, history, lang, state: data.state }) });
      if (response.status === 401) { lost(); return; }
      if (!response.body) throw new Error("No answer");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        const piece = decoder.decode(value, { stream: true });
        setTurns((all) => { const copy = [...all]; copy[copy.length - 1] = { role: "assistant", content: copy[copy.length - 1].content + piece }; return copy; });
      }
    } catch {
      setTurns((all) => { const copy = [...all]; copy[copy.length - 1] = { role: "assistant", content: t("Pramaan could not reach its server. Check that it is running and ask again.") }; return copy; });
    } finally {
      setBusy(false);
    }
  };

  /* Offer a shortcut to the place and trade an answer talks about, in English or the chosen language. */
  const mentioned = (content: string) => {
    const lower = content.toLowerCase();
    const has = (name: string) => lower.includes(name.toLowerCase()) || lower.includes(t(name).toLowerCase());
    return { d: data.districts.findIndex((x) => has(x.name)), k: data.trades.findIndex((x) => has(x.name)) };
  };

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1 className="h1">{t("Ask Pramaan")}</h1>
          <p className="lede">{t("Ask in your own words about any district, trade or field in {state}. Answers come from Pramaan's own forecasts.", { state: t(data.state) })}</p>
        </div>
        <span className="small" style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <i className="live-dot" style={{ background: ai?.ai ? "var(--s2)" : "#C3C8D6" }} />
          {ai === null ? t("Checking the assistant…") : ai.ai ? t("AI assistant is on") : t("Quick answers from Pramaan data")}
        </span>
      </div>

      <div className="chat">
        <section className="panel" style={{ display: "flex", flexDirection: "column" }}>
          <div className="bubbles" aria-live="polite">
            {turns.length === 0 ? (
              <div style={{ margin: "auto", textAlign: "center", maxWidth: 420, color: "var(--ink-2)" }}>
                <div style={{ width: 56, height: 56, margin: "0 auto 12px" }}>{NAV_ICONS.ask}</div>
                <h2 className="h2" style={{ color: "var(--ink)" }}>{t("What would you like to know?")}</h2>
                <p>{t("Pick a question on the right, or type your own below.")}</p>
              </div>
            ) : null}
            {turns.map((turn, i) => {
              const last = i === turns.length - 1;
              if (turn.role === "user") return <div key={i} className="bubble me">{turn.content}</div>;
              const ref = mentioned(turn.content + " " + (turns[i - 1]?.content ?? ""));
              return (
                <div key={i} className="bubble ai">
                  {turn.content ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{turn.content}</ReactMarkdown> : <span className="typing" aria-label={t("Pramaan is thinking")}><i /><i /><i /></span>}
                  {!busy || !last ? (ref.d >= 0 && turn.content ? (
                    <div style={{ marginTop: 10 }}>
                      <Button kind="quiet" icon="explore" onClick={() => { setPick({ district: ref.d, ...(ref.k >= 0 ? { trade: ref.k } : {}) }); go("/explore"); }}>
                        {ref.k >= 0
                          ? t("Open {trade} in {district}", { trade: t(data.trades[ref.k].name), district: t(data.districts[ref.d].name) })
                          : t("Open {district}", { district: t(data.districts[ref.d].name) })}
                      </Button>
                    </div>
                  ) : null) : null}
                </div>
              );
            })}
            <div ref={end} />
          </div>
          <form className="composer" onSubmit={(e) => { e.preventDefault(); ask(text); }}>
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder={t("For example: which trades need more seats in {district}?", { district: t(data.districts[2].name) })} aria-label={t("Your question")} disabled={busy} />
            <Button type="submit" icon="send">{busy ? t("Thinking") : t("Ask")}</Button>
          </form>
          {turns.length ? <div style={{ marginTop: 8 }}><Button kind="ghost" onClick={() => setTurns([])}>{t("Start a new conversation")}</Button></div> : null}
        </section>

        <aside className="panel">
          <Decal name="ask" />
          <div className="panel-head"><h2 className="h2">{t("Try asking")}</h2></div>
          <div className="suggest">
            {suggestions.map((s) => <button key={s} onClick={() => ask(s)} disabled={busy}>{s}</button>)}
          </div>
        </aside>
      </div>
    </div>
  );
}
