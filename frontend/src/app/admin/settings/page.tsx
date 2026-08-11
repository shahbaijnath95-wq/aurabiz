"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { API_BASE } from "@/lib/api";

export default function SettingsPage() {
  const [tab, setTab] = useState<"invoice" | "ai" | "payments" | "profile" | "hours">("invoice");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { businessId } = useAuth();
  const { toast } = useToast();

  // Invoice settings
  const [invoice, setInvoice] = useState({
    business_name: "", gst_number: "", address: "", phone: "", email: "",
    bank_name: "", account_number: "", ifsc_code: "", upi_id: "", terms: "",
  });

  // AI settings
  const [ai, setAi] = useState({
    provider: "openrouter", api_key: "", model: "", temperature: 0.7,
    max_tokens: 500, system_prompt: "", voice_orders_enabled: false,
  });

  // Payment settings
  const [payments, setPayments] = useState({
    razorpay_key: "", razorpay_secret: "", phonepe_merchant_id: "",
    phonepe_secret_key: "", default_upi_id: "", auto_collect: false,
  });

  // Profile settings
  const [profile, setProfile] = useState({
    name: "", type: "", phone_number: "", address: "", email: "", website: "", logo_url: "",
  });

  // Business hours settings
  const [hours, setHours] = useState({
    enabled: true, open_hour: 10, close_hour: 20,
    days: [1, 2, 3, 4, 5, 6], timezone: "Asia/Kolkata", closed_message: "",
  });

  useEffect(() => { loadSettings(); }, []);

  const loadSettings = async () => {
    try {
      const { settings } = await import("@/lib/api");
      const data = await settings.get() as Record<string, unknown>;
      if (data.invoice) setInvoice(data.invoice as typeof invoice);
      if (data.ai) setAi(data.ai as typeof ai);
      if (data.payments) setPayments(data.payments as typeof payments);
      if (data.profile) setProfile(data.profile as typeof profile);
      if (data.business_hours) setHours(data.business_hours as typeof hours);
    } catch {} finally { setLoading(false); }
  };

  const saveSection = async (section: string, data: unknown) => {
    setSaving(true);
    try {
      const { settings } = await import("@/lib/api");
      await settings.update(section, data);
      toast(`${section} settings save ho gayi!`, "success");
    } catch (e: unknown) {
      toast(e instanceof Error ? e.message : "Save nahi ho paya", "error");
    }
    setSaving(false);
  };

  const inputClass = "w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:border-amber-400 focus:ring-2 focus:ring-amber-100 outline-none transition-all";
  const labelClass = "block text-sm font-medium text-gray-700 mb-1";

  const tabs = [
    { id: "hours", label: "Business Hours", icon: "🕐" },
    { id: "invoice", label: "Invoice", icon: "📄" },
    { id: "ai", label: "AI API", icon: "🤖" },
    { id: "payments", label: "Payments", icon: "💳" },
    { id: "profile", label: "Business Profile", icon: "🏪" },
  ];

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-6">
          <a href="/admin" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Admin Panel</a>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500">Invoice, AI, Payments, Business profile manage karo</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white rounded-xl border border-gray-100 p-1 mb-6 w-fit">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t.id ? "bg-amber-500 text-white" : "text-gray-500 hover:bg-gray-50"}`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-20 text-gray-400">Loading...</div>
        ) : (
          <motion.div key={tab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-8 border border-gray-100 shadow-card">

            {/* ── BUSINESS HOURS SETTINGS ── */}
            {tab === "hours" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">Business Hours</h3>
                    <p className="text-sm text-gray-500">Shop kab khula hai aur kab band hota hai</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={hours.enabled}
                      onChange={e => setHours({ ...hours, enabled: e.target.checked })}
                      className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-amber-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
                    <span className="ml-2 text-sm font-medium text-gray-700">{hours.enabled ? "ON" : "OFF"}</span>
                  </label>
                </div>

                {/* Time Zone */}
                <div>
                  <label className={labelClass}>Time Zone</label>
                  <select value={hours.timezone} onChange={e => setHours({ ...hours, timezone: e.target.value })} className={inputClass}>
                    <option value="Asia/Kolkata">🇮🇳 India (IST, UTC+5:30)</option>
                    <option value="Asia/Dubai">🇦🇪 Dubai (GST, UTC+4)</option>
                    <option value="Asia/Singapore">🇸🇬 Singapore (SGT, UTC+8)</option>
                    <option value="America/New_York">🇺🇸 New York (EST, UTC-5)</option>
                    <option value="America/Los_Angeles">🇺🇸 Los Angeles (PST, UTC-8)</option>
                    <option value="Europe/London">🇬🇧 London (GMT, UTC+0)</option>
                    <option value="Asia/Kathmandu">🇳🇵 Nepal (NPT, UTC+5:45)</option>
                    <option value="Asia/Dhaka">🇧🇩 Bangladesh (BST, UTC+6)</option>
                  </select>
                </div>

                {/* Open / Close Time */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Shop Khulta Hai (Open)</label>
                    <select value={hours.open_hour} onChange={e => setHours({ ...hours, open_hour: Number(e.target.value) })} className={inputClass}>
                      {Array.from({ length: 24 }, (_, i) => (
                        <option key={i} value={i}>
                          {String(i).padStart(2, "0")}:00 — {i < 12 ? "AM" : i === 12 ? "PM" : "PM"} ({i === 0 ? "12 AM" : i < 12 ? `${i} AM` : i === 12 ? "12 PM" : `${i - 12} PM`})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Shop Banda Hai (Close)</label>
                    <select value={hours.close_hour} onChange={e => setHours({ ...hours, close_hour: Number(e.target.value) })} className={inputClass}>
                      {Array.from({ length: 25 }, (_, i) => (
                        <option key={i} value={i}>
                          {String(i).padStart(2, "0")}:00 — {i === 0 ? "12 AM" : i < 12 ? `${i} AM` : i === 12 ? "12 PM" : i === 24 ? "Midnight" : `${i - 12} PM`}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Visual Time Preview */}
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                  <p className="text-sm font-medium text-amber-800 mb-2">
                    ⏰ Shop: {String(hours.open_hour).padStart(2, "0")}:00 se {String(hours.close_hour).padStart(2, "0")}:00 tak
                    {hours.enabled ? " — OPEN" : " — CLOSED (disabled)"}
                  </p>
                  <div className="flex gap-1 mt-2">
                    {Array.from({ length: 24 }, (_, i) => (
                      <div key={i} className={`h-4 flex-1 rounded-sm ${i >= hours.open_hour && i < hours.close_hour && hours.enabled ? "bg-green-400" : "bg-gray-200"}`}
                        title={`${String(i).padStart(2, "0")}:00`} />
                    ))}
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-gray-400">
                    <span>00</span><span>06</span><span>12</span><span>18</span><span>24</span>
                  </div>
                </div>

                {/* Days */}
                <div>
                  <label className={labelClass}>Kaunse Din Open Hai</label>
                  <div className="flex gap-2 mt-1">
                    {[{ v: 0, l: "Sun", hi: "Ravi" }, { v: 1, l: "Mon", hi: "Som" }, { v: 2, l: "Tue", hi: "Mangal" },
                      { v: 3, l: "Wed", hi: "Budh" }, { v: 4, l: "Thu", hi: "Guru" }, { v: 5, l: "Fri", hi: "Shukra" },
                      { v: 6, l: "Sat", hi: "Shani" }].map(d => (
                      <button key={d.v} onClick={() => {
                        const newDays = hours.days.includes(d.v) ? hours.days.filter(x => x !== d.v) : [...hours.days, d.v].sort();
                        setHours({ ...hours, days: newDays });
                      }}
                        className={`px-3 py-2 rounded-xl text-sm font-medium border-2 transition-all ${hours.days.includes(d.v) ? "border-amber-400 bg-amber-50 text-amber-700" : "border-gray-200 text-gray-400 hover:border-gray-300"}`}>
                        <span className="block">{d.l}</span>
                        <span className="block text-xs">{d.hi}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Closed Message */}
                <div>
                  <label className={labelClass}>Band hone pe kya bole? (Auto-reply)</label>
                  <textarea value={hours.closed_message} onChange={e => setHours({ ...hours, closed_message: e.target.value })}
                    className={inputClass + " h-20 resize-none"}
                    placeholder="Hum abhi closed hain. Hamare working hours: Mon-Sat 10 AM - 8 PM. Kal subah milte hain!" />
                  <p className="text-xs text-gray-400 mt-1">Agar khali rakhe toh default message jayega</p>
                </div>

                {/* Current Status */}
                <div className={`p-4 rounded-xl border-2 ${hours.enabled ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}>
                  <p className={`text-sm font-medium ${hours.enabled ? "text-green-700" : "text-red-700"}`}>
                    {hours.enabled ? `🟢 Shop OPEN — ${String(hours.open_hour).padStart(2, "0")}:00 to ${String(hours.close_hour).padStart(2, "0")}:00` : "🔴 Shop CLOSED — Bot 'band' message bhejega"}
                  </p>
                </div>

                <button onClick={() => saveSection("business-hours", hours)} disabled={saving}
                  className="px-6 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors">
                  {saving ? "Saving..." : "Business Hours Save Karo"}
                </button>
              </div>
            )}

            {/* ── INVOICE SETTINGS ── */}
            {tab === "invoice" && (
              <div className="space-y-6">
                <h3 className="font-semibold text-gray-900 text-lg">Invoice Settings</h3>
                <p className="text-sm text-gray-500">Invoices pe ye details dikhengi</p>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Business Name</label>
                    <input type="text" value={invoice.business_name} onChange={e => setInvoice({ ...invoice, business_name: e.target.value })}
                      className={inputClass} placeholder="Priya Beauty Salon" />
                  </div>
                  <div>
                    <label className={labelClass}>GST Number</label>
                    <input type="text" value={invoice.gst_number} onChange={e => setInvoice({ ...invoice, gst_number: e.target.value })}
                      className={inputClass} placeholder="22AAAAA0000A1Z5" />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>Business Address</label>
                  <textarea value={invoice.address} onChange={e => setInvoice({ ...invoice, address: e.target.value })}
                    className={inputClass + " h-16 resize-none"} placeholder="Shop 123, MG Road, Mumbai 400001" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Phone</label>
                    <input type="text" value={invoice.phone} onChange={e => setInvoice({ ...invoice, phone: e.target.value })}
                      className={inputClass} placeholder="+91 98765 43210" />
                  </div>
                  <div>
                    <label className={labelClass}>Email</label>
                    <input type="email" value={invoice.email} onChange={e => setInvoice({ ...invoice, email: e.target.value })}
                      className={inputClass} placeholder="business@email.com" />
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-6">
                  <h4 className="font-medium text-gray-900 mb-4">Bank / UPI Details</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className={labelClass}>Bank Name</label>
                      <input type="text" value={invoice.bank_name} onChange={e => setInvoice({ ...invoice, bank_name: e.target.value })}
                        className={inputClass} placeholder="HDFC Bank" />
                    </div>
                    <div>
                      <label className={labelClass}>Account Number</label>
                      <input type="text" value={invoice.account_number} onChange={e => setInvoice({ ...invoice, account_number: e.target.value })}
                        className={inputClass} placeholder="1234567890" />
                    </div>
                    <div>
                      <label className={labelClass}>IFSC Code</label>
                      <input type="text" value={invoice.ifsc_code} onChange={e => setInvoice({ ...invoice, ifsc_code: e.target.value })}
                        className={inputClass} placeholder="HDFC0001234" />
                    </div>
                    <div>
                      <label className={labelClass}>UPI ID</label>
                      <input type="text" value={invoice.upi_id} onChange={e => setInvoice({ ...invoice, upi_id: e.target.value })}
                        className={inputClass} placeholder="business@upi" />
                    </div>
                  </div>
                </div>

                <div>
                  <label className={labelClass}>Invoice Notes / Terms</label>
                  <textarea value={invoice.terms} onChange={e => setInvoice({ ...invoice, terms: e.target.value })}
                    className={inputClass + " h-16 resize-none"} placeholder="Payment due within 7 days..." />
                </div>

                <button onClick={() => saveSection("invoice", invoice)} disabled={saving}
                  className="px-6 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors">
                  {saving ? "Saving..." : "Invoice Settings Save Karo"}
                </button>
              </div>
            )}

            {/* ── AI API SETTINGS ── */}
            {tab === "ai" && (
              <div className="space-y-6">
                <h3 className="font-semibold text-gray-900 text-lg">AI API Settings</h3>
                <p className="text-sm text-gray-500">AI model aur API key configure karo</p>

                <div>
                  <label className={labelClass}>AI Provider</label>
                  <div className="flex gap-3">
                    {[{ v: "openrouter", l: "OpenRouter (FREE)", d: "Free models available" }, { v: "cloudflare", l: "Cloudflare AI (FREE)", d: "10K neurons/day free" }, { v: "openai", l: "OpenAI", d: "GPT-4o, GPT-4" }, { v: "gemini", l: "Google Gemini", d: "Gemini Pro" }].map(p => (
                      <button key={p.v} onClick={() => setAi({ ...ai, provider: p.v })}
                        className={`flex-1 p-3 rounded-xl border-2 text-left transition-all ${ai.provider === p.v ? "border-amber-400 bg-amber-50" : "border-gray-200 hover:border-gray-300"}`}>
                        <p className="font-medium text-sm">{p.l}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{p.d}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className={labelClass}>API Key</label>
                  <input type="password" value={ai.api_key} onChange={e => setAi({ ...ai, api_key: e.target.value })}
                    className={inputClass} placeholder={ai.provider === "cloudflare" ? "account_id:api_token" : "sk-..."} />
                  <p className="text-xs text-gray-400 mt-1">
                    {ai.provider === "openrouter" ? "openrouter.ai se free key lo" : ai.provider === "cloudflare" ? "Workers AI dashboard se API token lo (account:token format)" : ai.provider === "openai" ? "platform.openai.com se key lo" : "aistudio.google.com se key lo"}
                  </p>
                </div>

                <div>
                  <label className={labelClass}>Model</label>
                  <input type="text" value={ai.model} onChange={e => setAi({ ...ai, model: e.target.value })}
                    className={inputClass} placeholder={ai.provider === "openrouter" ? "miimo-v2.5-free" : ai.provider === "cloudflare" ? "@cf/meta/llama-4-scout-17b-16e-instruct" : ai.provider === "openai" ? "gpt-4o" : "gemini-pro"} />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Temperature (0-1)</label>
                    <input type="number" min="0" max="1" step="0.1" value={ai.temperature}
                      onChange={e => setAi({ ...ai, temperature: Number(e.target.value) })} className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Max Tokens</label>
                    <input type="number" min="100" max="4000" value={ai.max_tokens}
                      onChange={e => setAi({ ...ai, max_tokens: Number(e.target.value) })} className={inputClass} />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>System Prompt (Custom AI Instructions)</label>
                  <textarea value={ai.system_prompt} onChange={e => setAi({ ...ai, system_prompt: e.target.value })}
                    className={inputClass + " h-24 resize-none"} placeholder="Tum ek helpful business assistant ho. Hindi mein jawab do..." />
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div>
                    <h4 className="font-medium text-gray-900">Enable WhatsApp Voice Orders</h4>
                    <p className="text-sm text-gray-500">Allow customers to send voice notes for placing orders (Powered by Whisper AI).</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={ai.voice_orders_enabled || false}
                      onChange={e => setAi({ ...ai, voice_orders_enabled: e.target.checked })}
                      className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-amber-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
                  </label>
                </div>

                <button onClick={() => saveSection("ai", ai)} disabled={saving}
                  className="px-6 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors">
                  {saving ? "Saving..." : "AI Settings Save Karo"}
                </button>
              </div>
            )}

            {/* ── PAYMENT SETTINGS ── */}
            {tab === "payments" && (
              <div className="space-y-6">
                <h3 className="font-semibold text-gray-900 text-lg">Payment Gateway Settings</h3>
                <p className="text-sm text-gray-500">Razorpay, PhonePe, UPI configure karo</p>

                {/* Razorpay */}
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="font-medium text-gray-900 mb-3">Razorpay</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className={labelClass}>API Key</label>
                      <input type="password" value={payments.razorpay_key} onChange={e => setPayments({ ...payments, razorpay_key: e.target.value })}
                        className={inputClass} placeholder="rzp_test_..." />
                    </div>
                    <div>
                      <label className={labelClass}>API Secret</label>
                      <input type="password" value={payments.razorpay_secret} onChange={e => setPayments({ ...payments, razorpay_secret: e.target.value })}
                        className={inputClass} placeholder="..." />
                    </div>
                  </div>
                </div>

                {/* PhonePe */}
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="font-medium text-gray-900 mb-3">PhonePe</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className={labelClass}>Merchant ID</label>
                      <input type="text" value={payments.phonepe_merchant_id} onChange={e => setPayments({ ...payments, phonepe_merchant_id: e.target.value })}
                        className={inputClass} placeholder="M1234567890" />
                    </div>
                    <div>
                      <label className={labelClass}>Secret Key</label>
                      <input type="password" value={payments.phonepe_secret_key} onChange={e => setPayments({ ...payments, phonepe_secret_key: e.target.value })}
                        className={inputClass} placeholder="..." />
                    </div>
                  </div>
                </div>

                {/* UPI */}
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="font-medium text-gray-900 mb-3">UPI (Direct)</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className={labelClass}>UPI ID</label>
                      <input type="text" value={payments.default_upi_id} onChange={e => setPayments({ ...payments, default_upi_id: e.target.value })}
                        className={inputClass} placeholder="business@upi" />
                    </div>
                    <div className="flex items-end">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={payments.auto_collect} onChange={e => setPayments({ ...payments, auto_collect: e.target.checked })}
                          className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-400" />
                        <span className="text-sm text-gray-700">Auto-collect payments</span>
                      </label>
                    </div>
                  </div>
                </div>

                <button onClick={() => saveSection("payments", payments)} disabled={saving}
                  className="px-6 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors">
                  {saving ? "Saving..." : "Payment Settings Save Karo"}
                </button>
              </div>
            )}

            {/* ── BUSINESS PROFILE ── */}
            {tab === "profile" && (
              <div className="space-y-6">
                <h3 className="font-semibold text-gray-900 text-lg">Business Profile</h3>
                <p className="text-sm text-gray-500">Apne business ki details bharo</p>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Business Name *</label>
                    <input type="text" value={profile.name} onChange={e => setProfile({ ...profile, name: e.target.value })}
                      className={inputClass} placeholder="Priya Beauty Salon" />
                  </div>
                  <div>
                    <label className={labelClass}>Business Type</label>
                    <select value={profile.type} onChange={e => setProfile({ ...profile, type: e.target.value })} className={inputClass}>
                      <option value="">Select karo</option>
                      <option value="salon">Salon / Beauty</option>
                      <option value="restaurant">Restaurant / Food</option>
                      <option value="retail">Retail / Shop</option>
                      <option value="electronics">Electronics Repair</option>
                      <option value="grocery">Grocery / Kirana</option>
                      <option value="clothing">Clothing / Fashion</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Phone Number</label>
                    <input type="text" value={profile.phone_number} onChange={e => setProfile({ ...profile, phone_number: e.target.value })}
                      className={inputClass} placeholder="+91 98765 43210" />
                  </div>
                  <div>
                    <label className={labelClass}>Email</label>
                    <input type="email" value={profile.email} onChange={e => setProfile({ ...profile, email: e.target.value })}
                      className={inputClass} placeholder="business@email.com" />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>Address</label>
                  <textarea value={profile.address} onChange={e => setProfile({ ...profile, address: e.target.value })}
                    className={inputClass + " h-16 resize-none"} placeholder="Shop 123, MG Road, Mumbai 400001" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Website</label>
                    <input type="url" value={profile.website} onChange={e => setProfile({ ...profile, website: e.target.value })}
                      className={inputClass} placeholder="https://mybusiness.com" />
                  </div>
                  <div>
                    <label className={labelClass}>Logo URL</label>
                    <input type="url" value={profile.logo_url} onChange={e => setProfile({ ...profile, logo_url: e.target.value })}
                      className={inputClass} placeholder="https://example.com/logo.png" />
                  </div>
                </div>

                <button onClick={() => saveSection("profile", profile)} disabled={saving}
                  className="px-6 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-medium hover:bg-amber-600 disabled:opacity-50 transition-colors">
                  {saving ? "Saving..." : "Profile Save Karo"}
                </button>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div></div>
  );
}
