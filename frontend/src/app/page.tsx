"use client";

import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { useState, useRef, useEffect, useCallback } from "react";
import {
  MessageSquare, BarChart3, Package, CreditCard, Bot, Zap,
  Check, ArrowRight, Star, ChevronDown, ChevronRight,
  Sparkles, Shield, Zap as ZapIcon, Clock, Users, TrendingUp
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

// ─── Data ───
const features = [
  { icon: MessageSquare, title: "Smart AI Replies", desc: "Customers ko Hinglish mein instant jawab — 24/7, bina koi wait. AI jo samajhta hai aapka business.", color: "from-blue-500 to-cyan-400" },
  { icon: BarChart3, title: "Analytics Dashboard", desc: "Sales, customers, revenue — sab ek hi jagah, real-time. Har decision data-driven.", color: "from-amber-500 to-orange-400" },
  { icon: Package, title: "Inventory Tracker", desc: "Stock khatam hone se pehle smart alert. Kabhi out-of-stock nahi — automatic reorder suggestions.", color: "from-emerald-500 to-green-400" },
  { icon: CreditCard, title: "Payments & Billing", desc: "UPI, Razorpay, PhonePe — sab accept karo seedha WhatsApp se. Payment links auto-generate.", color: "from-violet-500 to-purple-400" },
  { icon: Bot, title: "WhatsApp Automation", desc: "Broadcast messages, follow-ups, reminders — sab automated. Aapka business hamesha awake.", color: "from-pink-500 to-rose-400" },
  { icon: Zap, title: "Instant Setup", desc: "QR code scan karo, 2 minute mein ready. Koi coding, koi complex config — bas WhatsApp connect karo.", color: "from-yellow-500 to-amber-400" },
];

const steps = [
  { num: "01", icon: "📲", title: "WhatsApp Connect Karo", desc: "QR code scan karo aur AuraBiz assistant ready. Koi setup headache nahi." },
  { num: "02", icon: "🧠", title: "AI Ko Sikhao", desc: "Products, inventory, FAQ upload karo — AI sab seekh jayega automatically." },
  { num: "03", icon: "🚀", title: "Grow Karo", desc: "Customers chat karte hain, AI orders leta hai, aapka business scale hota hai." },
];

const testimonials = [
  { name: "Priya Sharma", role: "Salon Owner, Pune", quote: "Pehle 50+ messages roz miss hote the. Ab AI 24/7 bookings le leta hai — 2x revenue!", stars: 5, avatar: "PS" },
  { name: "Rahul Verma", role: "Kirana Store, Jaipur", quote: "Inventory alert sabse best hai. Kabhi stock out nahi hota!", stars: 5, avatar: "RV" },
  { name: "Amit Patel", role: "Electronics Repair, Surat", quote: "Follow-ups automatic hain — customers wapas aate hain. Kamaal ka system!", stars: 5, avatar: "AP" },
];

const tiers = [
  { name: "Starter", price: "₹999", period: "/mahina", features: ["500 messages/month", "1 user", "Basic analytics", "Loyalty program", "Email support"], highlight: false },
  { name: "Growth", price: "₹2,499", period: "/mahina", features: ["2,500 messages/month", "5 users", "Advanced analytics", "Loyalty + CRM", "Inventory + alerts", "Priority support", "Broadcast & follow-ups"], highlight: true },
  { name: "Enterprise", price: "₹4,999", period: "/mahina", features: ["Unlimited messages", "Unlimited users", "Everything in Growth", "Priority support", "API access", "Custom AI model", "Dedicated account manager"], highlight: false },
];

const faqs = [
  { q: "Kya WhatsApp number banega?", nahi: "Nahi! Aapka existing business WhatsApp number use hota hai. Koi nahi number lagta." },
  { q: "Kya WhatsApp band ho jayega?", nahi: "Bilkul nahi! AuraBiz official WhatsApp Business API use karta hai — 100% safe hai." },
  { q: "Trial mein kya milega?", nahi: "Starter plan ke sab features 14 din free. Koi credit card zaroori nahi." },
  { q: "Refund policy kya hai?", nahi: "7 din mein full refund — bilkul questions nahi pooche jayenge." },
  { q: "Data kahan store hota hai?", nahi: "Aapka data encrypted cloud pe store hota hai. Kabhi share nahi karte." },
];

const stats = [
  { value: "500+", label: "Active Businesses" },
  { value: "50K+", label: "Messages/Day" },
  { value: "₹2Cr+", label: "Revenue Generated" },
  { value: "4.9★", label: "Customer Rating" },
];

const chatDemo = [
  { from: "customer", text: "Hi! Aapke paas red kurta hai kya? 🛍️" },
  { from: "bot", text: "Haan ji! Red Silk Kurta size M — ₹1,299, stock mein 12 hain. Book karun? 😊" },
  { from: "customer", text: "Haan, 1 order karo. UPI se payment karna hai" },
  { from: "bot", text: "Done! ✅ Order #4821 confirm ho gaya. Payment link bhej raha hoon 👇" },
];

export default function LandingPage() {
  const [billing, setBilling] = useState<"monthly" | "yearly">("monthly");
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [checkout, setCheckout] = useState<null | { plan: string; amount: string }>(null);
  const [form, setForm] = useState({ name: "", email: "", phone: "", aiTier: "free" });
  const [buying, setBuying] = useState(false);
  const [purchaseResult, setPurchaseResult] = useState<null | { license_key: string; plan: string; amount_paid: number; ai_tier: string }>(null);
  const [purchaseError, setPurchaseError] = useState("");
  const [copied, setCopied] = useState(false);

  const heroRef = useRef(null);
  const heroInView = useInView(heroRef, { once: true });

  const visiblePrice = (p: string) =>
    billing === "yearly" ? "₹" + (parseInt(p.replace(/[^\d]/g, "")) * 10).toLocaleString("en-IN") : p;

  const openCheckout = (plan: string, _bill: "monthly" | "yearly", amount: string) => {
    setCheckout({ plan, amount });
    setPurchaseResult(null);
    setPurchaseError("");
    setCopied(false);
  };

  const submitPurchase = async () => {
    if (!form.name || !form.email) { setPurchaseError("Naam aur email required hai"); return; }
    setBuying(true);
    setPurchaseError("");
    try {
      const MASTER_URL = process.env.NEXT_PUBLIC_MASTER_URL || 'http://localhost:8010';

      // Step 1: Load Razorpay SDK
      const rpReady = await loadRazorpay();
      if (!rpReady) throw new Error("Payment system load nahi hua — internet check karo");

      // Step 2: Create Razorpay order on master backend
      const orderRes = await fetch(`${MASTER_URL}/api/license/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: checkout?.plan, billing, ai_tier: form.aiTier }),
      });
      const order = await orderRes.json();
      if (!orderRes.ok) throw new Error(order.detail || "Order create fail ho gaya");

      // Step 3: Open Razorpay checkout modal
      const options = {
        key: order.key || process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
        amount: order.amount,
        currency: "INR",
        name: "AuraBiz",
        description: `${checkout?.plan?.toUpperCase()} Plan — ${billing === 'yearly' ? '12 months' : '1 month'}`,
        order_id: order.razorpay_order_id,
        handler: async (response: any) => {
          // Step 4: Payment success — verify + generate license
          try {
            const verifyRes = await fetch(`${MASTER_URL}/api/license/purchase`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                plan: checkout?.plan, billing, ai_tier: form.aiTier,
                owner_name: form.name, owner_email: form.email, owner_phone: form.phone || null,
                payment_id: response.razorpay_payment_id,
                payment_signature: response.razorpay_signature,
                razorpay_order_id: response.razorpay_order_id,
              }),
            });
            const data = await verifyRes.json();
            if (!verifyRes.ok) throw new Error(data.detail || "Payment verification failed");
            setPurchaseResult(data);
          } catch (err: unknown) {
            setPurchaseError(err instanceof Error ? err.message : "Payment verify fail ho gaya");
          }
        },
        prefill: { name: form.name, email: form.email, contact: form.phone },
        theme: { color: "#f59e0b" },
        modal: {
          ondismiss: () => { setBuying(false); },
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (e: unknown) {
      setPurchaseError(e instanceof Error ? e.message : "Purchase fail ho gaya");
      setBuying(false);
    }
  };

  const copyKey = () => {
    if (!purchaseResult) return;
    navigator.clipboard.writeText(purchaseResult.license_key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-white overflow-x-hidden">
      {/* ── NAVBAR ── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-100">
        <nav className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/25 group-hover:shadow-amber-500/40 transition-shadow">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-extrabold text-xl tracking-tight">Aura<span className="text-amber-500">Biz</span></span>
          </Link>
          <div className="hidden md:flex items-center gap-8">
            {["Features", "How it works", "Pricing", "Reviews"].map((l) => (
              <a key={l} href={`#${l.toLowerCase().replace(" ", "-")}`} className="text-sm font-medium text-gray-600 hover:text-amber-600 transition-colors">{l}</a>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Link href="/admin-login" className="text-sm font-medium text-gray-600 hover:text-amber-600 transition-colors hidden sm:inline-flex">Admin Login</Link>
            <Link href="/setup" className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-semibold shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:-translate-y-0.5 transition-all">
              Free Trial →
            </Link>
          </div>
        </nav>
      </header>

      {/* ── HERO ── */}
      <section ref={heroRef} className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-white" />
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-amber-200/30 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-orange-200/20 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-24">
          <div className="text-center max-w-4xl mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={heroInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-50 border border-amber-200 mb-8">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-amber-700">500+ businesses already growing with AuraBiz</span>
            </motion.div>

            <motion.h1 initial={{ opacity: 0, y: 24 }} animate={heroInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.6, delay: 0.1 }}
              className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-gray-900 mb-6 leading-[1.1]">
              Aapka WhatsApp,{" "}
              <span className="bg-gradient-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent">ab AI Salesman</span>
            </motion.h1>

            <motion.p initial={{ opacity: 0, y: 24 }} animate={heroInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.6, delay: 0.2 }}
              className="text-lg md:text-xl text-gray-600 max-w-2xl mx-auto mb-10 leading-relaxed">
              Customers ko Hinglish mein smart jawab do 24/7. Billing, inventory, orders — sab automate ho jayega.
              Seedha WhatsApp se apna business chalao.
            </motion.p>

            <motion.div initial={{ opacity: 0, y: 24 }} animate={heroInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/setup" className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold text-lg shadow-xl shadow-amber-500/30 hover:shadow-amber-500/50 hover:-translate-y-1 transition-all">
                Start Free Trial <ArrowRight className="w-5 h-5" />
              </Link>
              <a href="#how-it-works" className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-white border-2 border-gray-200 text-gray-700 font-bold text-lg hover:border-amber-300 hover:bg-amber-50 transition-all">
                ▶ See How It Works
              </a>
            </motion.div>

            <motion.div initial={{ opacity: 0 }} animate={heroInView ? { opacity: 1 } : {}} transition={{ delay: 0.5 }}
              className="flex items-center justify-center gap-6 mt-8 text-sm text-gray-500">
              <span className="flex items-center gap-1"><Check className="w-4 h-4 text-green-500" /> No credit card</span>
              <span className="flex items-center gap-1"><Check className="w-4 h-4 text-green-500" /> 14-day free trial</span>
              <span className="flex items-center gap-1"><Check className="w-4 h-4 text-green-500" /> Setup in 2 min</span>
            </motion.div>
          </div>

          {/* Chat Demo */}
          <motion.div initial={{ opacity: 0, y: 40 }} animate={heroInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-16 max-w-lg mx-auto">
            <div className="rounded-3xl border-[8px] border-gray-900 bg-white shadow-2xl overflow-hidden">
              <div className="bg-[#075E54] px-5 py-4 flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-lg">🤖</div>
                <div>
                  <div className="text-white font-semibold text-sm">AuraBiz Assistant</div>
                  <div className="text-[#a8e6c9] text-xs flex items-center gap-1"><span className="w-1.5 h-1.5 bg-green-400 rounded-full" /> online</div>
                </div>
              </div>
              <div className="bg-[#ECE5DD] px-4 py-5 space-y-3 min-h-[260px]">
                {chatDemo.map((m, i) => (
                  <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={heroInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.6 + i * 0.2 }}
                    className={`flex ${m.from === "customer" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                      m.from === "customer" ? "bg-[#DCF8C6] rounded-br-sm text-gray-800" : "bg-white rounded-bl-sm text-gray-800"
                    }`}>
                      <div>{m.text}</div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── STATS ── */}
      <section className="py-12 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
              className="text-center">
              <div className="text-3xl md:text-4xl font-extrabold text-white mb-1">{s.value}</div>
              <div className="text-gray-400 text-sm">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section id="features" className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">Features</span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-gray-900 mt-3 mb-4">Sab kuch jo aapko chahiye</h2>
            <p className="text-gray-600 text-lg">Ek assistant jo sunta hai, samajhta hai, aur business chalata hai — bilkul apne jaisa.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                className="group p-6 rounded-2xl bg-white border border-gray-100 hover:border-amber-200 hover:shadow-xl hover:shadow-amber-500/5 transition-all">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform`}>
                  <f.icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── USE CASES ── */}
      <section className="py-20 md:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">Use Cases</span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-gray-900 mt-3 mb-4">Har business ke liye</h2>
            <p className="text-gray-600 text-lg">Chahe salon ho, ki yaan, ya electronics shop — AuraBiz har SMB ka WhatsApp banata hai smart.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: "✂️", title: "Salon & Spa", desc: "Bookings automate, reminders bhejo, repeat customers badhao", color: "from-pink-500 to-rose-400" },
              { icon: "🛒", title: "Kirana Store", desc: "Inventory track, stock alerts, COD/UPI orders lo", color: "from-emerald-500 to-green-400" },
              { icon: "🔧", title: "Repair Services", desc: "Service bookings, status updates, follow-ups automate", color: "from-blue-500 to-cyan-400" },
              { icon: "👗", title: "Clothing Store", desc: "New arrivals broadcast, size availability, order confirm", color: "from-violet-500 to-purple-400" },
            ].map((uc, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="group p-6 rounded-2xl bg-white border border-gray-100 hover:border-amber-200 hover:shadow-xl hover:shadow-amber-500/5 transition-all cursor-default">
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${uc.color} flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform`}>
                  {uc.icon}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{uc.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{uc.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── WHY AURABIZ ── */}
      <section className="py-20 md:py-28 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-sm font-bold text-amber-400 uppercase tracking-wider">Why AuraBiz</span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-white mt-3 mb-4">Competitors se kya alag hai?</h2>
            <p className="text-gray-400 text-lg">WATI/Interakt se 5x sasta. Setup 2 minute mein. Hinglish AI jo actually kaam kare.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: <ZapIcon className="w-6 h-6" />, title: "2 Minute Setup", desc: "QR scan karo aur shuru ho jao. WATI mein 1-2 din lagte hain setup mein.", color: "text-amber-400" },
              { icon: <Shield className="w-6 h-6" />, title: "100% WhatsApp Safe", desc: "Official Business API use karta hai. Koi ban risk nahi — aapka number safe.", color: "text-green-400" },
              { icon: <MessageSquare className="w-6 h-6" />, title: "Real Hinglish AI", desc: "Sirf template nahi — actual jo customer kuch bole, samjhe aur jawab de.", color: "text-blue-400" },
              { icon: <TrendingUp className="w-6 h-6" />, title: "5x Affordable", desc: "Starter ₹999/maahina. WATI Growth ₹4,999 se shuru hota hai.", color: "text-violet-400" },
              { icon: <Users className="w-6 h-6" />, title: "Multi-user Access", desc: "Growth mein 5 users, Enterprise mein unlimited. Team ke saath manage karo.", color: "text-pink-400" },
              { icon: <Clock className="w-6 h-6" />, title: "24/7 Availability", desc: "Aap so rahe ho, AI customers se baat kar raha hai. Koi message miss nahi.", color: "text-orange-400" },
            ].map((w, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all">
                <div className={`mb-4 ${w.color}`}>{w.icon}</div>
                <h3 className="text-lg font-bold text-white mb-2">{w.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{w.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── INTEGRATIONS ── */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-sm font-bold text-gray-500 uppercase tracking-wider">Trusted Integrations</p>
            <h3 className="text-xl font-bold text-gray-900 mt-2">Sab kuch ek jagah — tools jo aap already use karte ho</h3>
          </div>
          <div className="flex items-center justify-center gap-8 flex-wrap">
            {[
              { name: "WhatsApp", icon: "💬" },
              { name: "Razorpay", icon: "💳" },
              { name: "PhonePe", icon: "📱" },
              { name: "UPI", icon: "🏦" },
              { name: "Google Business", icon: "📍" },
              { name: "Instagram", icon: "📸" },
            ].map((ig, i) => (
              <motion.div key={i} initial={{ opacity: 0, scale: 0.8 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                className="flex flex-col items-center gap-2 p-4 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md transition-all">
                <span className="text-2xl">{ig.icon}</span>
                <span className="text-xs font-medium text-gray-600">{ig.name}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">Setup</span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-gray-900 mt-3 mb-4">3 steps mein shuru karo</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.15 }}
                className="relative text-center p-8 rounded-2xl bg-white border border-gray-100 shadow-sm">
                <div className="text-5xl mb-4">{s.icon}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{s.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ── */}
      <section id="reviews" className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">Reviews</span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-gray-900 mt-3 mb-4">Logon ka bharosa</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="p-6 rounded-2xl bg-white border border-gray-100 shadow-sm">
                <div className="flex text-amber-400 mb-4">{"★".repeat(t.stars)}</div>
                <p className="text-gray-700 text-sm leading-relaxed mb-6">"{t.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-white text-sm font-bold">{t.avatar}</div>
                  <div>
                    <div className="font-bold text-gray-900 text-sm">{t.name}</div>
                    <div className="text-gray-500 text-xs">{t.role}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURE COMPARISON ── */}
      <section className="py-20 md:py-28 bg-white">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">Compare Plans</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-gray-900 mt-3 mb-4">Features by Plan</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-100">
                  <th className="text-left py-4 pr-4 font-bold text-gray-900">Feature</th>
                  <th className="text-center py-4 px-3 font-bold text-gray-900">Starter <span className="text-xs text-gray-500 block">₹999</span></th>
                  <th className="text-center py-4 px-3 font-bold text-amber-600 bg-amber-50 rounded-t-xl">Growth <span className="text-xs text-amber-500 block">₹2,499</span></th>
                  <th className="text-center py-4 px-3 font-bold text-gray-900">Enterprise <span className="text-xs text-gray-500 block">₹4,999</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[
                  ["WhatsApp AI Chatbot", "✅", "✅", "✅"],
                  ["Messages/month", "500", "2,500", "Unlimited"],
                  ["Users", "1", "5", "Unlimited"],
                  ["Products", "100", "500", "Unlimited"],
                  ["Broadcast Messages", "—", "✅", "✅"],
                  ["Follow-ups & Reminders", "—", "✅", "✅"],
                  ["Inventory Alerts", "—", "✅", "✅"],
                  ["Analytics Dashboard", "Basic", "Advanced", "Advanced"],
                  ["Loyalty Program", "✅", "✅", "✅"],
                  ["CRM (Customer Profiles)", "—", "✅", "✅"],
                  ["Team Management", "—", "✅", "✅"],
                  ["API Access", "—", "—", "✅"],
                  ["Custom AI Model", "—", "—", "✅"],
                  ["Priority Support", "Email", "Priority", "Dedicated"],
                ].map(([feature, ...plans], i) => (
                  <tr key={i} className={i % 2 === 0 ? "bg-gray-50/50" : ""}>
                    <td className="py-3 pr-4 text-gray-700 font-medium">{feature}</td>
                    {plans.map((val, j) => (
                      <td key={j} className={`py-3 px-3 text-center ${j === 1 ? "bg-amber-50/50" : ""} ${val === "✅" ? "text-green-500" : val === "—" ? "text-gray-300" : "text-gray-600 text-xs"}`}>
                        {val}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── PRICING ── */}
      <section id="pricing" className="py-20 md:py-28 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">Pricing</span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-gray-900 mt-3 mb-4">Simple pricing, no hidden fees</h2>
            <p className="text-gray-600 text-lg">14 din free trial. Koi credit card nahi chahiye.</p>
          </div>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-3 mb-12">
            <span className={`text-sm font-semibold ${billing === "monthly" ? "text-gray-900" : "text-gray-400"}`}>Monthly</span>
            <button onClick={() => setBilling(billing === "monthly" ? "yearly" : "monthly")}
              className="relative w-14 h-7 rounded-full bg-amber-500 transition-colors">
              <div className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow-md transition-transform ${billing === "yearly" ? "translate-x-8" : "translate-x-1"}`} />
            </button>
            <span className={`text-sm font-semibold ${billing === "yearly" ? "text-gray-900" : "text-gray-400"}`}>Yearly <span className="text-amber-600 text-xs">(2 months free)</span></span>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto items-stretch">
            {tiers.map((t, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className={`relative rounded-2xl p-8 flex flex-col ${
                  t.highlight ? "bg-gradient-to-b from-amber-50 to-white border-2 border-amber-300 shadow-xl shadow-amber-500/10 scale-105" : "bg-white border border-gray-200 shadow-sm"
                }`}>
                {t.highlight && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 text-white text-xs font-bold whitespace-nowrap">
                    MOST POPULAR
                  </div>
                )}
                <h3 className="text-xl font-bold text-gray-900 mb-1">{t.name}</h3>
                <div className="flex items-end gap-1 mb-6">
                  <span className="text-4xl font-extrabold text-gray-900">{visiblePrice(t.price)}</span>
                  <span className="text-gray-500 mb-1">{billing === "yearly" ? "/saal" : t.period}</span>
                </div>
                <ul className="space-y-3 mb-8 flex-1">
                  {t.features.map((f, j) => (
                    <li key={j} className="flex items-start gap-2 text-gray-700 text-sm">
                      <Check className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                      {f}
                    </li>
                  ))}
                </ul>
                <button onClick={() => openCheckout(t.name.toLowerCase(), billing, t.price)}
                  className={`block w-full text-center py-3 rounded-xl font-semibold transition-all ${
                    t.highlight ? "bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:-translate-y-0.5" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}>
                  {t.highlight ? "Start Free Trial" : "Get Started"}
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECURITY & TRUST ── */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">Security & Trust</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-gray-900 mt-3 mb-4">Aapka data 100% safe</h2>
            <p className="text-gray-600">Enterprise-grade security jo aapke business ki har baat ko protect kare.</p>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { icon: "🔒", title: "End-to-End Encryption", desc: "Har message encrypted — sirf aap aur customer padh sake" },
              { icon: "🛡️", title: "GDPR Compliant", desc: "Data protection laws follow karte hain — aapka data sirf aapka" },
              { icon: "🔐", title: "Secure Cloud Storage", desc: "AWS pe encrypted storage — koi unauthorized access nahi" },
              { icon: "📋", title: "Regular Backups", desc: "Daily automatic backups — data kabhi lose nahi hoga" },
            ].map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="text-center p-6 rounded-2xl bg-white border border-gray-100 shadow-sm">
                <div className="text-3xl mb-3">{s.icon}</div>
                <h4 className="font-bold text-gray-900 text-sm mb-1">{s.title}</h4>
                <p className="text-gray-500 text-xs leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="py-20 md:py-28">
        <div className="max-w-3xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="text-sm font-bold text-amber-600 uppercase tracking-wider">FAQ</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-gray-900 mt-3">Sawalon ke jawab</h2>
          </div>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <div key={i} className="rounded-2xl bg-white border border-gray-100 overflow-hidden">
                <button onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between px-6 py-5 text-left">
                  <span className="font-semibold text-gray-900 pr-4">{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 text-gray-400 shrink-0 transition-transform ${openFaq === i ? "rotate-180" : ""}`} />
                </button>
                {openFaq === i && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                    className="px-6 pb-5 text-gray-600 text-sm leading-relaxed">{faq.nahi}</motion.div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── ROI CALCULATOR ── */}
      <section className="py-20 md:py-28 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-12">
            <span className="text-sm font-bold text-amber-400 uppercase tracking-wider">ROI Calculator</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-white mt-3 mb-4">Kitna bachenge aapke paise?</h2>
            <p className="text-gray-400">Dekho kitna time aur paisa AuraBiz aapko bachata hai roz.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { value: "₹15,000+", label: "Monthly Savings", desc: "Manual messaging ka kharcha khatam — AI le legi" },
              { value: "20 hrs", label: "Time Saved/Month", desc: "Follow-ups, reminders, orders — sab automated" },
              { value: "3x", label: "Revenue Boost", desc: "24/7 availability = zyada customers = zyada sales" },
            ].map((r, i) => (
              <motion.div key={i} initial={{ opacity: 0, scale: 0.9 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="text-center p-6 rounded-2xl bg-white/5 border border-white/10">
                <div className="text-3xl md:text-4xl font-extrabold text-amber-400 mb-2">{r.value}</div>
                <div className="text-white font-bold mb-1">{r.label}</div>
                <div className="text-gray-400 text-xs">{r.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section className="py-20 bg-gradient-to-br from-amber-500 via-orange-500 to-red-500">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-6 leading-tight">Aaj hi apna WhatsApp<br />business machine banao</h2>
          <p className="text-white/90 text-lg mb-10 max-w-xl mx-auto">14 din free trial. Setup 2 minute. No credit card required.</p>
          <Link href="/setup" className="inline-flex items-center gap-2 px-10 py-4 rounded-2xl bg-white text-orange-600 font-bold text-lg shadow-xl hover:-translate-y-1 transition-all">
            Free Trial Shuru Karo <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="py-14 px-6 bg-gray-900 text-gray-400">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-10">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center"><Sparkles className="w-4 h-4 text-white" /></div>
              <span className="font-extrabold text-white text-lg">AuraBiz</span>
            </div>
            <p className="text-sm leading-relaxed max-w-sm">AI-powered WhatsApp Business Assistant for Indian small businesses. Orders, payments, loyalty, follow-ups — sab ek chat mein.</p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2.5 text-sm">
              {["Features", "Pricing", "WhatsApp Bot", "AI Training"].map((l) => (<li key={l}><a href="#features" className="hover:text-amber-400 transition-colors">{l}</a></li>))}
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Company</h4>
            <ul className="space-y-2.5 text-sm">
              {["About us", "Contact", "Privacy Policy", "Terms of Service"].map((l) => (<li key={l}><a href="#" className="hover:text-amber-400 transition-colors">{l}</a></li>))}
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-10 pt-6 border-t border-gray-800 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="text-sm">© 2026 AuraBiz. Sab rights reserved.</p>
          <p className="text-sm">Made with ❤️ for Indian businesses 🇮🇳</p>
        </div>
      </footer>

      {/* ── CHECKOUT MODAL ── */}
      {checkout && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm" onClick={() => !buying && setCheckout(null)}>
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
            className="bg-white rounded-3xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-xl">🛒</span>
                  <div><h3 className="text-xl font-bold text-gray-900">Buy {checkout.plan}</h3>
                  <div className="text-sm text-gray-500">{checkout.amount} {billing === "yearly" ? "/ saal" : "/ mahina"}</div></div>
                </div>
                <button onClick={() => !buying && setCheckout(null)} className="w-8 h-8 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 flex items-center justify-center">✕</button>
              </div>

              {!purchaseResult ? (
                <>
                  <div className="space-y-4">
                    <div><label className="text-sm font-semibold text-gray-700 mb-1 block">Naam *</label>
                      <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100 transition-all" placeholder="e.g. Priya Sharma" /></div>
                    <div><label className="text-sm font-semibold text-gray-700 mb-1 block">Email *</label>
                      <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100 transition-all" placeholder="aapka@email.com" /></div>
                    <div><label className="text-sm font-semibold text-gray-700 mb-1 block">WhatsApp Number</label>
                      <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100 transition-all" placeholder="+91 98765 43210" /></div>
                    <div><label className="text-sm font-semibold text-gray-700 mb-2 block">AI Option</label>
                      <div className="grid grid-cols-2 gap-3">
                        <button onClick={() => setForm({ ...form, aiTier: "free" })}
                          className={`p-3 rounded-xl border text-left transition-all ${form.aiTier === "free" ? "border-amber-400 bg-amber-50 ring-2 ring-amber-100" : "border-gray-200 hover:border-gray-300"}`}>
                          <div className="font-bold text-gray-900">🆓 Free AI</div><div className="text-xs text-gray-500">Falcon engine + free providers</div>
                        </button>
                        <button onClick={() => setForm({ ...form, aiTier: "paid" })}
                          className={`p-3 rounded-xl border text-left transition-all ${form.aiTier === "paid" ? "border-amber-400 bg-amber-50 ring-2 ring-amber-100" : "border-gray-200 hover:border-gray-300"}`}>
                          <div className="font-bold text-gray-900">🤖 Paid AI</div><div className="text-xs text-gray-500">Premium model, best replies</div>
                        </button>
                      </div>
                    </div>
                  </div>
                  {purchaseError && <div className="mt-4 text-sm text-red-500 bg-red-50 border border-red-100 rounded-xl px-4 py-3">{purchaseError}</div>}
                  <button onClick={submitPurchase} disabled={buying}
                    className="w-full mt-6 py-3.5 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:-translate-y-0.5 transition-all disabled:opacity-50">
                    {buying ? "Processing..." : `Pay ${checkout.amount} →`}
                  </button>
                  <p className="text-center text-xs text-gray-400 mt-3">💳 UPI / Card / Netbanking — 100% secure payment</p>
                </>
              ) : (
                <div className="text-center">
                  <div className="w-16 h-16 mx-auto rounded-full bg-green-100 flex items-center justify-center text-3xl mb-4">✅</div>
                  <h4 className="text-2xl font-bold text-gray-900 mb-2">Purchase Successful!</h4>
                  <p className="text-gray-500 text-sm mb-6">Aapka {purchaseResult.plan} plan activate ho gaya.</p>
                  <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5 mb-6">
                    <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Aapki License Key</div>
                    <div className="font-mono text-lg font-bold text-amber-600 break-all mb-3">{purchaseResult.license_key}</div>
                    <button onClick={copyKey} className="w-full py-2.5 rounded-xl bg-white border border-gray-200 text-sm font-semibold hover:bg-gray-50 transition-colors">
                      {copied ? "✅ Copied!" : "📋 Copy License Key"}
                    </button>
                  </div>
                  <a href={`${process.env.NEXT_PUBLIC_MASTER_URL || 'http://localhost:8010'}/api/license/download-exe`} className="block w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold shadow-lg hover:-translate-y-0.5 transition-all">
                    ⬇️ Download AuraBiz for Windows (.exe)
                  </a>
                  <p className="text-xs text-gray-400 mt-3">Install karo → License key daalo → Dashboard kholo</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
