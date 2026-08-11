"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { webhooks as webhooksApi } from "@/lib/api";
import type { Webhook, WebhookLog, WebhookStats } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newUrl, setNewUrl] = useState("");
  const [newEvents, setNewEvents] = useState("message.received,order.created");
  const [selectedLogs, setSelectedLogs] = useState<WebhookLog[] | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [webhookStats, setWebhookStats] = useState<WebhookStats | null>(null);
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) return;
    webhooksApi.list(businessId)
      .then((data) => setWebhooks(Array.isArray(data) ? data : []))
      .catch(() => toast("Webhooks load nahi ho paye", "error"))
      .finally(() => setLoading(false));
    webhooksApi.stats(businessId)
      .then((data) => setWebhookStats(data))
      .catch(() => {});
  }, [businessId]);

  const handleAdd = async () => {
    if (!businessId) return;
    try {
      await webhooksApi.register({ business_id: businessId, url: newUrl, events: newEvents.split(",") });
      setShowAdd(false);
      setNewUrl("");
      toast("Webhook add ho gaya!", "success");
      if (businessId) {
        const data = await webhooksApi.list(businessId);
        setWebhooks(Array.isArray(data) ? data : []);
      }
    } catch { toast("Webhook add nahi ho paya", "error"); }
  };

  const handleDelete = async (id: string) => {
    try {
      await webhooksApi.delete(id);
      setWebhooks((prev) => prev.filter((w) => w.id !== id));
      toast("Webhook delete ho gaya!", "success");
    } catch { toast("Delete nahi ho paya", "error"); }
  };

  const handleTest = async (id: string) => {
    try {
      await webhooksApi.test(id);
      toast("Test webhook bhej diya!", "success");
    } catch { toast("Test nahi chala", "error"); }
  };

  const handleRetry = async (id: string) => {
    try {
      await webhooksApi.retry(id);
      toast("Retry bhej diya!", "success");
      if (selectedLogs) loadLogs(id);
    } catch { toast("Retry nahi ho paya", "error"); }
  };

  const loadLogs = async (id: string) => {
    setLogsLoading(true);
    try {
      const data = await webhooksApi.logs(id);
      setSelectedLogs(Array.isArray(data) ? data : []);
    } catch {
      toast("Logs load nahi ho paye", "error");
    } finally {
      setLogsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">Webhooks</h1>
            <p className="text-gray-500">External integrations ke liye webhook endpoints</p>
          </div>
          <button onClick={() => setShowAdd(true)} className="btn-gold text-sm">+ Webhook Add Karo</button>
        </div>

        {webhookStats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[
              { label: "Total Webhooks", value: String(webhookStats.total || 0), icon: "🔗" },
              { label: "Active", value: String(webhookStats.active || 0), icon: "✅" },
              { label: "Total Deliveries", value: String(webhookStats.total_deliveries || 0), icon: "📤" },
              { label: "Success Rate", value: `${webhookStats.success_rate || 0}%`, icon: "📊" },
            ].map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className="bg-white rounded-2xl p-4 border border-gray-100 shadow-card">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{s.icon}</span>
                  <span className="text-xs text-gray-400">{s.label}</span>
                </div>
                <div className="text-xl font-bold text-gray-900">{s.value}</div>
              </motion.div>
            ))}
          </div>
        )}

        {showAdd && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-card mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Naya Webhook</h3>
            <div className="space-y-4">
              <input value={newUrl} onChange={(e) => setNewUrl(e.target.value)} placeholder="https://your-server.com/webhook" className="input-angel" />
              <input value={newEvents} onChange={(e) => setNewEvents(e.target.value)} placeholder="Events (comma separated)" className="input-angel" />
              <div className="flex gap-3">
                <button onClick={() => setShowAdd(false)} className="btn-ghost text-sm">Cancel</button>
                <button onClick={handleAdd} className="btn-gold text-sm">Register Karo</button>
              </div>
            </div>
          </motion.div>
        )}

        <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left p-4 font-medium text-gray-500">URL</th>
                <th className="text-left p-4 font-medium text-gray-500">Events</th>
                <th className="text-center p-4 font-medium text-gray-500">Status</th>
                <th className="text-center p-4 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={4} className="text-center py-8 text-gray-400">Loading...</td></tr>
              ) : webhooks.length === 0 ? (
                <tr><td colSpan={4} className="text-center py-8 text-gray-400">Abhi koi webhook nahi hai</td></tr>
              ) : (
                webhooks.map((w, i) => (
                  <tr key={i} className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="p-4 font-mono text-xs text-gray-700">{w.url}</td>
                    <td className="p-4 text-gray-500 text-xs">{Array.isArray(w.events) ? w.events.join(", ") : w.events}</td>
                    <td className="p-4 text-center">
                      <span className={`text-xs font-medium ${w.is_active ? "text-emerald-600" : "text-gray-400"}`}>{w.is_active ? "Active" : "Inactive"}</span>
                    </td>
                    <td className="p-4 text-center space-x-2">
                      <button onClick={() => loadLogs(w.id)} className="text-blue-500 hover:text-blue-600 text-xs font-medium transition-colors">Logs</button>
                      <button onClick={() => handleRetry(w.id)} className="text-amber-600 hover:text-amber-700 text-xs font-medium transition-colors">Retry</button>
                      <button onClick={() => handleTest(w.id)} className="text-violet-500 hover:text-violet-600 text-xs font-medium transition-colors">Test</button>
                      <button onClick={() => handleDelete(w.id)} className="text-red-500 hover:text-red-600 text-xs font-medium transition-colors">Delete</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {selectedLogs !== null && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-6 bg-white rounded-2xl p-6 border border-gray-100 shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Delivery Logs</h3>
              <button onClick={() => setSelectedLogs(null)} className="text-gray-400 hover:text-gray-600 text-sm">Close</button>
            </div>
            {logsLoading ? (
              <div className="text-center py-6 text-gray-400 text-sm">Loading logs...</div>
            ) : selectedLogs.length === 0 ? (
              <div className="text-center py-6 text-gray-400 text-sm">Abhi koi delivery nahi hui</div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {selectedLogs.map((log: WebhookLog, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl text-xs">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`font-medium ${log.status === "success" ? "text-emerald-600" : log.status === "failed" ? "text-red-500" : "text-amber-500"}`}>
                          {log.status?.toUpperCase()}
                        </span>
                        <span className="text-gray-400">{log.event_type}</span>
                        {log.status_code && <span className="text-gray-400">HTTP {log.status_code}</span>}
                        {log.duration_ms && <span className="text-gray-400">{log.duration_ms}ms</span>}
                      </div>
                      <div className="text-gray-400 truncate">{log.url}</div>
                      {log.error_message && <div className="text-red-400 mt-1">{log.error_message}</div>}
                    </div>
                    <span className="text-gray-400 ml-4 whitespace-nowrap">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : ""}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div></div>
  );
}
