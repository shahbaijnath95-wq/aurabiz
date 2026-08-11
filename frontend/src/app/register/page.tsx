"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  User, Lock, Mail, Phone, Store, Check, ArrowRight, ArrowLeft,
  Sparkles, Eye, EyeOff, Shield, Zap, CreditCard
} from "lucide-react";

// ─── Razorpay SDK loader ───
declare global {
  interface Window {
    Razorpay: any;
  }
}
function loadRazorpay(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

const plans = [
  { id: "starter", name: "Starter", price: 999, period: "/mahina", features: ["500 messages", "1 user", "Basic analytics", "Loyalty points"], highlight: false },
  { id: "growth", name: "Growth", price: 2499, period: "/mahina", features: ["2,500 messages", "5 users", "Analytics Pro", "Loyalty + CRM", "Inventory + alerts", "Broadcast"], highlight: true },
  { id: "enterprise", name: "Enterprise", price: 4999, period: "/mahina", features: ["Unlimited messages", "Unlimited users", "Everything included", "Priority support", "API access", "Custom AI"], highlight: false },
];

const businessTypes = [
  { value: "kirana", label: "Kirana Store", icon: "🛒" },
  { value: "salon", label: "Salon / Beauty", icon: "✂️" },
  { value: "restaurant", label: "Restaurant / Cafe", icon: "🍽️" },
  { value: "clothing", label: "Clothing Shop", icon: "👗" },
  { value: "electronics", label: "Electronics", icon: "🔌" },
  { value: "pharmacy", label: "Pharmacy", icon: "💊" },
  { value: "other", label: "Other", icon: "🏪" },
];

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    otp: "",
    plan: "growth",
    businessName: "",
    businessType: "",
    whatsapp: "",
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpOtp, setOtpOtp] = useState("");
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown(c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  const steps = [
    { title: "Account", icon: Mail, desc: "Email aur password banao" },
    { title: "Plan", icon: Zap, desc: "Apna plan choose karo" },
    { title: "Business", icon: Store, desc: "Business details add karo" },
  ];

  const canProceed = () => {
    switch (step) {
      case 0: return form.email.includes("@") && form.password.length >= 6 && form.password === form.confirmPassword && form.full_name.length >= 2;
      case 1: return form.plan.length > 0;
      case 2: return form.businessName.length >= 2 && form.businessType.length > 0 && form.whatsapp.length >= 10;
      default: return true;
    }
  };

  const handleSendOtp = async () => {
    if (!form.email.includes("@")) return;
    setLoading(true);
    try {
      const res = await fetch("/api/v1/auth/send-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email }),
      });
      const data = await res.json();
      if (res.ok) {
        setOtpSent(true);
        setOtpOtp(data.otp || "");
        setCountdown(60);
      } else {
        alert(data.detail || "OTP bhejne me error");
      }
    } catch (e) {
      alert("Network error");
    }
    setLoading(false);
  };

  const handleVerifyOtp = async () => {
    if (form.otp.length !== 6) return;
    setLoading(true);
    try {
      const res = await fetch("/api/v1/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email, otp: form.otp }),
      });
      const data = await res.json();
      if (res.ok) {
        setStep(2);
      } else {
        alert(data.detail || "OTP galat hai");
      }
    } catch (e) {
      alert("Network error");
    }
    setLoading(false);
  };

  const handleRegister = async () => {
    setLoading(true);
    try {
      const MASTER_URL = process.env.NEXT_PUBLIC_MASTER_URL || "https://aurabiz.onrender.com";

      // Step 1: Register user
      const regRes = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: form.full_name,
          email: form.email,
          password: form.password,
          phone: form.phone || null,
        }),
      });
      if (!regRes.ok) {
        const d = await regRes.json();
        throw new Error(d.detail || "Registration failed");
      }

      // Step 2: Create business
      await fetch("/api/v1/auth/business", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: form.businessName, type: form.businessType, phone_number: form.whatsapp }),
      });

      // Step 3: Razorpay checkout for license
      const selectedPlan = plans.find(p => p.id === form.plan);
      const rpReady = await loadRazorpay();
      if (!rpReady) throw new Error("Payment system load nahi hua");

      const orderRes = await fetch(`${MASTER_URL}/api/license/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: form.plan, billing: "monthly", ai_tier: "free" }),
      });
      const order = await orderRes.json();
      if (!orderRes.ok) throw new Error(order.detail || "Order create fail");

      const options = {
        key: order.key || process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
        amount: order.amount,
        currency: "INR",
        name: "AuraBiz",
        description: `${selectedPlan?.name} Plan`,
        order_id: order.razorpay_order_id,
        handler: async (response: any) => {
          try {
            const licRes = await fetch(`${MASTER_URL}/api/license/purchase`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                plan: form.plan, billing: "monthly", ai_tier: "free",
                owner_name: form.full_name, owner_email: form.email, owner_phone: form.phone || null,
                payment_id: response.razorpay_payment_id,
                payment_signature: response.razorpay_signature,
                razorpay_order_id: response.razorpay_order_id,
              }),
            });
            const licData = await licRes.json();
            if (!licRes.ok) throw new Error(licData.detail || "License generate nahi hua");
            alert(`🎉 Welcome to AuraBiz!\n\nLicense Key: ${licData.license_key}\nPlan: ${selectedPlan?.name}\nExpiry: ${licData.expires_at}\n\nAb aap Dashboard pe ja sakte hain!`);
            router.push("/login");
          } catch (err: any) {
            alert(err.message || "Payment verify fail");
            setLoading(false);
          }
        },
        prefill: { name: form.full_name, email: form.email, contact: form.phone },
        theme: { color: "#f59e0b" },
        modal: { ondismiss: () => { setLoading(false); } },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (e: any) {
      alert(e.message || "Registration failed");
      setLoading(false);
    }
  };

  const passwordStrength = () => {
    if (form.password.length === 0) return { pct: 0, label: "", color: "" };
    if (form.password.length < 6) return { pct: 25, label: "Weak", color: "bg-red-500" };
    if (form.password.length < 8) return { pct: 50, label: "Medium", color: "bg-yellow-500" };
    if (form.password.length < 12) return { pct: 75, label: "Strong", color: "bg-blue-500" };
    return { pct: 100, label: "Very Strong", color: "bg-green-500" };
  };

  const strength = passwordStrength();

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-white flex items-center justify-center p-4 md:p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-80 h-80 bg-amber-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-orange-200/20 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4" />

      <div className="relative w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 group mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/25">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="font-extrabold text-xl tracking-tight">Aura<span className="text-amber-500">Biz</span></span>
          </Link>
          <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-2">Account Banao</h1>
          <p className="text-gray-500">Sirf 2 minute mein apna AI assistant ready karo</p>
        </div>

        {/* Progress */}
        <div className="flex items-center justify-between mb-8 bg-white/60 backdrop-blur rounded-2xl p-4 border border-white/40">
          {steps.map((s, i) => {
            const StepIcon = s.icon;
            return (
              <div key={i} className="flex items-center flex-1 last:flex-none">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  i < step ? "bg-green-500 text-white" : i === step ? "bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/30" : "bg-gray-200 text-gray-400"
                }`}>
                  {i < step ? <Check className="w-4 h-4" /> : <StepIcon className="w-4 h-4" />}
                </div>
                {i < steps.length - 1 && <div className={`flex-1 h-0.5 mx-2 rounded-full transition-all ${i < step ? "bg-green-500" : "bg-gray-200"}`} />}
              </div>
            );
          })}
        </div>

        {/* Card */}
        <AnimatePresence mode="wait">
          <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="bg-white rounded-3xl p-8 shadow-xl border border-gray-100">

            {/* Step 0: Account */}
            {step === 0 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{steps[0].title}</h2>
                  <p className="text-sm text-gray-500">{steps[0].desc}</p>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-1 block">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder="Rahul Sharma" className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-1 block">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="rahul@example.com" className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-1 block">Phone (optional)</label>
                  <div className="relative">
                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="+91 98765 43210" className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-1 block">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input type={showPassword ? "text" : "password"} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="Min 6 characters" className="w-full pl-11 pr-12 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {form.password.length > 0 && (
                    <div className="mt-2">
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${strength.color}`} style={{ width: `${strength.pct}%` }} />
                      </div>
                      <p className={`text-xs mt-1 font-medium ${strength.pct <= 25 ? "text-red-500" : strength.pct <= 50 ? "text-yellow-600" : "text-green-500"}`}>{strength.label}</p>
                    </div>
                  )}
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-1 block">Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input type="password" value={form.confirmPassword} onChange={e => setForm({ ...form, confirmPassword: e.target.value })} placeholder="Wahi password dubara" className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none" />
                  </div>
                  {form.confirmPassword.length > 0 && form.password !== form.confirmPassword && (
                    <p className="text-xs text-red-500 mt-1">Password match nahi kar raha</p>
                  )}
                </div>
                <button onClick={() => setStep(2)} disabled={!canProceed()} className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold shadow-lg shadow-amber-500/25 hover:-translate-y-0.5 transition-all disabled:opacity-40 flex items-center justify-center gap-2">
                  Continue <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Step 1: Plan */}
            {step === 1 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{steps[2].title}</h2>
                  <p className="text-sm text-gray-500">{steps[2].desc}</p>
                </div>
                <div className="grid gap-3">
                  {plans.map(p => (
                    <button key={p.id} onClick={() => setForm({ ...form, plan: p.id })} className={`p-4 rounded-xl border-2 text-left transition-all ${
                      form.plan === p.id ? "border-amber-400 bg-amber-50 ring-2 ring-amber-100" : "border-gray-200 hover:border-gray-300"
                    } ${p.highlight ? "ring-1 ring-amber-200" : ""}`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gray-900">{p.name}</span>
                          {p.highlight && <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 text-xs font-bold">POPULAR</span>}
                        </div>
                        <div className="text-right">
                          <span className="text-lg font-extrabold text-gray-900">₹{p.price.toLocaleString()}</span>
                          <span className="text-gray-400 text-xs">{p.period}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {p.features.map((f, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-md bg-gray-100 text-gray-600 text-xs flex items-center gap-1">
                            <Check className="w-3 h-3 text-green-500" /> {f}
                          </span>
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
                <button onClick={() => setStep(3)} className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold shadow-lg shadow-amber-500/25 hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2">
                  Continue <ArrowRight className="w-4 h-4" />
                </button>
                <button onClick={() => setStep(0)} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
              </div>
            )}

            {/* Step 2: Business */}
            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{steps[3].title}</h2>
                  <p className="text-sm text-gray-500">{steps[3].desc}</p>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-1 block">Business Name</label>
                  <div className="relative">
                    <Store className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.businessName} onChange={e => setForm({ ...form, businessName: e.target.value })} placeholder="Sharma Electronics" className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-2 block">Business Type</label>
                  <div className="grid grid-cols-2 gap-2">
                    {businessTypes.map(t => (
                      <button key={t.value} type="button" onClick={() => setForm({ ...form, businessType: t.value })} className={`p-3 rounded-xl border-2 text-left transition-all ${
                        form.businessType === t.value ? "border-amber-400 bg-amber-50" : "border-gray-200 hover:border-gray-300"
                      }`}>
                        <span className="text-lg">{t.icon}</span>
                        <span className="text-xs font-medium text-gray-700 block">{t.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold text-gray-700 mb-1 block">WhatsApp Business Number</label>
                  <div className="relative">
                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.whatsapp} onChange={e => setForm({ ...form, whatsapp: e.target.value.replace(/\D/g, "").slice(0, 10) })} placeholder="9876543210" className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none" />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">10 digit number — country code ke bina</p>
                </div>
                <button onClick={handleRegister} disabled={!canProceed() || loading} className="w-full py-3.5 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 text-white font-bold text-base shadow-lg shadow-green-500/25 hover:-translate-y-0.5 transition-all disabled:opacity-40 flex items-center justify-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  {loading ? "Creating Account..." : "Create Account & Get License →"}
                </button>
                <button onClick={() => setStep(1)} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500 mt-6">
          Pehle se account hai? <Link href="/login" className="text-amber-600 font-semibold hover:text-amber-700">Login karo</Link>
        </p>
      </div>
    </div>
  );
}
