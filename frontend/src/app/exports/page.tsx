"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { exportsApi } from "@/lib/api";
import type { ExportJob } from "@/lib/types";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function ExportsPage() {
  const router = useRouter();
  const { user, business, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const [exportList, setExportList] = useState<ExportJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ export_type: "customers", format: "csv" });

  const businessId = business?.id || "";

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
    if (businessId) loadExports();
  }, [authLoading, user, businessId]);

  async function loadExports() {
    try {
      const data = await exportsApi.list(businessId);
      setExportList(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await exportsApi.create({ ...form, business_id: businessId });
      loadExports();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Export fail ho gaya", "error"); }
    setCreating(false);
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete export?")) return;
    try {
      await exportsApi.delete(id);
      loadExports();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Delete fail ho gaya", "error"); }
  }

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    processing: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Data Export</h1>
      </div>

      {/* Create Export */}
      <div className="bg-white rounded-xl border p-4 mb-6">
        <h3 className="font-semibold mb-3">Create New Export</h3>
        <form onSubmit={handleCreate} className="flex gap-3 items-end">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Data Type</label>
            <select value={form.export_type} onChange={e => setForm({ ...form, export_type: e.target.value })}
              className="px-3 py-2 border rounded-lg">
              <option value="customers">Customers</option>
              <option value="transactions">Transactions</option>
              <option value="orders">Orders</option>
              <option value="products">Products</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Format</label>
            <select value={form.format} onChange={e => setForm({ ...form, format: e.target.value })}
              className="px-3 py-2 border rounded-lg">
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>
          <button type="submit" disabled={creating}
            className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50">
            {creating ? "Exporting..." : "Export"}
          </button>
        </form>
      </div>

      {/* Export History */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : exportList.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-400">No exports yet.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Format</th>
                <th className="text-left px-4 py-3">Rows</th>
                <th className="text-left px-4 py-3">Size</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Created</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {exportList.map((exp) => (
                <tr key={exp.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 capitalize">{exp.export_type}</td>
                  <td className="px-4 py-3 uppercase text-xs">{exp.format}</td>
                  <td className="px-4 py-3">{exp.row_count || "—"}</td>
                  <td className="px-4 py-3 text-gray-500">{exp.file_size ? `${(exp.file_size / 1024).toFixed(1)} KB` : "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[exp.status] || ""}`}>
                      {exp.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{exp.created_at || "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {exp.status === "completed" && (
                      <a href={exportsApi.download(exp.id)} target="_blank" rel="noopener"
                        className="text-blue-500 hover:underline text-xs mr-2">Download</a>
                    )}
                    <button onClick={() => handleDelete(exp.id)} className="text-red-500 hover:underline text-xs">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
    </div></div>
  );
}
