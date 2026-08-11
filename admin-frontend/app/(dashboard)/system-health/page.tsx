"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Activity, RefreshCw, Cpu, HardDrive, MemoryStick } from "lucide-react";

export default function SystemHealthPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getSystemHealth();
      setHealth(data);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000); // 30 sec refresh
    return () => clearInterval(interval);
  }, []);

  const services = health?.services || [
    { name: "Backend (FastAPI)", status: "unknown", port: 8000 },
    { name: "Master Backend", status: "unknown", port: 8010 },
    { name: "WhatsApp Bot", status: "unknown", port: 8001 },
    { name: "PostgreSQL", status: "unknown", port: 5432 },
    { name: "Redis", status: "unknown", port: 6379 },
    { name: "Qdrant", status: "unknown", port: 6333 },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Activity size={24} /> System Health
        </h1>
        <button onClick={load} className="bg-gray-700 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1">
          <RefreshCw size={14} /> Refresh (30s auto)
        </button>
      </div>

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : (
        <>
          {/* Resource Usage */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <ResourceCard
              label="CPU Usage"
              value={health?.cpu_percent ?? 0}
              unit="%"
              icon={Cpu}
              threshold={80}
            />
            <ResourceCard
              label="Memory Usage"
              value={health?.memory_percent ?? 0}
              unit="%"
              icon={MemoryStick}
              threshold={85}
            />
            <ResourceCard
              label="Disk Usage"
              value={health?.disk_percent ?? 0}
              unit="%"
              icon={HardDrive}
              threshold={90}
            />
          </div>

          {/* Services Status */}
          <h2 className="text-lg font-bold mb-3">Services Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((s: any) => (
              <div key={s.name} className="bg-white rounded-xl shadow p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium text-sm">{s.name}</p>
                    <p className="text-xs text-gray-500">Port {s.port}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`h-3 w-3 rounded-full ${
                      s.status === "healthy" || s.status === "online" ? "bg-green-500" :
                      s.status === "degraded" ? "bg-yellow-500" :
                      s.status === "down" || s.status === "offline" ? "bg-red-500" :
                      "bg-gray-400"
                    } ${s.status !== "unknown" ? "animate-pulse" : ""}`} />
                    <span className="text-xs capitalize">{s.status}</span>
                  </div>
                </div>
                {s.latency_ms && (
                  <p className="text-xs text-gray-500 mt-2">Latency: {s.latency_ms}ms</p>
                )}
                {s.uptime && (
                  <p className="text-xs text-gray-500">Uptime: {s.uptime}</p>
                )}
              </div>
            ))}
          </div>

          {/* Quick Stats */}
          {health?.stats && (
            <div className="mt-6 bg-white rounded-xl shadow p-4">
              <h3 className="font-bold mb-2">Platform Stats</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 text-xs">Requests Today</p>
                  <p className="font-bold">{health.stats.requests_today ?? 0}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Error Rate</p>
                  <p className="font-bold">{health.stats.error_rate ?? 0}%</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Avg Response Time</p>
                  <p className="font-bold">{health.stats.avg_response_ms ?? 0}ms</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Uptime (24h)</p>
                  <p className="font-bold">{health.stats.uptime_24h ?? "99.9"}%</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ResourceCard({ label, value, unit, icon: Icon, threshold }: { label: string; value: number; unit: string; icon: any; threshold: number }) {
  const isWarning = value >= threshold;
  const isCritical = value >= threshold + 5;
  const color = isCritical ? "bg-red-500" : isWarning ? "bg-yellow-500" : "bg-green-500";

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={`${color} text-white p-2 rounded-lg`}>
          <Icon size={20} />
        </div>
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-2xl font-bold">{value}{unit}</p>
        </div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  );
}
