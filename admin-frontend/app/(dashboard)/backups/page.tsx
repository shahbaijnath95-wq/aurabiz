"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Database, Plus, Download, RotateCcw, Trash2 } from "lucide-react";

export default function BackupsPage() {
  const [backups, setBackups] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getBackups();
      setBackups(data.backups || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (tenantId?: string) => {
    setCreating(true);
    try {
      await masterAPI.createBackup(tenantId);
      toast.success("Backup created");
      load();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleRestore = async (backupId: string) => {
    if (!confirm("Restore this backup? Current data will be overwritten.")) return;
    try {
      await masterAPI.restoreBackup(backupId);
      toast.success("Restore initiated");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDownload = async (backupId: string) => {
    try {
      const data = await masterAPI.downloadBackup(backupId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `backup-${backupId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (backupId: string) => {
    if (!confirm("Delete this backup?")) return;
    try {
      await masterAPI.deleteBackup(backupId);
      toast.success("Backup deleted");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Database size={24} /> Backups ({backups.length})
        </h1>
        <button
          onClick={() => handleCreate()}
          disabled={creating}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-blue-700 disabled:opacity-50"
        >
          <Plus size={14} /> {creating ? "Creating..." : "New Backup"}
        </button>
      </div>

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : backups.length === 0 ? (
        <div className="text-gray-400 text-sm">No backups found. Create one now.</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Backup ID</th>
                <th className="text-left px-4 py-3">Tenant</th>
                <th className="text-left px-4 py-3">Size</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Created</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {backups.map((b) => (
                <tr key={b.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs">{b.id.slice(0, 8)}...</td>
                  <td className="px-4 py-3">{b.tenant_name || "All Tenants"}</td>
                  <td className="px-4 py-3">{((b.size_bytes || 0) / 1024).toFixed(1)} KB</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      {b.type || "manual"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(b.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      onClick={() => handleDownload(b.id)}
                      className="text-blue-600 hover:underline text-xs inline-flex items-center gap-1"
                    >
                      <Download size={12} /> Download
                    </button>
                    <button
                      onClick={() => handleRestore(b.id)}
                      className="text-yellow-600 hover:underline text-xs inline-flex items-center gap-1"
                    >
                      <RotateCcw size={12} /> Restore
                    </button>
                    <button
                      onClick={() => handleDelete(b.id)}
                      className="text-red-600 hover:underline text-xs inline-flex items-center gap-1"
                    >
                      <Trash2 size={12} /> Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
