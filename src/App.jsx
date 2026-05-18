import React, { useState, useEffect, useCallback } from "react";
import { Routes, Route, Navigate, useNavigate, Link } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import AdminPage from "./pages/AdminPage";

const API = ``;

// ─────────────────────────────────────────────────────────────────────────────
// Protected Route
// ─────────────────────────────────────────────────────────────────────────────
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={S.fullLoader}>Loading…</div>;
  return user ? children : <Navigate to="/login" replace />;
}

// ─────────────────────────────────────────────────────────────────────────────
// Auth Pages
// ─────────────────────────────────────────────────────────────────────────────
function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try { await login(form.username, form.password); navigate("/"); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <AuthLayout>
      <h2 style={S.authTitle}>Welcome back</h2>
      <p style={S.authSubtitle}>Sign in to ArchAnalyse</p>
      {error && <div style={S.authError}>{error}</div>}
      <div style={S.authForm}>
        <label style={S.authLabel}>Username
          <input style={S.authInput} type="text" value={form.username} autoFocus
            placeholder="your_username" onChange={e => setForm({ ...form, username: e.target.value })} />
        </label>
        <label style={S.authLabel}>Password
          <input style={S.authInput} type="password" value={form.password}
            placeholder="••••••••" onChange={e => setForm({ ...form, password: e.target.value })}
            onKeyDown={e => e.key === "Enter" && handleSubmit(e)} />
        </label>
        <button style={{ ...S.authBtn, opacity: loading ? 0.6 : 1 }} disabled={loading} onClick={handleSubmit}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </div>
      <p style={S.authSwitch}>No account? <Link to="/register" style={S.authLink}>Create one</Link></p>
    </AuthLayout>
  );
}

function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault(); setError("");
    if (form.password !== form.confirm) { setError("Passwords do not match"); return; }
    if (form.password.length < 6) { setError("Password must be at least 6 characters"); return; }
    setLoading(true);
    try {
      await register(form.username, form.email, form.password);
      setSuccess(true);
    }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  if (success) {
    return (
      <AuthLayout>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 40, marginBottom: 16 }}>✅</div>
          <h2 style={S.authTitle}>Registration submitted</h2>
          <p style={{ fontSize: 14, color: "#4b5563", lineHeight: 1.6, margin: "0 0 24px" }}>
            Your account is pending admin approval.<br />You will be able to log in once an administrator approves your request.
          </p>
          <Link to="/login" style={{ ...S.authBtn, display: "block", textAlign: "center", textDecoration: "none" }}>
            Back to Sign in
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <h2 style={S.authTitle}>Create account</h2>
      <p style={S.authSubtitle}>Join ArchAnalyse</p>
      {error && <div style={S.authError}>{error}</div>}
      <div style={S.authForm}>
        <label style={S.authLabel}>Username
          <input style={S.authInput} type="text" value={form.username} autoFocus
            placeholder="at least 3 characters" onChange={e => setForm({ ...form, username: e.target.value })} />
        </label>
        <label style={S.authLabel}>Email
          <input style={S.authInput} type="email" value={form.email}
            placeholder="you@example.com" onChange={e => setForm({ ...form, email: e.target.value })} />
        </label>
        <label style={S.authLabel}>Password
          <input style={S.authInput} type="password" value={form.password}
            placeholder="at least 6 characters" onChange={e => setForm({ ...form, password: e.target.value })} />
        </label>
        <label style={S.authLabel}>Confirm password
          <input style={S.authInput} type="password" value={form.confirm}
            placeholder="••••••••" onChange={e => setForm({ ...form, confirm: e.target.value })}
            onKeyDown={e => e.key === "Enter" && handleSubmit(e)} />
        </label>
        <button style={{ ...S.authBtn, opacity: loading ? 0.6 : 1 }} disabled={loading} onClick={handleSubmit}>
          {loading ? "Creating account…" : "Create account"}
        </button>
      </div>
      <p style={S.authSwitch}>Already have an account? <Link to="/login" style={S.authLink}>Sign in</Link></p>
    </AuthLayout>
  );
}

