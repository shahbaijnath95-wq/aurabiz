"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function WhatsAppConnectPage() {
  const [status, setStatus] = useState<{connected: boolean; phone?: string; qr?: string; user?: {name?: string; phone?: string}; status?: string} | null>(null);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/bot/qr`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await res.json();
      setStatus(data);
    } catch {
      setStatus({ connected: false, status: "offline" });
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => { clearInterval(interval); };
  }, []);

  const handleLogout = async () => {
    if (!confirm("Bot disconnect karna hai? Phir se scan karna padega.")) return;
    try {
      const token = localStorage.getItem("token");
      await fetch(`${API_BASE}/bot/logout`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      setStatus({ connected: false, status: "disconnected" });
    } catch {}
  };

  const isConnected = status?.status === "connected" || status?.connected;
  const isConnecting = status?.status === "connecting";

  return (
    <div className="flex min-h-screen bg-surface-100">
      <Sidebar />
      <div className="flex-1 overflow-y-auto">
        <main className="layout-container">
          <div className="page-header">
            <a href="/admin" className="text-sm text-gold-600 hover:text-gold-700 flex items-center gap-1 mb-2 transition-colors">← Admin Panel</a>
            <h1 className="page-title">WhatsApp Bot</h1>
            <p className="page-subtitle">QR code scan karke bot connect karo</p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main QR/Status Card */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="lg:col-span-2 card card-hover-shadow"
            >
              <div className="p-8">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-surface-800">Bot Connection Status</h3>
                  <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
                    isConnected
                      ? "bg-success-50 text-success-700"
                      : isConnecting
                      ? "bg-warning-50 text-warning-700"
                      : "bg-surface-200 text-surface-600"
                  }`}>
                    <span className={`w-2 h-2 rounded-full ${
                      isConnected ? "status-online" : isConnecting ? "status-warning" : "status-offline"
                    }`} />
                    {isConnected ? "Connected" : isConnecting ? "Connecting..." : "Disconnected"}
                  </div>
                </div>

                <div className="flex flex-col items-center justify-center py-8">
                  <AnimatePresence mode="wait">
                    {loading ? (
                      <motion.div
                        key="loading"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center gap-4"
                      >
                        <div className="w-16 h-16 border-4 border-surface-200 border-t-gold-500 rounded-full animate-spin" />
                        <p className="text-surface-500">Checking connection...</p>
                      </motion.div>
                    ) : isConnected ? (
                      <motion.div
                        key="connected"
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center gap-4"
                      >
                        <div className="w-24 h-24 bg-success-100 rounded-full flex items-center justify-center">
                          <span className="text-4xl">✅</span>
                        </div>
                        <div className="text-center">
                          <p className="text-xl font-semibold text-surface-800">Bot Connected!</p>
                          {status?.user?.name && (
                            <p className="text-surface-500 mt-1">📱 {status.user.name}</p>
                          )}
                          {status?.user?.phone && (
                            <p className="text-surface-500">📞 {status.user.phone}</p>
                          )}
                        </div>
                      </motion.div>
                    ) : status?.qr ? (
                      <motion.div
                        key="qr"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center gap-4"
                      >
                        <div className="w-56 h-56 bg-white rounded-2xl border-2 border-surface-200 flex items-center justify-center overflow-hidden shadow-lg">
                          <img
                            src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(status.qr)}`}
                            alt="WhatsApp QR Code"
                            className="w-full h-full object-contain"
                          />
                        </div>
                        <p className="text-center text-surface-500 max-w-xs">
                          Scan QR code with your phone. Go to WhatsApp → Linked Devices → Scan QR.
                        </p>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="waiting"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col items-center gap-4"
                      >
                        <div className="w-16 h-16 border-4 border-surface-200 border-t-gold-500 rounded-full animate-spin" />
                        <p className="text-surface-500">QR generate ho raha hai...</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {isConnected && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="border-t border-surface-200 pt-6 mt-6"
                  >
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-red-600 hover:bg-error-50 rounded-xl transition-colors font-medium"
                    >
                      <span>⏻</span>
                      Disconnect Bot
                    </button>
                  </motion.div>
                )}
              </div>
            </motion.div>

            {/* How it works */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="space-y-6"
            >
              <div className="card p-6">
                <h3 className="font-semibold text-lg text-surface-800 mb-4">Kaise Kaam Karta Hai</h3>
                <div className="space-y-4">
                  {[
                    {
                      step: "1",
                      title: "QR Scan",
                      desc: "Phone se WhatsApp → Linked Devices → QR scan karo",
                      color: "bg-info-100 text-info-600",
                    },
                    {
                      step: "2",
                      title: "Auto Connect",
                      desc: "Bot connect ho jayega — 24/7 active",
                      color: "bg-warning-100 text-warning-600",
                    },
                    {
                      step: "3",
                      title: "AI Replies",
                      desc: "Customer ka message aayega — AI automatically reply karega",
                      color: "bg-success-100 text-success-600",
                    },
                  ].map((s) => (
                    <motion.div
                      key={s.step}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * parseInt(s.step) }}
                      className="flex gap-3"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${s.color} shrink-0`}>
                        {s.step}
                      </div>
                      <div>
                        <p className="font-medium text-surface-800 text-sm">{s.title}</p>
                        <p className="text-surface-500 text-xs">{s.desc}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              <div className="card p-6">
                <h3 className="font-semibold text-lg text-surface-800 mb-4">Bot Features</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">🤖</span>
                    <div>
                      <p className="font-medium text-surface-800 text-sm">AI Chatbot</p>
                      <p className="text-surface-500 text-xs">Hindi/Hinglish mein automatic replies</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-lg">💰</span>
                    <div>
                      <p className="font-medium text-surface-800 text-sm">Order Management</p>
                      <p className="text-surface-500 text-xs">Orders aur payments track karo</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-lg">📊</span>
                    <div>
                      <p className="font-medium text-surface-800 text-sm">Analytics</p>
                      <p className="text-surface-500 text-xs">Sales aur customer insights</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </main>
      </div>
    </div>
  );
}
