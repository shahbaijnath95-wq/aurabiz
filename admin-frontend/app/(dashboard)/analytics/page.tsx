"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import { BarChart3, TrendingUp, Users, MessageSquare, IndianRupee, ArrowUpRight, ArrowDownRight, RefreshCw, Crown, Zap, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

interface DailyStat {
  date: string;
  total_tenants: number;
  active_tenants: number;
  total_messages: number;
  total_orders: number;
  total_revenue: number;
  new_signups: number;
}

interface TopTenant {
  id: string;
  name: string;
  owner_email: string;
  plan: string;
  messages_used_this_month: number;
  total_orders: number;
  total_revenue: number;
  total_customers: number;
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<any>(null);
  const [dailyStats, setDailyStats] = useState<DailyStat[]>([]);
  const [growth, setGrowth] = useState<any>(null);
  const [topTenants, setTopTenants] = useState<TopTenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [aggregating, setAggregating] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ov, daily, gr, top] = await Promise.all([
        masterAPI.getAnalyticsOverview(),
        masterAPI.getDailyStats(days),
        masterAPI.getGrowthStats(),
        masterAPI.getTopTenants(10),
      ]);
      setOverview(ov);
      setDailyStats(daily.stats || []);
      setGrowth(gr);
      setTopTenants(top.tenants || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [days]);

  const handleAggregate = async () => {
    setAggregating(true);
    try {
      await masterAPI.aggregateStats();
      toast.success("Stats aggregated successfully!");
      loadData();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setAggregating(false);
    }
  };

  const formatCurrency = (n: number) => `₹${n.toLocaleString("en-IN")}`;

  const planColors: Record<string, string> = {
    starter: "#6366f1",
    growth: "#f59e0b",
    enterprise: "#10b981",
  };

  const planIcons: Record<string, any> = {
    starter: Zap,
    growth: Sparkles,
    enterprise: Crown,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // Chart helpers
  const maxRevenue = Math.max(...dailyStats.map(s => s.total_revenue), 1);
  const maxMessages = Math.max(...dailyStats.map(s => s.total_messages), 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Platform Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time platform performance metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  days === d
                    ? "bg-indigo-600 text-white"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
          <button
            onClick={handleAggregate}
            disabled={aggregating}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
          >
            <RefreshCw size={16} className={aggregating ? "animate-spin" : ""} />
            Sync Stats
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Revenue"
            value={formatCurrency(overview.total_revenue)}
            subtext={`${formatCurrency(overview.pending_revenue)} pending`}
            icon={IndianRupee}
            gradient="from-emerald-500 to-teal-600"
          />
          <StatCard
            label="Monthly MRR"
            value={formatCurrency(overview.mrr)}
            subtext={`${overview.active_tenants} paying tenants`}
            icon={TrendingUp}
            gradient="from-violet-500 to-purple-600"
          />
          <StatCard
            label="Active Tenants"
            value={overview.active_tenants}
            subtext={`${overview.total_tenants} total | ${overview.suspended_tenants} suspended`}
            icon={Users}
            gradient="from-blue-500 to-cyan-600"
          />
          <StatCard
            label="Messages (Month)"
            value={overview.total_messages_this_month?.toLocaleString() ?? "0"}
            subtext={`${overview.new_signups_this_month} new signups`}
            icon={MessageSquare}
            gradient="from-amber-500 to-orange-600"
          />
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Chart - Takes 2 cols */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Revenue Trend</h2>
            <span className="text-xs text-gray-400">Last {days} days</span>
          </div>
          {dailyStats.length > 0 ? (
            <div className="flex items-end gap-[2px] h-48">
              {dailyStats.map((stat, i) => {
                const height = (stat.total_revenue / maxRevenue) * 100;
                return (
                  <div
                    key={stat.date}
                    className="group relative flex-1 flex flex-col items-center justify-end"
                  >
                    <div
                      className="w-full rounded-t-sm transition-all duration-300 hover:opacity-80"
                      style={{
                        height: `${Math.max(height, 2)}%`,
                        background: `linear-gradient(to top, #6366f1, #a78bfa)`,
                      }}
                    />
                    {/* Tooltip */}
                    <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap z-10 shadow-lg">
                      <div className="font-medium">{stat.date}</div>
                      <div>Revenue: {formatCurrency(stat.total_revenue)}</div>
                      <div>Orders: {stat.total_orders}</div>
                      <div>Messages: {stat.total_messages}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
              No daily data yet. Click &quot;Sync Stats&quot; to aggregate.
            </div>
          )}
          {dailyStats.length > 0 && (
            <div className="flex justify-between mt-2 text-xs text-gray-400">
              <span>{dailyStats[0]?.date}</span>
              <span>{dailyStats[dailyStats.length - 1]?.date}</span>
            </div>
          )}
        </div>

        {/* Plan Distribution */}
        <div className="bg-white rounded-2xl shadow-sm border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Plan Distribution</h2>
          {growth && growth.plan_distribution ? (
            <div className="space-y-4">
              {Object.entries(growth.plan_distribution).map(([plan, count]) => {
                const total = growth.total_tenants || 1;
                const pct = Math.round(((count as number) / total) * 100);
                const PlanIcon = planIcons[plan] || Zap;
                return (
                  <div key={plan} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center"
                          style={{ backgroundColor: `${planColors[plan]}15` }}
                        >
                          <PlanIcon size={16} style={{ color: planColors[plan] }} />
                        </div>
                        <span className="text-sm font-medium capitalize">{plan}</span>
                      </div>
                      <span className="text-sm text-gray-500">{count as number} ({pct}%)</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700 ease-out"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: planColors[plan],
                        }}
                      />
                    </div>
                  </div>
                );
              })}

              <div className="mt-6 pt-4 border-t space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">MRR</span>
                  <span className="font-semibold text-gray-900">{formatCurrency(growth.mrr)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Churn Rate</span>
                  <span className="font-semibold text-gray-900">{growth.churn_rate}%</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data</div>
          )}
        </div>
      </div>

      {/* Growth Metrics */}
      {growth && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GrowthCard
            label="New Signups (Month)"
            value={growth.new_signups_this_month}
            change={growth.signup_growth_pct}
            subtext={`vs ${growth.new_signups_last_month} last month`}
          />
          <GrowthCard
            label="Churned (Month)"
            value={growth.churned_this_month}
            change={-growth.churn_rate}
            subtext={`${growth.churn_rate}% churn rate`}
          />
          <GrowthCard
            label="Active Tenants"
            value={growth.total_active}
            subtext={`out of ${growth.total_tenants} total`}
          />
          <GrowthCard
            label="MRR"
            value={formatCurrency(growth.mrr)}
            subtext="Monthly Recurring Revenue"
          />
        </div>
      )}

      {/* Top Tenants */}
      <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
        <div className="px-6 py-4 border-b bg-gradient-to-r from-gray-50 to-white">
          <h2 className="font-semibold text-gray-900">Top Tenants by Usage</h2>
          <p className="text-xs text-gray-500 mt-0.5">Ranked by message volume this month</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50/50">
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Business</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Messages</th>
                <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Orders</th>
                <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue</th>
                <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Customers</th>
              </tr>
            </thead>
            <tbody>
              {topTenants.map((t, i) => (
                <tr key={t.id} className="border-b hover:bg-indigo-50/30 transition-colors">
                  <td className="px-6 py-3">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${
                      i === 0 ? "bg-amber-100 text-amber-700" :
                      i === 1 ? "bg-gray-100 text-gray-600" :
                      i === 2 ? "bg-orange-100 text-orange-700" :
                      "bg-gray-50 text-gray-400"
                    }`}>
                      {i + 1}
                    </span>
                  </td>
                  <td className="px-6 py-3">
                    <div className="font-medium text-gray-900">{t.name}</div>
                    <div className="text-xs text-gray-400">{t.owner_email}</div>
                  </td>
                  <td className="px-6 py-3">
                    <span
                      className="px-2.5 py-1 rounded-full text-xs font-medium capitalize"
                      style={{
                        backgroundColor: `${planColors[t.plan] || "#6b7280"}15`,
                        color: planColors[t.plan] || "#6b7280",
                      }}
                    >
                      {t.plan}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right font-medium">{(t.messages_used_this_month ?? 0).toLocaleString()}</td>
                  <td className="px-6 py-3 text-right">{(t.total_orders ?? 0).toLocaleString()}</td>
                  <td className="px-6 py-3 text-right">{formatCurrency(t.total_revenue ?? 0)}</td>
                  <td className="px-6 py-3 text-right">{(t.total_customers ?? 0).toLocaleString()}</td>
                </tr>
              ))}
              {topTenants.length === 0 && (
                <tr><td colSpan={7} className="px-6 py-8 text-center text-gray-400">No tenants yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


// ─── Stat Card Component ───
function StatCard({ label, value, subtext, icon: Icon, gradient }: {
  label: string;
  value: string | number;
  subtext: string;
  icon: any;
  gradient: string;
}) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          <p className="text-xs text-gray-400 mt-1">{subtext}</p>
        </div>
        <div className={`bg-gradient-to-br ${gradient} p-2.5 rounded-xl text-white shadow-sm`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}


// ─── Growth Card Component ───
function GrowthCard({ label, value, change, subtext }: {
  label: string;
  value: string | number;
  change?: number;
  subtext?: string;
}) {
  const isPositive = change !== undefined && change >= 0;
  return (
    <div className="bg-white rounded-2xl shadow-sm border p-5 hover:shadow-md transition-shadow">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <div className="flex items-end gap-2 mt-1">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {change !== undefined && (
          <span className={`flex items-center gap-0.5 text-xs font-medium px-1.5 py-0.5 rounded-full ${
            isPositive ? "text-emerald-700 bg-emerald-50" : "text-red-700 bg-red-50"
          }`}>
            {isPositive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
            {Math.abs(change)}%
          </span>
        )}
      </div>
      {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
    </div>
  );
}
