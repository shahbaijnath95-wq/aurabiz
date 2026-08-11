"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { API_BASE } from "@/lib/api";

function PayContent() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order");
  const phone = searchParams.get("phone");

  const [order, setOrder] = useState<{ id: string; amount: number; business_id: string; status: string; customer_name?: string; product_name?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [paid, setPaid] = useState(false);
  const [qrCode, setQrCode] = useState("");

  useEffect(() => {
    if (!orderId && !phone) {
      setError("Order ID ya phone number zaroori hai");
      setLoading(false);
      return;
    }
    loadOrder();
  }, [orderId, phone]);

  const loadOrder = async () => {
    try {
      const id = orderId || phone;
      const res = await fetch(`${API_BASE}/orders/${id}/payment-link`);
      if (res.ok) {
        const data = await res.json();
        setOrder(data);
        if (data.qr_code) setQrCode(data.qr_code);
      } else {
        setError("Order nahi mila. Sahi order ID daalo.");
      }
    } catch {
      setError("Connection error. Baad mein try karo.");
    } finally {
      setLoading(false);
    }
  };

  const generateQR = async () => {
    if (!order) return;
    // Generate QR locally from UPI link (no backend endpoint needed)
    const upiLink = `upi://pay?pa=merchant@upi&pn=Payment&am=${order.amount}&currency=INR&tn=Order%20${order.id}`;
    const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(upiLink)}`;
    setQrCode(qrApiUrl);
  };

  const openUPI = () => {
    if (!order) return;
    const upiLink = `upi://pay?pa=merchant@upi&pn=Payment&am=${order.amount}&currency=INR&tn=Order%20Payment`;
    window.location.href = upiLink;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#faf9f7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#faf9f7] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-sm w-full text-center">
          <p className="text-4xl mb-3">❌</p>
          <p className="text-gray-700 font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#faf9f7] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-sm w-full">
        {paid ? (
          <div className="text-center">
            <p className="text-5xl mb-4">✅</p>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Payment Ho Gayi!</h2>
            <p className="text-gray-500">Shukriya! Aapka order confirm ho gaya hai.</p>
          </div>
        ) : (
          <>
            <div className="text-center mb-6">
              <p className="text-sm text-gray-400 mb-1">Bharo</p>
              <h1 className="text-3xl font-bold text-gray-900">₹{order?.amount || 0}</h1>
              {order?.product_name && (
                <p className="text-sm text-gray-500 mt-1">{order.product_name}</p>
              )}
            </div>

            {qrCode ? (
              <div className="flex justify-center mb-6">
                <div className="bg-white p-3 rounded-xl border border-gray-100">
                  <img src={qrCode} alt="UPI QR" className="w-48 h-48" />
                </div>
              </div>
            ) : (
              <div className="flex justify-center mb-6">
                <button onClick={generateQR}
                  className="px-6 py-3 bg-amber-500 text-white rounded-xl font-medium hover:bg-amber-600 transition-colors">
                  QR Code Generate Karo
                </button>
              </div>
            )}

            <div className="space-y-3">
              <button onClick={openUPI}
                className="w-full py-3 bg-emerald-500 text-white rounded-xl font-semibold hover:bg-emerald-600 transition-colors">
                UPI App Se Pay Karo
              </button>

              <div className="text-center">
                <p className="text-xs text-gray-400 mb-2">Ya scan karo QR code</p>
              </div>

              <button onClick={() => setPaid(true)}
                className="w-full py-3 border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors">
                Payment Ho Gaya
              </button>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-100 text-center">
              <p className="text-xs text-gray-400">Powered by AI WhatsApp Assistant</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function PayPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#faf9f7] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
      </div>
    }>
      <PayContent />
    </Suspense>
  );
}
