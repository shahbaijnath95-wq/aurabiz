"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import Sidebar from "@/components/Sidebar";
import { request } from "@/lib/api";

interface Coupon {
  id: string;
  code: string;
  discount_type: string;
  discount_value: number;
  min_order: number;
  max_uses: number;
  used_count: number;
  is_active: boolean;
  expires_at: string | null;
  created_at: string | null;
}

export default function CouponsPage() {
  const { business, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    code: "", discount_type: "percent", discount_value: 0, min_order: 0, max_uses: 100,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (business?.id) fetchCoupons();
  }, [business?.id]);

  async function fetchCoupons() {
    try {
      const data = await request<Coupon[]>(`/coupons/${business?.id}`);
      setCoupons(Array.isArray(data) ? data : (data as unknown as { coupons?: Coupon[] })?.coupons || []);
    } catch (e) { console.error(e); toast("Coupons load nahi ho paye", "error"); }
    setLoading(false);
  }

  async function createCoupon() {
    try {
      await request("/coupons", {
        method: "POST",
        body: JSON.stringify({ business_id: business?.id, ...form, code: form.code.toUpperCase() }),
      });
      setShowCreate(false);
      setForm({ code: "", discount_type: "percent", discount_value: 0, min_order: 0, max_uses: 100 });
      toast("Coupon ban gaya!", "success");
      fetchCoupons();
    } catch (e) { console.error(e); toast("Coupon nahi bana", "error"); }
  }

  async function toggleCoupon(id: string, isActive: boolean) {
    try {
      await request(`/coupons/${id}?is_active=${!isActive}`, { method: "PUT" });
      fetchCoupons();
    } catch (e) { console.error(e); toast("Toggle nahi ho paya", "error"); }
  }

  async function deleteCoupon(id: string) {
    if (!confirm("Coupon delete karna hai?")) return;
    try {
      await request(`/coupons/${id}`, { method: "DELETE" });
      toast("Coupon delete ho gaya!", "success");
      fetchCoupons();
    } catch (e) { console.error(e); toast("Delete nahi ho paya", "error"); }
  }

  return (
    <div className="flex min-h-screen bg-[#faf9f7]">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Coupons & Discounts</h1>
              <p className="text-sm text-gray-500 mt-1">Create coupons for your customers</p>
            </div>
            <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-amber-500 text-white rounded-xl font-medium hover:bg-amber-600 transition-colors">
              + Create Coupon
            </button>
          </div>

          {showCreate && (
            <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-100 shadow-sm">
              <h3 className="font-bold text-gray-900 mb-4">New Coupon</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Coupon Code</label>
                  <input value={form.code} onChange={e => setForm({...form, code: e.target.value})} placeholder="SAVE10" className="w-full mt-1 px-4 py-2 border border-gray-200 rounded-xl text-sm" />
                </div>
                <div>
                  <label className="text-sm text-gray-500">Discount Type</label>
                  <select value={form.discount_type} onChange={e => setForm({...form, discount_type: e.target.value})} className="w-full mt-1 px-4 py-2 border border-gray-200 rounded-xl text-sm">
                    <option value="percent">Percent (%)</option>
                    <option value="flat">Flat (₹)</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Discount Value</label>
                  <input type="number" value={form.discount_value} onChange={e => setForm({...form, discount_value: Number(e.target.value)})} className="w-full mt-1 px-4 py-2 border border-gray-200 rounded-xl text-sm" />
                </div>
                <div>
                  <label className="text-sm text-gray-500">Min Order (₹)</label>
                  <input type="number" value={form.min_order} onChange={e => setForm({...form, min_order: Number(e.target.value)})} className="w-full mt-1 px-4 py-2 border border-gray-200 rounded-xl text-sm" />
                </div>
                <div>
                  <label className="text-sm text-gray-500">Max Uses</label>
                  <input type="number" value={form.max_uses} onChange={e => setForm({...form, max_uses: Number(e.target.value)})} className="w-full mt-1 px-4 py-2 border border-gray-200 rounded-xl text-sm" />
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button onClick={createCoupon} className="px-4 py-2 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600">Create</button>
                <button onClick={() => setShowCreate(false)} className="px-4 py-2 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-gray-100 overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Code</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Discount</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Min Order</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Usage</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {coupons.map(c => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-mono font-bold text-amber-600">{c.code}</td>
                    <td className="px-6 py-4 text-sm">{c.discount_value}{c.discount_type === "percent" ? "%" : "₹"} OFF</td>
                    <td className="px-6 py-4 text-sm text-gray-500">₹{c.min_order}</td>
                    <td className="px-6 py-4 text-sm">{c.used_count}/{c.max_uses}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                        {c.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-6 py-4 flex gap-2">
                      <button onClick={() => toggleCoupon(c.id, c.is_active)} className="text-xs text-gray-500 hover:text-amber-600">{c.is_active ? "Disable" : "Enable"}</button>
                      <button onClick={() => deleteCoupon(c.id)} className="text-xs text-red-400 hover:text-red-600">Delete</button>
                    </td>
                  </tr>
                ))}
                {coupons.length === 0 && <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400">No coupons yet. Create one!</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

