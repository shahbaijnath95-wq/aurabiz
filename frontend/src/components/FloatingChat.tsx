"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { chat as chatApi } from "@/lib/api";
import { useToast } from "@/lib/toast-context";

interface FloatingChatMessage {
  id: string;
  text: string;
  sender: "user" | "bot";
  timestamp: string;
}

export default function FloatingChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<FloatingChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [showWelcome, setShowWelcome] = useState(true);
  const [connected, setConnected] = useState(false);
  const [sessionId] = useState(() => `float-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const businessId = typeof window !== "undefined" ? localStorage.getItem("business_id") || "default" : "default";

  useEffect(() => {
    if (open && messages.length === 0 && !showWelcome) {
      setTimeout(() => {
        sendMessage("Hello! Main AI business assistant hoon. Kya help chahiye?");
      }, 500);
    }
  }, [open]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: FloatingChatMessage = {
      id: `msg-${Date.now()}`,
      text: text.trim(),
      sender: "user",
      timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);
    try {
      const data = await chatApi.send({
        message: text.trim(),
        business_id: businessId,
        session_id: sessionId,
        customer_name: customerName || undefined,
        customer_phone: customerPhone || undefined,
      }) as unknown as { reply?: string; response?: string };
      const botMsg: FloatingChatMessage = {
        id: `msg-${Date.now() + 1}`,
        text: data.reply || data.response || "Maaf kijiye, abhi kuch gadbad ho raha hai.",
        sender: "bot",
        timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
      setConnected(true);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now() + 1}`,
          text: "Connection cut gaya! Phir se try karo.",
          sender: "bot",
          timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
    setIsTyping(false);
  };

  const handleWelcomeSubmit = () => {
    if (customerName.trim() && customerPhone.trim()) {
      setShowWelcome(false);
      setConnected(true);
      sendMessage(`Hi, main ${customerName} hoon. Mujhe aapki help chahiye.`);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <AnimatePresence>
        {!open && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-gradient-to-br from-gold-400 to-gold-500 rounded-full flex items-center justify-center shadow-gold-lg cursor-pointer"
            aria-label="Open chat"
          >
            <span className="text-white text-2xl">💬</span>
            {!connected && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-success-500 rounded-full border-2 border-surface-50" />
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed bottom-6 right-6 z-50 w-80 sm:w-96 bg-surface-50 rounded-2xl shadow-2xl border border-surface-200 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-gold-500 to-gold-600 px-4 py-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-white font-bold text-sm">
                ✦
              </div>
              <div className="flex-1">
                <h4 className="text-white font-semibold text-sm">AI Assistant</h4>
                <p className="text-white/70 text-xs">
                  {connected ? "Online" : "Connecting..."}
                </p>
              </div>
              <button onClick={() => setOpen(false)} className="text-white/70 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Messages */}
            <div className="h-72 overflow-y-auto p-4 space-y-3 bg-[#f0f0f0]">
              {showWelcome && (
                <div className="bg-white rounded-2xl rounded-tl-none p-4 shadow-sm">
                  <h4 className="font-semibold text-surface-800 mb-3 text-sm">Namaste! 👋</h4>
                  <p className="text-xs text-surface-500 mb-3">Main aapka AI business assistant hoon. Bataiye kaunse mein madad chahiye?</p>
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      placeholder="Aapka naam"
                      className="w-full px-3 py-2 rounded-lg bg-surface-100 border border-surface-200 text-sm text-surface-800 placeholder:text-surface-400 focus:outline-none focus:border-gold-400"
                    />
                    <input
                      type="tel"
                      value={customerPhone}
                      onChange={(e) => setCustomerPhone(e.target.value)}
                      placeholder="Phone number"
                      className="w-full px-3 py-2 rounded-lg bg-surface-100 border border-surface-200 text-sm text-surface-800 placeholder:text-surface-400 focus:outline-none focus:border-gold-400"
                    />
                    <button
                      onClick={handleWelcomeSubmit}
                      disabled={!customerName.trim() || !customerPhone.trim()}
                      className="w-full py-2 rounded-lg bg-gold-500 text-white text-sm font-medium hover:bg-gold-600 disabled:opacity-40 transition-colors"
                    >
                      Start Chatting →
                    </button>
                  </div>
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] px-3 py-2 rounded-lg text-xs ${msg.sender === "user"
                    ? "bg-gold-500 text-white rounded-br-none"
                    : "bg-white text-surface-800 rounded-bl-none border border-surface-100"
                  }`}>
                    {msg.text}
                    <span className={`text-[10px] mt-1 block ${msg.sender === "user" ? "text-white/60" : "text-surface-400"}`}>
                      {msg.timestamp}
                    </span>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white px-3 py-2 rounded-lg rounded-tl-none border border-surface-100">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1.5 h-1.5 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1.5 h-1.5 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            {connected && (
              <div className="p-3 border-t border-surface-200 bg-surface-50">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); }
                    }}
                    placeholder="Message type karo..."
                    className="flex-1 px-3 py-2 rounded-full bg-white border border-surface-200 text-sm text-surface-800 placeholder:text-surface-400 focus:outline-none focus:border-gold-400"
                    disabled={isTyping}
                  />
                  <button
                    onClick={() => sendMessage(input)}
                    disabled={!input.trim() || isTyping}
                    className="w-9 h-9 rounded-full bg-gold-500 hover:bg-gold-600 disabled:bg-surface-300 flex items-center justify-center transition-colors"
                  >
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}