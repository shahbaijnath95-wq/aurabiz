"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { analytics, conversationAnalytics } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

interface AnalyticsData {
  total_revenue?: number;
  revenue_change?: string;
  total_messages?: number;
  messages_change?: string;
  total_customers?: number;
  customers_change?: string;
  total_orders?: number;
  orders_change?: string;
  avg_order?: number;
  revenue_daily?: number[];
  top_products?: { name?: string; product_name?: string; sales?: number; quantity?: number }[];
  insights?: string[];
  customer_metrics?: Record<string, unknown>;
  recent_transactions?: Record<string, unknown>[];
}

interface StatCards {
  revenue?: { value?: number; change?: number };
  messages?: { value?: number; change?: number };
  customers?: { value?: number; change?: number };
  orders?: { value?: number; change?: number };
  avg_order?: { value?: number };
}

interface DashboardResponse {
  stat_cards?: StatCards;
  revenue_chart?: { revenue?: number }[];
  top_products?: { name?: string; product_name?: string; sales?: number; quantity?: number }[];
  ai_insights?: string[];
  customer_metrics?: Record<string, unknown>;
  recent_transactions?: Record<string, unknown>[];
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [convStats, setConvStats] = useState<Record<string, unknown> | null>(null);
  const [sentiment, setSentiment] = useState<Record<string, unknown> | null>(null);
  const [engagement, setEngagement] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState("7d");
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) return;
    setLoading(true);
    analytics.dashboard(businessId, period)
      .then((raw) => {
        const d = raw as unknown as DashboardResponse;
        const sc = d?.stat_cards || {};
        setData({
          total_revenue: sc.revenue?.value || 0,
          revenue_change: `+${sc.revenue?.change || 0}%`,
          total_messages: sc.messages?.value || 0,
          messages_change: `+${sc.messages?.change || 0}%`,
          total_customers: sc.customers?.value || 0,
          customers_change: `+${sc.customers?.change || 0}%`,
          total_orders: sc.orders?.value || 0,
          orders_change: `+${sc.orders?.change || 0}%`,
          avg_order: sc.avg_order?.value || 0,
          revenue_daily: (d.revenue_chart || []).map((r) => r.revenue || 0),
          top_products: d.top_products || [],
          insights: d.ai_insights || [],
          customer_metrics: d.customer_metrics || {},
          recent_transactions: d.recent_transactions || [],
        });
      })
      .catch(() => toast("Analytics load nahi ho paye — backend restart karo", "error"))
      .finally(() => setLoading(false));
    conversationAnalytics.stats(businessId)
      .then((d) => setConvStats(d as unknown as Record<string, unknown>))
      .catch(() => {});
    conversationAnalytics.sentiment(businessId)
      .then((d) => setSentiment(d as Record<string, unknown>))
      .catch(() => {});
    conversationAnalytics.engagement(businessId)
      .then((d) => setEngagement(d as Record<string, unknown>))
      .catch(() => {});
  }, [businessId, period]);

  const MiniBarChart = ({ data, color }: { data: number[]; color: string }) => {
    const max = Math.max(...data, 1);
    return (
      <div className="flex items-end gap-1 h-20">
        {data.map((v, i) => (
          <motion.div
            key={i}
            initial={{ height: 0 }}
            animate={{ height: `${(v / max) * 100}%` }}
            transition={{ duration: 0.5, delay: i * 0.05 }}
            className={`flex-1 rounded-t ${color} transition-all duration-500`}
            style={{ minHeight: 2 }}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="layout-container">
        <div className="page-header">
          <Link href="/dashboard" className="text-sm text-gold-600 hover:text-gold-700 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">Aapke business ka detailed data</p>
        </div>

        {/* Period Filter */}
        <div className="flex gap-2 mb-6">
          {["7d", "30d", "90d"].map((p) => (
            <motion.button
              key={p}
              whileTap={{ scale: 0.95 }}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${period === p ? "bg-gradient-to-r from-gold-400 to-gold-500 text-white shadow-sm" : "bg-surface-50 text-surface-500 hover:bg-surface-100 border border-surface-200"}`}
            >
              {p === "7d" ? "7 Din" : p === "30d" ? "30 Din" : "90 Din"}
            </motion.button>
          ))}
        </div>

        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.1 }}
                className="card p-6">
                <div className="shimmer h-4 w-20 rounded mb-3" />
                <div className="shimmer h-8 w-24 rounded" />
              </motion.div>
            ))}
          </div>
        ) : data ? (
          <>
            {/* Stat Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              {[
                { label: "Total Revenue", value: `₹${(data.total_revenue || 0).toLocaleString()}`, icon: "✦", color: "text-gold-500 bg-gold-50", change: data.revenue_change },
                { label: "Messages", value: String(data.total_messages || 0), icon: "◈", color: "text-info-500 bg-info-50", change: data.messages_change },
                { label: "Customers", value: String(data.total_customers || 0), icon: "✧", color: "text-violet-500 bg-violet-50", change: data.customers_change },
                { label: "Orders", value: String(data.total_orders || 0), icon: "⬡", color: "text-orange-500 bg-orange-50", change: data.orders_change },
              ].map((s, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="card card-hover-shadow">
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${s.color}`}>{s.icon}</div>
                        <span className="text-xs text-surface-400">{s.label}</span>
                      </div>
                      {s.change && (
                        <span className={`text-xs font-medium ${s.change.startsWith("+") ? "text-success-600" : "text-error-500"}`}>
                          {s.change.startsWith("+") ? "↑" : "↓"} {s.change}
                        </span>
                      )}
                    </div>
                    <div className="text-2xl font-bold text-surface-800">{s.value}</div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Revenue Chart + Top Products */}
            <div className="grid lg:grid-cols-3 gap-6 mb-8">
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                className="lg:col-span-2 card card-hover-shadow">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-surface-800">Revenue Trend</h3>
                    <span className="text-sm text-gold-600 font-medium">
                      ₹{data.revenue_daily?.reduce((a: number, b: number) => a + b, 0).toLocaleString()} total
                    </span>
                  </div>
                  <MiniBarChart data={data.revenue_daily || [0, 0, 0, 0, 0, 0, 0]} color="bg-gradient-to-t from-gold-400 to-gold-500" />
                  <div className="flex justify-between mt-2 text-xs text-surface-400">
                    <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
                  </div>
                </div>
              </motion.div>

              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                className="card card-hover-shadow">
                <div className="p-6">
                  <h3 className="font-semibold text-surface-800 mb-4">Top Products</h3>
                  <div className="space-y-3">
                    {(data.top_products || []).slice(0, 5).map((p: any, i: number) => {
                      const maxSales = Math.max(...(data.top_products || []).map((x: any) => x.sales || x.quantity || 1));
                      const pct = ((p.sales || p.quantity || 0) / maxSales) * 100;
                      return (
                        <div key={i}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-surface-700 truncate">{p.name || p.product_name}</span>
                            <span className="text-surface-400 text-xs">{p.sales || p.quantity || 0} sold</span>
                          </div>
                          <div className="h-1.5 bg-surface-200 rounded-full overflow-hidden">
                            <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.5, delay: i * 0.1 }}
                              className="h-full bg-gradient-to-r from-gold-400 to-gold-500 rounded-full" />
                          </div>
                        </div>
                      );
                    })}
                    {(!data.top_products || data.top_products.length === 0) && (
                      <p className="text-surface-400 text-sm text-center py-4">Abhi koi product data nahi hai</p>
                    )}
                  </div>
                </div>
              </motion.div>
            </div>

            {/* AI Insights */}
            {data.insights && data.insights.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                className="card card-hover-shadow mb-6">
                <div className="p-6">
                  <h3 className="font-semibold text-lg text-surface-800 mb-4">🧠 AI Insights</h3>
                  <div className="space-y-3">
                    {data.insights.map((insight: string, i: number) => (
                      <div key={i} className="flex items-start gap-3 text-sm text-surface-600">
                        <span className="text-gold-500 mt-0.5 shrink-0">✦</span>
                        <span>{insight}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Conv Stats */}
            {convStats && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
                className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {[
                  { label: "Total Conversations", value: String(convStats.total_conversations || 0), icon: "💬" },
                  { label: "Avg Response Time", value: `${convStats.avg_response_time_seconds || 0}s`, icon: "⚡" },
                  { label: "Resolution Rate", value: `${convStats.resolution_rate || 0}%`, icon: "✅" },
                  { label: "Avg Messages", value: String(convStats.avg_messages_per_conversation || 0), icon: "📊" },
                ].map((s, i) => (
                  <div key={i} className="card p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{s.icon}</span>
                      <span className="text-xs text-surface-400">{s.label}</span>
                    </div>
                    <div className="text-xl font-bold text-surface-800">{s.value}</div>
                  </div>
                ))}
              </motion.div>
            )}

            {/* Sentiment Analysis */}
            {sentiment && (sentiment as Record<string, unknown>).distribution && (() => {
              const dist = (sentiment as Record<string, unknown>).distribution as Record<string, number>;
              const total = (dist.positive || 0) + (dist.neutral || 0) + (dist.negative || 0);
              return (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
                  className="card card-hover-shadow mb-6">
                  <div className="p-6">
                    <h3 className="font-semibold text-lg text-surface-800 mb-4">Sentiment Analysis</h3>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { label: "Positive", value: dist.positive || 0, color: "bg-success-500" },
                        { label: "Neutral", value: dist.neutral || 0, color: "bg-surface-400" },
                        { label: "Negative", value: dist.negative || 0, color: "bg-error-400" },
                      ].map((s, i) => {
                        const pct = total > 0 ? Math.round((s.value / total) * 100) : 0;
                        return (
                          <div key={i} className="text-center">
                            <div className="text-sm text-surface-500 mb-2">{s.label}</div>
                            <div className="relative w-full h-3 bg-surface-200 rounded-full overflow-hidden mb-1">
                              <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.8 }}
                                className={`absolute inset-y-0 left-0 ${s.color} rounded-full`} />
                            </div>
                            <div className="text-xs text-surface-400">{pct}% ({s.value})</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </motion.div>
              );
            })()}

            {/* Peak Hours */}
            {engagement && (engagement as Record<string, unknown>).hourly_distribution && (() => {
              const hourly = (engagement as Record<string, unknown>).hourly_distribution as Record<string, number>;
              const max = Math.max(...Object.values(hourly).map(Number), 1);
              return (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
                  className="card card-hover-shadow">
                  <div className="p-6">
                    <h3 className="font-semibold text-lg text-surface-800 mb-4">Peak Hours</h3>
                    <div className="flex items-end gap-1 h-24">
                      {Object.entries(hourly).map(([hour, count]) => {
                        const h = (count / max) * 100;
                        return (
                          <motion.div key={hour} initial={{ height: 0 }} animate={{ height: `${h}%` }} transition={{ duration: 0.5 }}
                            className="flex-1 flex flex-col items-center">
                            <div className="w-full bg-gold-400 rounded-t" />
                            <span className="text-[9px] text-surface-400 mt-1">{hour}</span>
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>
                </motion.div>
              );
            })()}
          </>
        ) : (
          <div className="card p-12 text-center text-surface-400 border border-surface-200 shadow-card">Data load nahi ho paya</div>
        )}
      </div>
    </div></div>
  );
}
