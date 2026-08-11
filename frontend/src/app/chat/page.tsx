"use client";

import { Suspense, useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  text: string;
  sender: "user" | "bot";
  timestamp: string;
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="h-screen flex items-center justify-center bg-[#efeae2]"><p className="text-gray-500">Loading chat...</p></div>}>
      <ChatContent />
    </Suspense>
  );
}

function ChatContent() {
  const searchParams = useSearchParams();
  const businessId = searchParams.get("business") || "demo-business";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [showWelcome, setShowWelcome] = useState(true);
  const [connected, setConnected] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      text: text.trim(),
      sender: "user",
      timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const { chat } = await import("@/lib/api");
      const data = await chat.send({
        message: text.trim(),
        business_id: businessId,
        session_id: sessionId,
        customer_name: customerName || undefined,
        customer_phone: customerPhone || undefined,
      }) as unknown as { reply?: string; response?: string };

      const botMsg: Message = {
        id: `msg-${Date.now() + 1}`,
        text: data.reply || data.response || "Maaf kijiye, abhi kuch gadbad ho raha hai. Phir se try karo.",
        sender: "bot",
        timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now() + 1}`,
          text: "Connection cut gaya! Internet check karo aur phir bhejo.",
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
      setTimeout(() => {
        sendMessage(`Hi, main ${customerName} hoon. Mujhe aapki services ke baare mein jaanna hai.`);
      }, 500);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-[#efeae2]">
      {/* Header - WhatsApp style green */}
      <div className="bg-[#075e54] text-white px-4 py-3 flex items-center gap-3 shadow-md">
        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-lg font-bold">
          {businessId.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1">
          <h1 className="font-semibold text-sm">{businessId.replace(/-/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())}</h1>
          <p className="text-[11px] text-white/70">{connected ? "online" : "connecting..."}</p>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
        </div>
      </div>

      {/* Welcome Screen */}
      <AnimatePresence>
        {showWelcome && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-[#efeae2] z-50 flex items-center justify-center p-6"
          >
            <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-lg">
              <div className="text-center mb-6">
                <div className="w-16 h-16 rounded-full bg-[#075e54] flex items-center justify-center text-white text-2xl font-bold mx-auto mb-3">
                  {businessId.charAt(0).toUpperCase()}
                </div>
                <h2 className="text-lg font-bold text-gray-900">Namaste!</h2>
                <p className="text-sm text-gray-500 mt-1">Baat shuru karne ke liye apni details bharo</p>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Aapka Naam</label>
                  <input
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="e.g. Rahul Sharma"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-[#25d366] focus:ring-1 focus:ring-[#25d366] transition-colors"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Phone Number</label>
                  <input
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="e.g. 9876543210"
                    type="tel"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-[#25d366] focus:ring-1 focus:ring-[#25d366] transition-colors"
                  />
                </div>
                <button
                  onClick={handleWelcomeSubmit}
                  disabled={!customerName.trim() || !customerPhone.trim()}
                  className="w-full py-3 rounded-xl bg-[#25d366] hover:bg-[#20ba5a] disabled:bg-gray-300 text-white font-semibold text-sm transition-colors mt-2"
                >
                  Start Chatting →
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Background Pattern */}
      <div className="flex-1 overflow-y-auto px-4 py-3" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c5bfb5' fill-opacity='0.15'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
      }}>
        {/* Messages */}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"} mb-3`}>
            <div
              className={`max-w-[80%] px-3 py-2 rounded-lg shadow-sm ${
                msg.sender === "user"
                  ? "bg-[#dcf8c6] rounded-tr-none"
                  : "bg-white rounded-tl-none"
              }`}
            >
              <p className="text-[13px] text-gray-800 leading-relaxed">{msg.text}</p>
              <p className="text-[10px] text-gray-400 text-right mt-0.5">{msg.timestamp}</p>
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start mb-3">
            <div className="bg-white px-4 py-3 rounded-lg rounded-tl-none shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Bar - WhatsApp style */}
      {connected && (
        <div className="bg-[#f0f0f0] px-3 py-2 flex items-center gap-2 border-t border-gray-200">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage(input);
              }
            }}
            placeholder="Message type karo..."
            className="flex-1 px-4 py-2.5 rounded-full bg-white text-sm border border-gray-200 focus:outline-none focus:border-[#25d366] transition-colors"
            disabled={isTyping}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isTyping}
            className="w-10 h-10 rounded-full bg-[#25d366] hover:bg-[#20ba5a] disabled:bg-gray-300 flex items-center justify-center transition-colors shadow-md"
          >
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </div>
      )}

      {/* Footer */}
      <div className="bg-[#f0f0f0] text-center py-1.5">
        <p className="text-[10px] text-gray-400">Powered by AI Business Assistant</p>
      </div>
    </div>
  );
}
