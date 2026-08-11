"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { audit } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function AuditPage() {
  const [logs, setLogs] = useState<{id: string; action: string; entity_type: string; entity_id: string; details: string; created_at: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) return;
    const params: Record<string, string> = {};
    if (filter) params.action = filter;
    audit.logs(businessId, params)
      .then((data) => setLogs(Array.isArray(data) ? data : []))
      .catch(() => toast("Audit logs load nahi ho paye", "error"))
      .finally(() => setLoading(false));
  }, [businessId, filter]);

  const actionColor: Record<string, string> = {
    create: "text-emerald-600 bg-emerald-50",
    update: "text-amber-600 bg-amber-50",
    delete: "text-red-600 bg-red-50",
    login: "text-blue-600 bg-blue-50",
    send_message: "text-violet-600 bg-violet-50",
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">Audit Trail</h1>
            <p className="text-gray-500">System activity aur compliance logs</p>
          </div>
          <div className="flex gap-2">
            {["", "create", "update", "delete", "login"].map((f) => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${filter === f ? "bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-glow" : "bg-white text-gray-500 hover:bg-gray-50 border border-gray-200"}`}>
                {f || "All"}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left p-4 font-medium text-gray-500">Time</th>
                <th className="text-left p-4 font-medium text-gray-500">Action</th>
                <th className="text-left p-4 font-medium text-gray-500">Entity</th>
                <th className="text-left p-4 font-medium text-gray-500">IP Address</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={4} className="text-center py-8 text-gray-400">Loading...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={4} className="text-center py-8 text-gray-400">Abhi koi audit logs nahi hain</td></tr>
              ) : (
                logs.map((log, i) => (
                  <tr key={i} className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="p-4 text-gray-500 text-xs">{log.timestamp || "N/A"}</td>
                    <td className="p-4">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${actionColor[log.action] || "text-gray-600 bg-gray-50"}`}>{log.action}</span>
                    </td>
                    <td className="p-4 text-gray-700">{log.entity_type}</td>
                    <td className="p-4 text-gray-400 font-mono text-xs">{log.ip_address}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    
        </div></div>
  );
}
