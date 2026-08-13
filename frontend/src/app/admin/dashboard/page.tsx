"use client";
import { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";

const MASTER = "https://aurabiz.onrender.com";

interface License {
  id: string; license_key: string; plan: string; status: string;
  ai_tier: string; owner_name: string; owner_email: string; owner_phone: string;
  amount_paid: number; machine_id: string | null; activations_used: number;
  max_activations: number; expires_at: string; created_at: string; tenant_id: string;
}
interface Stats { total: number; activated: number; issued: number; revoked: number; revenue: number; paid_ai: number; free_ai: number; by_plan: Record<string, number>; }
interface Toast { id: number; message: string; type: "success" | "error" | "info"; }

/* ─── Toast Component ─── */
function ToastContainer({ toasts, remove }: { toasts: Toast[]; remove: (id: number) => void }) {
  if (!toasts.length) return null;
  return (
    <div className="fixed top-4 right-4 z-[100] space-y-2">
      {toasts.map(t => (
        <div key={t.id} className={`px-4 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2 ${t.type === "success" ? "bg-emerald-500 text-white" : t.type === "error" ? "bg-red-500 text-white" : "bg-blue-500 text-white"}`}>
          <span>{t.type === "success" ? "✓" : t.type === "error" ? "✕" : "ℹ"}</span>
          {t.message}
          <button onClick={() => remove(t.id)} className="ml-2 opacity-70 hover:opacity-100">✕</button>
        </div>
      ))}
    </div>
  );
}

/* ─── Confirm Dialog ─── */
function ConfirmDialog({ message, onConfirm, onCancel }: { message: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[90] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-6 max-w-sm w-full">
        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4"><span className="text-red-500 text-xl">⚠️</span></div>
        <p className="text-center text-gray-700 font-medium mb-6">{message}</p>
        <div className="flex gap-3">
          <button onClick={onCancel} className="flex-1 py-2.5 rounded-xl bg-gray-100 text-gray-700 font-medium hover:bg-gray-200">Cancel</button>
          <button onClick={onConfirm} className="flex-1 py-2.5 rounded-xl bg-red-500 text-white font-medium hover:bg-red-600">Confirm</button>
        </div>
      </div>
    </div>
  );
}

const PLANS: Record<string, { price: number; color: string; bg: string; border: string; features: string[] }> = {
  starter: { price: 999, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200", features: ["100 Products", "500 Messages/mo", "1 User", "Free AI", "Basic Analytics", "Email Support"] },
  growth: { price: 2499, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", features: ["500 Products", "2500 Messages/mo", "5 Users", "Free + Paid AI", "Revenue Tracking", "Priority Support", "Broadcast", "Templates"] },
  enterprise: { price: 4999, color: "text-purple-600", bg: "bg-purple-50", border: "border-purple-200", features: ["Unlimited Products", "Unlimited Messages", "Unlimited Users", "Free + Paid AI", "Advanced Analytics", "Dedicated Support", "Custom AI Training", "API Access", "White Label"] },
};

export default function AdminDashboard() {
  const router = useRouter();
  const [page, setPage] = useState("dashboard");
  const [stats, setStats] = useState<Stats | null>(null);
  const [licenses, setLicenses] = useState<License[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [copied, setCopied] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<License | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [confirmAction, setConfirmAction] = useState<(() => Promise<void>) | null>(null);
  const [confirmMsg, setConfirmMsg] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const addToast = useCallback((message: string, type: Toast["type"] = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  }, []);

  const removeToast = useCallback((id: number) => setToasts(prev => prev.filter(t => t.id !== id)), []);

  useEffect(() => {
    const t = localStorage.getItem("admin_token");
    if (!t) { router.push("/admin-login"); return; }
    load(t);
  }, []);

  const load = async (token: string) => {
    try {
      const h = { Authorization: `Bearer ${token}` };
      const [sRes, lRes] = await Promise.all([
        fetch(`${MASTER}/api/license/admin/licenses/stats`, { headers: h }),
        fetch(`${MASTER}/api/license/admin/licenses`, { headers: h }),
      ]);
      if (!sRes.ok || !lRes.ok) {
        // 401 = token invalid/expired → re-login required; else backend error
        const status = sRes.ok ? lRes.status : sRes.status;
        if (status === 401 || status === 403) {
          setLoadError("Session expired — phir se login karo. (Token invalid)");
        } else {
          setLoadError(`Backend se data nahi mila (HTTP ${status}). Master backend check karo.`);
        }
        setStats(null);
        setLicenses([]);
        return;
      }
      const s = await sRes.json();
      const l = await lRes.json();
      setLoadError("");
      if (s) setStats(s);
      if (l) setLicenses(l.licenses || []);
    } catch (e) { setLoadError("Network error — backend reachable nahi hai. Phir try karo."); }
    setLoading(false);
    setRefreshing(false);
  };

  const refresh = () => { setRefreshing(true); const t = localStorage.getItem("admin_token"); if (t) load(t); };

  const handleCopy = async (key: string) => {
    try { await navigator.clipboard.writeText(key); setCopied(key); addToast("License key copied!", "success"); setTimeout(() => setCopied(null), 2000); }
    catch { addToast("Failed to copy", "error"); }
  };

  const handleRevoke = (key: string, name: string) => {
    setConfirmMsg(`Revoke license for ${name}? This cannot be undone.`);
    setConfirmAction(async () => {
      const token = localStorage.getItem("admin_token");
      try {
        const res = await fetch(`${MASTER}/api/license/admin/licenses/${key}/revoke`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
        if (res.ok) { addToast("License revoked", "success"); load(token!); }
        else { addToast("Revoke failed", "error"); }
      } catch { addToast("Network error", "error"); }
      setConfirmAction(null);
    });
  };

  const filtered = useMemo(() => {
    let list = licenses;
    if (search) { const q = search.toLowerCase(); list = list.filter(l => l.owner_name?.toLowerCase().includes(q) || l.owner_email?.toLowerCase().includes(q) || l.license_key?.toLowerCase().includes(q)); }
    if (filter !== "all") list = list.filter(l => l.status === filter);
    return list;
  }, [licenses, search, filter]);

  const logout = () => { localStorage.removeItem("admin_token"); router.push("/admin-login"); };

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-500 text-sm">Dashboard load ho raha hai...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <ToastContainer toasts={toasts} remove={removeToast} />
      {confirmAction && <ConfirmDialog message={confirmMsg} onConfirm={confirmAction} onCancel={() => setConfirmAction(null)} />}
      {loadError && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[80] w-full max-w-lg px-4">
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm font-medium px-4 py-3 rounded-xl shadow-lg flex items-center justify-between gap-3">
            <span>{loadError}</span>
            <button onClick={() => { setLoadError(""); const t = localStorage.getItem("admin_token"); if (t) load(t); }} className="text-red-500 font-bold hover:text-red-700 whitespace-nowrap">Retry</button>
          </div>
        </div>
      )}
      {/* SIDEBAR */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg shadow-amber-200">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <div>
              <h1 className="text-gray-900 font-bold">AuraBiz</h1>
              <p className="text-gray-400 text-xs">Super Admin Console</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {[
            { id: "dashboard", icon: "📊", label: "Dashboard", desc: "Overview & stats" },
            { id: "customers", icon: "👥", label: "Customers", desc: "Manage customers" },
            { id: "licenses", icon: "🔑", label: "Licenses", desc: "All licenses" },
            { id: "revenue", icon: "💰", label: "Revenue", desc: "Earnings & payments" },
            { id: "plans", icon: "📦", label: "Plans & Pricing", desc: "Plan management" },
            { id: "analytics", icon: "📈", label: "Analytics", desc: "Growth insights" },
            { id: "settings", icon: "⚙️", label: "Settings", desc: "Platform config" },
          ].map(item => (
            <button key={item.id} onClick={() => setPage(item.id)}
              className={`w-full flex items-start gap-3 px-4 py-3 rounded-xl text-left transition-all ${page === item.id ? "bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 shadow-sm" : "hover:bg-gray-50 border border-transparent"}`}>
              <span className="text-lg mt-0.5">{item.icon}</span>
              <div>
                <p className={`text-sm font-semibold ${page === item.id ? "text-amber-700" : "text-gray-700"}`}>{item.label}</p>
                <p className="text-xs text-gray-400">{item.desc}</p>
              </div>
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 mb-3 border border-amber-100">
            <p className="text-xs text-amber-600 font-semibold">Total Revenue</p>
            <p className="text-xl font-bold text-amber-700">₹{(stats?.revenue || 0).toLocaleString()}</p>
          </div>
          <button onClick={logout} className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-gray-500 hover:bg-red-50 hover:text-red-500 transition-all">
            <span>🚪</span> Logout
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-200 px-8 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 capitalize">{page}</h2>
              <p className="text-sm text-gray-400 mt-0.5">Welcome back, Super Admin</p>
            </div>
            <div className="flex items-center gap-4">
              <button onClick={refresh} disabled={refreshing} className={`text-sm px-3 py-1.5 rounded-lg border ${refreshing ? "opacity-50" : "hover:bg-gray-50"}`}>{refreshing ? "⟳ Refreshing..." : "⟳ Refresh"}</button>
              <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center text-white font-bold shadow-lg shadow-amber-200">A</div>
            </div>
          </div>
        </div>

        <div className="p-8">
          {page === "dashboard" && <DashboardView stats={stats} licenses={licenses} setPage={setPage} />}
          {page === "customers" && <CustomersView licenses={licenses} search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} setSelectedCustomer={setSelectedCustomer} />}
          {page === "licenses" && <LicensesView licenses={filtered} search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} handleCopy={handleCopy} copied={copied} handleRevoke={handleRevoke} />}
          {page === "revenue" && <RevenueView stats={stats} licenses={licenses} />}
          {page === "plans" && <PlansView stats={stats} />}
          {page === "analytics" && <AnalyticsView stats={stats} licenses={licenses} />}
          {page === "settings" && <SettingsView />}
        </div>
      </main>

      {/* CUSTOMER DETAIL MODAL */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedCustomer(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900">Customer Details</h3>
              <button onClick={() => setSelectedCustomer(null)} className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200">✕</button>
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center text-white text-xl font-bold">{selectedCustomer.owner_name?.[0] || "?"}</div>
                <div><p className="text-lg font-semibold text-gray-900">{selectedCustomer.owner_name}</p><p className="text-gray-500">{selectedCustomer.owner_email}</p></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <InfoBlock label="Phone" value={selectedCustomer.owner_phone || "N/A"} />
                <InfoBlock label="Plan" value={selectedCustomer.plan} />
                <InfoBlock label="Status" value={selectedCustomer.status} />
                <InfoBlock label="AI Tier" value={selectedCustomer.ai_tier} />
                <InfoBlock label="Amount Paid" value={`₹${selectedCustomer.amount_paid}`} />
                <InfoBlock label="Activated" value={`${selectedCustomer.activations_used}/${selectedCustomer.max_activations}`} />
                <InfoBlock label="License Key" value={selectedCustomer.license_key} mono />
                <InfoBlock label="Expires" value={selectedCustomer.expires_at ? new Date(selectedCustomer.expires_at).toLocaleDateString("en-IN") : "N/A"} />
                <InfoBlock label="Joined" value={new Date(selectedCustomer.created_at).toLocaleDateString("en-IN")} />
                <InfoBlock label="Machine ID" value={selectedCustomer.machine_id || "Not activated"} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── DASHBOARD ─── */
function DashboardView({ stats, licenses, setPage }: { stats: Stats | null; licenses: License[]; setPage: (p: string) => void }) {
  const recent = [...licenses].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 7);
  const activePct = stats?.total ? Math.round((stats.activated / stats.total) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard icon="💰" label="Total Revenue" value={`₹${(stats?.revenue || 0).toLocaleString()}`} trend="+12%" trendUp color="amber" />
        <StatCard icon="👥" label="Total Customers" value={stats?.total || 0} trend={`+${stats?.issued || 0} pending`} trendUp color="blue" />
        <StatCard icon="✅" label="Active Licenses" value={stats?.activated || 0} trend={`${activePct}% active`} trendUp color="emerald" />
        <StatCard icon="🤖" label="Paid AI Users" value={stats?.paid_ai || 0} trend={`${stats?.free_ai || 0} free`} trendUp color="purple" />
      </div>

      {/* Plan Distribution */}
      <div className="grid grid-cols-3 gap-5">
        {Object.entries(PLANS).map(([key, plan]) => (
          <div key={key} className={`${plan.bg} border ${plan.border} rounded-2xl p-5`}>
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-bold text-gray-700 capitalize">{key}</span>
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${plan.bg} ${plan.color} border ${plan.border}`}>₹{plan.price}/mo</span>
            </div>
            <p className={`text-4xl font-bold ${plan.color}`}>{stats?.by_plan?.[key] || 0}</p>
            <p className="text-sm text-gray-500 mt-1">customers</p>
            <div className="mt-4 h-2.5 bg-white rounded-full overflow-hidden">
              <div className={`h-full rounded-full bg-gradient-to-r from-${plan.color.split("-")[1]}-400 to-${plan.color.split("-")[1]}-600`} style={{ width: `${stats?.total ? ((stats.by_plan?.[key] || 0) / stats.total * 100) : 0}%`, minWidth: stats?.by_plan?.[key] ? "8px" : "0" }}></div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent + Quick Actions */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-white rounded-2xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-gray-900 font-bold">Recent Purchases</h3>
            <button onClick={() => setPage("customers")} className="text-xs text-amber-600 font-semibold hover:text-amber-700">View All →</button>
          </div>
          <div className="divide-y divide-gray-100">
            {recent.length === 0 ? (
              <p className="px-5 py-10 text-center text-gray-400">Abhi koi purchase nahi</p>
            ) : recent.map(l => (
              <div key={l.id} className="px-5 py-3.5 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-amber-100 to-orange-100 rounded-full flex items-center justify-center text-amber-600 text-sm font-bold">{l.owner_name?.[0] || "?"}</div>
                  <div><p className="text-gray-900 text-sm font-semibold">{l.owner_name}</p><p className="text-gray-400 text-xs">{l.owner_email}</p></div>
                </div>
                <div className="text-right flex items-center gap-3">
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${l.plan === "starter" ? "bg-blue-100 text-blue-700" : l.plan === "growth" ? "bg-emerald-100 text-emerald-700" : "bg-purple-100 text-purple-700"}`}>{l.plan}</span>
                  <div><p className="text-gray-900 font-bold text-sm">₹{l.amount_paid}</p><p className="text-gray-400 text-xs">{new Date(l.created_at).toLocaleDateString("en-IN")}</p></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl p-5 text-white shadow-lg shadow-amber-200">
            <h4 className="font-bold mb-2">Quick Actions</h4>
            <div className="space-y-2">
              <button onClick={() => setPage("customers")} className="w-full text-left text-sm py-2 px-3 rounded-lg bg-white/20 hover:bg-white/30 transition-colors">👥 View Customers</button>
              <button onClick={() => setPage("licenses")} className="w-full text-left text-sm py-2 px-3 rounded-lg bg-white/20 hover:bg-white/30 transition-colors">🔑 Manage Licenses</button>
              <button onClick={() => setPage("revenue")} className="w-full text-left text-sm py-2 px-3 rounded-lg bg-white/20 hover:bg-white/30 transition-colors">💰 Revenue Report</button>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-5">
            <h4 className="font-bold text-gray-900 mb-3">AI Usage</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between"><span className="text-sm text-gray-500">Paid AI</span><span className="text-sm font-bold text-emerald-600">{stats?.paid_ai || 0}</span></div>
              <div className="flex items-center justify-between"><span className="text-sm text-gray-500">Free AI</span><span className="text-sm font-bold text-blue-600">{stats?.free_ai || 0}</span></div>
              <div className="h-px bg-gray-100"></div>
              <div className="flex items-center justify-between"><span className="text-sm font-semibold text-gray-700">Total</span><span className="text-sm font-bold text-gray-900">{(stats?.paid_ai || 0) + (stats?.free_ai || 0)}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── CUSTOMERS ─── */
function CustomersView({ licenses, search, setSearch, filter, setFilter, setSelectedCustomer }: { licenses: License[]; search: string; setSearch: (s: string) => void; filter: string; setFilter: (f: string) => void; setSelectedCustomer: (l: License) => void }) {
  const customers = useMemo(() => {
    const map = new Map<string, License>();
    licenses.forEach(l => { if (!map.has(l.owner_email)) map.set(l.owner_email, l); });
    let list = Array.from(map.values());
    if (search) { const q = search.toLowerCase(); list = list.filter(c => c.owner_name?.toLowerCase().includes(q) || c.owner_email?.toLowerCase().includes(q)); }
    return list;
  }, [licenses, search]);

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name or email..." className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent shadow-sm" />
        </div>
        <div className="flex items-center gap-2">
          {["all", "activated", "issued", "revoked"].map(s => (
            <button key={s} onClick={() => setFilter(s)} className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${filter === s ? "bg-amber-500 text-white shadow-md shadow-amber-200" : "bg-white text-gray-500 border border-gray-200 hover:border-amber-300"}`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-gray-100 bg-gray-50">
            {["Customer", "Phone", "Plan", "Status", "Paid", "Joined", ""].map(h => (
              <th key={h} className="text-left px-5 py-3 text-gray-500 font-semibold text-xs uppercase tracking-wider">{h}</th>
            ))}
          </tr></thead>
          <tbody className="divide-y divide-gray-100">
            {customers.map(c => (
              <tr key={c.id} className="hover:bg-amber-50/50 transition-colors">
                <td className="px-5 py-3"><div className="flex items-center gap-3"><div className="w-9 h-9 bg-gradient-to-br from-amber-100 to-orange-100 rounded-full flex items-center justify-center text-amber-600 text-xs font-bold">{c.owner_name?.[0] || "?"}</div><div><p className="text-gray-900 font-medium">{c.owner_name}</p><p className="text-gray-400 text-xs">{c.owner_email}</p></div></div></td>
                <td className="px-5 py-3 text-gray-600">{c.owner_phone || "-"}</td>
                <td className="px-5 py-3"><span className={`text-xs font-medium px-2.5 py-1 rounded-full capitalize ${c.plan === "starter" ? "bg-blue-100 text-blue-700" : c.plan === "growth" ? "bg-emerald-100 text-emerald-700" : "bg-purple-100 text-purple-700"}`}>{c.plan}</span></td>
                <td className="px-5 py-3"><StatusBadge status={c.status} /></td>
                <td className="px-5 py-3 font-semibold text-gray-900">₹{c.amount_paid}</td>
                <td className="px-5 py-3 text-gray-400 text-xs">{new Date(c.created_at).toLocaleDateString("en-IN")}</td>
                <td className="px-5 py-3"><button onClick={() => setSelectedCustomer(c)} className="text-xs text-amber-600 font-semibold hover:text-amber-700">View →</button></td>
              </tr>
            ))}
            {customers.length === 0 && <tr><td colSpan={7} className="text-center py-12 text-gray-400">Koi customer nahi mila</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─── LICENSES ─── */
function LicensesView({ licenses, search, setSearch, filter, setFilter, handleCopy, copied, handleRevoke }: any) {
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search license key or name..." className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent shadow-sm" />
        </div>
        <div className="flex items-center gap-2">
          {["all", "activated", "issued", "revoked"].map(s => (
            <button key={s} onClick={() => setFilter(s)} className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${filter === s ? "bg-amber-500 text-white shadow-md shadow-amber-200" : "bg-white text-gray-500 border border-gray-200 hover:border-amber-300"}`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-gray-100 bg-gray-50">
            {["License Key", "Owner", "Plan", "Status", "AI", "Amount", "Expires", "Actions"].map(h => (
              <th key={h} className="text-left px-4 py-3 text-gray-500 font-semibold text-xs uppercase tracking-wider">{h}</th>
            ))}
          </tr></thead>
          <tbody className="divide-y divide-gray-100">
            {licenses.map((l: License) => (
              <tr key={l.id} className="hover:bg-amber-50/50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-amber-600 font-semibold">{l.license_key}</td>
                <td className="px-4 py-3"><p className="text-gray-900 text-sm font-medium">{l.owner_name}</p><p className="text-gray-400 text-xs">{l.owner_email}</p></td>
                <td className="px-4 py-3 capitalize text-gray-600">{l.plan}</td>
                <td className="px-4 py-3"><StatusBadge status={l.status} /></td>
                <td className="px-4 py-3"><span className={`text-xs font-medium ${l.ai_tier === "paid" ? "text-emerald-600" : "text-gray-400"}`}>{l.ai_tier}</span></td>
                <td className="px-4 py-3 font-semibold text-gray-900">₹{l.amount_paid}</td>
                <td className="px-4 py-3 text-gray-400 text-xs">{l.expires_at ? new Date(l.expires_at).toLocaleDateString("en-IN") : "-"}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleCopy(l.license_key)} className="text-xs px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-amber-100 hover:text-amber-700 transition-all font-medium">{copied === l.license_key ? "Copied!" : "Copy"}</button>
                    {l.status !== "revoked" && <button onClick={() => handleRevoke(l.license_key, l.owner_name)} className="text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-all font-medium">Revoke</button>}
                  </div>
                </td>
              </tr>
            ))}
            {licenses.length === 0 && <tr><td colSpan={8} className="text-center py-12 text-gray-400">Koi license nahi mila</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─── REVENUE ─── */
function RevenueView({ stats, licenses }: { stats: Stats | null; licenses: License[] }) {
  const months = useMemo(() => {
    const map = new Map<string, { revenue: number; count: number }>();
    licenses.forEach(l => {
      const d = new Date(l.created_at);
      const key = `${d.toLocaleString("default", { month: "short" })} ${d.getFullYear()}`;
      const existing = map.get(key) || { revenue: 0, count: 0 };
      map.set(key, { revenue: existing.revenue + l.amount_paid, count: existing.count + 1 });
    });
    return Array.from(map.entries()).slice(-6);
  }, [licenses]);
  const maxRev = Math.max(...months.map(m => m[1].revenue), 1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-5">
        <div className="bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl p-6 text-white shadow-lg shadow-amber-200">
          <p className="text-amber-100 text-sm">Total Revenue</p>
          <p className="text-4xl font-bold mt-2">₹{(stats?.revenue || 0).toLocaleString()}</p>
          <p className="text-amber-100 text-sm mt-2">{licenses.length} transactions</p>
        </div>
        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
          <p className="text-gray-400 text-sm">Paid AI Revenue</p>
          <p className="text-4xl font-bold text-emerald-600 mt-2">₹{((stats?.paid_ai || 0) * 2499).toLocaleString()}</p>
          <p className="text-gray-400 text-sm mt-2">{stats?.paid_ai || 0} customers</p>
        </div>
        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
          <p className="text-gray-400 text-sm">Avg Revenue/Customer</p>
          <p className="text-4xl font-bold text-blue-600 mt-2">₹{stats?.total ? Math.round(stats.revenue / stats.total) : 0}</p>
          <p className="text-gray-400 text-sm mt-2">per customer</p>
        </div>
      </div>

      {/* Monthly Chart */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-gray-900 font-bold mb-5">Monthly Revenue</h3>
        <div className="flex items-end gap-4 h-48">
          {months.map(([month, data]) => (
            <div key={month} className="flex-1 flex flex-col items-center gap-2">
              <span className="text-xs font-semibold text-gray-600">₹{data.revenue.toLocaleString()}</span>
              <div className="w-full bg-gray-100 rounded-t-lg relative" style={{ height: "160px" }}>
                <div className="absolute bottom-0 w-full bg-gradient-to-t from-amber-500 to-orange-400 rounded-t-lg transition-all" style={{ height: `${(data.revenue / maxRev) * 100}%` }}></div>
              </div>
              <span className="text-xs text-gray-400">{month}</span>
            </div>
          ))}
          {months.length === 0 && <p className="text-gray-400 text-center w-full">Abhi koi revenue nahi</p>}
        </div>
      </div>

      {/* Payment History */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-gray-100"><h3 className="text-gray-900 font-bold">Payment History</h3></div>
        <table className="w-full text-sm">
          <thead><tr className="border-b border-gray-100 bg-gray-50">
            {["Date", "Customer", "Plan", "AI", "Amount"].map(h => (
              <th key={h} className="text-left px-5 py-2.5 text-gray-500 font-semibold text-xs uppercase tracking-wider">{h}</th>
            ))}
          </tr></thead>
          <tbody className="divide-y divide-gray-100">
            {[...licenses].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map(l => (
              <tr key={l.id} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-gray-500 text-xs">{new Date(l.created_at).toLocaleDateString("en-IN")}</td>
                <td className="px-5 py-3 text-gray-900 font-medium">{l.owner_name}</td>
                <td className="px-5 py-3 capitalize">{l.plan}</td>
                <td className="px-5 py-3"><span className={`text-xs ${l.ai_tier === "paid" ? "text-emerald-600 font-medium" : "text-gray-400"}`}>{l.ai_tier}</span></td>
                <td className="px-5 py-3 font-bold text-amber-600">₹{l.amount_paid}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─── PLANS ─── */
function PlansView({ stats }: { stats: Stats | null }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-6">
        {Object.entries(PLANS).map(([key, plan]) => (
          <div key={key} className={`bg-white rounded-2xl border-2 ${plan.border} p-6 hover:shadow-xl transition-all relative overflow-hidden`}>
            {key === "growth" && <div className="absolute top-4 right-4 bg-amber-500 text-white text-xs font-bold px-3 py-1 rounded-full">POPULAR</div>}
            <h3 className="text-lg font-bold text-gray-900 capitalize mb-1">{key}</h3>
            <p className="text-sm text-gray-400 mb-4">For {key === "starter" ? "small" : key === "growth" ? "growing" : "large"} businesses</p>
            <div className="mb-5"><span className={`text-4xl font-bold ${plan.color}`}>₹{plan.price.toLocaleString()}</span><span className="text-gray-400">/month</span></div>
            <p className="text-sm text-gray-500 mb-5">{stats?.by_plan?.[key] || 0} active customers</p>
            <ul className="space-y-3 mb-6">
              {plan.features.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-600"><span className="w-5 h-5 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center text-xs">✓</span>{f}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-gray-900 font-bold mb-4">Annual Pricing (Save 17%)</h3>
        <div className="grid grid-cols-4 gap-4">
          {Object.entries(PLANS).map(([key, plan]) => (
            <div key={key} className="text-center p-4 bg-gray-50 rounded-xl">
              <p className="text-sm text-gray-500 capitalize">{key}</p>
              <p className="text-xl font-bold text-gray-900 mt-1">₹{(plan.price * 10).toLocaleString()}</p>
              <p className="text-xs text-emerald-600 font-medium mt-1">Save ₹{(plan.price * 2).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── ANALYTICS ─── */
function AnalyticsView({ stats, licenses }: { stats: Stats | null; licenses: License[] }) {
  const planDist = Object.entries(PLANS).map(([key, plan]) => ({
    name: key, count: stats?.by_plan?.[key] || 0, pct: stats?.total ? Math.round(((stats.by_plan?.[key] || 0) / stats.total) * 100) : 0, color: plan.color, bg: plan.bg
  }));
  const recent7 = licenses.filter(l => { const d = new Date(l.created_at); return (Date.now() - d.getTime()) < 7 * 24 * 60 * 60 * 1000; }).length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-5">
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm"><p className="text-gray-400 text-sm">7-Day Growth</p><p className="text-3xl font-bold text-emerald-600 mt-1">+{recent7}</p></div>
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm"><p className="text-gray-400 text-sm">Total Customers</p><p className="text-3xl font-bold text-blue-600 mt-1">{stats?.total || 0}</p></div>
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm"><p className="text-gray-400 text-sm">Activation Rate</p><p className="text-3xl font-bold text-purple-600 mt-1">{stats?.total ? Math.round((stats.activated / stats.total) * 100) : 0}%</p></div>
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm"><p className="text-gray-400 text-sm">MRR</p><p className="text-3xl font-bold text-amber-600 mt-1">₹{((stats?.by_plan?.starter || 0) * 999 + (stats?.by_plan?.growth || 0) * 2499 + (stats?.by_plan?.enterprise || 0) * 4999).toLocaleString()}</p></div>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-gray-900 font-bold mb-4">Plan Distribution</h3>
          <div className="space-y-4">
            {planDist.map(p => (
              <div key={p.name}>
                <div className="flex items-center justify-between mb-1"><span className="text-sm text-gray-600 capitalize font-medium">{p.name}</span><span className="text-sm text-gray-500">{p.count} ({p.pct}%)</span></div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden"><div className={`h-full rounded-full ${p.color.replace("text-", "bg-")}`} style={{ width: `${p.pct}%` }}></div></div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-gray-900 font-bold mb-4">AI Usage Split</h3>
          <div className="flex items-center justify-center h-40">
            <div className="text-center">
              <p className="text-5xl font-bold text-emerald-600">{stats?.paid_ai || 0}</p>
              <p className="text-sm text-gray-400 mt-1">Paid AI</p>
              <p className="text-lg font-semibold text-gray-600 mt-3">{stats?.free_ai || 0} <span className="text-sm text-gray-400">Free AI</span></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── SETTINGS ─── */
function SettingsView() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-gray-900 font-bold mb-4">Platform Information</h3>
        <div className="space-y-3">
          <InfoRow label="Platform Name" value="AuraBiz" />
          <InfoRow label="Version" value="1.0.0" />
          <InfoRow label="Landing Page" value="aurabiz.vercel.app" link />
          <InfoRow label="Master Backend" value="aurabiz.onrender.com" link />
          <InfoRow label="Desktop App" value="AuraBiz Setup 1.0.0.exe (355 MB)" />
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-gray-900 font-bold mb-4">Payment Gateway</h3>
        <div className="space-y-3">
          <InfoRow label="Provider" value="Razorpay" />
          <InfoRow label="Mode" value="Test (sandbox)" />
          <InfoRow label="Status" value="Configured" status="green" />
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-gray-900 font-bold mb-4">API Endpoints</h3>
        <div className="space-y-2 font-mono text-sm">
          <p className="text-gray-500"><span className="text-emerald-600 font-semibold">POST</span> /admin/login</p>
          <p className="text-gray-500"><span className="text-emerald-600 font-semibold">GET</span> /api/license/plans</p>
          <p className="text-gray-500"><span className="text-emerald-600 font-semibold">POST</span> /api/license/create-order</p>
          <p className="text-gray-500"><span className="text-emerald-600 font-semibold">POST</span> /api/license/purchase</p>
          <p className="text-gray-500"><span className="text-emerald-600 font-semibold">POST</span> /api/license/activate</p>
          <p className="text-gray-500"><span className="text-emerald-600 font-semibold">POST</span> /api/license/validate</p>
          <p className="text-gray-500"><span className="text-amber-600 font-semibold">GET</span> /api/license/admin/licenses</p>
          <p className="text-gray-500"><span className="text-amber-600 font-semibold">GET</span> /api/license/admin/licenses/stats</p>
          <p className="text-gray-500"><span className="text-red-600 font-semibold">POST</span> /api/license/admin/licenses/:key/revoke</p>
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-gray-900 font-bold mb-4">Selling Flow</h3>
        <div className="space-y-3">
          <Step num={1} label="Customer visits" value="aurabiz.vercel.app" />
          <Step num={2} label="Chooses plan" value="Starter / Growth / Enterprise" />
          <Step num={3} label="Pays via Razorpay" value="UPI / Card / NetBanking" />
          <Step num={4} label="License auto-generated" value="Master backend creates key" />
          <Step num={5} label="Email sent" value="License key + EXE download link" />
          <Step num={6} label="Customer installs" value="EXE + License activation" />
          <Step num={7} label="Dashboard ready" value="Full business management" />
        </div>
      </div>
    </div>
  );
}

/* ─── SHARED ─── */
function StatCard({ icon, label, value, trend, trendUp, color }: { icon: string; label: string; value: any; trend: string; trendUp: boolean; color: string }) {
  const colors: Record<string, string> = { amber: "from-amber-50 to-orange-50 border-amber-200", blue: "from-blue-50 to-indigo-50 border-blue-200", emerald: "from-emerald-50 to-teal-50 border-emerald-200", purple: "from-purple-50 to-pink-50 border-purple-200" };
  return (
    <div className={`bg-gradient-to-br ${colors[color] || colors.amber} border rounded-2xl p-5 hover:shadow-lg transition-all`}>
      <div className="flex items-center justify-between mb-3"><span className="text-2xl">{icon}</span>{trend && <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${trendUp ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>{trend}</span>}</div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const s: Record<string, string> = { activated: "bg-emerald-100 text-emerald-700", issued: "bg-amber-100 text-amber-700", revoked: "bg-red-100 text-red-700", expired: "bg-gray-100 text-gray-600" };
  return <span className={`text-xs px-2.5 py-1 rounded-full capitalize font-semibold ${s[status] || s.expired}`}>{status}</span>;
}

function InfoRow({ label, value, link, status }: { label: string; value: string; link?: boolean; status?: string }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
      <span className="text-gray-500 text-sm">{label}</span>
      {status === "green" ? <span className="text-emerald-600 text-sm flex items-center gap-2"><span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>{value}</span>
        : link ? <a href={`https://${value}`} target="_blank" className="text-amber-600 text-sm font-medium hover:underline">{value}</a>
        : <span className="text-gray-900 text-sm font-medium">{value}</span>}
    </div>
  );
}

function InfoBlock({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return <div className="bg-gray-50 rounded-lg p-3"><p className="text-xs text-gray-400 mb-1">{label}</p><p className={`text-sm font-medium text-gray-900 ${mono ? "font-mono text-xs" : ""}`}>{value}</p></div>;
}

function Step({ num, label, value }: { num: number; label: string; value: string }) {
  return (
    <div className="flex items-center gap-4">
      <div className="w-8 h-8 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">{num}</div>
      <div><p className="text-sm font-semibold text-gray-900">{label}</p><p className="text-xs text-gray-400">{value}</p></div>
    </div>
  );
}
