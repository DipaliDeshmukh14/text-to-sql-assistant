import { useState, useRef, useEffect } from "react";
import "./App.css";

function LandingPage({ onStart }) {
  return (
    <div className="landing">
      <div className="landing-nav">
        <span className="brand-mark">Σ</span>
        <span className="brand-name">SQL Assistant</span>
      </div>

      <div className="landing-hero">
        <span className="eyebrow">Natural language → SQL → answers</span>
        <h1>Ask your database questions.<br />Get real answers.</h1>
        <p className="landing-sub">
          Connect a Postgres database or upload a CSV, then talk to your data in
          plain English. Every answer comes with the exact query behind it.
        </p>
        <button className="cta" onClick={onStart}>Get started →</button>
      </div>

      <div className="landing-trace-demo">
        <div className="demo-line demo-q">"Which customer spent the most?"</div>
        <div className="trace">
          <span className="trace-step">schema</span>
          <span className="trace-line" />
          <span className="trace-step">sql</span>
          <span className="trace-line" />
          <span className="trace-step">result</span>
        </div>
        <div className="demo-line demo-sql">SELECT c.name FROM customers c JOIN orders...</div>
        <div className="demo-line demo-a">→ Vikram Singh</div>
      </div>
    </div>
  );
}

function OnboardingPage({ onReady, onBack }) {
  const [dbUrl, setDbUrl] = useState("");
  const [status, setStatus] = useState("");
  const [connecting, setConnecting] = useState(false);

  const connect = async () => {
    if (!dbUrl.trim()) return;
    setConnecting(true);
    setStatus("");
    try {
      const res = await fetch("http://127.0.0.1:8000/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ db_url: dbUrl }),
      });
      const data = await res.json();
      if (res.ok) onReady(dbUrl);
      else setStatus(`⚠️ ${data.detail}`);
    } catch {
      setStatus("⚠️ Could not reach the server.");
    } finally {
      setConnecting(false);
    }
  };

  const upload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setConnecting(true);
    setStatus("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("http://127.0.0.1:8000/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) onReady(file.name);
      else setStatus(`⚠️ ${data.detail}`);
    } catch {
      setStatus("⚠️ Could not reach the server.");
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="onboarding">
      <button className="back-link" onClick={onBack}>← Back</button>
      <span className="brand-mark">Σ</span>
      <h1>Connect your data</h1>
      <p className="onboarding-sub">Paste a Postgres URL, upload a file, or skip to explore sample data.</p>

      <div className="onboarding-card">
        <label className="field-label">Postgres connection URL</label>
        <input
          type="text"
          placeholder="postgresql://user:pass@host:5432/dbname"
          value={dbUrl}
          onChange={(e) => setDbUrl(e.target.value)}
        />
        <button className="cta" onClick={connect} disabled={connecting}>
          {connecting ? "Connecting..." : "Connect"}
        </button>

        <div className="or-divider">or</div>

        <label className="upload-label">
          Upload a .csv or .sql file
          <input type="file" accept=".csv,.sql" onChange={upload} />
        </label>

        {status && <p className="onboarding-status">{status}</p>}
      </div>

      <button className="skip-link" onClick={() => onReady("Demo e-commerce data")}>
        Skip — use sample data instead →
      </button>
    </div>
  );
}

