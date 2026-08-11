"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Webhook, Plus, Trash2, Activity } from "lucide-react";

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ url: "", events: "", secret: "" });
  const [selectedWebhook, setSelectedWebhook] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getPlatformWebhooks();
      setWebhooks(data.webhooks || data.items || []);
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
      const events = form.events.split(",").map((e) => e.trim()).filter(Boolean);
      await masterAPI.createPlatformWebhook({ url: form.url, events, secret: form.secret });
      toast.success("Webhook created");
      setShowForm(false);
      setForm({ url: "", events: "", secret: "" });
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this webhook?")) return;
    try {
      await masterAPI.deletePlatformWebhook(id);
      toast.success("Webhook deleted");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const viewLogs = async (webhook: any) => {
    setSelectedWebhook(webhook);
    try {
      const data = await masterAPI.getWebhookDeliveryLogs(webhook.id);
      setLogs(data.logs || data.items || []);
    } catch (err: any) {
      setLogs([]);
    }
  };

  const toggleActive = async (w: any) => {
    try {
      await masterAPI.updatePlatformWebhook(w.id, { active: !w.active });
      toast.success("Updated");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Webhook size={24} /> Platform Webhooks ({webhooks.length})
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-blue-700"
        >
          <Plus size={14} /> Add Webhook
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-xl shadow p-4 mb-4 space-y-3">
          <input
            type="url"
            placeholder="Webhook URL (https://...)"
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
            className="border rounded px-3 py-2 text-sm w-full"
            required
          />
          <input
            type="text"
            placeholder="Events (comma-separated: tenant.created,payment.received)"
            value={form.events}
            onChange={(e) => setForm({ ...form, events: e.target.value })}
            className="border rounded px-3 py-2 text-sm w-full"
            required
          />
          <input
            type="text"
            placeholder="HMAC Secret"
            value={form.secret}
            onChange={(e) => setForm({ ...form, secret: e.target.value })}
            className="border rounded px-3 py-2 text-sm w-full"
            required
          />
          <button type="submit" className="bg-green-600 text-white px-3 py-2 rounded-lg text-sm">
            Create Webhook
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          {loading ? (
            <div className="animate-pulse text-gray-400">Loading...</div>
          ) : webhooks.length === 0 ? (
            <div className="text-gray-400 text-sm">No webhooks found</div>
          ) : (
            <div className="space-y-2">
              {webhooks.map((w) => (
                <div key={w.id} className="bg-white rounded-xl shadow p-4">
                  <div className="flex justify-between items-start mb-2">
                    <code className="text-sm font-mono truncate flex-1">{w.url}</code>
                    <button
                      onClick={() => toggleActive(w)}
                      className={`px-2 py-1 rounded-full text-xs font-medium ml-2 ${
                        w.active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {w.active ? "Active" : "Inactive"}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {(w.events || []).map((e: string) => (
                      <span key={e} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{e}</span>
                    ))}
                  </div>
                  <div className="flex gap-2 text-xs">
                    <button
                      onClick={() => viewLogs(w)}
                      className="text-blue-600 hover:underline inline-flex items-center gap-1"
                    >
                      <Activity size={12} /> Logs
                    </button>
                    <button
                      onClick={() => handleDelete(w.id)}
                      className="text-red-600 hover:underline inline-flex items-center gap-1"
                    >
                      <Trash2 size={12} /> Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          {selectedWebhook && (
            <div className="bg-white rounded-xl shadow p-4 sticky top-4">
              <h3 className="font-bold mb-2">Delivery Logs</h3>
              <code className="text-xs text-gray-500 block mb-2 truncate">{selectedWebhook.url}</code>
              {logs.length === 0 ? (
                <p className="text-sm text-gray-400">No deliveries yet</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {logs.map((log) => (
                    <div key={log.id} className="border rounded p-2 text-xs">
                      <div className="flex justify-between">
                        <span className="font-mono">{log.event}</span>
                        <span className={`px-2 py-0.5 rounded ${
                          log.status_code === 200 ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        }`}>
                          {log.status_code}
                        </span>
                      </div>
                      <p className="text-gray-500 mt-1">{new Date(log.created_at).toLocaleString()}</p>
                      {log.error && <p className="text-red-500 mt-1">{log.error}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
