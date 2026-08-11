"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import { Plus, Trash2, Edit, Save, Zap, Settings, ChevronDown, ChevronUp } from "lucide-react";
import toast from "react-hot-toast";

interface Provider {
  id: string;
  name: string;
  provider_key: string;
  model: string;
  is_active: boolean;
  priority: number;
  rate_limit_rpm: number;
  rate_limit_rpd: number;
  cost_per_1k_tokens: number;
  has_api_key: boolean;
}

interface OpenCodeModel {
  id: string;
  name: string;
  provider: string;
  max_tokens: number;
  speed: string;
  reasoning: boolean;
  cost: string;
  recommended: boolean;
  languages: string[];
}

interface OmniRouteConfig {
  omniroute: { url: string; enabled: boolean; require_api_key: boolean; description: string };
  opencode_models: OpenCodeModel[];
  default_model: string;
  fallback_chain: string[];
  settings: { max_tokens: number; temperature: number; timeout_seconds: number; max_retries: number };
}

export default function AIConfigPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "", provider_key: "", api_key: "", account_id: "",
    model: "", priority: 0, rate_limit_rpm: 50, rate_limit_rpd: 1500,
    cost_per_1k_tokens: 0, is_active: true,
  });

  // OmniRoute state
  const [omniConfig, setOmniConfig] = useState<OmniRouteConfig | null>(null);
  const [showOmniSettings, setShowOmniSettings] = useState(false);
  const [omniSettings, setOmniSettings] = useState({ max_tokens: 500, temperature: 0.7, timeout_seconds: 25, max_retries: 2 });
  const [defaultModel, setDefaultModel] = useState("");
  const [fallbackChain, setFallbackChain] = useState<string[]>([]);

  const load = async () => {
    try {
      const data = await masterAPI.getAIProviders();
      setProviders(data.providers);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadOmniConfig = async () => {
    try {
      const config: OmniRouteConfig = await masterAPI.request("/omniroute/config");
      setOmniConfig(config);
      setOmniSettings(config.settings || { max_tokens: 500, temperature: 0.7, timeout_seconds: 25, max_retries: 2 });
      setDefaultModel(config.default_model || "");
      setFallbackChain(config.fallback_chain || []);
    } catch (err) {
      console.error("Failed to load OmniRoute config:", err);
    }
  };

  useEffect(() => { load(); loadOmniConfig(); }, []);

  const resetForm = () => {
    setForm({ name: "", provider_key: "", api_key: "", account_id: "", model: "", priority: 0, rate_limit_rpm: 50, rate_limit_rpd: 1500, cost_per_1k_tokens: 0, is_active: true });
    setEditId(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editId) {
        await masterAPI.updateAIProvider(editId, form);
        toast.success("Provider updated");
      } else {
        await masterAPI.createAIProvider(form);
        toast.success("Provider created");
      }
      resetForm();
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleEdit = async (p: Provider) => {
    try {
      const full = await masterAPI.request(`/admin/ai-providers/${p.id}`);
      setForm(full);
      setEditId(p.id);
      setShowForm(true);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await masterAPI.deleteAIProvider(id);
      toast.success("Deleted");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleSetDefaultModel = async (modelId: string) => {
    try {
      await masterAPI.request("/omniroute/default-model", { method: "PUT", body: { model_id: modelId } });
      setDefaultModel(modelId);
      toast.success(`Default model: ${modelId}`);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleToggleFallback = async (modelId: string) => {
    const newChain = fallbackChain.includes(modelId)
      ? fallbackChain.filter((m) => m !== modelId)
      : [...fallbackChain, modelId];
    try {
      await masterAPI.request("/omniroute/fallback-chain", { method: "PUT", body: { chain: newChain } });
      setFallbackChain(newChain);
      toast.success("Fallback chain updated");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleSaveSettings = async () => {
    try {
      await masterAPI.request("/omniroute/settings", { method: "PUT", body: omniSettings });
      toast.success("Settings saved");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const speedColor = (speed: string) => {
    if (speed === "fast") return "text-green-600 bg-green-50";
    if (speed === "medium") return "text-yellow-600 bg-yellow-50";
    return "text-red-600 bg-red-50";
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* OmniRoute Section */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl shadow-lg p-6 mb-8 border border-purple-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="bg-purple-600 text-white p-2 rounded-lg"><Zap size={20} /></div>
            <div>
              <h2 className="text-xl font-bold text-purple-900">OmniRoute AI Gateway</h2>
              <p className="text-sm text-purple-600">305+ models, 50+ free tiers — Configure OpenCode free models</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${omniConfig?.omniroute?.enabled ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
              {omniConfig?.omniroute?.enabled ? "Connected" : "Disconnected"}
            </span>
            <button onClick={() => setShowOmniSettings(!showOmniSettings)} className="p-2 rounded-lg hover:bg-purple-100">
              <Settings size={18} className="text-purple-600" />
            </button>
          </div>
        </div>

        {/* OmniRoute Settings */}
        {showOmniSettings && (
          <div className="bg-white rounded-lg p-4 mb-4 border border-purple-100">
            <h3 className="font-semibold mb-3">Request Settings</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="text-xs text-gray-500">Max Tokens</label>
                <input type="number" value={omniSettings.max_tokens} onChange={(e) => setOmniSettings({ ...omniSettings, max_tokens: +e.target.value })} className="w-full border rounded px-2 py-1 text-sm" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Temperature</label>
                <input type="number" step="0.1" value={omniSettings.temperature} onChange={(e) => setOmniSettings({ ...omniSettings, temperature: +e.target.value })} className="w-full border rounded px-2 py-1 text-sm" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Timeout (sec)</label>
                <input type="number" value={omniSettings.timeout_seconds} onChange={(e) => setOmniSettings({ ...omniSettings, timeout_seconds: +e.target.value })} className="w-full border rounded px-2 py-1 text-sm" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Max Retries</label>
                <input type="number" value={omniSettings.max_retries} onChange={(e) => setOmniSettings({ ...omniSettings, max_retries: +e.target.value })} className="w-full border rounded px-2 py-1 text-sm" />
              </div>
            </div>
            <button onClick={handleSaveSettings} className="mt-3 bg-purple-600 text-white px-4 py-1.5 rounded-lg text-sm flex items-center gap-1">
              <Save size={14} /> Save Settings
            </button>
          </div>
        )}

        {/* Default Model */}
        <div className="mb-3">
          <label className="text-sm font-medium text-purple-800">Default Model:</label>
          <span className="ml-2 text-sm text-purple-600 font-mono">{defaultModel || "Not set"}</span>
        </div>

        {/* Fallback Chain */}
        <div className="mb-4">
          <label className="text-sm font-medium text-purple-800">Fallback Chain:</label>
          <div className="flex flex-wrap gap-1 mt-1">
            {fallbackChain.length === 0 && <span className="text-xs text-gray-400">No fallback configured</span>}
            {fallbackChain.map((m, i) => (
              <span key={m} className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs font-mono">
                {i + 1}. {m.split("/").pop()}
              </span>
            ))}
          </div>
        </div>

        {/* OpenCode Models Grid */}
        <h3 className="font-semibold text-purple-900 mb-3">Available OpenCode Free Models</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {omniConfig?.opencode_models?.map((model) => (
            <div key={model.id} className={`bg-white rounded-lg p-3 border transition-all hover:shadow-md ${defaultModel === model.id ? "border-purple-500 ring-2 ring-purple-200" : "border-gray-200"}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm text-gray-900">{model.name}</span>
                {model.recommended && <span className="bg-green-100 text-green-700 text-[10px] px-1.5 py-0.5 rounded font-medium">RECOMMENDED</span>}
              </div>
              <div className="text-xs text-gray-500 mb-2 font-mono">{model.id}</div>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${speedColor(model.speed)}`}>{model.speed}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">{(model.max_tokens / 1000).toFixed(0)}K</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-50 text-green-600">{model.cost}</span>
              </div>
              <div className="flex gap-1">
                <button onClick={() => handleSetDefaultModel(model.id)} className={`flex-1 text-[11px] py-1 rounded ${defaultModel === model.id ? "bg-purple-600 text-white" : "bg-purple-50 text-purple-700 hover:bg-purple-100"}`}>
                  {defaultModel === model.id ? "Active" : "Set Default"}
                </button>
                <button onClick={() => handleToggleFallback(model.id)} className={`flex-1 text-[11px] py-1 rounded ${fallbackChain.includes(model.id) ? "bg-blue-600 text-white" : "bg-blue-50 text-blue-700 hover:bg-blue-100"}`}>
                  {fallbackChain.includes(model.id) ? "In Chain" : "+ Fallback"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Original Provider Table */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">AI Provider Configuration</h1>
        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2"
        >
          <Plus size={16} /> Add Provider
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{editId ? "Edit" : "Add"} Provider</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider Key</label>
              <select value={form.provider_key} onChange={(e) => setForm({ ...form, provider_key: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" required>
                <option value="">Select...</option>
                <option value="opencode">OpenCode Free AI (No API Key)</option>
                <option value="falcon">Falcon AI (via OpenRouter/HF)</option>
                <option value="cloudflare">Cloudflare Workers AI</option>
                <option value="gemini">Google Gemini</option>
                <option value="groq">Groq</option>
                <option value="openrouter">OpenRouter</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key {form.provider_key === "opencode" ? "(Not Required - Free)" : ""}</label>
              <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" required={form.provider_key !== "opencode"} placeholder={form.provider_key === "opencode" ? "free" : ""} />
            </div>
            {form.provider_key === "cloudflare" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Account ID</label>
                <input value={form.account_id} onChange={(e) => setForm({ ...form, account_id: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
              {form.provider_key === "opencode" ? (
                <select value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                  {omniConfig?.opencode_models?.map((m) => (
                    <option key={m.id} value={m.id}>{m.name} ({m.cost})</option>
                  ))}
                </select>
              ) : (
                <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="model-name" />
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority (lower = higher priority)</label>
              <input type="number" value={form.priority} onChange={(e) => setForm({ ...form, priority: +e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rate Limit (RPM)</label>
              <input type="number" value={form.rate_limit_rpm} onChange={(e) => setForm({ ...form, rate_limit_rpm: +e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rate Limit (RPD)</label>
              <input type="number" value={form.rate_limit_rpd} onChange={(e) => setForm({ ...form, rate_limit_rpd: +e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div className="md:col-span-2 flex gap-3">
              <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm flex items-center gap-2">
                <Save size={16} /> {editId ? "Update" : "Create"}
              </button>
              <button type="button" onClick={resetForm} className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg text-sm">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3">Name</th>
              <th className="text-left px-4 py-3">Provider</th>
              <th className="text-left px-4 py-3">Model</th>
              <th className="text-left px-4 py-3">Priority</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{p.name}</td>
                <td className="px-4 py-3"><span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">{p.provider_key}</span></td>
                <td className="px-4 py-3 font-mono text-xs">{p.model}</td>
                <td className="px-4 py-3">{p.priority}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${p.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                    {p.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-4 py-3 flex gap-1">
                  <button onClick={() => handleEdit(p)} className="p-1.5 rounded hover:bg-blue-50 text-blue-600"><Edit size={14} /></button>
                  <button onClick={() => handleDelete(p.id, p.name)} className="p-1.5 rounded hover:bg-red-50 text-red-600"><Trash2 size={14} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
