"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { API_BASE } from "@/lib/api";
import type { IntegrationStatus } from "@/lib/types";

interface Integration {
  id: string;
  name: string;
  icon: string;
  desc: string;
  color: string;
  category: string;
  fields: { key: string; label: string; type: string; placeholder: string; required?: boolean }[];
}

const integrations: Integration[] = [
  {
    id: "razorpay", name: "Razorpay", icon: "💳", desc: "UPI, Cards, NetBanking accept karo",
    color: "bg-blue-50 text-blue-600", category: "Payments",
    fields: [
      { key: "key_id", label: "API Key ID", type: "password", placeholder: "rzp_test_...", required: true },
      { key: "key_secret", label: "API Key Secret", type: "password", placeholder: "...", required: true },
    ],
  },
  {
    id: "phonepe", name: "PhonePe", icon: "📱", desc: "PhonePe se payment accept karo",
    color: "bg-violet-50 text-violet-600", category: "Payments",
    fields: [
      { key: "merchant_id", label: "Merchant ID", type: "text", placeholder: "M1234567890", required: true },
      { key: "secret_key", label: "Secret Key", type: "password", placeholder: "...", required: true },
      { key: "salt_key", label: "Salt Key", type: "password", placeholder: "...", required: true },
    ],
  },
  {
    id: "google_business", name: "Google Business", icon: "🗺️", desc: "Reviews aur listings manage karo",
    color: "bg-green-50 text-green-600", category: "Marketing",
    fields: [
      { key: "place_id", label: "Google Place ID", type: "text", placeholder: "ChIJN1t_tDeuEmsRUsoyG83frY4", required: true },
      { key: "api_key", label: "Google API Key", type: "password", placeholder: "AIza...", required: true },
    ],
  },
  {
    id: "instagram", name: "Instagram", icon: "📸", desc: "DMs aur media handle karo",
    color: "bg-pink-50 text-pink-600", category: "Marketing",
    fields: [
      { key: "access_token", label: "Access Token", type: "password", placeholder: "IGQV...", required: true },
      { key: "page_id", label: "Facebook Page ID", type: "text", placeholder: "123456789", required: true },
    ],
  },
  {
    id: "slack", name: "Slack", icon: "💬", desc: "Orders ki notification Slack pe aaye",
    color: "bg-purple-50 text-purple-600", category: "Notifications",
    fields: [
      { key: "webhook_url", label: "Webhook URL", type: "url", placeholder: "https://hooks.slack.com/services/...", required: true },
      { key: "channel", label: "Channel Name", type: "text", placeholder: "#orders", required: false },
    ],
  },
  {
    id: "email_smtp", name: "Email (SMTP)", icon: "📧", desc: "Invoices aur confirmations email pe bhejo",
    color: "bg-amber-50 text-amber-600", category: "Notifications",
    fields: [
      { key: "smtp_host", label: "SMTP Host", type: "text", placeholder: "smtp.gmail.com", required: true },
      { key: "smtp_port", label: "Port", type: "number", placeholder: "587", required: true },
      { key: "smtp_user", label: "Username / Email", type: "text", placeholder: "you@gmail.com", required: true },
      { key: "smtp_pass", label: "Password / App Password", type: "password", placeholder: "...", required: true },
      { key: "from_name", label: "From Name", type: "text", placeholder: "Priya Beauty Salon" },
    ],
  },
  {
    id: "sms_msg91", name: "SMS (MSG91)", icon: "✉️", desc: "Order updates SMS se bhejo",
    color: "bg-cyan-50 text-cyan-600", category: "Notifications",
    fields: [
      { key: "api_key", label: "MSG91 API Key", type: "password", placeholder: "...", required: true },
      { key: "sender_id", label: "Sender ID", type: "text", placeholder: "PRISHA", required: true },
      { key: "template_id", label: "Template ID", type: "text", placeholder: "1234567890" },
    ],
  },
  {
    id: "shiprocket", name: "Shiprocket", icon: "🚚", desc: "Shipping aur delivery manage karo",
    color: "bg-orange-50 text-orange-600", category: "Shipping",
    fields: [
      { key: "email", label: "Shiprocket Email", type: "email", placeholder: "you@email.com", required: true },
      { key: "password", label: "Password", type: "password", placeholder: "...", required: true },
    ],
  },
  {
    id: "tally", name: "Tally ERP", icon: "📊", desc: "Accounting data sync karo",
    color: "bg-emerald-50 text-emerald-600", category: "Accounting",
    fields: [
      { key: "tally_url", label: "Tally Server URL", type: "url", placeholder: "http://localhost:9000", required: true },
      { key: "company_name", label: "Company Name", type: "text", placeholder: "My Business Pvt Ltd" },
    ],
  },
];

