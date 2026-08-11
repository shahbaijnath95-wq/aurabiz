"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { LifeBuoy, RefreshCw } from "lucide-react";

export default function SupportPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<any>(null);
  const [reply, setReply] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getSupportTickets({ status: statusFilter || undefined, page });
      setTickets(data.tickets || data.items || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, statusFilter]);

  const handleUpdate = async (id: string, updates: any) => {
    try {
      await masterAPI.updateSupportTicket(id, updates);
      toast.success("Ticket updated");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleReply = async () => {
    if (!reply.trim() || !selectedTicket) return;
    try {
      await masterAPI.replySupportTicket(selectedTicket.id, reply);
      toast.success("Reply sent");
      setReply("");
      const updated = await masterAPI.getSupportTicket(selectedTicket.id);
      setSelectedTicket(updated);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <LifeBuoy size={24} /> Support Tickets ({total})
        </h1>
        <button onClick={load} className="bg-gray-700 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <select
        value={statusFilter}
        onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        className="border rounded-lg px-3 py-2 text-sm mb-4"
      >
        <option value="">All Status</option>
        <option value="open">Open</option>
        <option value="in_progress">In Progress</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          {loading ? (
            <div className="animate-pulse text-gray-400">Loading...</div>
          ) : tickets.length === 0 ? (
            <div className="text-gray-400 text-sm">No tickets found</div>
          ) : (
            <div className="space-y-2">
              {tickets.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTicket(t)}
                  className={`w-full text-left bg-white rounded-xl shadow p-4 hover:shadow-md transition-shadow ${
                    selectedTicket?.id === t.id ? "ring-2 ring-blue-600" : ""
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{t.subject}</p>
                      <p className="text-xs text-gray-500">
                        {t.tenant_name} • {new Date(t.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        t.priority === "critical" ? "bg-red-100 text-red-700" :
                        t.priority === "high" ? "bg-orange-100 text-orange-700" :
                        t.priority === "medium" ? "bg-yellow-100 text-yellow-700" :
                        "bg-gray-100 text-gray-700"
                      }`}>
                        {t.priority}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        t.status === "open" ? "bg-blue-100 text-blue-700" :
                        t.status === "in_progress" ? "bg-purple-100 text-purple-700" :
                        t.status === "resolved" ? "bg-green-100 text-green-700" :
                        "bg-gray-100 text-gray-700"
                      }`}>
                        {t.status}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          {selectedTicket ? (
            <div className="bg-white rounded-xl shadow p-4 sticky top-4">
              <h3 className="font-bold mb-2">{selectedTicket.subject}</h3>
              <p className="text-sm text-gray-600 mb-2">{selectedTicket.description}</p>
              <p className="text-xs text-gray-500 mb-4">From: {selectedTicket.tenant_name}</p>

              <div className="space-y-2 mb-4">
                <select
                  value={selectedTicket.status}
                  onChange={(e) => {
                    handleUpdate(selectedTicket.id, { status: e.target.value });
                    setSelectedTicket({ ...selectedTicket, status: e.target.value });
                  }}
                  className="border rounded px-2 py-1 text-sm w-full"
                >
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
                <select
                  value={selectedTicket.priority}
                  onChange={(e) => {
                    handleUpdate(selectedTicket.id, { priority: e.target.value });
                    setSelectedTicket({ ...selectedTicket, priority: e.target.value });
                  }}
                  className="border rounded px-2 py-1 text-sm w-full"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              {selectedTicket.messages && selectedTicket.messages.length > 0 && (
                <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
                  {selectedTicket.messages.map((m: any, i: number) => (
                    <div key={i} className={`text-sm p-2 rounded ${m.from_admin ? "bg-blue-50 ml-4" : "bg-gray-50 mr-4"}`}>
                      <p className="text-xs text-gray-500">{m.from_admin ? "Admin" : selectedTicket.tenant_name}</p>
                      <p>{m.message}</p>
                    </div>
                  ))}
                </div>
              )}

              <textarea
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder="Type your reply..."
                className="w-full border rounded px-2 py-1 text-sm mb-2"
                rows={3}
              />
              <button
                onClick={handleReply}
                className="w-full bg-blue-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-blue-700"
              >
                Send Reply
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow p-4 text-center text-gray-400 text-sm">
              Select a ticket to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
