"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  BarChart3,
  IndianRupee,
  Users,
  Handshake,
  Package,
  ShoppingBag,
  Calendar,
  Ticket,
  Star,
  Megaphone,
  MessageSquareText,
  Inbox,
  Bot,
  BrainCircuit,
  Webhook,
  Plug,
  UserCog,
  Target,
  Clock,
  Download,
  ClipboardList,
  Settings,
  ChevronDown,
  ChevronRight,
  Search,
  LogOut,
  Sparkles,
  X,
} from "lucide-react";

// ─── Menu Items with Lucide Icons ───
const menuItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, section: "Main", badge: null },
  { href: "/analytics", label: "Analytics", icon: BarChart3, section: "Main", badge: null },
  { href: "/revenue", label: "Revenue", icon: IndianRupee, section: "Main", badge: null },
  { href: "/customer-portal", label: "Customers", icon: Users, section: "Main", badge: null },
  { href: "/wholesalers", label: "Wholesalers", icon: Handshake, section: "Main", badge: null },
  { href: "/dashboard/inventory", label: "Inventory", icon: Package, section: "Business", badge: null },
  { href: "/catalog", label: "Catalog", icon: ShoppingBag, section: "Business", badge: null },
  { href: "/admin/orders", label: "Orders", icon: ShoppingBag, section: "Business", badge: "3" },
  { href: "/admin/appointments", label: "Appointments", icon: Calendar, section: "Business", badge: null },
  { href: "/admin/coupons", label: "Coupons", icon: Ticket, section: "Business", badge: null },
  { href: "/admin/feedback", label: "Feedback", icon: Star, section: "Business", badge: null },
  { href: "/admin/broadcast", label: "Broadcast", icon: Megaphone, section: "WhatsApp", badge: null },
  { href: "/templates", label: "Templates", icon: MessageSquareText, section: "WhatsApp", badge: null },
  { href: "/admin/inbox", label: "Inbox", icon: Inbox, section: "WhatsApp", badge: "12" },
  { href: "/admin/whatsapp", label: "WhatsApp Bot", icon: Bot, section: "WhatsApp", badge: "Live" },
  { href: "/ai-training", label: "AI Training", icon: BrainCircuit, section: "WhatsApp", badge: null },
  { href: "/webhooks", label: "Webhooks", icon: Webhook, section: "Tools", badge: null },
  { href: "/integrations", label: "Integrations", icon: Plug, section: "Tools", badge: null },
  { href: "/teams", label: "Teams", icon: UserCog, section: "Tools", badge: null },
  { href: "/segments", label: "Segments", icon: Target, section: "Tools", badge: null },
  { href: "/scheduled-messages", label: "Scheduled", icon: Clock, section: "Tools", badge: null },
  { href: "/exports", label: "Data Export", icon: Download, section: "Tools", badge: null },
  { href: "/followups", label: "Follow-ups", icon: ClipboardList, section: "Tools", badge: null },
  { href: "/audit", label: "Audit Log", icon: ClipboardList, section: "Tools", badge: null },
  { href: "/admin", label: "Admin", icon: Settings, section: "Settings", badge: null },
  { href: "/admin/settings", label: "Settings", icon: Settings, section: "Settings", badge: null },
];

const sectionOrder = ["Main", "Business", "WhatsApp", "Tools", "Settings"];
const sectionIcons: Record<string, typeof LayoutDashboard> = {
  Main: LayoutDashboard,
  Business: ShoppingBag,
  WhatsApp: MessageSquareText,
  Tools: Plug,
  Settings: Settings,
};

