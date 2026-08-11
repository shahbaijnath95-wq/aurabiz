"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Users2, Plus, IndianRupee } from "lucide-react";

export default function ResellersPage() {
  const [resellers, setResellers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", commission_rate: 30 });

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getResellers();
      setResellers(data.resellers || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await masterAPI.createReseller(form);
      toast.success("Reseller added");
      setShowForm(false);
      setForm({ name: "", email: "", commission_rate: 30 });
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const totalCommission = resellers.reduce((sum, r) => sum + (r.total_commission ?? 0), 0);
  const totalTenants = resellers.reduce((sum, r) => sum + (r.tenants_count ?? 0), 0);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <Users2 size={24} /> Resellers ({resellers.length})
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-blue-700"
        >
          <Plus size={14} /> Add Reseller
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <StatCard label="Total Resellers" value={resellers.length} />
        <StatCard label="Tenants Onboarded" value={totalTenants} />
        <StatCard label="Total Commission" value={`₹${totalCommission.toLocaleString()}`} icon={IndianRupee} />
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-xl shadow p-4 mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            type="text"
            placeholder="Reseller Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
            required
          />
          <input
            type="number"
            placeholder="Commission %"
            value={form.commission_rate}
            onChange={(e) => setForm({ ...form, commission_rate: Number(e.target.value) })}
            className="border rounded px-3 py-2 text-sm"
            min={0}
            max={50}
          />
          <button type="submit" className="bg-green-600 text-white px-3 py-2 rounded-lg text-sm col-span-full">
            Create Reseller
          </button>
        </form>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : resellers.length === 0 ? (
        <div className="text-gray-400 text-sm">No resellers yet</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Commission</th>
                <th className="text-left px-4 py-3">Tenants</th>
                <th className="text-left px-4 py-3">Total Earned</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {resellers.map((r) => (
                <tr key={r.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{r.name}</td>
                  <td className="px-4 py-3 text-gray-500">{r.email}</td>
                  <td className="px-4 py-3">{r.commission_rate}%</td>
                  <td className="px-4 py-3">{r.tenants_count ?? 0}</td>
                  <td className="px-4 py-3 font-medium">₹{(r.total_commission ?? 0).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      r.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                    }`}>
                      {r.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={async () => {
                        try {
                          const data = await masterAPI.getResellerPayouts(r.id);
                          toast.success(`${data.payouts?.length || 0} payouts found`);
                        } catch (err: any) {
                          toast.error(err.message);
                        }
                      }}
                      className="text-blue-600 hover:underline text-xs"
                    >
                      View Payouts
                    </button>
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

function StatCard({ label, value, icon: Icon }: { label: string; value: any; icon?: any }) {
  return (
    <div className="bg-white rounded-xl shadow p-4">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="bg-blue-100 text-blue-600 p-2 rounded-lg">
            <Icon size={20} />
          </div>
        )}
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}
