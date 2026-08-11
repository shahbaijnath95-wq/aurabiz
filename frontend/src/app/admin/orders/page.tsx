"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { orders as ordersApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";

interface OrderItem {
  id: string;
  product_name: string;
  quantity: number;
  total_price: number;
  status: string;
  customer_name: string;
  customer_phone: string;
  delivery_type: string;
  delivery_address: string;
  discount_amount: number;
  coupon_code: string;
  created_at: string;
}

export default function OrdersPage() {
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) window.location.href = "/login";
  }, [isAuthenticated, authLoading]);

  useEffect(() => {
    if (!businessId) { setLoading(false); return; }
    fetchOrders();
  }, [businessId]);

  const fetchOrders = async () => {
    if (!businessId) { setLoading(false); return; }
    try {
      const data = await ordersApi.list(businessId) as unknown as OrderItem[];
      setOrders(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Orders fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (orderId: string, status: string) => {
    try {
      await ordersApi.update(orderId, { status });
      fetchOrders();
    } catch (e) {
      console.error("Update error:", e);
    }
  };

  const downloadInvoice = async (orderId: string) => {
    try {
      const token = localStorage.getItem("token");
      const url = ordersApi.invoice(orderId);
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error("Invoice nahi ban paya");
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `invoice-${orderId.slice(0, 8)}.pdf`;
      a.click();
      window.URL.revokeObjectURL(blobUrl);
    } catch (e) {
      console.error("Invoice error:", e);
    }
  };

  const filtered = filter === "all" ? orders : orders.filter((o) => o.status === filter);

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    confirmed: "bg-blue-100 text-blue-700",
    preparing: "bg-indigo-100 text-indigo-700",
    shipped: "bg-purple-100 text-purple-700",
    delivered: "bg-green-100 text-green-700",
    cancelled: "bg-red-100 text-red-700",
  };

  return (
    <div className="flex min-h-screen bg-[#faf9f7]">
      <Sidebar />
      <main className="flex-1 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
              <p className="text-sm text-gray-500">Customer orders manage karo</p>
            </div>
            <div className="flex gap-2">
              {["all", "pending", "confirmed", "preparing", "shipped", "delivered", "cancelled"].map((s) => (
                <button key={s} onClick={() => setFilter(s)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filter === s ? "bg-amber-500 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"}`}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="text-center py-20 text-gray-400">Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-4xl mb-3">🛒</p>
              <p className="text-gray-500 font-medium">Koi order nahi mila</p>
              <p className="text-sm text-gray-400 mt-1">WhatsApp se orders yahan dikhenge</p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-100 overflow-x-auto">
              <table className="w-full min-w-[600px]">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Order</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Customer</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Qty</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Total</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Status</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Date</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Action</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((order) => (
                    <tr key={order.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="px-5 py-3">
                        <p className="text-sm font-medium text-gray-900">{order.product_name}</p>
                        <p className="text-xs text-gray-400">{order.id.slice(0, 12)}...</p>
                      </td>
                      <td className="px-5 py-3">
                        <p className="text-sm text-gray-700">{order.customer_name}</p>
                        <p className="text-xs text-gray-400">{order.customer_phone}</p>
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-700">{order.quantity}</td>
                      <td className="px-5 py-3 text-sm font-semibold text-gray-900">₹{order.total_price}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[order.status] || "bg-gray-100 text-gray-600"}`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-xs text-gray-400">{new Date(order.created_at).toLocaleDateString("en-IN")}</td>
                      <td className="px-5 py-3">
                        <select value={order.status} onChange={(e) => updateStatus(order.id, e.target.value)}
                          className="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white">
                          <option value="pending">Pending</option>
                          <option value="confirmed">Confirmed</option>
                          <option value="preparing">Preparing</option>
                          <option value="shipped">Shipped</option>
                          <option value="delivered">Delivered</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </td>
                      <td className="px-5 py-3">
                        <button onClick={() => downloadInvoice(order.id)}
                          className="text-xs text-amber-600 hover:text-amber-700 font-medium flex items-center gap-1"
                          title="Download Invoice PDF">
                          📄 Invoice
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