export default function Sidebar() {
  const pathname = usePathname();
  const { user, business, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(
    Object.fromEntries(sectionOrder.map((s) => [s, true]))
  );

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const filteredItems = searchQuery
    ? menuItems.filter((i) => i.label.toLowerCase().includes(searchQuery.toLowerCase()))
    : menuItems;

  const sections = searchQuery
    ? [...new Set(filteredItems.map((i) => i.section))]
    : sectionOrder;

  return (
    <>
      {/* ── Mobile hamburger ── */}
      <motion.button
        whileTap={{ scale: 0.95 }}
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 bg-white rounded-xl shadow-lg border border-surface-200 hover:bg-surface-50 transition-colors"
        aria-label="Open menu"
      >
        <svg className="w-5 h-5 text-surface-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </motion.button>

      {/* ── Mobile overlay ── */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* ── Sidebar ── */}
      <aside
        className={`fixed lg:sticky top-0 left-0 z-50 lg:z-auto w-[260px] bg-gradient-to-b from-[#1a1a2e] via-[#16213e] to-[#0f3460] flex flex-col h-screen transition-transform duration-300 shadow-2xl ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* ── Logo ── */}
        <div className="p-4 border-b border-white/10 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3" onClick={() => setMobileOpen(false)}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-gold-400 to-amber-500 flex items-center justify-center shadow-lg shadow-gold-500/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-extrabold text-white text-sm tracking-tight">AuraBiz</h1>
              <p className="text-[10px] text-white/40">AI Business Assistant</p>
            </div>
          </Link>
          <motion.button whileTap={{ scale: 0.9 }} onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-white/10 text-white/50 hover:text-white">
            <X className="w-5 h-5" />
          </motion.button>
        </div>

        {/* ── Search ── */}
        <div className="px-3 pt-3 pb-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Menu search karo..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white/80 text-xs placeholder:text-white/30 focus:outline-none focus:border-gold-400/50 focus:bg-white/10 transition-all"
            />
          </div>
        </div>

        {/* ── Menu ── */}
        <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-1 scrollbar-thin">
          {sections.map((section) => {
            const items = filteredItems.filter((i) => i.section === section);
            if (items.length === 0) return null;
            const isExpanded = expandedSections[section] !== false;
            const SectionIcon = sectionIcons[section] || LayoutDashboard;

            return (
              <div key={section} className="mb-1">
                {/* Section Header */}
                {!searchQuery && (
                  <button
                    onClick={() => toggleSection(section)}
                    className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-white/5 transition-colors group"
                  >
                    <div className="flex items-center gap-2">
                      <SectionIcon className="w-3.5 h-3.5 text-white/30" />
                      <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">{section}</span>
                    </div>
                    <motion.div animate={{ rotate: isExpanded ? 0 : -90 }} transition={{ duration: 0.2 }}>
                      <ChevronDown className="w-3 h-3 text-white/30" />
                    </motion.div>
                  </button>
                )}

                {/* Section Items */}
                <AnimatePresence initial={false}>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="space-y-0.5 overflow-hidden"
                    >
                      {items.map((menuItem) => {
                        const isActive =
                          pathname === menuItem.href ||
                          (menuItem.href !== "/dashboard" && pathname.startsWith(menuItem.href));
                        const Icon = menuItem.icon;

                        return (
                          <Link
                            key={menuItem.href}
                            href={menuItem.href}
                            onClick={() => setMobileOpen(false)}
                            className={`relative flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] font-medium transition-all group ${
                              isActive
                                ? "bg-gradient-to-r from-gold-400/20 to-amber-500/10 text-gold-400"
                                : "text-white/60 hover:bg-white/5 hover:text-white/90"
                            }`}
                          >
                            {/* Active indicator */}
                            {isActive && (
                              <motion.div
                                layoutId="activeIndicator"
                                className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-gold-400"
                                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                              />
                            )}
                            <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-gold-400" : "text-white/40 group-hover:text-white/70"}`} />
                            <span className="truncate">{menuItem.label}</span>
                            {menuItem.badge && (
                              <span className={`ml-auto px-1.5 py-0.5 rounded-md text-[9px] font-bold ${
                                menuItem.badge === "Live"
                                  ? "bg-success-500/20 text-success-400 animate-pulse"
                                  : "bg-white/10 text-white/50"
                              }`}>
                                {menuItem.badge}
                              </span>
                            )}
                            {isActive && (
                              <ChevronRight className="w-3 h-3 ml-auto text-gold-400/60" />
                            )}
                          </Link>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </nav>

        {/* ── User Card ── */}
        <div className="p-3 border-t border-white/10">
          <div className="flex items-center gap-3 bg-white/5 rounded-xl p-2.5 hover:bg-white/8 transition-colors">
            <div className="relative">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gold-400 to-amber-500 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-gold-500/20">
                {user?.full_name?.charAt(0) || "A"}
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-success-500 rounded-full border-2 border-[#1a1a2e]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.full_name || "User"}</p>
              <p className="text-[10px] text-white/40 truncate">{business?.name || "Business"}</p>
            </div>
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={logout}
              className="p-1.5 rounded-lg text-white/30 hover:text-red-400 hover:bg-white/5 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </motion.button>
          </div>
          {/* Version */}
          <p className="text-center text-[9px] text-white/20 mt-2">AuraBiz v1.0.0</p>
        </div>
      </aside>
    </>
  );
}
