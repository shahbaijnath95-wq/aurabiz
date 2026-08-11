"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { revenue } from "@/lib/api";
import type { RevenueData } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function RevenuePage() {
  const [data, setData] = useState<RevenueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) return;
    setLoading(true);
    revenue.forecast(businessId, days)
      .then(setData)
      .catch(() => toast("Revenue data load nahi ho paya", "error"))
      .finally(() => setLoading(false));
  }, [businessId, days]);

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">Revenue Forecast</h1>
            <p className="text-gray-500">AI-powered revenue prediction</p>
          </div>
          <div className="flex gap-2">
            {[7, 30, 90].map((d) => (
              <button key={d} onClick={() => setDays(d)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${days === d ? "bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-glow" : "bg-white text-gray-500 hover:bg-gray-50 border border-gray-200"}`}>
                {d} Din
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="bg-white rounded-2xl p-6 animate-pulse h-32 shimmer" />)}
          </div>
        ) : data ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Forecasted Revenue", value: `₹${(data.forecasted_revenue || data.total || 0).toLocaleString()}`, icon: "✦", color: "text-amber-500 bg-amber-50" },
              { label: "Growth Rate", value: `${data.growth_rate || data.growth || 0}%`, icon: "📈", color: "text-emerald-500 bg-emerald-50" },
              { label: "Peak Day", value: data.peak_day || "N/A", icon: "📅", color: "text-blue-500 bg-blue-50" },
              { label: "Avg Daily", value: `₹${(data.avg_daily || data.average || 0).toLocaleString()}`, icon: "📊", color: "text-violet-500 bg-violet-50" },
            ].map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="bg-white rounded-2xl p-4 border border-gray-100 shadow-card card-hover">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${s.color}`}>{s.icon}</div>
                  <span className="text-xs text-gray-400">{s.label}</span>
                </div>
                <div className="text-xl font-bold text-gray-900">{s.value}</div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-2xl p-12 text-center text-gray-400 border border-gray-100 shadow-card">Data load nahi ho paya</div>
        )}
      </div>
    
        </div></div>
  );
}
