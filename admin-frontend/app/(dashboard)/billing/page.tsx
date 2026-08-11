"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import { IndianRupee, Plus, Check, Clock, AlertTriangle, X, FileText, TrendingUp, CreditCard, Receipt } from "lucide-react";
import toast from "react-hot-toast";

interface Invoice {
  id: string;
  tenant_id: string;
  tenant_name: string;
  amount: number;
  currency: string;
  status: string;
  plan: string;
  billing_period: string;
  payment_id: string | null;
  created_at: string;
  paid_at: string | null;
}

interface Revenue {
  total_collected: number;
  total_pending: number;
  total_overdue: number;
  overdue_count: number;
  total_invoices: number;
  paid_count: number;
  collection_rate: number;
  mrr: number;
  plan_revenue: Record<string, number>;
}

interface TenantOption {
  id: string;
  name: string;
  plan: string;
}

const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: any }> = {
  pending: { color: "text-amber-700", bg: "bg-amber-50", icon: Clock },
  paid: { color: "text-emerald-700", bg: "bg-emerald-50", icon: Check },
  overdue: { color: "text-red-700", bg: "bg-red-50", icon: AlertTriangle },
  failed: { color: "text-gray-700", bg: "bg-gray-100", icon: X },
};

const PLAN_PRICES: Record<string, number> = {
  starter: 999,
  growth: 2499,
  enterprise: 4999,
};

