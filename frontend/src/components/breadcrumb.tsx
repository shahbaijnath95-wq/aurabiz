"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// ============================================================
// BREADCRUMB — Automatic breadcrumb navigation
// ============================================================

interface BreadcrumbItem {
  label: string;
  href?: string;
}

const PATH_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  admin: "Admin",
  inbox: "Inbox",
  orders: "Orders",
  settings: "Settings",
  whatsapp: "WhatsApp Bot",
  appointments: "Appointments",
  coupons: "Coupons",
  feedback: "Feedback",
  broadcast: "Broadcast",
  inventory: "Inventory",
  catalog: "Catalog",
  analytics: "Analytics",
  revenue: "Revenue",
  teams: "Teams",
  segments: "Segments",
  "scheduled-messages": "Scheduled",
  exports: "Data Export",
  followups: "Follow-ups",
  audit: "Audit Log",
  webhooks: "Webhooks",
  integrations: "Integrations",
  templates: "Templates",
  chat: "Chat",
  pay: "Payment",
  login: "Login",
  register: "Register",
  setup: "Setup",
  "customer-portal": "Customers",
  loyalty: "Loyalty",
};

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  className?: string;
}

export default function Breadcrumb({ items, className = "" }: BreadcrumbProps) {
  const pathname = usePathname();

  // Auto-generate breadcrumbs from pathname if items not provided
  const breadcrumbs = items || generateBreadcrumbs(pathname);

  if (breadcrumbs.length <= 1) return null;

  return (
    <nav className={`flex items-center gap-1.5 text-sm ${className}`} aria-label="Breadcrumb">
      {breadcrumbs.map((item, index) => (
        <div key={index} className="flex items-center gap-1.5">
          {index > 0 && (
            <span className="text-gray-300">/</span>
          )}
          {item.href && index < breadcrumbs.length - 1 ? (
            <Link
              href={item.href}
              className="text-gray-500 hover:text-amber-600 transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            <span className={index === breadcrumbs.length - 1 ? "text-gray-900 font-medium" : "text-gray-500"}>
              {item.label}
            </span>
          )}
        </div>
      ))}
    </nav>
  );
}

function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean);
  const items: BreadcrumbItem[] = [
    { label: "Home", href: "/dashboard" },
  ];

  let currentPath = "";
  segments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const label = PATH_LABELS[segment] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, " ");

    if (index < segments.length - 1) {
      items.push({ label, href: currentPath });
    } else {
      items.push({ label });
    }
  });

  return items;
}

// ============================================================
// PAGE HEADER — Title + Breadcrumb + Actions
// ============================================================

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumb?: BreadcrumbItem[];
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, breadcrumb, actions, className = "" }: PageHeaderProps) {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 ${className}`}>
      <div>
        {breadcrumb && <Breadcrumb items={breadcrumb} className="mb-2" />}
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {description && (
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}
