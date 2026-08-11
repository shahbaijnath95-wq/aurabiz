"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { auth } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import {
  User, Lock, Store, Phone, Check, ArrowRight, ArrowLeft,
  Sparkles, Eye, EyeOff, PartyPopper
} from "lucide-react";

const steps = [
  { title: "Aapka Naam", subtitle: "Pehle apna account banao", icon: User },
  { title: "Password", subtitle: "Secure rakhna zaroori hai", icon: Lock },
  { title: "Business Info", subtitle: "Apni dukan ke baare mein", icon: Store },
  { title: "WhatsApp Number", subtitle: "Customers se connect karne ke liye", icon: Phone },
  { title: "Tayyar!", subtitle: "Aapka AI assistant ready hai", icon: PartyPopper },
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

export default function SetupPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    businessName: "",
    businessType: "",
    phone: "",
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const { toast } = useToast();
  const router = useRouter();

  const canProceed = () => {
    switch (step) {
      case 0: return form.full_name.trim().length >= 2 && form.email.trim().includes("@");
      case 1: return form.password.length >= 6 && form.password === form.confirmPassword;
      case 2: return form.businessName.trim().length >= 2 && form.businessType.length > 0;
      case 3: return form.phone.trim().length >= 10;
      default: return true;
    }
  };

  const passwordStrength = () => {
    if (form.password.length === 0) return { pct: 0, color: "", label: "" };
    if (form.password.length < 6) return { pct: 25, color: "bg-red-500", label: "Weak" };
    if (form.password.length < 8) return { pct: 50, color: "bg-yellow-500", label: "Medium" };
    if (form.password.length < 12) return { pct: 75, color: "bg-blue-500", label: "Strong" };
    return { pct: 100, color: "bg-green-500", label: "Very Strong" };
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      await auth.register({ full_name: form.full_name, email: form.email, password: form.password });
      await auth.createBusiness({ name: form.businessName, type: form.businessType, phone_number: form.phone });
      toast("Sab ho gaya! Welcome to AuraBiz!", "success");
      router.push("/dashboard");
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Setup fail ho gaya", "error");
    }
    setLoading(false);
  };

  const strength = passwordStrength();

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-white flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-amber-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-orange-200/20 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4" />

      <div className="relative w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-10">
          <Link href="/" className="inline-flex items-center gap-2 group mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/25">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="font-extrabold text-xl tracking-tight">Aura<span className="text-amber-500">Biz</span></span>
          </Link>
          <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-2">Apna Business Setup Karo</h1>
          <p className="text-gray-500">Sirf 2 minute mein apna AI assistant ready karo</p>
        </div>

        {/* Step Indicators */}
        <div className="flex items-center justify-between mb-8">
          {steps.map((s, i) => {
            const StepIcon = s.icon;
            return (
              <div key={i} className="flex items-center flex-1 last:flex-none">
                <div className={`relative flex items-center justify-center w-10 h-10 rounded-full transition-all duration-500 ${
                  i < step ? "bg-green-500 text-white" : i === step ? "bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/30 scale-110" : "bg-white border-2 border-gray-200 text-gray-400"
                }`}>
                  {i < step ? <Check className="w-5 h-5" /> : <StepIcon className="w-4 h-4" />}
                  {i === step && <span className="absolute inset-0 rounded-full border-2 border-amber-400 animate-ping opacity-30" />}
                </div>
                {i < steps.length - 1 && (
                  <div className="flex-1 h-1 mx-2 rounded-full overflow-hidden bg-gray-200">
                    <div className={`h-full rounded-full transition-all duration-500 ${i < step ? "w-full bg-green-500" : "w-0 bg-amber-500"}`} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Card */}
        <AnimatePresence mode="wait">
          <motion.div key={step} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.3 }}
            className="bg-white rounded-3xl p-8 shadow-xl border border-gray-100">

            {/* Step Header */}
            <div className="mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-1">{steps[step].title}</h2>
              <p className="text-sm text-gray-500">{steps[step].subtitle}</p>
            </div>

            {/* Step 0: Name + Email */}
            {step === 0 && (
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Aapka Naam</label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                      placeholder="Jaise: Rahul Sharma" autoFocus
                      className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none transition-all" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">@</span>
                    <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email"
                      placeholder="rahul@example.com"
                      className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none transition-all" />
                  </div>
                </div>
              </div>
            )}

            {/* Step 1: Password */}
            {step === 1 && (
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                      type={showPassword ? "text" : "password"} placeholder="Kam se kam 6 characters" autoFocus
                      className="w-full pl-11 pr-12 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none transition-all" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {/* Password Strength */}
                  {form.password.length > 0 && (
                    <div className="mt-2">
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <motion.div initial={{ width: 0 }} animate={{ width: `${strength.pct}%` }} className={`h-full rounded-full ${strength.color}`} />
                      </div>
                      <p className={`text-xs mt-1 font-medium ${strength.pct <= 25 ? "text-red-500" : strength.pct <= 50 ? "text-yellow-600" : strength.pct <= 75 ? "text-blue-500" : "text-green-500"}`}>{strength.label}</p>
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Password Confirm Karo</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.confirmPassword} onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                      type={showConfirm ? "text" : "password"} placeholder="Wahi password dubara daalo"
                      className="w-full pl-11 pr-12 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none transition-all" />
                    <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {form.confirmPassword.length > 0 && form.password !== form.confirmPassword && (
                    <p className="text-xs text-red-500 mt-1">Password match nahi kar raha</p>
                  )}
                </div>
              </div>
            )}

            {/* Step 2: Business Info */}
            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Business Ka Naam</label>
                  <div className="relative">
                    <Store className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.businessName} onChange={(e) => setForm({ ...form, businessName: e.target.value })}
                      placeholder="Jaise: Sharma Kirana Store" autoFocus
                      className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none transition-all" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Business Type</label>
                  <div className="grid grid-cols-2 gap-3">
                    {businessTypes.map((t) => (
                      <button key={t.value} onClick={() => setForm({ ...form, businessType: t.value })}
                        className={`p-3 rounded-xl border-2 text-left transition-all ${
                          form.businessType === t.value
                            ? "border-amber-400 bg-amber-50 ring-2 ring-amber-100"
                            : "border-gray-200 hover:border-gray-300"
                        }`}>
                        <span className="text-xl block mb-1">{t.icon}</span>
                        <span className="text-sm font-medium text-gray-700">{t.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: WhatsApp */}
            {step === 3 && (
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">WhatsApp Business Number</label>
                  <div className="relative">
                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/[^0-9]/g, "").slice(0, 10) })}
                      placeholder="9876543210" type="tel" autoFocus
                      className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-gray-200 text-sm focus:border-amber-400 focus:ring-4 focus:ring-amber-100 outline-none transition-all" />
                  </div>
                  <p className="text-xs text-gray-400 mt-2">10 digit number — country code ke bina</p>
                </div>
                <div className="p-4 rounded-xl bg-green-50 border border-green-100">
                  <p className="text-sm text-green-700 font-medium">✅ WhatsApp ready!</p>
                  <p className="text-xs text-green-600 mt-1">Aapka number setup hone ke baad customers se connect ho jayega</p>
                </div>
              </div>
            )}

            {/* Step 4: Done */}
            {step === 4 && (
              <div className="text-center py-6">
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200 }}
                  className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center mb-6 shadow-lg shadow-green-500/30">
                  <PartyPopper className="w-10 h-10 text-white" />
                </motion.div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Shabash! 🎉</h3>
                <p className="text-gray-500 mb-6">Aapka AI assistant tayyar hai</p>

                <div className="bg-gray-50 rounded-2xl p-5 text-left space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                      <User className="w-4 h-4 text-amber-600" />
                    </div>
                    <div><p className="text-xs text-gray-400">Name</p><p className="text-sm font-semibold text-gray-800">{form.full_name}</p></div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                      <Store className="w-4 h-4 text-amber-600" />
                    </div>
                    <div><p className="text-xs text-gray-400">Business</p><p className="text-sm font-semibold text-gray-800">{form.businessName}</p></div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                      <Phone className="w-4 h-4 text-amber-600" />
                    </div>
                    <div><p className="text-xs text-gray-400">WhatsApp</p><p className="text-sm font-semibold text-gray-800">{form.phone}</p></div>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex gap-3 mt-8">
              {step > 0 && step < 4 && (
                <button onClick={() => setStep(step - 1)} className="px-5 py-3 rounded-xl border-2 border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 transition-colors flex items-center gap-2">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
              )}
              {step < 4 ? (
                <button onClick={() => setStep(step + 1)} disabled={!canProceed()}
                  className="flex-1 py-3 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-amber-400 to-orange-500 shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:-translate-y-0.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2">
                  {step === 3 ? "Complete Setup" : "Continue"} <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button onClick={handleFinish} disabled={loading}
                  className="flex-1 py-3 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-green-500 to-emerald-500 shadow-lg shadow-green-500/25 hover:shadow-green-500/40 hover:-translate-y-0.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                  {loading ? "Setting up..." : "Go to Dashboard"} <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Footer */}
        <p className="text-center text-xs text-gray-400 mt-6">Setup karte waqt koi paise nahi lenge — 14 din free trial</p>
      </div>
    </div>
  );
}
