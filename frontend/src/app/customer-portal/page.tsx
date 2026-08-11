"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { customers } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function CustomerPortalPage() {
  const [custList, setCustList] = useState<{id: string; name: string; phone_number: string; total_orders: number; total_spent: number; loyalty_points?: number}[]>([]);
  const [filtered, setFiltered] = useState<{id: string; name: string; phone_number: string; total_orders: number; total_spent: number; loyalty_points?: number}[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<{id: string; name: string; phone_number: string; total_orders: number; total_spent: number; loyalty_points?: number} | null>(null);
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) return;
    customers.list(businessId, { limit: 100 })
      .then((data) => {
        const list = Array.isArray(data) ? data : (data as { customers?: typeof data[] })?.customers || [];
        setCustList(list);
        setFiltered(list);
      })
      .catch(() => toast("Customers load nahi ho paye", "error"))
      .finally(() => setLoading(false));
  }, [businessId]);

  useEffect(() => {
    if (!search.trim()) { setFiltered(custList); return; }
    const q = search.toLowerCase();
    setFiltered(custList.filter((c) =>
      c.name.toLowerCase().includes(q) ||
      (c.phone_number || "").includes(q)
    ));
  }, [search, custList]);

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="layout-container">
        <div className="page-header">
          <Link href="/dashboard" className="text-sm text-gold-600 hover:text-gold-700 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
          <h1 className="page-title">Customers</h1>
          <p className="page-subtitle">{custList.length} customers hain aapke mein</p>
        </div>

        {/* Search Bar */}
        <div className="relative mb-6">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-surface-400">🔍</span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Customer name ya phone number search karo..."
            className="w-full pl-11 pr-4 py-3 rounded-xl bg-surface-50 border border-surface-200 text-surface-800 placeholder:text-surface-400 focus:outline-none focus:border-gold-400 focus:ring-2 focus:ring-gold-100 transition-all"
          />
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
                className="card p-6">
                <div className="shimmer h-4 w-16 rounded mb-3" />
                <div className="shimmer h-3 w-24 rounded mb-2" />
                <div className="shimmer h-3 w-32 rounded" />
              </motion.div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="card p-12 text-center text-surface-400">
            <div className="text-4xl mb-3">🔍</div>
            <p className="text-surface-500">Koi customer nahi mila</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((c, i) => (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                whileHover={{ y: -2 }}
                className={`card card-hover-shadow cursor-pointer ${selected?.id === c.id ? "border-gold-400 ring-2 ring-gold-100" : ""}`}
                onClick={() => setSelected(c)}
              >
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gold-400 to-gold-500 text-white flex items-center justify-center text-lg font-bold shrink-0">
                      {(c.name || "U").charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-surface-800 truncate">{c.name || "Unknown"}</h3>
                      <p className="text-surface-400 text-sm truncate">{c.phone_number || "N/A"}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-surface-100 rounded-xl p-3 text-center">
                      <div className="text-lg font-bold text-surface-800">{c.total_orders || 0}</div>
                      <div className="text-xs text-surface-400">Orders</div>
                    </div>
                    <div className="bg-surface-100 rounded-xl p-3 text-center">
                      <div className="text-lg font-bold text-surface-800">₹{(c.total_spend || 0).toLocaleString()}</div>
                      <div className="text-xs text-surface-400">Total Spend</div>
                    </div>
                  </div>
                  {c.loyalty_points && (
                    <div className="mt-3 flex items-center gap-2 bg-gold-50 rounded-xl px-3 py-2">
                      <span className="text-gold-500">⭐</span>
                      <span className="text-sm font-medium text-gold-700">{c.loyalty_points} loyalty points</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div></div>
  );
}