function ChatApp({ initialSource, onBack }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dbUrl, setDbUrl] = useState("");
  const [dbStatus, setDbStatus] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [activeSource, setActiveSource] = useState(initialSource);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askQuestion = async () => {
    if (!question.trim()) return;
    const userQuestion = question;
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", text: userQuestion }]);
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQuestion }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessages((prev) => [...prev, { role: "error", text: data.detail || "Something went wrong." }]);
      } else {
        setMessages((prev) => [...prev, {
          role: "assistant", explanation: data.explanation, sql: data.generated_sql,
          columns: data.columns, results: data.results,
        }]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "error", text: "Could not reach the server." }]);
    } finally {
      setLoading(false);
    }
  };

  const connectDatabase = async () => {
    if (!dbUrl.trim()) return;
    setConnecting(true);
    setDbStatus("");
    try {
      const res = await fetch("http://127.0.0.1:8000/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ db_url: dbUrl }),
      });
      const data = await res.json();
      setDbStatus(res.ok ? "✅ Connected!" : `⚠️ ${data.detail}`);
      if (res.ok) { setMessages([]); setActiveSource(dbUrl); }
    } catch {
      setDbStatus("⚠️ Could not reach the server.");
    } finally {
      setConnecting(false);
    }
  };

  const uploadFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setConnecting(true);
    setDbStatus("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("http://127.0.0.1:8000/upload", { method: "POST", body: formData });
      const data = await res.json();
      setDbStatus(res.ok ? `✅ ${data.message}` : `⚠️ ${data.detail}`);
      if (res.ok) { setMessages([]); setActiveSource(file.name); }
    } catch {
      setDbStatus("⚠️ Could not reach the server.");
    } finally {
      setConnecting(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  const suggestions = ["Count all rows", "Show me the first 5 records", "What's the average value in each numeric column?"];

  return (
    <div className="app-shell">
      <div className="sidebar">
        <h2>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{marginRight: "6px", verticalAlign: "-2px"}}>
            <ellipse cx="12" cy="5" rx="8" ry="3" stroke="#D97F0C" strokeWidth="1.8"/>
            <path d="M4 5V19C4 20.66 7.58 22 12 22C16.42 22 20 20.66 20 19V5" stroke="#D97F0C" strokeWidth="1.8"/>
            <path d="M4 12C4 13.66 7.58 15 12 15C16.42 15 20 13.66 20 12" stroke="#D97F0C" strokeWidth="1.8"/>
          </svg>
          Data Source
        </h2>
        <input type="text" placeholder="postgresql://user:pass@host/db" value={dbUrl} onChange={(e) => setDbUrl(e.target.value)} />
        <button onClick={connectDatabase} disabled={connecting}>Connect</button>
        <div className="or-divider">or</div>
        <label className="upload-label">
          Upload .csv / .sql
          <input type="file" accept=".csv,.sql" onChange={uploadFile} />
        </label>
        {dbStatus && <p className="db-status">{dbStatus}</p>}
        <div className="active-badge">
          <span className="pulse-dot" />
          <span className="active-text">{activeSource}</span>
        </div>
      </div>

      <div className="chat-area">
        <div className="brand">
          <button className="back-link chat-back" onClick={onBack}>← Change data source</button>
          <span className="brand-mark">Σ</span>
          <h1>SQL Assistant</h1>
        </div>
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <p className="empty-hint">Ask a question about your data — try one of these:</p>
              <div className="chip-row">
                {suggestions.map((ex) => (
                  <button key={ex} className="chip" onClick={() => setQuestion(ex)}>{ex}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>
              {m.role === "user" && <p>{m.text}</p>}
              {m.role === "error" && <p>⚠️ {m.text}</p>}
              {m.role === "assistant" && (
                <>
                  {m.sql && (
                    <div className="trace">
                      <span className="trace-step">schema</span>
                      <span className="trace-line" />
                      <span className="trace-step">sql</span>
                      <span className="trace-line" />
                      <span className="trace-step">result</span>
                    </div>
                  )}
                  <p className="explanation">{m.explanation}</p>
                  {m.sql && (
                    <details>
                      <summary>View SQL</summary>
                      <code>{m.sql}</code>
                    </details>
                  )}
                  {m.results && m.results.length > 0 ? (
                    <table>
                      <thead><tr>{m.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                      <tbody>
                        {m.results.map((row, ri) => (
                          <tr key={ri}>{m.columns.map((c) => <td key={c}>{row[c]}</td>)}</tr>
                        ))}
                      </tbody>
                    </table>
                  ) : m.sql ? (
                    <p className="no-results">No results found.</p>
                  ) : null}
                </>
              )}
            </div>
          ))}
          {loading && <div className="bubble assistant thinking">Thinking...</div>}
          <div ref={bottomRef} />
        </div>

        <div className="input-row">
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={handleKeyDown} placeholder="Ask a follow-up question..." rows={1} />
          <button onClick={askQuestion} disabled={loading}>Ask</button>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState("landing"); // landing | onboarding | chat
  const [activeSource, setActiveSource] = useState("");

  if (view === "landing") return <LandingPage onStart={() => setView("onboarding")} />;
  if (view === "onboarding")
    return (
      <OnboardingPage
        onReady={(src) => { setActiveSource(src); setView("chat"); }}
        onBack={() => setView("landing")}
      />
    );
  return <ChatApp initialSource={activeSource} onBack={() => setView("onboarding")} />;
}

export default App;