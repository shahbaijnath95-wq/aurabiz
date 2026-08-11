"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Settings } from "lucide-react";

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getIntegrations();
      setIntegrations(data.integrations || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await masterAPI.toggleIntegration(id, enabled);
      toast.success(enabled ? "Integration enabled" : "Integration disabled");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold inline-flex items-center gap-2 mb-4">
        <Settings size={24} /> Integrations
      </h1>

      <p className="text-sm text-gray-500 mb-4">
        Enable/disable third-party integrations. Per-tenant configuration available in their dashboard.
      </p>

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : integrations.length === 0 ? (
        <div className="text-gray-400 text-sm">No integrations available</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {integrations.map((i) => (
            <div key={i.id} className="bg-white rounded-xl shadow p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-bold">{i.name}</h3>
                  <p className="text-xs text-gray-500">{i.category}</p>
                </div>
                <button
                  onClick={() => handleToggle(i.id, !i.enabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    i.enabled ? "bg-green-600" : "bg-gray-300"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      i.enabled ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-2">{i.description}</p>
              <div className="flex justify-between items-center text-xs">
                <span className={`px-2 py-1 rounded-full font-medium ${
                  i.enabled ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                }`}>
                  {i.enabled ? "Enabled" : "Disabled"}
                </span>
                {i.price && (
                  <span className="text-gray-500">
                    {i.price === 0 ? "Free" : `₹${i.price}/mo`}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
        <h3 className="font-bold text-blue-900 mb-1">Available Integrations</h3>
        <p className="text-sm text-blue-700">
          Razorpay, PhonePe, Tally ERP, Google Business, Instagram, Zoho CRM, Shopify, WooCommerce,
          Salesforce, HubSpot, Google Sheets, Slack, Discord, Zapier.
        </p>
        <p className="text-xs text-blue-600 mt-2">
          💡 Sell add-on integrations at ₹499-999/mo per integration per tenant.
        </p>
      </div>
    </div>
  );
}
