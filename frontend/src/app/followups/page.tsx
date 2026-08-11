"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { followups } from "@/lib/api";
import type { FollowUp, FollowUpStats } from "@/lib/types";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function FollowupsPage() {
  const router = useRouter();
  const { user, business, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const [followupList, setFollowupList] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [stats, setStats] = useState<FollowUpStats | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    customer_id: "", message: "", followup_type: "manual",
    scheduled_for: "",
  });

  const businessId = business?.id || "";

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
    if (businessId) {
      loadFollowups();
      loadStats();
    }
  }, [authLoading, user, businessId, filter]);

  async function loadFollowups() {
    try {
      const data = await followups.list(businessId, filter === "all" ? undefined : filter);
      setFollowupList(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function loadStats() {
    try {
      const data = await followups.stats(businessId);
      setStats(data);
    } catch (e) { console.error(e); }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await followups.create({ ...form, business_id: businessId });
      setForm({ customer_id: "", message: "", followup_type: "manual", scheduled_for: "" });
      setShowCreate(false);
      loadFollowups();
      loadStats();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Create fail ho gaya", "error"); }
  }

  async function handleComplete(id: string) {
    try {
      await followups.complete(id);
      loadFollowups();
      loadStats();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Complete fail ho gaya", "error"); }
  }

  async function handleCancel(id: string) {
    if (!confirm("Cancel follow-up?")) return;
    try {
      await followups.cancel(id);
      loadFollowups();
      loadStats();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Cancel fail ho gaya", "error"); }
  }

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    sent: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    cancelled: "bg-gray-100 text-gray-500",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Follow-ups</h1>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600">
          + Create Follow-up
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl border p-4 text-center">
            <p className="text-2xl font-bold text-amber-500">{stats.pending || 0}</p>
            <p className="text-xs text-gray-500">Pending</p>
          </div>
          <div className="bg-white rounded-xl border p-4 text-center">
            <p className="text-2xl font-bold text-blue-500">{stats.sent || 0}</p>
            <p className="text-xs text-gray-500">Sent</p>
          </div>
          <div className="bg-white rounded-xl border p-4 text-center">
            <p className="text-2xl font-bold text-green-500">{stats.completed || 0}</p>
            <p className="text-xs text-gray-500">Completed</p>
          </div>
          <div className="bg-white rounded-xl border p-4 text-center">
            <p className="text-2xl font-bold text-red-500">{stats.failed || 0}</p>
            <p className="text-xs text-gray-500">Failed</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {["all", "pending", "sent", "completed", "cancelled", "failed"].map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm capitalize ${filter === f ? "bg-amber-500 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
            {f}
          </button>
        ))}
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold mb-3">New Follow-up</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <input value={form.customer_id} onChange={e => setForm({ ...form, customer_id: e.target.value })}
              placeholder="Customer ID" className="w-full px-3 py-2 border rounded-lg" required />
            <textarea value={form.message} onChange={e => setForm({ ...form, message: e.target.value })}
              placeholder="Follow-up message" className="w-full px-3 py-2 border rounded-lg h-24" required />
            <div className="grid grid-cols-2 gap-3">
              <select value={form.followup_type} onChange={e => setForm({ ...form, followup_type: e.target.value })}
                className="px-3 py-2 border rounded-lg">
                <option value="manual">Manual</option>
                <option value="order_update">Order Update</option>
                <option value="payment_reminder">Payment Reminder</option>
                <option value="feedback_request">Feedback Request</option>
              </select>
              <input type="datetime-local" value={form.scheduled_for} onChange={e => setForm({ ...form, scheduled_for: e.target.value })}
                className="px-3 py-2 border rounded-lg" />
            </div>
            <div className="flex gap-2">
              <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded-lg">Create</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-200 rounded-lg">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : followupList.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-400">No follow-ups found.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Message</th>
                <th className="text-left px-4 py-3">Customer</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Scheduled</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {followupList.map((fu) => (
                <tr key={fu.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 max-w-xs truncate">{fu.message}</td>
                  <td className="px-4 py-3 text-gray-500">{fu.customer_id?.slice(0, 8)}...</td>
                  <td className="px-4 py-3 text-xs capitalize">{fu.followup_type?.replace("_", " ")}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{fu.scheduled_for || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[fu.status] || ""}`}>
                      {fu.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {fu.status === "pending" && (
                      <>
                        <button onClick={() => handleComplete(fu.id)} className="text-green-500 hover:underline text-xs mr-2">Complete</button>
                        <button onClick={() => handleCancel(fu.id)} className="text-orange-500 hover:underline text-xs">Cancel</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
    </div></div>
  );
}
