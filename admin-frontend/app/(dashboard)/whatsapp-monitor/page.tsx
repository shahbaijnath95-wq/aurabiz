"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Activity, RefreshCw, Wifi, WifiOff, Ban } from "lucide-react";

export default function WhatsAppMonitorPage() {
  const [bots, setBots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getWhatsAppStatus();
      setBots(data.bots || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleReconnect = async (tenantId: string, name: string) => {
    try {
      await masterAPI.forceReconnectBot(tenantId);
      toast.success(`Reconnect triggered for ${name}`);
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDisconnect = async (tenantId: string, name: string) => {
    if (!confirm(`Disconnect WhatsApp bot for "${name}"?`)) return;
    try {
      await masterAPI.disconnectBot(tenantId);
      toast.success(`${name} disconnected`);
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const stats = {
    connected: bots.filter((b) => b.status === "connected").length,
    disconnected: bots.filter((b) => b.status === "disconnected").length,
    banned: bots.filter((b) => b.status === "banned").length,
    qr_pending: bots.filter((b) => b.status === "qr_pending").length,
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Activity size={24} /> WhatsApp Bot Monitor
        </h1>
        <button onClick={load} className="bg-gray-700 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-gray-800">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <StatCard label="Connected" value={stats.connected} color="bg-green-500" icon={Wifi} />
        <StatCard label="Disconnected" value={stats.disconnected} color="bg-gray-500" icon={WifiOff} />
        <StatCard label="QR Pending" value={stats.qr_pending} color="bg-yellow-500" icon={Activity} />
        <StatCard label="Banned" value={stats.banned} color="bg-red-500" icon={Ban} />
      </div>

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : bots.length === 0 ? (
        <div className="text-gray-400 text-sm">No bots found</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Business</th>
                <th className="text-left px-4 py-3">Phone</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Last Message</th>
                <th className="text-left px-4 py-3">Queue</th>
                <th className="text-left px-4 py-3">Messages Today</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {bots.map((b) => (
                <tr key={b.tenant_id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{b.business_name}</td>
                  <td className="px-4 py-3 text-gray-500">{b.phone_number || "-"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      b.status === "connected" ? "bg-green-100 text-green-700" :
                      b.status === "banned" ? "bg-red-100 text-red-700" :
                      b.status === "qr_pending" ? "bg-yellow-100 text-yellow-700" :
                      "bg-gray-100 text-gray-700"
                    }`}>
                      {b.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {b.last_message_at ? new Date(b.last_message_at).toLocaleString() : "-"}
                  </td>
                  <td className="px-4 py-3">{b.queue_depth ?? 0}</td>
                  <td className="px-4 py-3">{b.messages_today ?? 0}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {b.status !== "connected" && (
                      <button
                        onClick={() => handleReconnect(b.tenant_id, b.business_name)}
                        className="text-blue-600 hover:underline text-xs"
                      >
                        Reconnect
                      </button>
                    )}
                    {b.status === "connected" && (
                      <button
                        onClick={() => handleDisconnect(b.tenant_id, b.business_name)}
                        className="text-red-600 hover:underline text-xs"
                      >
                        Disconnect
                      </button>
                    )}
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

function StatCard({ label, value, color, icon: Icon }: { label: string; value: number; color: string; icon: any }) {
  return (
    <div className="bg-white rounded-xl shadow p-4">
      <div className="flex items-center gap-3">
        <div className={`${color} text-white p-2 rounded-lg`}>
          <Icon size={20} />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}
