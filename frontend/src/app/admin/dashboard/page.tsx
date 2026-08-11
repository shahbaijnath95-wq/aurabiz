"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const MASTER_URL = "https://aurabiz.onrender.com";

interface Stats {
  total: number;
  activated: number;
  issued: number;
  revoked: number;
  revenue: number;
  paid_ai: number;
  free_ai: number;
  by_plan: { starter: number; growth: number; enterprise: number };
}

interface License {
  id: string;
  license_key: string;
  plan: string;
  status: string;
  owner_name: string;
  owner_email: string;
  amount_paid: number;
  created_at: string;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [licenses, setLicenses] = useState<License[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    if (!token) {
      router.push("/admin-login");
      return;
    }
    loadData(token);
  }, []);

  const loadData = async (token: string) => {
    try {
      const headers = { Authorization: `Bearer ${token}` };

      const [statsRes, licRes] = await Promise.all([
        fetch(`${MASTER_URL}/api/license/admin/licenses/stats`, { headers }),
        fetch(`${MASTER_URL}/api/license/admin/licenses`, { headers }),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (licRes.ok) {
        const data = await licRes.json();
        setLicenses(data.licenses || []);
      }
    } catch (e) {
      console.error("Load error:", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">Super Admin Dashboard</h1>
              <p className="text-sm text-gray-500">AuraBiz Platform Management</p>
            </div>
          </div>
          <button
            onClick={() => { localStorage.removeItem("admin_token"); router.push("/admin-login"); }}
            className="text-sm text-gray-500 hover:text-red-500"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard title="Total Licenses" value={stats?.total || 0} color="blue" />
          <StatCard title="Activated" value={stats?.activated || 0} color="green" />
          <StatCard title="Revenue" value={`₹${(stats?.revenue || 0).toLocaleString()}`} color="purple" />
          <StatCard title="Pending" value={stats?.issued || 0} color="amber" />
        </div>

        {/* Plan Distribution */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 border text-center">
            <p className="text-sm text-gray-500">Starter Plan</p>
            <p className="text-2xl font-bold text-blue-600">{stats?.by_plan?.starter || 0}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border text-center">
            <p className="text-sm text-gray-500">Growth Plan</p>
            <p className="text-2xl font-bold text-green-600">{stats?.by_plan?.growth || 0}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border text-center">
            <p className="text-sm text-gray-500">Enterprise Plan</p>
            <p className="text-2xl font-bold text-purple-600">{stats?.by_plan?.enterprise || 0}</p>
          </div>
        </div>

        {/* Licenses Table */}
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="px-4 py-3 border-b">
            <h2 className="font-semibold text-gray-900">All Licenses ({licenses.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">License Key</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Owner</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Plan</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Amount</th>
                </tr>
              </thead>
              <tbody>
                {licenses.length === 0 ? (
                  <tr><td colSpan={5} className="text-center py-8 text-gray-400">Koi license nahi abhi</td></tr>
                ) : licenses.map((lic) => (
                  <tr key={lic.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-xs">{lic.license_key}</td>
                    <td className="px-4 py-2">{lic.owner_name}<br/><span className="text-gray-400 text-xs">{lic.owner_email}</span></td>
                    <td className="px-4 py-2"><span className="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700">{lic.plan}</span></td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        lic.status === "activated" ? "bg-green-100 text-green-700" :
                        lic.status === "issued" ? "bg-yellow-100 text-yellow-700" :
                        "bg-red-100 text-red-700"
                      }`}>{lic.status}</span>
                    </td>
                    <td className="px-4 py-2">₹{lic.amount_paid}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: any; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    amber: "bg-amber-50 text-amber-600",
  };
  return (
    <div className="bg-white rounded-xl p-4 border">
      <p className="text-sm text-gray-500 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${colors[color]?.split(" ")[1] || "text-gray-900"}`}>{value}</p>
    </div>
  );
}