function AuthLayout({ children }) {
  return (
    <div style={S.authPage}>
      <div style={S.authBg}>
        <svg style={{ width: "100%", height: "100%" }} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="sg" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(37,99,235,0.08)" strokeWidth="0.5" />
            </pattern>
            <pattern id="bg" width="100" height="100" patternUnits="userSpaceOnUse">
              <rect width="100" height="100" fill="url(#sg)" />
              <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(37,99,235,0.12)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#bg)" />
          <circle cx="20%" cy="30%" r="140" fill="none" stroke="rgba(37,99,235,0.05)" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx="80%" cy="70%" r="100" fill="none" stroke="rgba(37,99,235,0.05)" strokeWidth="1" strokeDasharray="4 4" />
        </svg>
      </div>
      <div style={S.authCard}>
        <div style={S.authCardLogo}>
          <div style={S.logoMark}>A</div>
          <div><div style={S.logoName}>ArchAnalyse</div><div style={S.logoSub}>Architectural Drawing Intelligence</div></div>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tabs
// ─────────────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "segment",  label: "Wall Segmentation",  icon: "🧱", desc: "Detect and extract wall regions from floor plan images using AI" },
  { id: "history",  label: "History",            icon: "🕘", desc: "Your previous wall segmentation results" },
];

// ─────────────────────────────────────────────────────────────────────────────
// Shared components
// ─────────────────────────────────────────────────────────────────────────────
function SectionCard({ title, description, children }) {
  return (
    <div style={S.card}>
      <div style={S.cardTop}>
        <h2 style={S.cardTitle}>{title}</h2>
        {description && <p style={S.cardDesc}>{description}</p>}
      </div>
      <div style={S.cardBody}>{children}</div>
    </div>
  );
}


// ─────────────────────────────────────────────────────────────────────────────
// History Tab
// ─────────────────────────────────────────────────────────────────────────────
function HistoryTab({ token }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setRecords(await res.json());
    } catch (_) {}
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const handleDelete = async (id) => {
    setDeleting(id);
    try {
      await fetch(`${API}/api/history/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setRecords(prev => prev.filter(r => r.id !== id));
      if (selected?.id === id) setSelected(null);
    } catch (_) {}
    finally { setDeleting(null); }
  };

  const formatDate = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const exportHistoryPdf = async (id, filename) => {
    try {
      const res = await fetch(`${API}/api/history/${id}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) { alert("PDF export failed"); return; }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename.replace(/\.[^.]+$/, "") + "_segmentation.pdf"; a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) { alert("Export failed: " + err.message); }
  };

  if (loading) return <div style={S.historyEmpty}>Loading history…</div>;
  if (!records.length) return (
    <div style={S.historyEmpty}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>🕘</div>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>No history yet</div>
      <div style={{ fontSize: 13, color: "#9ca3af" }}>Run Wall Segmentation to see results here</div>
    </div>
  );

  return (
    <div>
      {/* Grid of history cards */}
      <div style={S.historyGrid}>
        {records.map(r => (
          <div key={r.id}
            style={{ ...S.historyCard, outline: selected?.id === r.id ? "2px solid #2563eb" : "2px solid transparent" }}
            onClick={() => setSelected(r)}>
            <img src={`${API}${r.original_url}`} alt={r.filename} style={S.historyThumb} />
            <div style={S.historyCardBody}>
              <div style={S.historyFilename}>{r.filename}</div>
              <div style={S.historyMeta}>{r.wall_pct}% wall · {r.width}×{r.height}px</div>
              <div style={S.historyDate}>{formatDate(r.created_at)}</div>
              <button
                style={S.deleteBtn}
                disabled={deleting === r.id}
                onClick={e => { e.stopPropagation(); handleDelete(r.id); }}>
                {deleting === r.id ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Detail panel */}
      {selected && (
        <div style={S.card}>
          <div style={S.cardTop}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
              <div>
                <h2 style={S.cardTitle}>{selected.filename}</h2>
                <p style={S.cardDesc}>{selected.wall_pct}% wall coverage · {selected.width}×{selected.height}px · {formatDate(selected.created_at)}</p>
              </div>
              <button style={S.exportPdfBtn} onClick={() => exportHistoryPdf(selected.id, selected.filename)}>⬇ Export PDF</button>
            </div>
          </div>
          <div style={{ ...S.cardBody, ...S.detailGrid }}>
            {[
              { url: selected.original_url,  label: "Original" },
              { url: selected.overlay_url,   label: "Overlay" },
              { url: selected.extracted_url, label: "Extracted Walls" },
            ].map(({ url, label }) => (
              <div key={label} style={S.detailPane}>
                <div style={S.detailPaneHeader}>
                  <span style={S.detailPaneTitle}>{label}</span>
                  <a href={`${API}${url}`} download style={S.dlBtn}>Download</a>
                </div>
                <img src={`${API}${url}`} alt={label} style={S.detailImg} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main App
// ─────────────────────────────────────────────────────────────────────────────
function MainApp() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("segment");

  // Segmentation state
  const [segFiles, setSegFiles]       = useState([]);
  const [results, setResults]         = useState([]);
  const [progress, setProgress]       = useState(null);
  const [isRunning, setIsRunning]     = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [segError, setSegError]       = useState("");

  const onSegFiles = (e) => {
    const files = Array.from(e.target.files).filter(f => f.type.startsWith("image/"));
    setSegFiles(files); setResults([]); setProgress(null); setSelectedIdx(null); setSegError("");
  };

  const handleRunBatch = async () => {
    if (!segFiles.length) return;
    setIsRunning(true); setResults([]); setProgress({ done: 0, total: segFiles.length });
    setSelectedIdx(null); setSegError("");
    const fd = new FormData();
    segFiles.forEach(f => fd.append("images", f));
    try {
      const resp = await fetch(`${API}/api/segment-batch`, {
        method: "POST", body: fd,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!resp.ok) { setSegError("Server error: " + resp.status); return; }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n"); buf = lines.pop();
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const item = JSON.parse(line);
            setResults(prev => { const n = [...prev]; n[item.index] = item; return n; });
            setProgress({ done: item.index + 1, total: item.total });
          } catch (_) {}
        }
      }
    } catch (err) { setSegError("Cannot reach backend: " + err.message); }
    finally { setIsRunning(false); }
  };

  const downloadImg = (b64, name) => {
    const a = document.createElement("a");
    a.href = `data:image/png;base64,${b64}`; a.download = name; a.click();
  };

  const exportSegmentPdf = async (result) => {
    try {
      const res = await fetch(`${API}/api/export-segment-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({
          filename: result.filename,
          wall_pct: String(result.wall_pct),
          width: result.width,
          height: result.height,
          original: result.original,
          overlay: result.overlay,
          extracted: result.extracted,
        }),
      });
      if (!res.ok) { alert("PDF export failed"); return; }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = result.filename.replace(/\.[^.]+$/, "") + "_segmentation.pdf"; a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) { alert("Export failed: " + err.message); }
  };

  const sel = selectedIdx !== null ? results[selectedIdx] : null;
  const readyCount = results.filter(Boolean).length;

  return (
    <div style={S.page}>
      <header style={S.header}>
        <div style={S.headerInner}>
          <div style={S.logo}>
            <div style={S.logoMark}>A</div>
            <div><div style={S.logoName}>ArchAnalyse</div><div style={S.logoSub}>Architectural Drawing Intelligence</div></div>
          </div>
          <nav style={S.nav}>
            {TABS.map(t => (
              <button key={t.id}
                style={{ ...S.navBtn, ...(tab === t.id ? S.navBtnActive : {}) }}
                onClick={() => setTab(t.id)}>
                {t.icon} {t.label}
              </button>
            ))}
          </nav>
          <div style={S.userArea}>
            <span style={S.userGreeting}>👤 {user?.username}</span>
            {user?.is_admin && (
              <button style={S.adminBtn} onClick={() => navigate("/admin")}>Admin</button>
            )}
            <button style={S.logoutBtn} onClick={logout}>Sign out</button>
          </div>
        </div>
      </header>

      <div style={S.hero}>
        <div style={S.heroInner}>
          <div style={S.heroBadge}>{TABS.find(t => t.id === tab)?.icon} {TABS.find(t => t.id === tab)?.label}</div>
          <p style={S.heroDesc}>{TABS.find(t => t.id === tab)?.desc}</p>
        </div>
      </div>

      <main style={S.main}>
        {/* ══ SEGMENTATION ══ */}
        {tab === "segment" && (
          <>
            <SectionCard title="Step 1 — Choose floor plan images"
              description="Select one or more floor plan images. Results are automatically saved to your history.">
              <div style={S.segUploadRow}>
                <label style={S.fileBtn}>
                  Choose images
                  <input type="file" accept="image/*" multiple onChange={onSegFiles} style={{ display: "none" }} />
                </label>
                {segFiles.length > 0 && <span style={S.fileNameActive}>{segFiles.length} image{segFiles.length > 1 ? "s" : ""} selected</span>}
              </div>
              {segFiles.length > 0 && (
                <div style={S.fileListPreview}>
                  {segFiles.map((f, i) => <span key={i} style={S.fileChip}>{f.name}</span>)}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Step 2 — Run segmentation">
              <p style={S.stepNote}>Results are saved to your History tab automatically.</p>
              <div style={S.actionRow}>
                <button style={{ ...S.primaryBtn, opacity: (!segFiles.length || isRunning) ? 0.6 : 1 }}
                  disabled={!segFiles.length || isRunning} onClick={handleRunBatch}>
                  {isRunning ? "Processing…" : "Run Segmentation"}
                </button>
              </div>
              {progress && (
                <div style={S.progressBlock}>
                  <div style={S.progressInfo}>
                    <span>{isRunning ? `Processing image ${progress.done} of ${progress.total}…` : `All ${progress.total} image${progress.total > 1 ? "s" : ""} processed`}</span>
                    <span style={S.progressPct}>{Math.round((progress.done / progress.total) * 100)}%</span>
                  </div>
                  <div style={S.progressTrack}><div style={{ ...S.progressFill, width: `${(progress.done / progress.total) * 100}%` }} /></div>
                </div>
              )}
              {segError && <div style={S.errorBox}>{segError}</div>}
            </SectionCard>

            {readyCount > 0 && (
              <SectionCard title="Step 3 — View results" description="Click a thumbnail to inspect the result.">
                <div style={S.thumbRow}>
                  {results.map((r, i) => r && (
                    <button key={i}
                      style={{ ...S.thumb, outline: selectedIdx === i ? "2px solid #2563eb" : "2px solid transparent" }}
                      onClick={() => setSelectedIdx(i)}>
                      {r.error ? <div style={S.thumbErr}>⚠</div>
                        : <img src={`data:image/png;base64,${r.original}`} alt={r.filename} style={S.thumbImg} />}
                      <div style={S.thumbLabel}>{r.filename}</div>
                      {!r.error && <div style={S.thumbStat}>{r.wall_pct}% wall</div>}
                    </button>
                  ))}
                </div>
                {sel && !sel.error && (
                  <div style={S.detail}>
                    <div style={S.detailHeader}>
                      <strong>{sel.filename}</strong>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={S.detailMeta}>{sel.width} × {sel.height} px · {sel.wall_pct}% wall coverage</span>
                        <button style={S.exportPdfBtn} onClick={() => exportSegmentPdf(sel)}>⬇ Export PDF</button>
                      </div>
                    </div>
                    <div style={S.detailGrid}>
                      {[{ key: "overlay", label: "Overlay", note: "Wall regions highlighted in red" },
                        { key: "extracted", label: "Extracted Walls", note: "Wall pixels only" }].map(({ key, label, note }) => (
                        <div key={key} style={S.detailPane}>
                          <div style={S.detailPaneHeader}>
                            <span style={S.detailPaneTitle}>{label}</span>
                            <button style={S.dlBtn} onClick={() => downloadImg(sel[key], `${sel.filename}_${key}.png`)}>Download</button>
                          </div>
                          <img src={`data:image/png;base64,${sel[key]}`} alt={label} style={S.detailImg} />
                          <p style={S.detailNote}>{note}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {sel?.error && <div style={S.errorBox}>Could not process {sel.filename}: {sel.error}</div>}
              </SectionCard>
            )}
          </>
        )}

        {/* ══ HISTORY ══ */}
        {tab === "history" && <HistoryTab token={token} />}

      </main>

      <footer style={S.footer}>ArchAnalyse · Built by a team of 3</footer>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/admin"    element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
      <Route path="/*"        element={<ProtectedRoute><MainApp /></ProtectedRoute>} />
    </Routes>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────
const S = {
  fullLoader: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f4f6f9", fontSize: 15, color: "#6b7280" },
  page:  { minHeight: "100vh", background: "#f4f6f9", fontFamily: "'Inter', 'DM Sans', system-ui, sans-serif", color: "#111" },
  header:      { background: "#fff", borderBottom: "1px solid #e5e7eb", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 1100, margin: "0 auto", padding: "0 24px", height: 60, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 },
  logo:        { display: "flex", alignItems: "center", gap: 10, flexShrink: 0 },
  logoMark:    { width: 34, height: 34, background: "#2563eb", borderRadius: 8, color: "#fff", fontWeight: 800, fontSize: 18, display: "flex", alignItems: "center", justifyContent: "center" },
  logoName:    { fontWeight: 700, fontSize: 15, color: "#111" },
  logoSub:     { fontSize: 11, color: "#6b7280", marginTop: 1 },
  nav:         { display: "flex", gap: 4, flex: 1, justifyContent: "center" },
  navBtn:      { padding: "7px 16px", borderRadius: 8, border: "none", background: "transparent", color: "#6b7280", fontWeight: 500, fontSize: 14, cursor: "pointer", transition: "all 0.15s" },
  navBtnActive:{ background: "#eff6ff", color: "#2563eb", fontWeight: 600 },
  userArea:     { display: "flex", alignItems: "center", gap: 10, flexShrink: 0 },
  userGreeting: { fontSize: 13, color: "#374151", fontWeight: 500 },
  logoutBtn:    { padding: "6px 14px", background: "#fff", border: "1px solid #d1d5db", borderRadius: 7, fontSize: 13, color: "#6b7280", cursor: "pointer", fontWeight: 500 },
  adminBtn:     { padding: "6px 14px", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 7, fontSize: 13, color: "#2563eb", cursor: "pointer", fontWeight: 600 },
  hero:      { background: "#fff", borderBottom: "1px solid #e5e7eb" },
  heroInner: { maxWidth: 1100, margin: "0 auto", padding: "24px 24px" },
  heroBadge: { display: "inline-block", background: "#eff6ff", color: "#2563eb", padding: "4px 12px", borderRadius: 20, fontSize: 13, fontWeight: 600, marginBottom: 8 },
  heroDesc:  { fontSize: 15, color: "#4b5563", maxWidth: 620, margin: 0, lineHeight: 1.6 },
  main: { maxWidth: 1100, margin: "0 auto", padding: "28px 24px", display: "flex", flexDirection: "column", gap: 20 },
  card:      { background: "#fff", borderRadius: 12, border: "1px solid #e5e7eb", overflow: "hidden" },
  cardTop:   { padding: "20px 24px 16px", borderBottom: "1px solid #f3f4f6" },
  cardTitle: { fontSize: 16, fontWeight: 700, color: "#111", marginBottom: 4 },
  cardDesc:  { fontSize: 13, color: "#6b7280", lineHeight: 1.6, margin: 0 },
  cardBody:  { padding: "20px 24px" },
  fileRow:      { display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, padding: "12px 0", borderBottom: "1px solid #f3f4f6" },
  fileRowLeft:  { flex: "0 0 260px" },
  fileRowLabel: { display: "block", fontSize: 14, fontWeight: 600, color: "#111", marginBottom: 2 },
  fileRowHint:  { display: "block", fontSize: 12, color: "#9ca3af" },
  fileRowRight: { display: "flex", alignItems: "center", gap: 10, flex: 1 },
  fileBtn:      { display: "inline-block", padding: "7px 16px", background: "#f3f4f6", border: "1px solid #d1d5db", borderRadius: 7, fontSize: 13, fontWeight: 500, color: "#374151", cursor: "pointer", whiteSpace: "nowrap" },
  primaryBtn:   { padding: "10px 28px", background: "#2563eb", color: "#fff", border: "none", borderRadius: 8, fontWeight: 600, fontSize: 15, cursor: "pointer" },
  secondaryBtn: { padding: "10px 24px", background: "#fff", color: "#2563eb", border: "1px solid #2563eb", borderRadius: 8, fontWeight: 600, fontSize: 15, cursor: "pointer" },
  dlBtn:        { padding: "5px 12px", background: "#fff", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 12, cursor: "pointer", color: "#374151", textDecoration: "none" },
  fileNameEmpty:  { fontSize: 13, color: "#9ca3af" },
  fileNameActive: { fontSize: 13, color: "#111", fontWeight: 500 },
  stepNote:   { fontSize: 13, color: "#6b7280", marginBottom: 16, lineHeight: 1.6 },
  actionRow:  { display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" },
  statusRow:  { marginTop: 14, fontSize: 13, color: "#6b7280", display: "flex", alignItems: "center", gap: 6 },
  spinner:    { display: "inline-block", width: 14, height: 14, border: "2px solid #d1d5db", borderTopColor: "#2563eb", borderRadius: "50%", animation: "spin 0.7s linear infinite" },
  successBanner: { marginTop: 14, padding: "10px 14px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, fontSize: 13, color: "#15803d" },
  errorBox:   { marginTop: 14, padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: 13, color: "#dc2626" },
  segUploadRow:    { display: "flex", alignItems: "center", gap: 12, marginBottom: 12 },
  fileListPreview: { display: "flex", flexWrap: "wrap", gap: 6 },
  fileChip:        { padding: "3px 10px", background: "#eff6ff", color: "#2563eb", borderRadius: 20, fontSize: 12, fontWeight: 500 },
  progressBlock: { marginTop: 16 },
  progressInfo:  { display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13, color: "#4b5563" },
  progressPct:   { fontWeight: 700, color: "#2563eb" },
  progressTrack: { height: 6, background: "#e5e7eb", borderRadius: 99, overflow: "hidden" },
  progressFill:  { height: "100%", background: "#2563eb", borderRadius: 99, transition: "width 0.3s ease" },
  thumbRow:  { display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 24 },
  thumb:     { background: "none", border: "none", cursor: "pointer", borderRadius: 10, overflow: "hidden", width: 140, textAlign: "left", padding: 0 },
  thumbImg:  { width: 140, height: 100, objectFit: "cover", display: "block", background: "#f3f4f6" },
  thumbErr:  { width: 140, height: 100, display: "flex", alignItems: "center", justifyContent: "center", background: "#fef2f2", fontSize: 24 },
  thumbLabel:{ padding: "5px 6px 2px", fontSize: 11, color: "#374151", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", background: "#fff" },
  thumbStat: { padding: "0 6px 6px", fontSize: 11, fontWeight: 600, color: "#2563eb", background: "#fff" },
  detail:           { borderTop: "1px solid #f3f4f6", paddingTop: 20 },
  detailHeader:     { display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  detailMeta:       { fontSize: 12, color: "#9ca3af", fontFamily: "monospace" },
  detailGrid:       { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 },
  detailPane:       { border: "1px solid #e5e7eb", borderRadius: 10, overflow: "hidden" },
  detailPaneHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", background: "#f9fafb", borderBottom: "1px solid #e5e7eb" },
  detailPaneTitle:  { fontSize: 13, fontWeight: 600, color: "#374151" },
  detailImg:        { width: "100%", display: "block", objectFit: "contain", maxHeight: 360, background: "#f3f4f6" },
  detailNote:       { padding: "8px 14px", fontSize: 12, color: "#9ca3af", margin: 0, background: "#fff" },
  footer: { textAlign: "center", padding: "28px 0", fontSize: 12, color: "#9ca3af", borderTop: "1px solid #e5e7eb", background: "#fff", marginTop: 40 },

  // History
  historyEmpty: { textAlign: "center", padding: "60px 24px", color: "#6b7280", fontSize: 15 },
  historyGrid:  { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 24 },
  historyCard:  { background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, overflow: "hidden", cursor: "pointer", transition: "box-shadow 0.15s" },
  historyThumb: { width: "100%", height: 130, objectFit: "cover", display: "block", background: "#f3f4f6" },
  historyCardBody: { padding: "10px 12px 12px" },
  historyFilename: { fontSize: 12, fontWeight: 600, color: "#111", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginBottom: 3 },
  historyMeta:     { fontSize: 11, color: "#2563eb", fontWeight: 600, marginBottom: 2 },
  historyDate:     { fontSize: 11, color: "#9ca3af", marginBottom: 8 },
  deleteBtn:       { padding: "4px 10px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 6, fontSize: 11, color: "#dc2626", cursor: "pointer", fontWeight: 500 },

  // Auth
  authPage:    { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f0f4ff", position: "relative", fontFamily: "'Inter', system-ui, sans-serif" },
  authBg:      { position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" },
  authCard:    { position: "relative", zIndex: 1, background: "#fff", border: "1px solid #e5e7eb", borderRadius: 16, padding: "2.5rem 2.75rem", width: "100%", maxWidth: 400, boxShadow: "0 4px 24px rgba(37,99,235,0.08)" },
  authCardLogo:{ display: "flex", alignItems: "center", gap: 10, marginBottom: "2rem" },
  authTitle:   { fontSize: "1.4rem", fontWeight: 700, color: "#111", margin: "0 0 0.2rem" },
  authSubtitle:{ fontSize: "0.82rem", color: "#6b7280", margin: "0 0 1.5rem", textTransform: "uppercase", letterSpacing: "0.04em" },
  authForm:    { display: "flex", flexDirection: "column", gap: "1rem" },
  authLabel:   { display: "flex", flexDirection: "column", gap: "0.3rem", fontSize: "0.75rem", fontWeight: 600, color: "#374151", textTransform: "uppercase", letterSpacing: "0.05em" },
  authInput:   { background: "#f9fafb", border: "1px solid #d1d5db", borderRadius: 8, padding: "0.6rem 0.8rem", color: "#111", fontSize: "0.9rem", outline: "none", fontFamily: "inherit" },
  authBtn:     { marginTop: "0.4rem", background: "#2563eb", border: "none", borderRadius: 8, color: "#fff", fontFamily: "inherit", fontSize: "0.85rem", fontWeight: 600, letterSpacing: "0.04em", textTransform: "uppercase", padding: "0.75rem 1rem", cursor: "pointer" },
  authError:   { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626", fontSize: "0.8rem", padding: "0.55rem 0.8rem", marginBottom: "0.5rem" },
  authSwitch:  { marginTop: "1.5rem", fontSize: "0.8rem", color: "#9ca3af", textAlign: "center" },
  authLink:    { color: "#2563eb", textDecoration: "none", fontWeight: 500 },

  // Export PDF button
  exportPdfBtn: { padding: "7px 14px", background: "#1d4ed8", border: "none", borderRadius: 7, color: "#fff", fontSize: 12, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap" },
};