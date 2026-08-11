"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { chat as chatApi } from "@/lib/api";
import type { Conversation, ChatMessage } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import { motion, AnimatePresence } from "framer-motion";

interface InboxMessage {
  id: string;
  direction?: string;
  sender?: string;
  content?: string;
  message?: string;
  message_type: string;
  timestamp?: string;
  created_at?: string;
}

export default function AdminInboxPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearType, setClearType] = useState<"messages" | "conversation">("messages");
  const [clearing, setClearing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterDir, setFilterDir] = useState<string>("all");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) { setLoading(false); return; }
    chatApi.conversations(businessId)
      .then((data) => {
        const list = Array.isArray(data) ? data : (data as Record<string, unknown>)?.conversations;
        setConversations(Array.isArray(list) ? list : []);
      })
      .catch((err) => {
        console.error("[INBOX] API error:", err);
        toast("Conversations load nahi ho payi", "error");
      })
      .finally(() => setLoading(false));
  }, [businessId]);

  const loadMessages = async (conv: Conversation) => {
    setSelectedConv(conv);
    setLoadingMessages(true);
    try {
      const data = await chatApi.messages(conv.id);
      const list = Array.isArray(data) ? data : (data as Record<string, unknown>)?.messages;
      setMessages(Array.isArray(list) ? list : []);
    } catch {
      toast("Messages load nahi ho paye", "error");
    } finally {
      setLoadingMessages(false);
    }
  };

  const sendReply = async () => {
    if (!replyText.trim() || !selectedConv || !businessId) return;
    setSending(true);
    try {
      await chatApi.reply({
        conversation_id: selectedConv.id,
        message: replyText.trim(),
        business_id: businessId,
      });
      setMessages((prev) => [...prev, {
        id: `admin-${Date.now()}`,
        direction: "outbound",
        content: replyText.trim(),
        message_type: "text",
        timestamp: new Date().toISOString(),
      }]);
      setReplyText("");
      toast("Reply bhej diya!", "success");
    } catch {
      toast("Reply nahi ja paya", "error");
    } finally {
      setSending(false);
    }
  };

  const handleClear = async () => {
    if (!selectedConv) return;
    setClearing(true);
    try {
      if (clearType === "messages") {
        await chatApi.clearMessages(selectedConv.id);
        setMessages([]);
        toast("Saare messages delete ho gaye!", "success");
      } else {
        await chatApi.deleteConversation(selectedConv.id);
        setMessages([]);
        setSelectedConv(null);
        setConversations((prev) => prev.filter((c) => c.id !== selectedConv.id));
        toast("Poora conversation delete ho gaya!", "success");
      }
      setShowClearModal(false);
    } catch {
      toast("Delete nahi ho paya", "error");
    } finally {
      setClearing(false);
    }
  };

  useEffect(() => {
    if (!businessId) return;
    const interval = setInterval(() => {
      chatApi.conversations(businessId)
        .then((data) => setConversations(Array.isArray(data) ? data : []))
        .catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, [businessId]);

  useEffect(() => {
    if (!selectedConv?.id) return;
    const interval = setInterval(() => {
      chatApi.messages(selectedConv.id)
        .then((data) => {
          if (Array.isArray(data)) setMessages(data);
        })
        .catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [selectedConv?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const timeAgo = (dateStr?: string) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (diff < 60) return "Abhi";
    if (diff < 3600) return `${Math.floor(diff / 60)}m pehle`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h pehle`;
    return `${Math.floor(diff / 86400)}d pehle`;
  };

  const filteredConversations = conversations.filter((conv) => {
    const matchSearch = !searchQuery || (
      conv.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.last_message?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    const matchDir = filterDir === "all" || conv.last_direction === filterDir;
    return matchSearch && matchDir;
  });

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="layout-container">
        <div className="page-header">
          <Link href="/dashboard" className="text-sm text-gold-600 hover:text-gold-700 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
          <h1 className="page-title">Inbox</h1>
          <p className="page-subtitle">Customer messages dekho aur reply karo</p>
        </div>

        <div className="flex flex-col md:flex-row gap-6" style={{ height: "calc(100vh - 200px)" }}>
          {/* Conversation List */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full md:w-80 flex-shrink-0 bg-surface-50 rounded-2xl border border-surface-200 shadow-md overflow-hidden flex flex-col"
          >
            <div className="p-4 border-b border-surface-200">
              <h2 className="font-semibold text-surface-800 mb-3">Conversations ({conversations.length})</h2>
              <div className="relative mb-3">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-400 text-sm">🔍</span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search customer..."
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-50 border border-surface-200 text-sm text-surface-800 placeholder:text-surface-400 focus:outline-none focus:border-gold-400 focus:ring-2 focus:ring-gold-100 transition-all"
                />
              </div>
              <div className="flex gap-2">
                {["all", "inbound", "outbound"].map((dir) => (
                  <button
                    key={dir}
                    onClick={() => setFilterDir(dir)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      filterDir === dir
                        ? "bg-gold-500 text-white"
                        : "bg-surface-200 text-surface-500 hover:bg-surface-300"
                    }`}
                  >
                    {dir === "all" ? "All" : dir === "inbound" ? "📩 In" : "📤 Out"}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="p-4 text-center text-surface-400">Loading...</div>
              ) : filteredConversations.length === 0 ? (
                <div className="p-4 text-center text-surface-400">Koi conversation nahi hai</div>
              ) : (
                filteredConversations.map((conv) => (
                  <motion.div
                    key={conv.id}
                    whileHover={{ backgroundColor: "var(--surface-100)" }}
                    onClick={() => loadMessages(conv)}
                    className={`p-4 border-b border-surface-100 cursor-pointer transition-colors ${selectedConv?.id === conv.id ? "bg-gold-50 border-l-2 border-l-gold-500" : ""}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-500 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                        {conv.customer_name?.charAt(0) || "?"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-surface-800 text-sm truncate">{conv.customer_name}</span>
                          <span className="text-xs text-surface-400">{timeAgo(conv.last_message_at)}</span>
                        </div>
                        <p className="text-xs text-surface-400 truncate mt-0.5">
                          {conv.last_direction === "inbound" ? "📩" : "🤖"} {conv.last_message || "No messages"}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>

          {/* Chat View */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex-1 bg-surface-50 rounded-2xl border border-surface-200 shadow-md flex flex-col overflow-hidden"
          >
            {!selectedConv ? (
              <div className="flex-1 flex items-center justify-center text-surface-400">
                <div className="text-center">
                  <div className="text-5xl mb-3">💬</div>
                  <p className="text-surface-500">Conversation select karo left side se</p>
                </div>
              </div>
            ) : (
              <>
                {/* Chat Header */}
                <div className="p-4 border-b border-surface-200 flex items-center justify-between bg-surface-50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-500 text-white flex items-center justify-center text-sm font-bold">
                      {selectedConv.customer_name?.charAt(0) || "?"}
                    </div>
                    <div>
                      <h3 className="font-semibold text-surface-800">{selectedConv.customer_name}</h3>
                      <p className="text-xs text-surface-400">{selectedConv.customer_phone} • {selectedConv.channel}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => { setClearType("messages"); setShowClearModal(true); }}
                      className="px-3 py-1.5 text-xs font-medium text-surface-600 bg-surface-200 hover:bg-surface-300 rounded-lg transition-colors"
                      title="Saare messages delete karo"
                    >
                      🧹 Clear
                    </button>
                    <button
                      onClick={() => { setClearType("conversation"); setShowClearModal(true); }}
                      className="px-3 py-1.5 text-xs font-medium text-error-600 bg-error-50 hover:bg-error-100 rounded-lg transition-colors"
                      title="Poora conversation delete karo"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {loadingMessages ? (
                    <div className="text-center text-surface-400 py-8">Messages load ho rahe hain...</div>
                  ) : messages.length === 0 ? (
                    <div className="text-center text-surface-400 py-8">Koi message nahi hai abhi</div>
                  ) : (
                    <AnimatePresence>
                      {messages.map((m) => (
                        <motion.div
                          key={m.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`flex ${m.direction === "outbound" || m.direction === "outgoing" ? "justify-end" : "justify-start"}`}
                        >
                          <div className={`max-w-xs lg:max-w-md px-4 py-2.5 rounded-2xl text-sm ${m.direction === "outbound" || m.direction === "outgoing"
                            ? "bg-gradient-to-r from-gold-400 to-gold-500 text-white rounded-br-md shadow-sm"
                            : "bg-white text-surface-800 rounded-bl-md shadow-sm border border-surface-100"
                          }`}>
                            <p>{m.content}</p>
                            <p className={`text-xs mt-1 ${m.direction === "outbound" || m.direction === "outgoing" ? "text-white/70" : "text-surface-400"}`}>
                              {m.timestamp ? new Date(m.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : ""}
                            </p>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Reply Input */}
                <div className="p-4 border-t border-surface-200 bg-surface-50">
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendReply()}
                      placeholder="Reply type karo..."
                      className="flex-1 px-4 py-2.5 rounded-xl bg-white border border-surface-200 text-surface-800 text-sm placeholder:text-surface-400 focus:outline-none focus:border-gold-400 focus:ring-2 focus:ring-gold-100 transition-all"
                      disabled={sending}
                    />
                    <button
                      onClick={sendReply}
                      disabled={sending || !replyText.trim()}
                      className="px-5 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-500 hover:to-gold-600 disabled:opacity-40 transition-all shadow-sm"
                    >
                      {sending ? "..." : "📤 Send"}
                    </button>
                  </div>
                  <p className="text-xs text-surface-400 mt-2">⚠️ Admin manual reply — AI override ho jayega is conversation pe</p>
                </div>
              </>
            )}
          </motion.div>
        </div>
      </div>

      {/* Clear Chat Confirmation Modal */}
      <AnimatePresence>
        {showClearModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
            onClick={() => setShowClearModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-surface-50 rounded-2xl shadow-xl max-w-sm w-full mx-4 p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="text-center mb-4">
                <div className="text-4xl mb-3">{clearType === "messages" ? "🧹" : "🗑️"}</div>
                <h3 className="text-lg font-bold text-surface-800">
                  {clearType === "messages" ? "Saaf karna hai?" : "Delete karna hai?"}
                </h3>
                <p className="text-sm text-surface-500 mt-2">
                  {clearType === "messages"
                    ? `"${selectedConv?.customer_name}" ke saare messages delete ho jayenge. Ye action undo nahi ho sakta.`
                    : `"${selectedConv?.customer_name}" ka poora conversation delete ho jayega — messages + conversation record. Ye action undo nahi ho sakta.`}
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowClearModal(false)}
                  className="flex-1 px-4 py-2.5 text-sm font-medium text-surface-700 bg-surface-200 hover:bg-surface-300 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleClear}
                  disabled={clearing}
                  className={`flex-1 px-4 py-2.5 text-sm font-medium text-white rounded-xl transition-colors disabled:opacity-40 ${
                    clearType === "messages"
                      ? "bg-gold-500 hover:bg-gold-600"
                      : "bg-error-500 hover:bg-error-600"
                  }`}
                >
                  {clearing ? "Ho raha hai..." : clearType === "messages" ? "🧹 Saaf Karo" : "🗑️ Delete Karo"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div></div>
  );
}