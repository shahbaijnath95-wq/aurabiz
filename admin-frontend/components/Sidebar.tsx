"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard,
  Users,
  Bot,
  BarChart3,
  IndianRupee,
  LogOut,
  Shield,
  Bell,
  LifeBuoy,
  UserCog,
  Key,
  Webhook,
  Activity,
  Flag,
  Database,
  Settings,
  Palette,
  Users2,
  KeyRound,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/tenants", label: "Tenants", icon: Users },
  { href: "/licenses", label: "Licenses", icon: KeyRound },
  { href: "/ai-config", label: "AI Config", icon: Bot },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/billing", label: "Billing", icon: IndianRupee },
];

const NAV_ADMIN = [
  { href: "/audit", label: "Audit Log", icon: Shield },
  { href: "/team", label: "Team", icon: UserCog },
  { href: "/api-keys", label: "API Keys", icon: Key },
  { href: "/feature-flags", label: "Feature Flags", icon: Flag },
];

const NAV_OPS = [
  { href: "/whatsapp-monitor", label: "WhatsApp Monitor", icon: Activity },
  { href: "/support", label: "Support", icon: LifeBuoy },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/webhooks", label: "Webhooks", icon: Webhook },
  { href: "/backups", label: "Backups", icon: Database },
  { href: "/system-health", label: "System Health", icon: Activity },
];

const NAV_GROWTH = [
  { href: "/resellers", label: "Resellers", icon: Users2 },
  { href: "/white-label", label: "White-Label", icon: Palette },
  { href: "/integrations", label: "Integrations", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { admin, logout } = useAuth();

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === href;
    return pathname.startsWith(href);
  };

  const Section = ({ title, items }: { title: string; items: typeof NAV_ITEMS }) => (
    <div className="mb-2">
      <p className="px-3 py-1 text-xs uppercase text-gray-500 font-semibold">{title}</p>
      {items.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
            isActive(href)
              ? "bg-blue-600 text-white"
              : "text-gray-300 hover:bg-gray-800"
          }`}
        >
          <Icon size={18} />
          {label}
        </Link>
      ))}
    </div>
  );

  return (
    <aside className="w-64 bg-gradient-to-b from-slate-900 via-slate-900 to-blue-900 text-white min-h-screen flex flex-col overflow-y-auto shadow-xl shrink-0">
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
            <Bot size={20} />
          </div>
          <div>
            <h1 className="text-base font-bold leading-tight">AuraBiz Admin</h1>
            <p className="text-[11px] text-white/50">Platform Control</p>
          </div>
        </div>
        {admin && <p className="text-[11px] text-white/40 mt-2 truncate">{admin.email}</p>}
      </div>
      <nav className="flex-1 p-2">
        <Section title="Main" items={NAV_ITEMS} />
        <Section title="Administration" items={NAV_ADMIN} />
        <Section title="Operations" items={NAV_OPS} />
        <Section title="Growth" items={NAV_GROWTH} />
      </nav>
      <div className="p-3 border-t border-white/10">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-white/60 hover:bg-white/10 hover:text-white w-full transition-colors"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
}
