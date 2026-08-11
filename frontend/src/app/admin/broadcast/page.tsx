"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import Sidebar from "@/components/Sidebar";
import { request } from "@/lib/api";

interface Broadcast {
  id: string;
  message: string;
  target_count: number;
  sent_count: number;
  failed_count: number;
  status: string;
  created_at: string | null;
}

export default function BroadcastPage() {
  const { business, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
  const [broadcasts, setBroadcasts] = useState<Broadcast[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (business?.id) fetchBroadcasts();
  }, [business?.id]);

  async function fetchBroadcasts() {
    try {
      const data = await request<Broadcast[]>(`/broadcast/${business?.id}`);
      setBroadcasts(Array.isArray(data) ? data : (data as unknown as { broadcasts?: Broadcast[] })?.broadcasts || []);
    } catch (e) { console.error(e); toast("Broadcasts load nahi ho paye", "error"); }
    setLoading(false);
  }

  async function sendBroadcast() {
    if (!message.trim()) return;
    if (!confirm(`Sabhi customers ko message bhejna hai?\n\n"${message}"`)) return;
    setSending(true);
    try {
      const data = await request<{ sent_count?: number; failed_count?: number; target_count?: number }>("/broadcast", {
        method: "POST",
        body: JSON.stringify({ business_id: business?.id, message: message.trim() }),
      });
      toast(`Broadcast sent! Sent: ${data.sent_count}, Failed: ${data.failed_count}, Total: ${data.target_count}`, "success");
      setMessage("");
      fetchBroadcasts();
    } catch (e) { console.error(e); toast("Broadcast send nahi ho paya", "error"); }
    setSending(false);
  }

  return (
    <div className="flex min-h-screen bg-[#faf9f7]">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Broadcast Messages</h1>
            <p className="text-sm text-gray-500 mt-1">Send messages to all customers at once</p>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm mb-8">
            <h3 className="font-bold text-gray-900 mb-3">New Broadcast</h3>
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Type your message here... (Hinglish mein likho for best results)"
              className="w-full h-32 px-4 py-3 border border-gray-200 rounded-xl text-sm resize-none focus:ring-2 focus:ring-amber-200 focus:border-amber-400 outline-none"
            />
            <div className="flex items-center justify-between mt-4">
              <p className="text-xs text-gray-400">{message.length} characters</p>
              <button
                onClick={sendBroadcast}
                disabled={sending || !message.trim()}
                className="px-6 py-2.5 bg-amber-500 text-white rounded-xl font-medium hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? "Sending..." : "📢 Send to All Customers"}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 overflow-x-auto">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-bold text-gray-900">Broadcast History</h3>
            </div>
            <table className="w-full">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Message</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Sent</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Failed</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {broadcasts.map(b => (
                  <tr key={b.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm max-w-xs truncate">{b.message}</td>
                    <td className="px-6 py-4 text-sm text-green-600 font-medium">{b.sent_count}</td>
                    <td className="px-6 py-4 text-sm text-red-500">{b.failed_count}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${b.status === "sent" ? "bg-green-100 text-green-700" : b.status === "sending" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-500"}`}>
                        {b.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-400">{b.created_at ? new Date(b.created_at).toLocaleDateString("en-IN") : "-"}</td>
                  </tr>
                ))}
                {broadcasts.length === 0 && <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-400">No broadcasts sent yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

