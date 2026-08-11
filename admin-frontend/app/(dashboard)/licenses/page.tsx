"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import { KeyRound, IndianRupee, Cpu, Bot, Shield, CheckCircle2, Ban, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

interface License {
  id: string;
  license_key: string;
  plan: string;
  status: string;
  ai_tier: string;
  owner_name: string;
  owner_email: string;
  owner_phone: string | null;
  amount_paid: number;
  machine_id: string | null;
  activations_used: number;
  max_activations: number;
  expires_at: string | null;
  created_at: string | null;
  tenant_id: string | null;
}

interface LicenseStats {
  total: number;
  activated: number;
  issued: number;
  revoked: number;
  revenue: number;
  paid_ai: number;
  free_ai: number;
  by_plan: Record<string, number>;
}

const STATUS_STYLES: Record<string, string> = {
  activated: "bg-emerald-50 text-emerald-700",
  issued: "bg-amber-50 text-amber-700",
  expired: "bg-gray-100 text-gray-600",
  revoked: "bg-red-50 text-red-600",
};

export default function LicensesPage() {
  const [licenses, setLicenses] = useState<License[]>([]);
  const [stats, setStats] = useState<LicenseStats | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [l, s] = await Promise.all([masterAPI.getLicenses(), masterAPI.getLicenseStats()]);
      setLicenses(l.licenses || []);
      setStats(s);
    } catch (e: any) {
      toast.error(e.message || "Load fail ho gaya");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const revoke = async (key: string) => {
    if (!confirm(`License ${key} revoke karna hai? Customer ka app band ho jayega.`)) return;
    try {
      await masterAPI.revokeLicense(key);
      toast.success("License revoked");
      load();
    } catch (e: any) {
      toast.error(e.message || "Revoke fail");
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const cards = [
    { label: "Total Licenses", value: stats?.total ?? 0, icon: KeyRound, color: "text-blue-600 bg-blue-50" },
    { label: "Activated", value: stats?.activated ?? 0, icon: CheckCircle2, color: "text-emerald-600 bg-emerald-50" },
    { label: "Revenue", value: "₹" + (stats?.revenue ?? 0).toLocaleString("en-IN"), icon: IndianRupee, color: "text-amber-600 bg-amber-50" },
    { label: "Paid AI", value: stats?.paid_ai ?? 0, icon: Cpu, color: "text-violet-600 bg-violet-50" },
    { label: "Free AI", value: stats?.free_ai ?? 0, icon: Bot, color: "text-sky-600 bg-sky-50" },
    { label: "Revoked", value: stats?.revoked ?? 0, icon: Ban, color: "text-red-600 bg-red-50" },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Licenses</h1>
          <p className="text-sm text-gray-500">Desktop app (.exe) ke saare customers</p>
        </div>
        <button onClick={load} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${c.color}`}>
              <c.icon className="w-5 h-5" />
            </div>
            <div className="text-xl font-bold text-gray-900">{c.value}</div>
            <div className="text-xs text-gray-500">{c.label}</div>
          </div>
        ))}
      </div>

      {/* Plans breakdown */}
      {stats && (
        <div className="flex gap-2 flex-wrap">
          {Object.entries(stats.by_plan).map(([plan, count]) => (
            <span key={plan} className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-xs font-medium text-gray-700">
              {plan}: {count}
            </span>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">License Key</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Customer</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Plan</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">AI</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Paid</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Machine</th>
              <th className="text-right px-4 py-3 font-semibold text-gray-600">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {licenses.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-gray-400">Koi license nahi abhi tak</td>
              </tr>
            )}
            {licenses.map((l) => (
              <tr key={l.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-mono text-xs font-semibold text-blue-700">{l.license_key}</div>
                  <div className="text-[10px] text-gray-400">{l.created_at?.slice(0, 10)}</div>
                </td>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{l.owner_name || "—"}</div>
                  <div className="text-xs text-gray-500">{l.owner_email}</div>
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium capitalize">{l.plan}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[l.status] || "bg-gray-100 text-gray-600"}`}>
                    {l.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {l.ai_tier === "paid" ? (
                    <span className="px-2 py-0.5 bg-violet-50 text-violet-700 rounded-full text-xs font-medium">🤖 Paid</span>
                  ) : (
                    <span className="px-2 py-0.5 bg-sky-50 text-sky-700 rounded-full text-xs font-medium">🆓 Free</span>
                  )}
                </td>
                <td className="px-4 py-3 font-medium text-gray-800">₹{l.amount_paid.toLocaleString("en-IN")}</td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {l.machine_id ? `${l.activations_used}/${l.max_activations}` : "Not activated"}
                </td>
                <td className="px-4 py-3 text-right">
                  {l.status !== "revoked" ? (
                    <button
                      onClick={() => revoke(l.license_key)}
                      className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-medium hover:bg-red-100 flex items-center gap-1 ml-auto"
                    >
                      <Ban className="w-3 h-3" /> Revoke
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400">Revoked</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
