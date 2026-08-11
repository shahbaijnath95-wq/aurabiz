"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { segments } from "@/lib/api";
import type { Segment, SegmentRule } from "@/lib/types";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function SegmentsPage() {
  const router = useRouter();
  const { user, business, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const [segmentList, setSegmentList] = useState<Segment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: "", description: "", segment_type: "dynamic",
    rules: [{ field: "total_spent", operator: "gte", value: "1000" }],
  });

  const businessId = business?.id || "";

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
    if (businessId) loadSegments();
  }, [authLoading, user, businessId]);

  async function loadSegments() {
    try {
      const data = await segments.list(businessId);
      setSegmentList(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await segments.create({
        ...form,
        business_id: businessId,
        rules: JSON.stringify(form.rules),
      });
      setShowCreate(false);
      loadSegments();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Create fail ho gaya", "error"); }
  }

  function addRule() {
    setForm({ ...form, rules: [...form.rules, { field: "total_orders", operator: "gte", value: "5" }] });
  }

  function removeRule(idx: number) {
    setForm({ ...form, rules: form.rules.filter((_, i) => i !== idx) });
  }

  function updateRule(idx: number, key: string, value: string) {
    const rules = [...form.rules];
    rules[idx] = { ...rules[idx], [key]: value };
    setForm({ ...form, rules });
  }

  async function handleRefresh(segmentId: string) {
    try {
      await segments.refresh(segmentId);
      loadSegments();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Refresh fail ho gaya", "error"); }
  }

  async function handleAutoSegments() {
    try {
      await segments.auto(businessId);
      loadSegments();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Auto segments fail ho gaya", "error"); }
  }

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Customer Segments</h1>
        <div className="flex gap-2">
          <button onClick={handleAutoSegments} className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600">
            Auto-Segment
          </button>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600">
            + Create Segment
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold mb-3">New Segment</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                placeholder="Segment name" className="px-3 py-2 border rounded-lg" required />
              <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
                placeholder="Description" className="px-3 py-2 border rounded-lg" />
              <select value={form.segment_type} onChange={e => setForm({ ...form, segment_type: e.target.value })}
                className="px-3 py-2 border rounded-lg">
                <option value="dynamic">Dynamic</option>
                <option value="static">Static</option>
              </select>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Rules</p>
              {form.rules.map((rule, idx) => (
                <div key={idx} className="flex gap-2 mb-2">
                  <select value={rule.field} onChange={e => updateRule(idx, "field", e.target.value)}
                    className="px-2 py-1 border rounded text-sm">
                    <option value="total_spent">Total Spent</option>
                    <option value="total_orders">Total Orders</option>
                    <option value="lifecycle_stage">Lifecycle Stage</option>
                    <option value="tags">Tags</option>
                  </select>
                  <select value={rule.operator} onChange={e => updateRule(idx, "operator", e.target.value)}
                    className="px-2 py-1 border rounded text-sm">
                    <option value="gte">{">="}</option>
                    <option value="lte">{"<="}</option>
                    <option value="eq">{"="}</option>
                    <option value="contains">Contains</option>
                  </select>
                  <input value={rule.value} onChange={e => updateRule(idx, "value", e.target.value)}
                    placeholder="Value" className="px-2 py-1 border rounded text-sm w-32" />
                  <button type="button" onClick={() => removeRule(idx)} className="text-red-500 text-sm">X</button>
                </div>
              ))}
              <button type="button" onClick={addRule} className="text-sm text-blue-500 hover:underline">+ Add Rule</button>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded-lg">Create</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-200 rounded-lg">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : segmentList.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-400">No segments yet. Create your first segment or use Auto-Segment!</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {segmentList.map((seg) => (
            <div key={seg.id} className="bg-white rounded-xl border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{seg.name}</h3>
                  <p className="text-sm text-gray-500">{seg.description || "No description"}</p>
                  <div className="flex gap-3 mt-1 text-xs text-gray-400">
                    <span>{seg.customer_count || 0} customers</span>
                    <span>•</span>
                    <span>{seg.segment_type}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleRefresh(seg.id)}
                    className="px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100">
                    Refresh
                  </button>
                  <button onClick={() => { if (confirm("Delete segment?")) segments.delete(seg.id).then(loadSegments); }}
                    className="px-3 py-1 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
    </div></div>
  );
}
