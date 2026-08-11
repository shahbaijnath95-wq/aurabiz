"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import {
  ArrowLeft,
  Ban,
  CheckCircle,
  Eye,
  IndianRupee,
  Users,
  MessageSquare,
  Package,
  ShoppingCart,
  LogIn,
} from "lucide-react";

export default function TenantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [tenant, setTenant] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "customers" | "orders" | "messages" | "products">("overview");
  const [tableData, setTableData] = useState<any[]>([]);
  const [tableLoading, setTableLoading] = useState(false);

  useEffect(() => {
    masterAPI.getTenant(id)
      .then(setTenant)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (activeTab === "overview") return;
    setTableLoading(true);
    const tableMap: Record<string, string> = {
      customers: "customers",
      orders: "orders",
      messages: "whatsapp_messages",
      products: "products",
    };
    masterAPI.getTenantData(id, tableMap[activeTab])
      .then((data) => setTableData(data.records || data.items || []))
      .catch(() => setTableData([]))
      .finally(() => setTableLoading(false));
  }, [activeTab, id]);

  const handleSuspend = async () => {
    if (!confirm(`Suspend "${tenant.name}"?`)) return;
    try {
      await masterAPI.suspendTenant(id, "Suspended from detail view");
      toast.success("Tenant suspended");
      const updated = await masterAPI.getTenant(id);
      setTenant(updated);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleReactivate = async () => {
    try {
      await masterAPI.reactivateTenant(id);
      toast.success("Reactivated");
      const updated = await masterAPI.getTenant(id);
      setTenant(updated);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handlePlanChange = async (newPlan: string) => {
    try {
      await masterAPI.updateTenantPlan(id, newPlan);
      toast.success(`Plan changed to ${newPlan}`);
      const updated = await masterAPI.getTenant(id);
      setTenant(updated);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleImpersonate = async () => {
    try {
      const data = await masterAPI.impersonateTenant(id);
      if (data.token) {
        localStorage.setItem("token", data.token);
        window.open("http://127.0.0.1:3001/dashboard", "_blank");
      }
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  if (loading) return <div className="animate-pulse text-gray-400">Loading...</div>;
  if (!tenant) return <div className="text-red-500">Tenant not found</div>;

  const msgUsed = tenant.messages_used ?? 0;
  const msgMax = tenant.max_messages ?? 0;
  const msgPct = msgMax > 0 ? Math.min((msgUsed / msgMax) * 100, 100) : 0;

  return (
    <div>
      <button onClick={() => router.push("/tenants")} className="text-gray-500 hover:text-gray-700 text-sm mb-3 inline-flex items-center gap-1">
        <ArrowLeft size={14} /> Back to Tenants
      </button>

      <div className="bg-white rounded-xl shadow p-6 mb-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{tenant.name}</h1>
            <p className="text-gray-500 text-sm">{tenant.slug}</p>
            <div className="mt-2 flex gap-4 text-sm text-gray-600">
              <span>Owner: {tenant.owner_name}</span>
              <span>Email: {tenant.owner_email}</span>
              {tenant.owner_phone && <span>Phone: {tenant.owner_phone}</span>}
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleImpersonate} className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-blue-700">
              <LogIn size={14} /> Impersonate
            </button>
            {tenant.status === "active" ? (
              <button onClick={handleSuspend} className="bg-red-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-red-700">
                <Ban size={14} /> Suspend
              </button>
            ) : (
              <button onClick={handleReactivate} className="bg-green-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-green-700">
                <CheckCircle size={14} /> Reactivate
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div>
            <label className="text-xs text-gray-500 uppercase">Status</label>
            <span className={`block px-2 py-1 rounded-full text-xs font-medium w-fit mt-1 ${
              tenant.status === "active" ? "bg-green-100 text-green-700" :
              tenant.status === "suspended" ? "bg-red-100 text-red-700" :
              "bg-gray-100 text-gray-700"
            }`}>
              {tenant.status}
            </span>
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase">Plan</label>
            <select
              value={tenant.plan}
              onChange={(e) => handlePlanChange(e.target.value)}
              className="block border rounded px-2 py-1 text-sm mt-1"
            >
              <option value="starter">Starter</option>
              <option value="growth">Growth</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase">Created</label>
            <p className="text-sm mt-1">{new Date(tenant.created_at).toLocaleDateString()}</p>
          </div>
          {tenant.trial_ends_at && (
            <div>
              <label className="text-xs text-gray-500 uppercase">Trial Ends</label>
              <p className="text-sm mt-1">{new Date(tenant.trial_ends_at).toLocaleDateString()}</p>
            </div>
          )}
        </div>

        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Messages Used: {msgUsed} / {msgMax || "∞"}</span>
            <span>{msgPct.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${msgPct}%` }}></div>
          </div>
        </div>
      </div>

      <div className="flex gap-1 border-b mb-4">
        {[
          { key: "overview", label: "Overview", icon: Eye },
          { key: "customers", label: "Customers", icon: Users },
          { key: "orders", label: "Orders", icon: ShoppingCart },
          { key: "messages", label: "Messages", icon: MessageSquare },
          { key: "products", label: "Products", icon: Package },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as any)}
            className={`px-4 py-2 text-sm border-b-2 transition-colors inline-flex items-center gap-1 ${
              activeTab === key ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {activeTab === "overview" ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard label="Total Revenue" icon={IndianRupee} value={`₹${tenant.total_revenue ?? 0}`} />
          <StatCard label="Total Orders" icon={ShoppingCart} value={tenant.total_orders ?? 0} />
          <StatCard label="Total Customers" icon={Users} value={tenant.total_customers ?? 0} />
        </div>
      ) : tableLoading ? (
        <div className="animate-pulse text-gray-400">Loading {activeTab}...</div>
      ) : tableData.length === 0 ? (
        <div className="text-gray-400 text-sm">No {activeTab} found</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {Object.keys(tableData[0]).slice(0, 6).map((key) => (
                  <th key={key} className="text-left px-4 py-3 capitalize">{key.replace(/_/g, " ")}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, i) => (
                <tr key={i} className="border-b hover:bg-gray-50">
                  {Object.values(row).slice(0, 6).map((val: any, j) => (
                    <td key={j} className="px-4 py-3">
                      {typeof val === "object" ? JSON.stringify(val).slice(0, 50) : String(val ?? "").slice(0, 80)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, icon: Icon, value }: { label: string; icon: any; value: any }) {
  return (
    <div className="bg-white rounded-xl shadow p-4">
      <div className="flex items-center gap-3">
        <div className="bg-blue-100 text-blue-600 p-2 rounded-lg">
          <Icon size={20} />
        </div>
        <div>
          <p className="text-xl font-bold">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}
