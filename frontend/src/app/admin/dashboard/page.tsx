"use client";
import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";

const MASTER = "https://aurabiz.onrender.com";

/* ─── Types ─── */
interface License {
  id: string; license_key: string; plan: string; status: string;
  ai_tier: string; owner_name: string; owner_email: string; owner_phone: string;
  amount_paid: number; machine_id: string | null; activations_used: number;
  max_activations: number; expires_at: string; created_at: string; tenant_id: string;
}
interface Stats { total: number; activated: number; issued: number; revoked: number; revenue: number; paid_ai: number; free_ai: number; by_plan: Record<string, number>; }

const PLANS: Record<string, { price: number; color: string; features: string[] }> = {
  starter: { price: 999, color: "blue", features: ["100 Products", "500 Messages/mo", "1 User", "Free AI", "Basic Analytics", "Email Support"] },
  growth: { price: 2499, color: "green", features: ["500 Products", "2500 Messages/mo", "5 Users", "Free + Paid AI", "Revenue Tracking", "Priority Support", "Broadcast"] },
  enterprise: { price: 4999, color: "purple", features: ["Unlimited Products", "Unlimited Messages", "Unlimited Users", "Free + Paid AI", "Advanced Analytics", "Dedicated Support", "Custom AI Training", "API Access"] },
};

