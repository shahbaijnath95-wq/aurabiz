"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { loyalty as loyaltyApi } from "@/lib/api";
import type { LoyaltyTier } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function LoyaltyPage() {
  const [tiers, setTiers] = useState<LoyaltyTier[]>([]);
  const [members, setMembers] = useState<{id: string; name: string; points: number; tier: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) { setLoading(false); return; }
    Promise.all([
      loyaltyApi.tiers(businessId).catch(() => ({ tiers: [] })),
      loyaltyApi.analytics(businessId).catch(() => ({ members: [] })),
    ]).then(([t, a]) => {
      setTiers(Array.isArray(t) ? t : (t as { tiers?: LoyaltyTier[] })?.tiers || []);
      setMembers((a as { members?: unknown[]; customers?: unknown[] })?.members || (a as { customers?: unknown[] })?.customers || []);
    }).finally(() => setLoading(false));
  }, [businessId]);

  const tierColor: Record<string, string> = {
    Bronze: "from-amber-700 to-amber-900",
    Silver: "from-gray-400 to-gray-500",
    Gold: "from-yellow-400 to-amber-500",
    Platinum: "from-violet-500 to-purple-600",
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
          <h1 className="text-2xl font-bold text-gray-900">Loyalty Program</h1>
          <p className="text-gray-500">Apne customers ko reward karo</p>
        </div>

        {loading ? (
          <div className="grid md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="bg-white rounded-2xl p-6 animate-pulse h-40 shimmer" />)}
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-4 gap-4 mb-8">
              {tiers.map((t, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-card card-hover">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${tierColor[t.name] || "from-gray-400 to-gray-500"} mb-3 flex items-center justify-center text-white text-lg font-bold`}>
                    {t.name?.charAt(0) || "?"}
                  </div>
                  <h3 className="font-semibold text-gray-900">{t.name}</h3>
                  <p className="text-sm text-gray-400">{t.min_points || 0}+ points</p>
                  <p className="text-xs text-gray-500 mt-1">{t.members || t.member_count || 0} members</p>
                </motion.div>
              ))}
              {tiers.length === 0 && (
                <div className="col-span-4 bg-white rounded-2xl p-8 text-center text-gray-400 border border-gray-100 shadow-card">
                  Abhi koi tier nahi hai — pehla banao!
                </div>
              )}
            </div>

            {members.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
                <div className="p-4 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-900">Loyalty Members ({members.length})</h3>
                </div>
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-4 font-medium text-gray-500">Name</th>
                      <th className="text-center p-4 font-medium text-gray-500">Points</th>
                      <th className="text-center p-4 font-medium text-gray-500">Tier</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.slice(0, 10).map((m, i) => (
                      <tr key={i} className="border-t border-gray-50">
                        <td className="p-4 text-gray-900">{m.name || m.customer_name}</td>
                        <td className="p-4 text-center font-medium">{m.points || m.loyalty_points || 0}</td>
                        <td className="p-4 text-center">
                          <span className="text-xs font-medium px-2 py-1 rounded-full bg-amber-50 text-amber-700">{m.tier || "Bronze"}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    
        </div></div>
  );
}
