"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Flag, Plus, Trash2 } from "lucide-react";

export default function FeatureFlagsPage() {
  const [flags, setFlags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ flag_name: "", description: "", enabled: false });

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getFeatureFlags();
      setFlags(data.flags || data.items || []);
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
      await masterAPI.createFeatureFlag(form);
      toast.success("Feature flag created");
      setShowForm(false);
      setForm({ flag_name: "", description: "", enabled: false });
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const toggleFlag = async (flag: any) => {
    try {
      await masterAPI.updateFeatureFlag(flag.id, { enabled: !flag.enabled });
      toast.success(`${flag.flag_name} ${flag.enabled ? "disabled" : "enabled"}`);
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete flag "${name}"?`)) return;
    try {
      await masterAPI.deleteFeatureFlag(id);
      toast.success("Flag deleted");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Flag size={24} /> Feature Flags ({flags.length})
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-blue-700"
        >
          <Plus size={14} /> New Flag
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-xl shadow p-4 mb-4 space-y-3">
          <input
            type="text"
            placeholder="Flag Name (e.g., voice_notes_enabled)"
            value={form.flag_name}
            onChange={(e) => setForm({ ...form, flag_name: e.target.value })}
            className="border rounded px-3 py-2 text-sm w-full"
            required
          />
          <input
            type="text"
            placeholder="Description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="border rounded px-3 py-2 text-sm w-full"
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            Enabled by default
          </label>
          <button type="submit" className="bg-green-600 text-white px-3 py-2 rounded-lg text-sm">
            Create Flag
          </button>
        </form>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : flags.length === 0 ? (
        <div className="text-gray-400 text-sm">No feature flags found</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {flags.map((f) => (
            <div key={f.id} className="bg-white rounded-xl shadow p-4">
              <div className="flex justify-between items-start mb-2">
                <code className="text-sm font-mono font-medium">{f.flag_name}</code>
                <button
                  onClick={() => toggleFlag(f)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    f.enabled ? "bg-green-600" : "bg-gray-300"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      f.enabled ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
              <p className="text-xs text-gray-500 mb-3">{f.description || "No description"}</p>
              <div className="flex justify-between items-center">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  f.enabled ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                }`}>
                  {f.enabled ? "Enabled" : "Disabled"}
                </span>
                <button
                  onClick={() => handleDelete(f.id, f.flag_name)}
                  className="text-red-600 hover:underline text-xs inline-flex items-center gap-1"
                >
                  <Trash2 size={12} /> Delete
                </button>
              </div>
              {f.target_tenant_ids && f.target_tenant_ids.length > 0 && (
                <p className="text-xs text-gray-400 mt-2">
                  Applied to {f.target_tenant_ids.length} tenants
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