export default function BillingPage() {
  const [revenue, setRevenue] = useState<Revenue | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [totalInvoices, setTotalInvoices] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [tenants, setTenants] = useState<TenantOption[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [rev, inv] = await Promise.all([
        masterAPI.getRevenue(),
        masterAPI.getInvoices({ status: statusFilter || undefined, page }),
      ]);
      setRevenue(rev);
      setInvoices(inv.invoices);
      setTotalInvoices(inv.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [page, statusFilter]);

  const loadTenants = async () => {
    try {
      const data = await masterAPI.getTenants({ limit: 100 });
      setTenants(data.tenants.map((t: any) => ({ id: t.id, name: t.name, plan: t.plan })));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkPaid = async (id: string) => {
    try {
      await masterAPI.updateInvoice(id, { status: "paid" });
      toast.success("Invoice marked as paid");
      loadData();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleMarkOverdue = async (id: string) => {
    try {
      await masterAPI.updateInvoice(id, { status: "overdue" });
      toast.success("Invoice marked as overdue");
      loadData();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const formatCurrency = (n: number) => `₹${n.toLocaleString("en-IN")}`;

  if (loading && !revenue) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing & Invoices</h1>
          <p className="text-sm text-gray-500 mt-1">Manage subscriptions, invoices, and revenue</p>
        </div>
        <button
          onClick={() => { setShowCreateModal(true); loadTenants(); }}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm"
        >
          <Plus size={16} />
          Create Invoice
        </button>
      </div>

      {/* Revenue Cards */}
      {revenue && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <RevenueCard
            label="Total Collected"
            value={formatCurrency(revenue.total_collected)}
            subtext={`${revenue.paid_count} paid invoices`}
            icon={IndianRupee}
            gradient="from-emerald-500 to-teal-600"
          />
          <RevenueCard
            label="MRR"
            value={formatCurrency(revenue.mrr)}
            subtext="Monthly Recurring Revenue"
            icon={TrendingUp}
            gradient="from-violet-500 to-purple-600"
          />
          <RevenueCard
            label="Pending"
            value={formatCurrency(revenue.total_pending)}
            subtext={`${revenue.collection_rate}% collection rate`}
            icon={CreditCard}
            gradient="from-amber-500 to-orange-600"
          />
          <RevenueCard
            label="Overdue"
            value={formatCurrency(revenue.total_overdue)}
            subtext={`${revenue.overdue_count} overdue invoices`}
            icon={AlertTriangle}
            gradient="from-red-500 to-rose-600"
          />
        </div>
      )}

      {/* Plan Revenue Breakdown */}
      {revenue && revenue.plan_revenue && (
        <div className="bg-white rounded-2xl shadow-sm border p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Revenue by Plan</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {Object.entries(PLAN_PRICES).map(([plan, price]) => {
              const rev = revenue.plan_revenue[plan] || 0;
              return (
                <div key={plan} className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 border">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    plan === "starter" ? "bg-indigo-100 text-indigo-600" :
                    plan === "growth" ? "bg-amber-100 text-amber-600" :
                    "bg-emerald-100 text-emerald-600"
                  }`}>
                    <Receipt size={22} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 capitalize">{plan}</p>
                    <p className="text-xs text-gray-500">{formatCurrency(price)}/mo</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-900">{formatCurrency(rev)}</p>
                    <p className="text-xs text-gray-400">collected</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Invoice Filters */}
      <div className="flex items-center gap-3">
        <div className="flex bg-white rounded-lg shadow-sm border overflow-hidden">
          {["", "pending", "paid", "overdue", "failed"].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                statusFilter === s
                  ? "bg-indigo-600 text-white"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <span className="text-sm text-gray-400">{totalInvoices} invoices</span>
      </div>

      {/* Invoice Table */}
      <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50/50">
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Tenant</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Period</th>
                <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => {
                const sc = STATUS_CONFIG[inv.status] || STATUS_CONFIG.pending;
                const StatusIcon = sc.icon;
                return (
                  <tr key={inv.id} className="border-b hover:bg-indigo-50/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <FileText size={16} className="text-gray-400" />
                        <span className="font-mono text-xs text-gray-500">{inv.id.slice(0, 8)}</span>
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {new Date(inv.created_at).toLocaleDateString("en-IN")}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-medium text-gray-900">{inv.tenant_name}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="capitalize text-gray-600">{inv.plan}</span>
                    </td>
                    <td className="px-6 py-4 text-gray-500">{inv.billing_period || "-"}</td>
                    <td className="px-6 py-4 text-right font-semibold text-gray-900">
                      {formatCurrency(inv.amount)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${sc.bg} ${sc.color}`}>
                        <StatusIcon size={12} />
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {inv.status === "pending" && (
                          <>
                            <button
                              onClick={() => handleMarkPaid(inv.id)}
                              className="text-xs bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-lg hover:bg-emerald-100 transition-colors font-medium"
                            >
                              Mark Paid
                            </button>
                            <button
                              onClick={() => handleMarkOverdue(inv.id)}
                              className="text-xs bg-red-50 text-red-700 px-3 py-1.5 rounded-lg hover:bg-red-100 transition-colors font-medium"
                            >
                              Overdue
                            </button>
                          </>
                        )}
                        {inv.status === "overdue" && (
                          <button
                            onClick={() => handleMarkPaid(inv.id)}
                            className="text-xs bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-lg hover:bg-emerald-100 transition-colors font-medium"
                          >
                            Mark Paid
                          </button>
                        )}
                        {inv.status === "paid" && inv.paid_at && (
                          <span className="text-xs text-gray-400">
                            Paid {new Date(inv.paid_at).toLocaleDateString("en-IN")}
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {invoices.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <FileText size={32} className="text-gray-300" />
                      <span className="text-gray-400">No invoices found</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalInvoices > 20 && (
          <div className="flex justify-between items-center px-6 py-3 border-t bg-gray-50/50">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="text-sm text-gray-600 disabled:opacity-50 hover:text-indigo-600"
            >
              ← Previous
            </button>
            <span className="text-sm text-gray-400">
              Page {page} of {Math.ceil(totalInvoices / 20) || 1}
            </span>
            <button
              disabled={page >= Math.ceil(totalInvoices / 20)}
              onClick={() => setPage(page + 1)}
              className="text-sm text-gray-600 disabled:opacity-50 hover:text-indigo-600"
            >
              Next →
            </button>
          </div>
        )}
      </div>

      {/* Create Invoice Modal */}
      {showCreateModal && (
        <CreateInvoiceModal
          tenants={tenants}
          onClose={() => setShowCreateModal(false)}
          onCreated={() => { setShowCreateModal(false); loadData(); }}
        />
      )}
    </div>
  );
}


// ─── Revenue Card ───
function RevenueCard({ label, value, subtext, icon: Icon, gradient }: {
  label: string;
  value: string;
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


// ─── Create Invoice Modal ───
function CreateInvoiceModal({ tenants, onClose, onCreated }: {
  tenants: TenantOption[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [tenantId, setTenantId] = useState("");
  const [plan, setPlan] = useState("growth");
  const [amount, setAmount] = useState(999);
  const [billingPeriod, setBillingPeriod] = useState(
    new Date().toISOString().slice(0, 7) // "YYYY-MM"
  );
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!tenantId) {
      toast.error("Please select a tenant");
      return;
    }
    setCreating(true);
    try {
      await masterAPI.createInvoice({
        tenant_id: tenantId,
        amount,
        plan,
        billing_period: billingPeriod,
      });
      toast.success("Invoice created!");
      onCreated();
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 m-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-gray-900">Create Invoice</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tenant</label>
            <select
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              className="w-full border rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            >
              <option value="">Select tenant...</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.plan})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
            <select
              value={plan}
              onChange={(e) => {
                setPlan(e.target.value);
                setAmount(PLAN_PRICES[e.target.value] || 999);
              }}
              className="w-full border rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            >
              <option value="starter">Starter (Free)</option>
              <option value="growth">Growth (₹999/mo)</option>
              <option value="enterprise">Enterprise (₹2,999/mo)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₹)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full border rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              min={0}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Billing Period</label>
            <input
              type="month"
              value={billingPeriod}
              onChange={(e) => setBillingPeriod(e.target.value)}
              className="w-full border rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2.5 text-sm text-gray-600 hover:text-gray-800 font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
          >
            {creating ? "Creating..." : "Create Invoice"}
          </button>
        </div>
      </div>
    </div>
  );
}
