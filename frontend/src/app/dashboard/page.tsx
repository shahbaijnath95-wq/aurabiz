"use client";
import Sidebar from "@/components/Sidebar";
import { PageLoader } from "@/components/skeleton";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { analytics, orders as ordersApi, customers } from "@/lib/api";
import type { DashboardStats as DashboardStatsType } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { useWebSocket } from "@/lib/use-websocket";
import { useToast } from "@/lib/toast-context";
import Link from "next/link";

interface DashboardStatsData {
  total_revenue?: number;
  revenue?: number;
  revenue_change?: string;
  total_messages?: number;
  messages?: number;
  messages_change?: string;
  total_customers?: number;
  customers?: number;
  customers_change?: string;
  total_orders?: number;
  orders?: number;
  orders_change?: string;
  revenue_daily?: number[];
  top_products?: { name?: string; product_name?: string; sales?: number; quantity?: number }[];
}

interface StatCards {
  revenue?: { value?: number; change?: number };
  messages?: { value?: number; change?: number };
  customers?: { value?: number; change?: number };
  orders?: { value?: number; change?: number };
}

interface DashboardResponse {
  stat_cards?: StatCards;
  revenue_chart?: { revenue?: number }[];
  top_products?: { name?: string; product_name?: string; sales?: number; quantity?: number }[];
}

interface WebSocketMessage {
  type?: string;
  customer_name?: string;
  message?: string;
  amount?: number;
  [key: string]: unknown;
}

interface RecentOrder {
  id: string;
  customer_name: string;
  product_name: string;
  total_price: number;
  status: string;
  created_at: string;
}

// ─── Container animation ───
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

// ─── Premium Stat Card with sparkline ───
function StatCard({ title, value, change, icon, gradient, sparkData, delay }: {
  title: string; value: string; change?: string; icon: string; gradient: string; sparkData: number[]; delay: number;
}) {
  const isPositive = change && !change.startsWith("-");
  const max = Math.max(...sparkData, 1);
  const points = sparkData.map((v, i) => `${(i / Math.max(sparkData.length - 1, 1)) * 100},${100 - (v / max) * 80}`).join(" ");

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="relative overflow-hidden rounded-2xl bg-white border border-surface-200 p-5 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all group"
    >
      <div className="absolute -top-10 -right-10 w-28 h-28 rounded-full opacity-10 group-hover:opacity-20 transition-opacity bg-gold-400" />
      <div className="flex items-start justify-between mb-3">
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-lg shadow-gold-sm`}>{icon}</div>
        {change && (
          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${isPositive ? "bg-success-50 text-success-600" : "bg-error-50 text-error-500"}`}>
            {isPositive ? "↑" : "↓"} {change.replace("+", "").replace("-", "")}
          </span>
        )}
      </div>
      <div className="text-2xl font-extrabold text-surface-800 mb-0.5 tracking-tight">{value}</div>
      <div className="text-surface-500 text-xs font-medium mb-3">{title}</div>
      {/* Mini sparkline */}
      <svg viewBox="0 0 100 20" className="w-full h-5" preserveAspectRatio="none">
        <defs>
          <linearGradient id={`g-${title}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e67a00" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#e67a00" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,100 ${points} 100,100`} fill={`url(#g-${title})`} />
        <polyline points={points} fill="none" stroke="#e67a00" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </motion.div>
  );
}

