"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import { Download, Shield } from "lucide-react";

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getAuditLogs({ page, action: actionFilter || undefined, limit: 50 });
      setLogs(data.logs || data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, actionFilter]);

  const handleExport = async () => {
    try {
      const data = await masterAPI.exportAuditLogs();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-logs-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Shield size={24} /> Audit Log ({total})
        </h1>
        <button onClick={handleExport} className="bg-gray-700 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-gray-800">
          <Download size={14} /> Export
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Filter by action (e.g., tenant.create)"
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
          className="border rounded-lg px-3 py-2 text-sm w-64"
        />
      </div>

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : logs.length === 0 ? (
        <div className="text-gray-400 text-sm">No audit logs found</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Time</th>
                <th className="text-left px-4 py-3">Admin</th>
                <th className="text-left px-4 py-3">Action</th>
                <th className="text-left px-4 py-3">Tenant</th>
                <th className="text-left px-4 py-3">IP</th>
                <th className="text-left px-4 py-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">{log.admin_email || log.admin_user_id}</td>
                  <td className="px-4 py-3">
                    <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">{log.action}</code>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{log.target_tenant_id || "-"}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{log.ip_address || "-"}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">
                    {log.details ? JSON.stringify(log.details).slice(0, 80) : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex justify-between items-center mt-4">
        <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="text-sm text-gray-600 disabled:opacity-50">← Prev</button>
        <span className="text-sm text-gray-500">Page {page}</span>
        <button disabled={logs.length < 50} onClick={() => setPage(page + 1)} className="text-sm text-gray-600 disabled:opacity-50">Next →</button>
      </div>
    </div>
  );
}
