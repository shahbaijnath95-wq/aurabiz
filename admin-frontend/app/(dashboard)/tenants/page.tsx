"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { masterAPI } from "@/lib/api";
import { Search, Eye, Ban, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";

interface Tenant {
  id: string;
  slug: string;
  name: string;
  owner_name: string;
  owner_email: string;
  status: string;
  plan: string;
  messages_used: number | null;
  max_messages: number | null;
  created_at: string;
}

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getTenants({ page, search: search || undefined, status: statusFilter || undefined });
      setTenants(data.tenants);
      setTotal(data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    load();
  };

  const handleSuspend = async (id: string, name: string) => {
    if (!confirm(`Suspend "${name}"?`)) return;
    try {
      await masterAPI.suspendTenant(id, "Suspended by admin");
      toast.success(`${name} suspended`);
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleReactivate = async (id: string) => {
    try {
      await masterAPI.reactivateTenant(id);
      toast.success("Reactivated");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Tenants ({total})</h1>

      <div className="flex gap-3 mb-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm w-64"
          />
          <button className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm"><Search size={16} /></button>
        </form>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Owner</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Plan</th>
                <th className="text-left px-4 py-3">Messages</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((t) => (
                <tr key={t.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{t.name}</td>
                  <td className="px-4 py-3">{t.owner_name}</td>
                  <td className="px-4 py-3 text-gray-500">{t.owner_email}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      t.status === "active" ? "bg-green-100 text-green-700" :
                      t.status === "suspended" ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-700"
                    }`}>
                      {t.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 capitalize">{t.plan}</td>
                  <td className="px-4 py-3">{t.messages_used ?? 0} / {t.max_messages ?? "∞"}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <Link href={`/tenants/${t.id}`} className="text-blue-600 hover:underline inline-flex items-center gap-1">
                      <Eye size={14} /> View
                    </Link>
                    {t.status === "active" ? (
                      <button onClick={() => handleSuspend(t.id, t.name)} className="text-red-600 hover:underline inline-flex items-center gap-1">
                        <Ban size={14} /> Suspend
                      </button>
                    ) : (
                      <button onClick={() => handleReactivate(t.id)} className="text-green-600 hover:underline inline-flex items-center gap-1">
                        <CheckCircle size={14} /> Reactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex justify-between items-center mt-4">
        <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="text-sm text-gray-600 disabled:opacity-50">← Prev</button>
        <span className="text-sm text-gray-500">Page {page} of {Math.ceil(total / 20) || 1}</span>
        <button disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(page + 1)} className="text-sm text-gray-600 disabled:opacity-50">Next →</button>
      </div>
    </div>
  );
}
