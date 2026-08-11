"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import Sidebar from "@/components/Sidebar";
import { request } from "@/lib/api";

interface Feedback {
  id: string;
  customer_name: string | null;
  rating: number;
  comment: string | null;
  order_id: string | null;
  created_at: string | null;
}

interface FeedbackStats {
  total: number;
  average_rating: number;
  "5_star": number;
  "4_star": number;
  "3_star": number;
  "2_star": number;
  "1_star": number;
}

export default function FeedbackPage() {
  const { business, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (business?.id) {
      fetchFeedbacks();
      fetchStats();
    }
  }, [business?.id]);

  async function fetchFeedbacks() {
    try {
      const data = await request<Feedback[]>(`/feedback/${business?.id}`);
      setFeedbacks(Array.isArray(data) ? data : (data as unknown as { feedbacks?: Feedback[] })?.feedbacks || []);
    } catch (e) { console.error(e); toast("Feedback load nahi ho paya", "error"); }
    setLoading(false);
  }

  async function fetchStats() {
    try {
      const data = await request<FeedbackStats>(`/feedback/${business?.id}/stats`);
      setStats(data);
    } catch (e) { console.error(e); }
  }

  function renderStars(rating: number) {
    return "⭐".repeat(rating) + "☆".repeat(5 - rating);
  }

  return (
    <div className="flex min-h-screen bg-[#faf9f7]">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Customer Feedback</h1>
            <p className="text-sm text-gray-500 mt-1">Ratings and reviews from your customers</p>
          </div>

          {stats && (
            <div className="grid grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-2xl p-5 border border-gray-100">
                <p className="text-sm text-gray-500">Total Reviews</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats.total}</p>
              </div>
              <div className="bg-white rounded-2xl p-5 border border-gray-100">
                <p className="text-sm text-gray-500">Average Rating</p>
                <p className="text-3xl font-bold text-amber-500 mt-1">{stats.average_rating} ⭐</p>
              </div>
              <div className="bg-white rounded-2xl p-5 border border-gray-100">
                <p className="text-sm text-gray-500">5 Star Reviews</p>
                <p className="text-3xl font-bold text-green-500 mt-1">{stats["5_star"]}</p>
              </div>
              <div className="bg-white rounded-2xl p-5 border border-gray-100">
                <p className="text-sm text-gray-500">Low Ratings (1-2)</p>
                <p className="text-3xl font-bold text-red-500 mt-1">{stats["1_star"] + stats["2_star"]}</p>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-gray-100 overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Customer</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Rating</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Review</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {feedbacks.map(f => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium">{f.customer_name || "Anonymous"}</td>
                    <td className="px-6 py-4 text-sm">{renderStars(f.rating)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 max-w-md">{f.comment || "-"}</td>
                    <td className="px-6 py-4 text-xs text-gray-400">{f.created_at ? new Date(f.created_at).toLocaleDateString("en-IN") : "-"}</td>
                  </tr>
                ))}
                {feedbacks.length === 0 && <tr><td colSpan={4} className="px-6 py-12 text-center text-gray-400">No feedback yet. Customers will rate after orders!</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

