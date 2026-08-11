"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { Palette, Save } from "lucide-react";

export default function WhiteLabelPage() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getWhiteLabelConfigs();
      setConfigs(data.configs || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    if (!selected) return;
    try {
      await masterAPI.updateWhiteLabelConfig(selected.tenant_id, {
        logo_url: selected.logo_url,
        primary_color: selected.primary_color,
        domain: selected.domain,
        remove_branding: selected.remove_branding,
      });
      toast.success("White-label config saved");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold inline-flex items-center gap-2 mb-4">
        <Palette size={24} /> White-Label Customization
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          {loading ? (
            <div className="animate-pulse text-gray-400">Loading...</div>
          ) : configs.length === 0 ? (
            <div className="text-gray-400 text-sm">
              No white-label configs yet. Enterprise tenants will appear here.
            </div>
          ) : (
            <div className="space-y-2">
              {configs.map((c) => (
                <button
                  key={c.tenant_id}
                  onClick={() => setSelected(c)}
                  className={`w-full text-left bg-white rounded-xl shadow p-4 hover:shadow-md transition-shadow ${
                    selected?.tenant_id === c.tenant_id ? "ring-2 ring-blue-600" : ""
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{c.tenant_name}</p>
                      <p className="text-xs text-gray-500">{c.domain || "No custom domain"}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      c.remove_branding ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-700"
                    }`}>
                      {c.remove_branding ? "White-labeled" : "Branded"}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {selected && (
          <div className="bg-white rounded-xl shadow p-4">
            <h3 className="font-bold mb-4">{selected.tenant_name} — Customization</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 uppercase">Logo URL</label>
                <input
                  type="url"
                  value={selected.logo_url || ""}
                  onChange={(e) => setSelected({ ...selected, logo_url: e.target.value })}
                  className="border rounded px-3 py-2 text-sm w-full mt-1"
                  placeholder="https://example.com/logo.png"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 uppercase">Primary Color</label>
                <div className="flex gap-2 mt-1">
                  <input
                    type="color"
                    value={selected.primary_color || "#3B82F6"}
                    onChange={(e) => setSelected({ ...selected, primary_color: e.target.value })}
                    className="border rounded h-10 w-16"
                  />
                  <input
                    type="text"
                    value={selected.primary_color || ""}
                    onChange={(e) => setSelected({ ...selected, primary_color: e.target.value })}
                    className="border rounded px-3 py-2 text-sm flex-1"
                    placeholder="#3B82F6"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-500 uppercase">Custom Domain</label>
                <input
                  type="text"
                  value={selected.domain || ""}
                  onChange={(e) => setSelected({ ...selected, domain: e.target.value })}
                  className="border rounded px-3 py-2 text-sm w-full mt-1"
                  placeholder="priya-salon.yourplatform.com"
                />
              </div>
              <label className="flex items-center gap-2 text-sm bg-gray-50 p-3 rounded">
                <input
                  type="checkbox"
                  checked={selected.remove_branding ?? false}
                  onChange={(e) => setSelected({ ...selected, remove_branding: e.target.checked })}
                />
                <div>
                  <p className="font-medium">Remove "Powered by" branding</p>
                  <p className="text-xs text-gray-500">Enterprise tier only (₹2,999/mo)</p>
                </div>
              </label>
              <button
                onClick={handleSave}
                className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm w-full inline-flex items-center justify-center gap-1 hover:bg-blue-700"
              >
                <Save size={14} /> Save Changes
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
