"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { admin as adminApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

interface AdminPayment {
  id: string;
  amount: number;
  customer_name: string;
  customer_email: string;
  payment_method: string;
  status: string;
  created_at: string;
  qr_url?: string;
}

export default function AdminPaymentsPage() {
  const [payments, setPayments] = useState<AdminPayment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateQR, setShowGenerateQR] = useState(false);
  const [qrAmount, setQrAmount] = useState("");
  const [qrName, setQrName] = useState("");
  const [qrEmail, setQrEmail] = useState("");
  const [qrPhone, setQrPhone] = useState("");
  const [qrGenerating, setQrGenerating] = useState(false);

  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  const loadPayments = () => {
    if (!businessId) return;
    adminApi.payments(businessId)
      .then((data) => {
        const list = Array.isArray(data) ? data as unknown as AdminPayment[] : (data as unknown as { payments?: AdminPayment[] })?.payments || [];
        setPayments(list);
      })
      .catch(() => toast("Payments load nahi ho paye", "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPayments(); }, [businessId]);

  const generateQRCode = async () => {
    if (!qrAmount || isNaN(Number(qrAmount))) {
      toast("Valid amount daalo", "error");
      return;
    }
    setQrGenerating(true);
    try {
      const data = await adminApi.generateQR(qrAmount, qrName, qrEmail, qrPhone, businessId || undefined);
      setPayments([{ id: data.payment_id, amount: Number(qrAmount), customer_name: qrName || "Walk-in", customer_email: qrEmail, payment_method: "qr", status: "pending", created_at: new Date().toISOString(), qr_url: data.qr_code }, ...payments]);
      toast("QR code ban gaya!", "success");
      setShowGenerateQR(false);
      setQrAmount(""); setQrName(""); setQrEmail(""); setQrPhone("");
    } catch (err: any) {
      toast(err.message || "QR nahi ban paya", "error");
    } finally {
      setQrGenerating(false);
    }
  };

  const updateStatus = async (id: string, status: string) => {
    try {
      await adminApi.updatePaymentStatus(id, status);
      setPayments(payments.map(p => p.id === id ? { ...p, status } : p));
      toast("Status updated!", "success");
    } catch {
      toast("Update nahi ho paya", "error");
    }
  };

  const inputClass = "w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:border-amber-400 focus:ring-2 focus:ring-amber-100 outline-none transition-all";

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/admin" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Admin Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">Payment Management</h1>
            <p className="text-gray-500">Saare payments aur QR code generate karo</p>
          </div>
          <button onClick={() => setShowGenerateQR(true)} className="px-4 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 transition-all shadow-lg">
            + QR Generate Karo
          </button>
        </div>

        {showGenerateQR && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={() => setShowGenerateQR(false)}>
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-gray-900">Naya QR Payment</h2>
                <button onClick={() => setShowGenerateQR(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₹) *</label>
                  <input type="number" placeholder="500" value={qrAmount} onChange={(e) => setQrAmount(e.target.value)} className={inputClass} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Customer Name</label>
                  <input type="text" placeholder="Rahul Sharma" value={qrName} onChange={(e) => setQrName(e.target.value)} className={inputClass} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input type="email" placeholder="rahul@example.com" value={qrEmail} onChange={(e) => setQrEmail(e.target.value)} className={inputClass} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input type="tel" placeholder="9876543210" value={qrPhone} onChange={(e) => setQrPhone(e.target.value)} className={inputClass} />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button onClick={() => setShowGenerateQR(false)} className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">Cancel</button>
                <button onClick={generateQRCode} disabled={qrGenerating} className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-amber-400 to-orange-500 hover:from-amber-500 hover:to-orange-600 disabled:opacity-40 transition-all">
                  {qrGenerating ? "Bana raha hai..." : "QR Generate Karo"}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left p-4 font-medium text-gray-500">Customer</th>
                <th className="text-right p-4 font-medium text-gray-500">Amount</th>
                <th className="text-center p-4 font-medium text-gray-500">Method</th>
                <th className="text-center p-4 font-medium text-gray-500">Status</th>
                <th className="text-center p-4 font-medium text-gray-500">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="text-center py-8 text-gray-400">Loading...</td></tr>
              ) : payments.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-8 text-gray-400">Abhi koi payment nahi hai. QR generate karo!</td></tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id} className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="p-4">
                      <p className="font-medium text-gray-900">{p.customer_name}</p>
                      <p className="text-xs text-gray-400">{p.customer_email}</p>
                    </td>
                    <td className="p-4 text-right text-gray-700 font-medium">₹{p.amount.toLocaleString("en-IN")}</td>
                    <td className="p-4 text-center">
                      <span className="inline-flex items-center gap-1 text-xs font-medium capitalize">
                        {p.payment_method === "qr" ? "📱 QR" : p.payment_method === "razorpay" ? "💳 Razorpay" : "💰 Cash"}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${p.status === "completed" ? "text-emerald-600 bg-emerald-50" : p.status === "pending" ? "text-amber-600 bg-amber-50" : "text-red-600 bg-red-50"}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${p.status === "completed" ? "bg-emerald-500" : p.status === "pending" ? "bg-amber-500" : "bg-red-500"}`}></span>
                        {p.status}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {p.status === "pending" && (
                          <button onClick={() => updateStatus(p.id, "completed")} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500 text-white hover:bg-emerald-600 transition-colors">
                            ✅ Complete
                          </button>
                        )}
                      </div>
                    </td>
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
