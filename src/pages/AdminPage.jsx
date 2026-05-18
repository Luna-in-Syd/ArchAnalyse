import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function AdminPage() {
  const { user, token } = useAuth();
  const navigate = useNavigate();

  const [tab, setTab] = useState("pending"); // "pending" | "all"
  const [pendingUsers, setPendingUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null); // { type: "success"|"error", text }

  // Redirect non-admins away
  useEffect(() => {
    if (user && !user.is_admin) navigate("/", { replace: true });
  }, [user, navigate]);

  const fetchPending = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/admin/pending`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load pending users");
      setPendingUsers(await res.json());
    } catch (e) {
      setActionMsg({ type: "error", text: e.message });
    } finally {
      setLoading(false);
    }
  }, [token]);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load users");
      setAllUsers(await res.json());
    } catch (e) {
      setActionMsg({ type: "error", text: e.message });
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (tab === "pending") fetchPending();
    else fetchAll();
  }, [tab, fetchPending, fetchAll]);

  const approveUser = async (userId, username) => {
    try {
      const res = await fetch(`${API}/api/admin/approve/${userId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Approval failed");
      setActionMsg({ type: "success", text: `${username} has been approved.` });
      fetchPending();
      fetchAll();
    } catch (e) {
      setActionMsg({ type: "error", text: e.message });
    }
  };

  const deleteUser = async (userId, username) => {
    if (!window.confirm(`Remove user "${username}"? This cannot be undone.`)) return;
    try {
      const res = await fetch(`${API}/api/admin/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Deletion failed");
      setActionMsg({ type: "success", text: `${username} has been removed.` });
      fetchPending();
      fetchAll();
    } catch (e) {
      setActionMsg({ type: "error", text: e.message });
    }
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" });
  };

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.headerInner}>
          <div style={S.logo}>
            <div style={S.logoMark}>A</div>
            <div>
              <div style={S.logoName}>ArchAnalyse</div>
              <div style={S.logoSub}>Admin Panel</div>
            </div>
          </div>
          <button style={S.backBtn} onClick={() => navigate("/")}>
            ← Back to App
          </button>
        </div>
      </div>

      <div style={S.main}>
        <div style={S.titleRow}>
          <h1 style={S.pageTitle}>User Management</h1>
          <p style={S.pageDesc}>Approve new registrations and manage existing users.</p>
        </div>

        {actionMsg && (
          <div style={actionMsg.type === "success" ? S.successBanner : S.errorBox}>
            {actionMsg.text}
            <button style={S.dismissBtn} onClick={() => setActionMsg(null)}>✕</button>
          </div>
        )}

        <div style={S.card}>
          <div style={S.tabRow}>
            <button
              style={{ ...S.tabBtn, ...(tab === "pending" ? S.tabBtnActive : {}) }}
              onClick={() => setTab("pending")}
            >
              Pending Approval
              {pendingUsers.length > 0 && (
                <span style={S.badge}>{pendingUsers.length}</span>
              )}
            </button>
            <button
              style={{ ...S.tabBtn, ...(tab === "all" ? S.tabBtnActive : {}) }}
              onClick={() => setTab("all")}
            >
              All Users
            </button>
          </div>

          <div style={S.cardBody}>
            {loading && <div style={S.emptyState}>Loading…</div>}

            {/* PENDING TAB */}
            {!loading && tab === "pending" && (
              pendingUsers.length === 0 ? (
                <div style={S.emptyState}>
                  <div style={S.emptyIcon}>✓</div>
                  <div>No pending approvals</div>
                </div>
              ) : (
                <table style={S.table}>
                  <thead>
                    <tr>
                      <th style={S.th}>Username</th>
                      <th style={S.th}>Email</th>
                      <th style={S.th}>Registered</th>
                      <th style={S.th}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingUsers.map((u) => (
                      <tr key={u.id} style={S.tr}>
                        <td style={S.td}>
                          <span style={S.username}>{u.username}</span>
                        </td>
                        <td style={S.td}>{u.email}</td>
                        <td style={S.td}>{formatDate(u.created_at)}</td>
                        <td style={S.td}>
                          <div style={S.actionBtns}>
                            <button
                              style={S.approveBtn}
                              onClick={() => approveUser(u.id, u.username)}
                            >
                              Approve
                            </button>
                            <button
                              style={S.rejectBtn}
                              onClick={() => deleteUser(u.id, u.username)}
                            >
                              Reject
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            )}

            {/* ALL USERS TAB */}
            {!loading && tab === "all" && (
              allUsers.length === 0 ? (
                <div style={S.emptyState}>No users yet</div>
              ) : (
                <table style={S.table}>
                  <thead>
                    <tr>
                      <th style={S.th}>Username</th>
                      <th style={S.th}>Email</th>
                      <th style={S.th}>Status</th>
                      <th style={S.th}>Registered</th>
                      <th style={S.th}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allUsers.map((u) => (
                      <tr key={u.id} style={S.tr}>
                        <td style={S.td}>
                          <span style={S.username}>{u.username}</span>
                        </td>
                        <td style={S.td}>{u.email}</td>
                        <td style={S.td}>
                          <span style={u.is_approved ? S.badgeApproved : S.badgePending}>
                            {u.is_approved ? "Approved" : "Pending"}
                          </span>
                        </td>
                        <td style={S.td}>{formatDate(u.created_at)}</td>
                        <td style={S.td}>
                          <div style={S.actionBtns}>
                            {!u.is_approved && (
                              <button
                                style={S.approveBtn}
                                onClick={() => approveUser(u.id, u.username)}
                              >
                                Approve
                              </button>
                            )}
                            <button
                              style={S.rejectBtn}
                              onClick={() => deleteUser(u.id, u.username)}
                            >
                              Remove
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const S = {
  page: { minHeight: "100vh", background: "#f4f6f9", fontFamily: "'Inter', 'DM Sans', system-ui, sans-serif", color: "#111" },
  header: { background: "#fff", borderBottom: "1px solid #e5e7eb", position: "sticky", top: 0, zIndex: 100 },
  headerInner: { maxWidth: 1100, margin: "0 auto", padding: "0 24px", height: 60, display: "flex", alignItems: "center", justifyContent: "space-between" },
  logo: { display: "flex", alignItems: "center", gap: 10 },
  logoMark: { width: 34, height: 34, background: "#2563eb", borderRadius: 8, color: "#fff", fontWeight: 800, fontSize: 18, display: "flex", alignItems: "center", justifyContent: "center" },
  logoName: { fontWeight: 700, fontSize: 15, color: "#111" },
  logoSub: { fontSize: 11, color: "#6b7280", marginTop: 1 },
  backBtn: { padding: "7px 16px", background: "#fff", border: "1px solid #d1d5db", borderRadius: 7, fontSize: 13, color: "#374151", cursor: "pointer", fontWeight: 500 },
  main: { maxWidth: 1100, margin: "0 auto", padding: "32px 24px", display: "flex", flexDirection: "column", gap: 20 },
  titleRow: { marginBottom: 4 },
  pageTitle: { fontSize: 22, fontWeight: 700, color: "#111", margin: "0 0 6px" },
  pageDesc: { fontSize: 14, color: "#6b7280", margin: 0 },
  successBanner: { padding: "12px 16px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, fontSize: 13, color: "#15803d", display: "flex", justifyContent: "space-between", alignItems: "center" },
  errorBox: { padding: "12px 16px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: 13, color: "#dc2626", display: "flex", justifyContent: "space-between", alignItems: "center" },
  dismissBtn: { background: "none", border: "none", cursor: "pointer", fontSize: 14, color: "inherit", padding: "0 4px" },
  card: { background: "#fff", borderRadius: 12, border: "1px solid #e5e7eb", overflow: "hidden" },
  tabRow: { display: "flex", borderBottom: "1px solid #e5e7eb", padding: "0 8px" },
  tabBtn: { padding: "14px 20px", border: "none", background: "transparent", fontSize: 14, fontWeight: 500, color: "#6b7280", cursor: "pointer", display: "flex", alignItems: "center", gap: 8, borderBottom: "2px solid transparent", marginBottom: -1 },
  tabBtnActive: { color: "#2563eb", fontWeight: 600, borderBottomColor: "#2563eb" },
  badge: { background: "#fee2e2", color: "#dc2626", borderRadius: 20, padding: "1px 7px", fontSize: 11, fontWeight: 700 },
  cardBody: { padding: "8px 0" },
  emptyState: { textAlign: "center", padding: "48px 24px", color: "#9ca3af", fontSize: 14 },
  emptyIcon: { fontSize: 28, marginBottom: 8, color: "#86efac" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: { padding: "10px 20px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.04em", borderBottom: "1px solid #f3f4f6" },
  tr: { borderBottom: "1px solid #f9fafb" },
  td: { padding: "14px 20px", fontSize: 13, color: "#374151", verticalAlign: "middle" },
  username: { fontWeight: 600, color: "#111" },
  actionBtns: { display: "flex", gap: 8 },
  approveBtn: { padding: "5px 14px", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 6, fontSize: 12, fontWeight: 600, color: "#2563eb", cursor: "pointer" },
  rejectBtn: { padding: "5px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 6, fontSize: 12, fontWeight: 600, color: "#dc2626", cursor: "pointer" },
  badgeApproved: { padding: "3px 10px", background: "#f0fdf4", color: "#16a34a", borderRadius: 20, fontSize: 12, fontWeight: 600 },
  badgePending: { padding: "3px 10px", background: "#fffbeb", color: "#d97706", borderRadius: 20, fontSize: 12, fontWeight: 600 },
};