export default function IntegrationsPage() {
  const [statuses, setStatuses] = useState<Record<string, IntegrationStatus>>({});
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<Integration | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [connecting, setConnecting] = useState(false);
  const [filter, setFilter] = useState("all");
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) window.location.href = "/login";
  }, [isAuthenticated, authLoading]);

  useEffect(() => {
    if (!businessId) { setLoading(false); return; }
    fetch(`${API_BASE}/integrations/status/${businessId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    })
      .then(r => r.json())
      .then(data => {
        const map: Record<string, IntegrationStatus> = {};
        (data.integrations || []).forEach((i: IntegrationStatus) => { map[i.type] = i; });
        setStatuses(map);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [businessId]);

  const openConnect = (intg: Integration) => {
    setForm({});
    setModal(intg);
  };

  const handleConnect = async () => {
    if (!modal || !businessId) return;
    const required = modal.fields.filter(f => f.required);
    for (const f of required) {
      if (!form[f.key]?.trim()) {
        toast(`${f.label} zaroori hai`, "error");
        return;
      }
    }
    setConnecting(true);
    try {
      const res = await fetch(`${API_BASE}/integrations/connect/${modal.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: JSON.stringify({ business_id: businessId, credentials: form, config: {} }),
      });
      if (res.ok) {
        setStatuses(prev => ({ ...prev, [modal.id]: { type: modal.id, status: "connected" } }));
        toast(`${modal.name} connect ho gaya!`, "success");
        setModal(null);
      } else {
        const err = await res.json().catch(() => ({}));
        toast(err.detail || "Connect nahi ho paya", "error");
      }
    } catch { toast("Connection error", "error"); }
    setConnecting(false);
  };

  const handleDisconnect = async (type: string) => {
    if (!businessId || !confirm("Disconnect karna hai?")) return;
    try {
      await fetch(`${API_BASE}/integrations/disconnect/${type}?business_id=${businessId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      setStatuses(prev => { const n = { ...prev }; delete n[type]; return n; });
      toast("Disconnected!", "success");
    } catch { toast("Disconnect nahi ho paya", "error"); }
  };

  const categories = ["all", ...Array.from(new Set(integrations.map(i => i.category)))];
  const filtered = filter === "all" ? integrations : integrations.filter(i => i.category === filter);

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-6">
          <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="text-gray-500">Apne favorite tools connect karo — payments, notifications, shipping, accounting</p>
        </div>

        {/* Category Filter */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {categories.map(c => (
            <button key={c} onClick={() => setFilter(c)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${filter === c ? "bg-amber-500 text-white" : "bg-white text-gray-500 border border-gray-200 hover:bg-gray-50"}`}>
              {c === "all" ? "Sab" : c}
            </button>
          ))}
        </div>

        {/* Integration Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((intg) => {
            const connected = statuses[intg.id]?.status === "connected";
            return (
              <motion.div key={intg.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl p-5 border border-gray-100 shadow-card hover:shadow-md transition-all">
                <div className="flex items-start gap-4 mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${intg.color}`}>{intg.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900 text-sm">{intg.name}</h3>
                      {connected && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-600 font-medium">Connected</span>}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{intg.desc}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-1 rounded-full">{intg.category}</span>
                  <div className="flex-1" />
                  {connected ? (
                    <button onClick={() => handleDisconnect(intg.id)}
                      className="text-xs text-red-400 hover:text-red-600 font-medium transition-colors">Disconnect</button>
                  ) : (
                    <button onClick={() => openConnect(intg)}
                      className="text-xs bg-amber-500 text-white px-4 py-1.5 rounded-lg font-medium hover:bg-amber-600 transition-colors">
                      Connect
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Connect Modal */}
        <AnimatePresence>
          {modal && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
              onClick={() => setModal(null)}>
              <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
                className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                <div className="flex items-center gap-3 mb-6">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${modal.color}`}>{modal.icon}</div>
                  <div>
                    <h2 className="font-bold text-gray-900">{modal.name} Connect Karo</h2>
                    <p className="text-xs text-gray-400">{modal.desc}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {modal.fields.map(f => (
                    <div key={f.key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {f.label} {f.required && <span className="text-red-400">*</span>}
                      </label>
                      <input type={f.type} placeholder={f.placeholder} value={form[f.key] || ""}
                        onChange={e => setForm({ ...form, [f.key]: e.target.value })}
                        className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:border-amber-400 focus:ring-2 focus:ring-amber-100 outline-none transition-all" />
                    </div>
                  ))}
                </div>

                <div className="flex gap-3 mt-6">
                  <button onClick={() => setModal(null)}
                    className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">
                    Cancel
                  </button>
                  <button onClick={handleConnect} disabled={connecting}
                    className="flex-1 px-4 py-2.5 rounded-xl bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors">
                    {connecting ? "Connecting..." : "Connect Karo"}
                  </button>
                </div>

                {/* Help text */}
                <div className="mt-4 p-3 bg-gray-50 rounded-xl">
                  <p className="text-xs text-gray-400">
                    {modal.id === "razorpay" && "Dashboard.razorpay.com → Settings → API Keys se key lo."}
                    {modal.id === "phonepe" && "PhonePe Business Dashboard se Merchant ID aur keys lo."}
                    {modal.id === "google_business" && "Google Cloud Console se API key banao aur Place ID find karo."}
                    {modal.id === "instagram" && "Facebook Developer Portal se Access Token lo."}
                    {modal.id === "slack" && "Slack Apps → Incoming Webhooks se URL banao."}
                    {modal.id === "email_smtp" && "Gmail ho toh App Password banao (2FA enabled)."}
                    {modal.id === "sms_msg91" && "MSG91.com pe register karo aur API key lo."}
                    {modal.id === "shiprocket" && "Shiprocket pe account banao aur API access lo."}
                    {modal.id === "tally" && "Tally mein ODBC enabled karo aur server URL do."}
                  </p>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div></div>
  );
}
