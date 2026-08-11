"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Key, Plus, Trash2, Copy } from "lucide-react";

export default function APIKeysPage() {
  const [keys, setKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", permissions: "read", rate_limit: 100 });
  const [newKey, setNewKey] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getAPIKeys();
      setKeys(data.keys || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const perms = form.permissions === "read" ? ["read"] : form.permissions === "write" ? ["read", "write"] : ["read", "write", "admin"];
      const data = await masterAPI.createAPIKey({ name: form.name, permissions: perms, rate_limit: form.rate_limit });
      setNewKey(data.key || data.api_key);
      toast.success("API key created");
      setShowForm(false);
      setForm({ name: "", permissions: "read", rate_limit: 100 });
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleRevoke = async (id: string, name: string) => {
    if (!confirm(`Revoke API key "${name}"? This cannot be undone.`)) return;
    try {
      await masterAPI.revokeAPIKey(id);
      toast.success("Key revoked");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const copyKey = () => {
    if (newKey) {
      navigator.clipboard.writeText(newKey);
      toast.success("Copied to clipboard");
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Key size={24} /> API Keys ({keys.length})
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-blue-700"
        >
          <Plus size={14} /> Generate Key
        </button>
      </div>

      {newKey && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-4">
          <p className="text-sm font-medium text-yellow-800 mb-2">
            ⚠️ Copy your API key now. It won't be shown again.
          </p>
          <div className="flex gap-2">
            <code className="flex-1 bg-white px-3 py-2 rounded font-mono text-sm truncate">{newKey}</code>
            <button onClick={copyKey} className="bg-blue-600 text-white px-3 py-2 rounded text-sm inline-flex items-center gap-1">
              <Copy size={14} /> Copy
            </button>
            <button onClick={() => setNewKey(null)} className="bg-gray-600 text-white px-3 py-2 rounded text-sm">
              Done
            </button>
          </div>
        </div>
      )}

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-xl shadow p-4 mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            type="text"
            placeholder="Key Name (e.g., Mobile App)"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
            required
          />
          <select
            value={form.permissions}
            onChange={(e) => setForm({ ...form, permissions: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="read">Read Only</option>
            <option value="write">Read + Write</option>
            <option value="admin">Full Admin</option>
          </select>
          <input
            type="number"
            placeholder="Rate Limit (req/min)"
            value={form.rate_limit}
            onChange={(e) => setForm({ ...form, rate_limit: Number(e.target.value) })}
            className="border rounded px-3 py-2 text-sm"
          />
          <button type="submit" className="bg-green-600 text-white px-3 py-2 rounded-lg text-sm col-span-full">
            Generate
          </button>
        </form>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : keys.length === 0 ? (
        <div className="text-gray-400 text-sm">No API keys found</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Key (masked)</th>
                <th className="text-left px-4 py-3">Permissions</th>
                <th className="text-left px-4 py-3">Rate Limit</th>
                <th className="text-left px-4 py-3">Last Used</th>
                <th className="text-left px-4 py-3">Created</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{k.name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{k.key_preview || "••••••••"}</td>
                  <td className="px-4 py-3">
                    {(k.permissions || []).map((p: string) => (
                      <span key={p} className="px-2 py-0.5 bg-gray-100 rounded text-xs mr-1">{p}</span>
                    ))}
                  </td>
                  <td className="px-4 py-3">{k.rate_limit || "-"} /min</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "Never"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(k.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleRevoke(k.id, k.name)}
                      className="text-red-600 hover:underline text-xs inline-flex items-center gap-1"
                    >
                      <Trash2 size={12} /> Revoke
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
