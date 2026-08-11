"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { scheduledMessages } from "@/lib/api";
import type { ScheduledMessage } from "@/lib/types";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function ScheduledMessagesPage() {
  const router = useRouter();
  const { user, business, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const [messages, setMessages] = useState<ScheduledMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    content: "", customer_id: "", message_type: "text",
    scheduled_for: "",
  });

  const businessId = business?.id || "";

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
    if (businessId) loadMessages();
  }, [authLoading, user, businessId, filter]);

  async function loadMessages() {
    try {
      const data = await scheduledMessages.list(businessId, filter === "all" ? undefined : filter);
      setMessages(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await scheduledMessages.create({ ...form, business_id: businessId });
      setForm({ content: "", customer_id: "", message_type: "text", scheduled_for: "" });
      setShowCreate(false);
      loadMessages();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Create fail ho gaya", "error"); }
  }

  async function handleCancel(id: string) {
    if (!confirm("Cancel scheduled message?")) return;
    try {
      await scheduledMessages.cancel(id);
      loadMessages();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Cancel fail ho gaya", "error"); }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete message?")) return;
    try {
      await scheduledMessages.delete(id);
      loadMessages();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Delete fail ho gaya", "error"); }
  }

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    sent: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    cancelled: "bg-gray-100 text-gray-500",
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Scheduled Messages</h1>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600">
          + Schedule Message
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {["all", "pending", "sent", "failed", "cancelled"].map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm capitalize ${filter === f ? "bg-amber-500 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
            {f}
          </button>
        ))}
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold mb-3">Schedule New Message</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <input value={form.customer_id} onChange={e => setForm({ ...form, customer_id: e.target.value })}
              placeholder="Customer ID" className="w-full px-3 py-2 border rounded-lg" required />
            <textarea value={form.content} onChange={e => setForm({ ...form, content: e.target.value })}
              placeholder="Message content" className="w-full px-3 py-2 border rounded-lg h-24" required />
            <div className="grid grid-cols-2 gap-3">
              <select value={form.message_type} onChange={e => setForm({ ...form, message_type: e.target.value })}
                className="px-3 py-2 border rounded-lg">
                <option value="text">Text</option>
                <option value="image">Image</option>
                <option value="document">Document</option>
              </select>
              <input type="datetime-local" value={form.scheduled_for} onChange={e => setForm({ ...form, scheduled_for: e.target.value })}
                className="px-3 py-2 border rounded-lg" required />
            </div>
            <div className="flex gap-2">
              <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded-lg">Schedule</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-200 rounded-lg">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : messages.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-400">No scheduled messages.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Message</th>
                <th className="text-left px-4 py-3">Customer</th>
                <th className="text-left px-4 py-3">Scheduled</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((msg) => (
                <tr key={msg.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 max-w-xs truncate">{msg.content}</td>
                  <td className="px-4 py-3 text-gray-500">{msg.customer_id?.slice(0, 8)}...</td>
                  <td className="px-4 py-3 text-gray-500">{msg.scheduled_for || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[msg.status] || ""}`}>
                      {msg.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {msg.status === "pending" && (
                      <button onClick={() => handleCancel(msg.id)} className="text-orange-500 hover:underline text-xs mr-2">Cancel</button>
                    )}
                    <button onClick={() => handleDelete(msg.id)} className="text-red-500 hover:underline text-xs">Delete</button>
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
