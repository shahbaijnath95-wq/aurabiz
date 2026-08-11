"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import { Users, MessageSquare, Bot, Activity } from "lucide-react";

interface Overview {
  total_tenants: number;
  active_tenants: number;
  suspended_tenants: number;
  total_messages_this_month: number;
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    masterAPI.getAnalyticsOverview()
      .then(setOverview)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse text-gray-400">Loading...</div>;
  if (!overview) return <div className="text-red-500">Failed to load</div>;

  const cards = [
    { label: "Total Tenants", value: overview.total_tenants, icon: Users, color: "bg-blue-500" },
    { label: "Active Tenants", value: overview.active_tenants, icon: Activity, color: "bg-green-500" },
    { label: "Suspended", value: overview.suspended_tenants, icon: Bot, color: "bg-red-500" },
    { label: "Messages (Month)", value: overview.total_messages_this_month, icon: MessageSquare, color: "bg-purple-500" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl shadow p-4">
            <div className="flex items-center gap-3">
              <div className={`${color} text-white p-2 rounded-lg`}>
                <Icon size={20} />
              </div>
              <div>
                <p className="text-2xl font-bold">{value ?? 0}</p>
                <p className="text-sm text-gray-500">{label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