// ─── Revenue Area Chart ───
function RevenueChart({ data }: { data: number[] }) {
  const max = Math.max(...data, 1);
  const points = data.map((v, i) => ({ x: (i / Math.max(data.length - 1, 1)) * 100, y: 100 - (v / max) * 85 - 8 }));
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x},${p.y}`).join(" ");
  const areaPath = `${linePath} L 100,100 L 0,100 Z`;
  const total = data.reduce((a, b) => a + b, 0);
  const last = data[data.length - 1] || 0;
  const prev = data[data.length - 2] || 0;
  const trendUp = last >= prev;

  return (
    <div className="relative">
      <svg viewBox="0 0 100 100" className="w-full h-44" preserveAspectRatio="none">
        <defs>
          <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e67a00" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#e67a00" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#revGrad)" />
        <motion.path
          d={linePath}
          fill="none"
          stroke="#e67a00"
          strokeWidth="2"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.2, ease: "easeInOut" }}
        />
        {points.map((p, i) => (
          <motion.circle key={i} cx={p.x} cy={p.y} r="1.8" fill="#fff" stroke="#e67a00" strokeWidth="0.8"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 + i * 0.05 }}
          />
        ))}
      </svg>
      <div className="flex justify-between mt-2 text-[11px] text-surface-400 px-1">
        <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
      </div>
      <div className={`absolute top-1 right-0 px-2.5 py-1 rounded-full text-xs font-bold ${trendUp ? "bg-success-50 text-success-600" : "bg-error-50 text-error-500"}`}>
        {trendUp ? "📈 Growing" : "📉 Dip"}
      </div>
      <div className="absolute top-1 left-0 text-2xl font-extrabold text-gold-600">₹{total.toLocaleString()}</div>
    </div>
  );
}

// ─── Live Activity Feed ───
function ActivityFeed({ items }: { items: Array<{ text: string; time: string; type: string }> }) {
  const config: Record<string, { icon: string; bg: string }> = {
    message: { icon: "💬", bg: "bg-info-50 text-info-600 ring-info-100" },
    sale: { icon: "🛒", bg: "bg-gold-50 text-gold-600 ring-gold-100" },
    loyalty: { icon: "⭐", bg: "bg-violet-50 text-violet-600 ring-violet-100" },
    alert: { icon: "⚠️", bg: "bg-error-50 text-error-500 ring-error-100" },
  };
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
      className="rounded-2xl bg-white border border-surface-200 shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-surface-200 flex items-center justify-between">
        <h3 className="font-bold text-surface-800">Live Activity</h3>
        <span className="px-2.5 py-1 rounded-full bg-surface-100 text-surface-500 text-xs font-semibold">{items.length} events</span>
      </div>
      <div className="p-3 space-y-0.5 max-h-80 overflow-y-auto">
        {items.map((act, i) => {
          const c = config[act.type] || { icon: "•", bg: "bg-surface-100 text-surface-500" };
          return (
            <motion.div key={i} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
              className="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-surface-50 transition-colors">
              <div className={`w-8 h-8 rounded-lg ring-1 flex items-center justify-center text-xs shrink-0 ${c.bg}`}>{c.icon}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-surface-700 leading-snug truncate">{act.text}</p>
                <p className="text-[11px] text-surface-400 mt-0.5">{act.time}</p>
              </div>
            </motion.div>
          );
        })}
        {items.length === 0 && (
          <div className="text-center py-10">
            <div className="text-3xl mb-2">📭</div>
            <p className="text-surface-400 text-sm">Abhi koi activity nahi — WhatsApp pe message aane ka wait karo</p>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStatsData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activity, setActivity] = useState<Array<{ text: string; time: string; type: string }>>([]);
  const [recentOrders, setRecentOrders] = useState<RecentOrder[]>([]);
  const { businessId, isAuthenticated, loading: authLoading, user, business } = useAuth();
  const { lastMessage } = useWebSocket(businessId || undefined) as { lastMessage: WebSocketMessage | null };
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) { setLoading(false); return; }
    setLoading(true);
    Promise.all([
      analytics.dashboard(businessId).catch(() => ({})),
      ordersApi.list(businessId).catch(() => []),
    ]).then(([raw, orders]) => {
      const d = raw as unknown as DashboardResponse;
      const sc = d?.stat_cards || {};
      setStats({
        total_revenue: sc.revenue?.value || 0,
        revenue_change: `+${sc.revenue?.change || 0}%`,
        total_messages: sc.messages?.value || 0,
        messages_change: `+${sc.messages?.change || 0}%`,
        total_customers: sc.customers?.value || 0,
        customers_change: `+${sc.customers?.change || 0}%`,
        total_orders: sc.orders?.value || 0,
        orders_change: `+${sc.orders?.change || 0}%`,
        revenue_daily: (d.revenue_chart || []).map((r: { revenue?: number }) => r.revenue || 0),
        top_products: d.top_products || [],
      });
      // Extract recent orders
      const orderList = Array.isArray(orders) ? orders : [];
      setRecentOrders(orderList.slice(0, 5).map((o: Record<string, unknown>) => ({
        id: o.id as string || "",
        customer_name: (o.customer_name as string) || "Customer",
        product_name: (o.product_name as string) || "Product",
        total_price: (o.total_price as number) || 0,
        status: (o.status as string) || "pending",
        created_at: (o.created_at as string) || "",
      })));
      setLoading(false);
      setError("");
    }).catch(() => {
      setStats({});
      setLoading(false);
      setError("Backend chal raha hai kya? Data load nahi ho raha.");
    });
  }, [businessId]);

  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.type === "new_message") {
      setActivity(prev => [{ text: `${lastMessage.customer_name}: "${lastMessage.message?.slice(0, 50)}..."`, time: "Abhi", type: "message" }, ...prev.slice(0, 14)]);
    } else if (lastMessage.type === "new_order") {
      setActivity(prev => [{ text: `${lastMessage.customer_name} ne ₹${lastMessage.amount} ka order kiya`, time: "Abhi", type: "sale" }, ...prev.slice(0, 14)]);
    }
  }, [lastMessage]);

  const d = stats || {};
  const revenueData = d.revenue_daily || [0, 0, 0, 0, 0, 0, 0];
  const today = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const firstName = user?.full_name?.split(" ")[0] || "Boss";

  const sparkData = useMemo(() => {
    const base = revenueData.map(v => v || Math.floor(Math.random() * 500) + 100);
    return base;
  }, [revenueData]);

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-surface-100 via-surface-50 to-gold-50/30">
      <Sidebar />
      <div className="flex-1 overflow-y-auto">
        <main className="p-6 lg:p-8 max-w-[1400px] mx-auto">
          {/* ── Header ── */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
            className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <p className="text-sm text-gold-600 font-semibold mb-1">{today}</p>
              <h1 className="text-2xl md:text-3xl font-extrabold text-surface-800 tracking-tight">Namaste, {firstName}! 👋</h1>
              <p className="text-surface-500 mt-1 text-sm">{business?.name || "Aapke business"} — aaj ka overview</p>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl bg-white border border-surface-200 shadow-sm">
                <span className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
                <span className="text-xs font-medium text-surface-600">WhatsApp Live</span>
              </div>
              <Link href="/dashboard/inventory" className="btn-gold text-sm py-2">+ Add Product</Link>
              <Link href="/admin/orders" className="btn-ghost text-sm py-2">View Orders</Link>
            </div>
          </motion.div>

          {error && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
              className="bg-warning-50 border border-warning-200 text-warning-700 rounded-xl p-4 mb-6 flex items-center gap-3">
              <span className="text-lg">⚠️</span>
              <div><p className="font-medium">{error}</p></div>
            </motion.div>
          )}

          {loading ? (
            <PageLoader />
          ) : (
            <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">

              {/* ── Stat Cards with Sparklines ── */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Revenue" value={`₹${(d.total_revenue || d.revenue || 0).toLocaleString()}`} change={d.revenue_change || "+12%"} icon="₹" gradient="from-gold-400 to-gold-600 text-white" sparkData={sparkData} delay={0} />
                <StatCard title="Messages" value={String(d.total_messages || d.messages || 0)} change={d.messages_change || "+5"} icon="💬" gradient="from-info-400 to-info-600 text-white" sparkData={sparkData.map(v => v * 0.7)} delay={0.08} />
                <StatCard title="Customers" value={String(d.total_customers || d.customers || 0)} change={d.customers_change || "+3"} icon="👥" gradient="from-violet-400 to-violet-600 text-white" sparkData={sparkData.map(v => v * 0.5)} delay={0.16} />
                <StatCard title="Orders" value={String(d.total_orders || d.orders || 0)} change={d.orders_change || "0"} icon="🛒" gradient="from-success-400 to-success-600 text-white" sparkData={sparkData.map(v => v * 0.6)} delay={0.24} />
              </div>

              {/* ── Revenue + Quick Actions ── */}
              <div className="grid lg:grid-cols-3 gap-6">
                <motion.div variants={item} className="lg:col-span-2 rounded-2xl bg-white border border-surface-200 shadow-sm p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-bold text-surface-800 text-lg">Revenue Overview</h3>
                      <p className="text-xs text-surface-400">Last 7 days performance</p>
                    </div>
                    <div className="flex gap-2">
                      <button className="px-3 py-1.5 rounded-lg bg-surface-100 text-surface-600 text-xs font-semibold hover:bg-surface-200 transition-colors">7D</button>
                      <button className="px-3 py-1.5 rounded-lg text-surface-400 text-xs font-semibold hover:bg-surface-100 transition-colors">30D</button>
                    </div>
                  </div>
                  <RevenueChart data={revenueData} />
                </motion.div>

                {/* Quick Actions */}
                <motion.div variants={item} className="rounded-2xl bg-white border border-surface-200 shadow-sm p-6">
                  <h3 className="font-bold text-surface-800 mb-4">Quick Actions</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { href: "/dashboard/inventory", icon: "📦", label: "Add Product", color: "from-gold-400 to-gold-500" },
                      { href: "/admin/orders", icon: "🛒", label: "Orders", color: "from-info-400 to-info-500" },
                      { href: "/admin/inbox", icon: "💬", label: "Inbox", color: "from-success-400 to-success-500" },
                      { href: "/admin/whatsapp", icon: "🤖", label: "WhatsApp", color: "from-violet-400 to-violet-500" },
                      { href: "/analytics", icon: "📊", label: "Analytics", color: "from-pink-400 to-pink-500" },
                      { href: "/admin/settings", icon: "⚙️", label: "Settings", color: "from-surface-400 to-surface-500" },
                    ].map((a) => (
                      <Link key={a.href} href={a.href} className="group">
                        <div className={`p-3.5 rounded-xl bg-gradient-to-br ${a.color} text-white flex flex-col gap-1.5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all`}>
                          <span className="text-lg">{a.icon}</span>
                          <span className="text-[11px] font-semibold">{a.label}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </motion.div>
              </div>

              {/* ── Top Products + Recent Orders ── */}
              <div className="grid lg:grid-cols-2 gap-6">
                {/* Top Products */}
                <motion.div variants={item} className="rounded-2xl bg-white border border-surface-200 shadow-sm p-6">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="font-bold text-surface-800">Top Products</h3>
                    <span className="px-2.5 py-1 rounded-full bg-gold-50 text-gold-600 text-xs font-semibold">Bestsellers</span>
                  </div>
                  <div className="space-y-4">
                    {(d.top_products || []).slice(0, 5).map((p: { name?: string; product_name?: string; sales?: number; quantity?: number }, i: number) => {
                      const maxSales = Math.max(...(d.top_products || []).map((x: { sales?: number; quantity?: number }) => x.sales || x.quantity || 1));
                      const pct = ((p.sales || p.quantity || 0) / maxSales) * 100;
                      const rankColors = ["bg-gold-400", "bg-surface-300", "bg-orange-400"];
                      return (
                        <div key={i}>
                          <div className="flex justify-between items-center mb-1.5">
                            <div className="flex items-center gap-2.5 min-w-0">
                              <span className={`w-6 h-6 rounded-md ${rankColors[i] || "bg-surface-200"} text-white text-[11px] font-bold flex items-center justify-center shrink-0`}>{i + 1}</span>
                              <span className="font-medium text-surface-700 text-sm truncate">{p.name || p.product_name}</span>
                            </div>
                            <span className="text-surface-400 text-xs shrink-0">{p.sales || p.quantity || 0} sold</span>
                          </div>
                          <div className="h-1.5 bg-surface-100 rounded-full overflow-hidden ml-8">
                            <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.6, delay: 0.3 + i * 0.1 }}
                              className="h-full bg-gradient-to-r from-gold-400 to-gold-500 rounded-full" />
                          </div>
                        </div>
                      );
                    })}
                    {(!d.top_products || d.top_products.length === 0) && (
                      <div className="text-center py-8"><div className="text-3xl mb-2">🏷️</div><p className="text-surface-400 text-sm">Abhi koi product data nahi — products add karo</p></div>
                    )}
                  </div>
                </motion.div>

                {/* Recent Orders */}
                <motion.div variants={item} className="rounded-2xl bg-white border border-surface-200 shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
                    <h3 className="font-bold text-surface-800">Recent Orders</h3>
                    <Link href="/admin/orders" className="text-xs text-gold-600 font-semibold hover:text-gold-700">View All →</Link>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-surface-50">
                          <th className="text-left px-6 py-3 text-xs font-semibold text-surface-500 uppercase">Customer</th>
                          <th className="text-left px-6 py-3 text-xs font-semibold text-surface-500 uppercase">Product</th>
                          <th className="text-right px-6 py-3 text-xs font-semibold text-surface-500 uppercase">Amount</th>
                          <th className="text-center px-6 py-3 text-xs font-semibold text-surface-500 uppercase">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-surface-100">
                        {recentOrders.map((o) => {
                          const statusColors: Record<string, string> = {
                            confirmed: "bg-success-50 text-success-600",
                            pending: "bg-warning-50 text-warning-700",
                            delivered: "bg-info-50 text-info-600",
                            cancelled: "bg-error-50 text-error-500",
                          };
                          const sc = statusColors[o.status] || "bg-surface-100 text-surface-500";
                          return (
                            <tr key={o.id} className="hover:bg-surface-50 transition-colors">
                              <td className="px-6 py-3 font-medium text-surface-700">{o.customer_name}</td>
                              <td className="px-6 py-3 text-surface-600">{o.product_name}</td>
                              <td className="px-6 py-3 text-right font-semibold text-surface-800">₹{o.total_price.toLocaleString()}</td>
                              <td className="px-6 py-3 text-center">
                                <span className={`px-2.5 py-1 rounded-full text-xs font-bold capitalize ${sc}`}>{o.status}</span>
                              </td>
                            </tr>
                          );
                        })}
                        {recentOrders.length === 0 && (
                          <tr><td colSpan={4} className="px-6 py-10 text-center text-surface-400">Abhi koi order nahi hai</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              </div>

              {/* ── Activity Feed ── */}
              <motion.div variants={item}>
                <ActivityFeed items={activity} />
              </motion.div>
            </motion.div>
          )}
        </main>
      </div>
    </div>
  );
}
