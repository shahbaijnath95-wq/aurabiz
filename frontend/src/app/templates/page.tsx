"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { templates as tplApi } from "@/lib/api";
import type { Template } from "@/lib/types";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", category: "MARKETING", body: "" });
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    tplApi.list()
      .then((data) => setTemplates(Array.isArray(data) ? data : []))
      .catch(() => toast("Templates load nahi ho paye", "error"))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    try {
      await tplApi.create(form);
      setShowAdd(false);
      setForm({ name: "", category: "MARKETING", body: "" });
      toast("Template ban gaya!", "success");
      const data = await tplApi.list();
      setTemplates(Array.isArray(data) ? data : []);
    } catch { toast("Template nahi bana", "error"); }
  };

  const handleDelete = async (id: string) => {
    try {
      await tplApi.delete(id);
      setTemplates((prev) => prev.filter((t) => t.id !== id));
      toast("Template delete ho gaya!", "success");
    } catch { toast("Delete nahi ho paya", "error"); }
  };

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">WhatsApp Templates</h1>
            <p className="text-gray-500">Pre-approved message templates manage karo</p>
          </div>
          <button onClick={() => setShowAdd(true)} className="btn-gold text-sm">+ Template Banao</button>
        </div>

        {showAdd && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-card mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Naya Template</h3>
            <div className="space-y-4">
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Template name" className="input-angel" />
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="input-angel">
                <option value="MARKETING">Marketing</option>
                <option value="UTILITY">Utility</option>
                <option value="AUTHENTICATION">Authentication</option>
              </select>
              <textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} rows={4} placeholder="Message body..." className="input-angel" />
              <div className="flex gap-3">
                <button onClick={() => setShowAdd(false)} className="btn-ghost text-sm">Cancel</button>
                <button onClick={handleCreate} className="btn-gold text-sm">Create Karo</button>
              </div>
            </div>
          </motion.div>
        )}

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            [1, 2, 3].map((i) => <div key={i} className="bg-white rounded-2xl p-6 animate-pulse h-48 shimmer" />)
          ) : templates.length === 0 ? (
            <div className="col-span-full bg-white rounded-2xl p-12 text-center text-gray-400 border border-gray-100 shadow-card">
              Abhi koi template nahi hai — pehla banao!
            </div>
          ) : (
            templates.map((t) => (
              <motion.div key={t.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-card card-hover">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{t.name}</h3>
                  <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-50 text-gray-500">{t.category}</span>
                </div>
                <p className="text-sm text-gray-600 mb-4 line-clamp-3">{t.body}</p>
                <button onClick={() => handleDelete(t.id)} className="text-red-500 hover:text-red-600 text-xs font-medium transition-colors">Delete</button>
              </motion.div>
            ))
          )}
        </div>
      </div>
    
        </div></div>
  );
}