export default function AdminDashboard() {
  const router = useRouter();
  const [page, setPage] = useState("dashboard");
  const [stats, setStats] = useState<Stats | null>(null);
  const [licenses, setLicenses] = useState<License[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [copied, setCopied] = useState("");

  useEffect(() => {
    const t = localStorage.getItem("admin_token");
    if (!t) { router.push("/admin-login"); return; }
    load(t);
  }, []);

  const load = async (token: string) => {
    try {
      const h = { Authorization: `Bearer ${token}` };
      const [s, l] = await Promise.all([
        fetch(`${MASTER}/api/license/admin/licenses/stats`, { headers: h }).then(r => r.ok ? r.json() : null),
        fetch(`${MASTER}/api/license/admin/licenses`, { headers: h }).then(r => r.ok ? r.json() : null),
      ]);
      if (s) setStats(s);
      if (l) setLicenses(l.licenses || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const filtered = useMemo(() => {
    let list = licenses;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(l => l.owner_name?.toLowerCase().includes(q) || l.owner_email?.toLowerCase().includes(q) || l.license_key?.toLowerCase().includes(q));
    }
    if (filter !== "all") list = list.filter(l => l.status === filter);
    return list;
  }, [licenses, search, filter]);

  const copyKey = (key: string) => { navigator.clipboard.writeText(key); setCopied(key); setTimeout(() => setCopied(""), 2000); };

  const revoke = async (key: string) => {
    if (!confirm(`License ${key} revoke karna hai?`)) return;
    const token = localStorage.getItem("admin_token");
    try {
      await fetch(`${MASTER}/api/license/admin/licenses/${key}/revoke`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      load(token!);
    } catch (e) { alert("Revoke failed"); }
  };

  const logout = () => { localStorage.removeItem("admin_token"); router.push("/admin-login"); };

  if (loading) return <div className="min-h-screen bg-gray-950 flex items-center justify-center"><div className="text-center"><div className="w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div><p className="text-gray-400">Loading...</p></div></div>;

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* SIDEBAR */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center"><span className="text-white font-bold text-lg">A</span></div>
            <div><h1 className="text-white font-bold text-sm">AuraBiz</h1><p className="text-gray-500 text-xs">Super Admin</p></div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {[
            { id: "dashboard", icon: "📊", label: "Dashboard" },
            { id: "customers", icon: "👥", label: "Customers" },
            { id: "licenses", icon: "🔑", label: "Licenses" },
            { id: "revenue", icon: "💰", label: "Revenue" },
            { id: "plans", icon: "📦", label: "Plans & Pricing" },
            { id: "settings", icon: "⚙️", label: "Settings" },
          ].map(item => (
            <button key={item.id} onClick={() => setPage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${page === item.id ? "bg-amber-500/10 text-amber-500 font-semibold" : "text-gray-400 hover:bg-gray-800 hover:text-white"}`}>
              <span className="text-base">{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-red-500/10 hover:text-red-400 transition-all">
            <span>🚪</span>Logout
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 overflow-y-auto">
        {/* TOPBAR */}
        <div className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur border-b border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white capitalize">{page}</h2>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500">Admin</span>
              <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center text-white text-sm font-bold">S</div>
            </div>
          </div>
        </div>

        <div className="p-6">
          {page === "dashboard" && <DashboardView stats={stats} licenses={licenses} />}
          {page === "customers" && <CustomersView licenses={licenses} search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} />}
          {page === "licenses" && <LicensesView licenses={filtered} search={search} setSearch={setSearch} filter={filter} setFilter={setFilter} copyKey={copyKey} copied={copied} revoke={revoke} />}
          {page === "revenue" && <RevenueView stats={stats} licenses={licenses} />}
          {page === "plans" && <PlansView stats={stats} />}
          {page === "settings" && <SettingsView />}
        </div>
      </main>
    </div>
  );
}

/* ─── DASHBOARD ─── */
function DashboardView({ stats, licenses }: { stats: Stats | null; licenses: License[] }) {
  const recent = [...licenses].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5);
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon="💰" label="Total Revenue" value={`₹${(stats?.revenue || 0).toLocaleString()}`} change="+12%" color="amber" />
        <StatCard icon="👥" label="Total Customers" value={stats?.total || 0} change="" color="blue" />
        <StatCard icon="✅" label="Active Licenses" value={stats?.activated || 0} change="" color="green" />
        <StatCard icon="⏳" label="Pending" value={stats?.issued || 0} change="" color="orange" />
      </div>

      {/* Plan Distribution */}
      <div className="grid grid-cols-3 gap-4">
        {Object.entries(PLANS).map(([key, plan]) => (
          <div key={key} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-gray-300 capitalize">{key}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500">₹{plan.price}/mo</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats?.by_plan?.[key] || 0}</p>
            <p className="text-xs text-gray-500 mt-1">customers</p>
            <div className="mt-3 h-2 bg-gray-800 rounded-full overflow-hidden">
              <div className={`h-full rounded-full bg-${plan.color}-500`} style={{ width: `${stats?.total ? ((stats.by_plan?.[key] || 0) / stats.total * 100) : 0}%` }}></div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Purchases */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-white font-semibold">Recent Purchases</h3>
        </div>
        <div className="divide-y divide-gray-800">
          {recent.length === 0 ? (
            <p className="px-5 py-8 text-center text-gray-500">Abhi koi purchase nahi</p>
          ) : recent.map(l => (
            <div key={l.id} className="px-5 py-3 flex items-center justify-between hover:bg-gray-800/50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-amber-500/10 rounded-full flex items-center justify-center text-amber-500 text-sm font-bold">{l.owner_name?.[0] || "?"}</div>
                <div><p className="text-white text-sm font-medium">{l.owner_name}</p><p className="text-gray-500 text-xs">{l.owner_email}</p></div>
              </div>
              <div className="text-right">
                <span className={`text-xs px-2 py-0.5 rounded-full ${l.plan === "starter" ? "bg-blue-500/10 text-blue-400" : l.plan === "growth" ? "bg-green-500/10 text-green-400" : "bg-purple-500/10 text-purple-400"}`}>{l.plan}</span>
                <p className="text-white text-sm mt-1">₹{l.amount_paid}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── CUSTOMERS ─── */
function CustomersView({ licenses, search, setSearch, filter, setFilter }: { licenses: License[]; search: string; setSearch: (s: string) => void; filter: string; setFilter: (f: string) => void }) {
  const customers = useMemo(() => {
    const map = new Map<string, License>();
    licenses.forEach(l => { if (!map.has(l.owner_email)) map.set(l.owner_email, l); });
    let list = Array.from(map.values());
    if (search) { const q = search.toLowerCase(); list = list.filter(c => c.owner_name?.toLowerCase().includes(q) || c.owner_email?.toLowerCase().includes(q)); }
    return list;
  }, [licenses, search]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name or email..." className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent" />
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-gray-800">
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Customer</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Phone</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Plan</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Status</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Paid</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Joined</th>
          </tr></thead>
          <tbody className="divide-y divide-gray-800">
            {customers.map(c => (
              <tr key={c.id} className="hover:bg-gray-800/50">
                <td className="px-5 py-3"><p className="text-white font-medium">{c.owner_name}</p><p className="text-gray-500 text-xs">{c.owner_email}</p></td>
                <td className="px-5 py-3 text-gray-300">{c.owner_phone || "-"}</td>
                <td className="px-5 py-3"><span className={`text-xs px-2 py-0.5 rounded-full capitalize ${c.plan === "starter" ? "bg-blue-500/10 text-blue-400" : c.plan === "growth" ? "bg-green-500/10 text-green-400" : "bg-purple-500/10 text-purple-400"}`}>{c.plan}</span></td>
                <td className="px-5 py-3"><StatusBadge status={c.status} /></td>
                <td className="px-5 py-3 text-white">₹{c.amount_paid}</td>
                <td className="px-5 py-3 text-gray-400 text-xs">{new Date(c.created_at).toLocaleDateString("en-IN")}</td>
              </tr>
            ))}
            {customers.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-gray-500">Koi customer nahi</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─── LICENSES ─── */
function LicensesView({ licenses, search, setSearch, filter, setFilter, copyKey, copied, revoke }: any) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search license key or name..." className="flex-1 min-w-[200px] bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:ring-2 focus:ring-amber-500" />
        {["all", "activated", "issued", "revoked"].map(s => (
          <button key={s} onClick={() => setFilter(s)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filter === s ? "bg-amber-500 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
        ))}
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-gray-800">
            <th className="text-left px-5 py-3 text-gray-400 font-medium">License Key</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Owner</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Plan</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Status</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">AI</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Amount</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Expires</th>
            <th className="text-left px-5 py-3 text-gray-400 font-medium">Actions</th>
          </tr></thead>
          <tbody className="divide-y divide-gray-800">
            {licenses.map((l: License) => (
              <tr key={l.id} className="hover:bg-gray-800/50">
                <td className="px-5 py-3 font-mono text-xs text-amber-400">{l.license_key}</td>
                <td className="px-5 py-3"><p className="text-white text-sm">{l.owner_name}</p><p className="text-gray-500 text-xs">{l.owner_email}</p></td>
                <td className="px-5 py-3"><span className="text-xs capitalize">{l.plan}</span></td>
                <td className="px-5 py-3"><StatusBadge status={l.status} /></td>
                <td className="px-5 py-3"><span className={`text-xs ${l.ai_tier === "paid" ? "text-green-400" : "text-gray-400"}`}>{l.ai_tier}</span></td>
                <td className="px-5 py-3 text-white">₹{l.amount_paid}</td>
                <td className="px-5 py-3 text-gray-400 text-xs">{l.expires_at ? new Date(l.expires_at).toLocaleDateString("en-IN") : "-"}</td>
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => copyKey(l.license_key)} className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400 hover:text-white transition-all">{copied === l.license_key ? "Copied!" : "Copy"}</button>
                    {l.status !== "revoked" && <button onClick={() => revoke(l.license_key)} className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all">Revoke</button>}
                  </div>
                </td>
              </tr>
            ))}
            {licenses.length === 0 && <tr><td colSpan={8} className="text-center py-8 text-gray-500">Koi license nahi</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ─── REVENUE ─── */
function RevenueView({ stats, licenses }: { stats: Stats | null; licenses: License[] }) {
  const months = useMemo(() => {
    const map = new Map<string, number>();
    licenses.forEach(l => {
      const d = new Date(l.created_at);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      map.set(key, (map.get(key) || 0) + l.amount_paid);
    });
    return Array.from(map.entries()).sort((a, b) => b[0].localeCompare(a[0])).slice(0, 6);
  }, [licenses]);
  const maxRev = Math.max(...months.map(m => m[1]), 1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5"><p className="text-gray-400 text-sm">Total Revenue</p><p className="text-3xl font-bold text-amber-500 mt-1">₹{(stats?.revenue || 0).toLocaleString()}</p></div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5"><p className="text-gray-400 text-sm">Paid AI Users</p><p className="text-3xl font-bold text-green-500 mt-1">{stats?.paid_ai || 0}</p></div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5"><p className="text-gray-400 text-sm">Free AI Users</p><p className="text-3xl font-bold text-blue-500 mt-1">{stats?.free_ai || 0}</p></div>
      </div>

      {/* Monthly Revenue Chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4">Monthly Revenue</h3>
        <div className="space-y-3">
          {months.map(([month, rev]) => (
            <div key={month} className="flex items-center gap-4">
              <span className="text-gray-400 text-sm w-20">{month}</span>
              <div className="flex-1 h-8 bg-gray-800 rounded-lg overflow-hidden">
                <div className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-lg flex items-center px-3" style={{ width: `${(rev / maxRev) * 100}%`, minWidth: "60px" }}>
                  <span className="text-white text-xs font-semibold">₹{rev.toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
          {months.length === 0 && <p className="text-gray-500 text-center py-4">Abhi koi revenue nahi</p>}
        </div>
      </div>

      {/* Revenue by Plan */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4">Revenue by Plan</h3>
        <div className="space-y-3">
          {Object.entries(PLANS).map(([key, plan]) => {
            const count = stats?.by_plan?.[key] || 0;
            const rev = count * plan.price;
            return (
              <div key={key} className="flex items-center gap-4">
                <span className="text-gray-300 text-sm w-24 capitalize">{key}</span>
                <div className="flex-1 h-8 bg-gray-800 rounded-lg overflow-hidden">
                  <div className={`h-full bg-${plan.color}-500 rounded-lg flex items-center px-3`} style={{ width: `${stats?.total ? (count / stats.total * 100) : 0}%`, minWidth: count > 0 ? "60px" : "0" }}>
                    <span className="text-white text-xs font-semibold">{count} × ₹{plan.price}</span>
                  </div>
                </div>
                <span className="text-white text-sm font-semibold w-24 text-right">₹{rev.toLocaleString()}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Payment History */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800"><h3 className="text-white font-semibold">Payment History</h3></div>
        <table className="w-full text-sm">
          <thead><tr className="border-b border-gray-800">
            <th className="text-left px-5 py-2 text-gray-400 font-medium">Date</th>
            <th className="text-left px-5 py-2 text-gray-400 font-medium">Customer</th>
            <th className="text-left px-5 py-2 text-gray-400 font-medium">Plan</th>
            <th className="text-left px-5 py-2 text-gray-400 font-medium">Amount</th>
          </tr></thead>
          <tbody className="divide-y divide-gray-800">
            {[...licenses].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map(l => (
              <tr key={l.id} className="hover:bg-gray-800/50">
                <td className="px-5 py-2 text-gray-400 text-xs">{new Date(l.created_at).toLocaleDateString("en-IN")}</td>
                <td className="px-5 py-2 text-white">{l.owner_name}</td>
                <td className="px-5 py-2 capitalize">{l.plan}</td>
                <td className="px-5 py-2 text-amber-500 font-semibold">₹{l.amount_paid}</td>
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
          <div key={key} className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-amber-500/50 transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-lg font-bold text-white capitalize">{key}</span>
              {key === "growth" && <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500 text-white font-semibold">POPULAR</span>}
            </div>
            <div className="mb-4"><span className="text-3xl font-bold text-amber-500">₹{plan.price.toLocaleString()}</span><span className="text-gray-500 text-sm">/month</span></div>
            <div className="mb-4"><p className="text-sm text-gray-400">{stats?.by_plan?.[key] || 0} active customers</p></div>
            <ul className="space-y-2 mb-6">
              {plan.features.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-300"><span className="text-green-500">✓</span>{f}</li>
              ))}
            </ul>
            <div className="text-center py-2 rounded-lg bg-gray-800 text-gray-400 text-sm">Currently Active</div>
          </div>
        ))}
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-3">Pricing Summary</h3>
        <div className="grid grid-cols-4 gap-4 text-center">
          <div><p className="text-gray-400 text-sm">Annual Starter</p><p className="text-white font-bold">₹9,990</p><p className="text-green-500 text-xs">Save ₹1,998</p></div>
          <div><p className="text-gray-400 text-sm">Annual Growth</p><p className="text-white font-bold">₹24,990</p><p className="text-green-500 text-xs">Save ₹4,998</p></div>
          <div><p className="text-gray-400 text-sm">Annual Enterprise</p><p className="text-white font-bold">₹49,990</p><p className="text-green-500 text-xs">Save ₹9,990</p></div>
          <div><p className="text-gray-400 text-sm">Free Tier</p><p className="text-white font-bold">₹0</p><p className="text-gray-500 text-xs">14-day trial</p></div>
        </div>
      </div>
    </div>
  );
}

/* ─── SETTINGS ─── */
function SettingsView() {
  return (
    <div className="space-y-6 max-w-2xl">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4">Platform Information</h3>
        <div className="space-y-3">
          <InfoRow label="Platform Name" value="AuraBiz" />
          <InfoRow label="Version" value="1.0.0" />
          <InfoRow label="Landing Page" value="aurabiz.vercel.app" link />
          <InfoRow label="Master Backend" value="aurabiz.onrender.com" link />
          <InfoRow label="Desktop App" value="AuraBiz Setup 1.0.0.exe (355 MB)" />
        </div>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4">Payment Gateway</h3>
        <div className="space-y-3">
          <InfoRow label="Provider" value="Razorpay" />
          <InfoRow label="Mode" value="Test (sandbox)" />
          <InfoRow label="Status" value="Configured" status="green" />
        </div>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4">API Endpoints</h3>
        <div className="space-y-2 font-mono text-sm">
          <p className="text-gray-400"><span className="text-green-400">POST</span> /admin/login</p>
          <p className="text-gray-400"><span className="text-green-400">GET</span> /api/license/plans</p>
          <p className="text-gray-400"><span className="text-green-400">POST</span> /api/license/purchase</p>
          <p className="text-gray-400"><span className="text-green-400">POST</span> /api/license/activate</p>
          <p className="text-gray-400"><span className="text-green-400">POST</span> /api/license/validate</p>
          <p className="text-gray-400"><span className="text-yellow-400">GET</span> /api/license/admin/licenses</p>
          <p className="text-gray-400"><span className="text-yellow-400">POST</span> /api/license/admin/licenses/:key/revoke</p>
        </div>
      </div>
    </div>
  );
}

/* ─── SHARED COMPONENTS ─── */
function StatCard({ icon, label, value, change, color }: { icon: string; label: string; value: any; change: string; color: string }) {
  const colors: Record<string, string> = { amber: "text-amber-500", blue: "text-blue-500", green: "text-green-500", orange: "text-orange-500" };
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-all">
      <div className="flex items-center justify-between mb-3"><span className="text-2xl">{icon}</span>{change && <span className="text-xs text-green-500 font-semibold">{change}</span>}</div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = { activated: "bg-green-500/10 text-green-400", issued: "bg-yellow-500/10 text-yellow-400", revoked: "bg-red-500/10 text-red-400", expired: "bg-gray-500/10 text-gray-400" };
  return <span className={`text-xs px-2 py-0.5 rounded-full capitalize font-medium ${styles[status] || styles.expired}`}>{status}</span>;
}

function InfoRow({ label, value, link, status }: { label: string; value: string; link?: boolean; status?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
      <span className="text-gray-400 text-sm">{label}</span>
      {status === "green" ? <span className="text-green-400 text-sm flex items-center gap-1"><span className="w-2 h-2 bg-green-500 rounded-full"></span>{value}</span>
        : link ? <a href={`https://${value}`} target="_blank" className="text-amber-400 text-sm hover:underline">{value}</a>
        : <span className="text-white text-sm">{value}</span>}
    </div>
  );
}
