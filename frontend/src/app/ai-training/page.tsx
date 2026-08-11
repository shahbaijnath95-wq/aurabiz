"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { motion, AnimatePresence } from "framer-motion";
import {
  BrainCircuit, Target, MessageSquareText, Search, Plus, Trash2,
  Languages, Sparkles, Upload, Download, Play, BarChart3, Tag, Zap, BookOpen,
  AlertCircle, TrendingUp, Filter, X, RefreshCw, Wand2, Clock, Globe, FileText
} from "lucide-react";
import { request } from "@/lib/api";

interface TrainingEntry {
  query: string;
  query_hash: string;
  response: string;
  intent: string;
  language: string;
  weight: number;
  use_count: number;
  learned_at: string;
}

interface DetailedStats {
  total_learned: number;
  accuracy: number;
  total_use_count: number;
  intent_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  top_queries: TrainingEntry[];
}

const intentOptions = ["custom", "greeting", "price_inquiry", "order_intent", "complaint", "feedback", "product_inquiry"];
const languageOptions = [
  { value: "hi", label: "Hinglish / Hindi" },
  { value: "en", label: "English" },
  { value: "mr", label: "Marathi" },
];

const quickTemplates = [
  { query: "Dukan kab khulti hai?", response: "Dukan subah {{opening_time}} baje se {{closing_time}} baje tak khuli hai.", intent: "custom", language: "hi" },
  { query: "Price kitni hai?", response: "{{product_name}} ki price ₹{{price}} hai. Stock mein {{stock}} {{unit}} available hai.", intent: "price_inquiry", language: "hi" },
  { query: "Order kab deliver hoga?", response: "Order {{delivery_days}} din mein deliver ho jayega. Tracking link bhej deta hoon.", intent: "order_intent", language: "hi" },
  { query: "Return policy kya hai?", response: "{{return_days}} din mein return kar sakte hain — bill aur original packaging ke saath.", intent: "complaint", language: "hi" },
  { query: "Stock available hai?", response: "Haan ji, {{product_name}} available hai! Kitne chahiye?", intent: "product_inquiry", language: "hi" },
  { query: "Thank you!", response: "Aapka dhanyavaad, {{customer_name}} ji! Phir milenge. 🙏", intent: "feedback", language: "hi" },
];

const templateVariables = ["product_name", "price", "stock", "unit", "category", "customer_name", "business_name", "opening_time", "closing_time", "delivery_days", "return_days"];

export default function AITrainingDashboard() {
  const [stats, setStats] = useState<DetailedStats | null>(null);
  const [data, setData] = useState<TrainingEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterIntent, setFilterIntent] = useState("all");
  const [showFilters, setShowFilters] = useState(false);

  // Form State
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [language, setLanguage] = useState("hi");
  const [intent, setIntent] = useState("custom");
  const [weight, setWeight] = useState(5);

  // UI State
  const [activeTab, setActiveTab] = useState<"train" | "templates" | "analytics" | "knowledge">("train");
  const [testQuery, setTestQuery] = useState("");
  const [testResult, setTestResult] = useState<string | null>(null);
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [bulkText, setBulkText] = useState("");

  // Phase 1 New Features
  const [showImportChat, setShowImportChat] = useState(false);
  const [importLimit, setImportLimit] = useState(50);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<string | null>(null);
  const [showVarPicker, setShowVarPicker] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Phase 2: Knowledge Base + Translation
  const [kbQuery, setKbQuery] = useState("");
  const [kbResult, setKbResult] = useState<string | null>(null);
  const [kbLoading, setKbLoading] = useState(false);
  const [translateLang, setTranslateLang] = useState("en");
  const [translating, setTranslating] = useState(false);
  const [translateResult, setTranslateResult] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const statsJson = await request<any>("/trainer/stats/detailed");
      setStats(statsJson);
      const dataJson = await request<any>("/trainer/data");
      setData(dataJson?.data || (Array.isArray(dataJson) ? dataJson : []));
      setErrorMsg(null);
    } catch (e: any) {
      setErrorMsg(e.message || "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // Fetch suggestions when query changes
  useEffect(() => {
    if (query.trim().length < 5) { setSuggestions([]); return; }
    const timer = setTimeout(async () => {
      try {
        const result = await request<any>("/trainer/suggest", { method: "POST", body: JSON.stringify({ query, response: "", intent, language }) });
        setSuggestions(result?.suggestions || []);
        setShowSuggestions((result?.suggestions || []).length > 0);
      } catch { setSuggestions([]); }
    }, 600);
    return () => clearTimeout(timer);
  }, [query]);

  const handleDelete = async (hash: string) => {
    if (!confirm("Remove this memory?")) return;
    try { await request(`/trainer/entry/${hash}`, { method: "DELETE" }); fetchData(); } catch (e) { console.error(e); }
  };

  const handleManualTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await request("/trainer/learn", { method: "POST", body: JSON.stringify({ query, response, intent, language, weight }) });
      setQuery(""); setResponse(""); setWeight(5); setSuggestions([]); fetchData();
    } catch (e) { console.error(e); }
  };

  const handleTemplateUse = (template: typeof quickTemplates[0]) => {
    setQuery(template.query); setResponse(template.response);
    setIntent(template.intent); setLanguage(template.language); setActiveTab("train");
  };

  const insertVariable = (variable: string) => {
    setResponse(prev => prev + `{{${variable}}}`);
    setShowVarPicker(false);
  };

  const handleTest = async () => {
    if (!testQuery.trim()) return;
    setTestResult(null);
    try {
      const result = await request<any>("/trainer/test", { method: "POST", body: JSON.stringify({ query: testQuery, language }) });
      setTestResult(result?.response || result?.reply || "No response generated");
    } catch { setTestResult("Test failed — backend may not support this endpoint yet"); }
  };

  const handleImportChat = async () => {
    setImporting(true); setImportResult(null);
    try {
      const result = await request<any>("/trainer/import-chat", { method: "POST", body: JSON.stringify({ limit: importLimit }) });
      setImportResult(result?.message || `Imported ${result?.imported || 0} conversations`);
      fetchData();
    } catch { setImportResult("Import failed"); }
    setImporting(false);
  };

  const handleBulkUpload = async () => {
    if (!bulkText.trim()) return;
    const lines = bulkText.split("\n").filter(l => l.trim());
    let success = 0;
    for (const line of lines) {
      const parts = line.split("|").map(p => p.trim());
      if (parts.length >= 2) {
        try {
          await request("/trainer/learn", { method: "POST", body: JSON.stringify({ query: parts[0], response: parts[1], intent: parts[2] || "custom", language: parts[3] || "hi" }) });
          success++;
        } catch { /* skip */ }
      }
    }
    setBulkText(""); setShowBulkUpload(false); fetchData();
    alert(`${success} entries trained successfully!`);
  };

  const handleExport = () => {
    const csv = data.map(e => `"${e.query.replace(/"/g, '""')}","${e.response.replace(/"/g, '""')}","${e.intent}","${e.language}"`).join("\n");
    const blob = new Blob([`query,response,intent,language\n${csv}`], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "training_data.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  // Phase 2: AI-powered suggestions
  const handleAiSuggest = async () => {
    if (!query.trim()) return;
    setSuggestions([]); setShowSuggestions(true);
    try {
      const result = await request<any>("/trainer/suggest-ai", { method: "POST", body: JSON.stringify({ query, language, use_ai: true }) });
      setSuggestions(result?.suggestions || []);
    } catch { setSuggestions([]); }
  };

  // Phase 2: Knowledge Base Query
  const handleKbQuery = async () => {
    if (!kbQuery.trim()) return;
    setKbLoading(true); setKbResult(null);
    try {
      const result = await request<any>("/knowledge/query", { method: "POST", body: JSON.stringify({ query: kbQuery, top_k: 3 }) });
      setKbResult(result?.answer || "Koi jawab nahi mila — pehle knowledge base me document upload karo.");
    } catch { setKbResult("Knowledge base configured nahi hai."); }
    setKbLoading(false);
  };

  // Phase 2: Translate training data
  const handleTranslate = async () => {
    if (data.length === 0) return;
    setTranslating(true); setTranslateResult(null);
    try {
      const entries = data.slice(0, 10).map(e => ({ query: e.query, response: e.response, intent: e.intent }));
      const result = await request<any>("/trainer/translate-batch", { method: "POST", body: JSON.stringify({ entries, target_langs: [translateLang] }) });
      setTranslateResult(`${result?.count || 0} entries translate ho gaye!`);
      fetchData();
    } catch { setTranslateResult("Translate failed"); }
    setTranslating(false);
  };

  const filteredData = data.filter(entry => {
    const matchSearch = entry.query.toLowerCase().includes(searchQuery.toLowerCase()) || entry.response.toLowerCase().includes(searchQuery.toLowerCase());
    const matchIntent = filterIntent === "all" || entry.intent === filterIntent;
    return matchSearch && matchIntent;
  });

  // Auth guard
  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("token")) {
      window.location.href = "/login";
    }
  }, []);

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-surface-100 via-surface-50 to-amber-50/30">
      <Sidebar />
      <div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2.5 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl shadow-lg shadow-amber-500/20">
                <BrainCircuit className="w-7 h-7 text-white" />
              </div>
              <h1 className="text-3xl md:text-4xl font-extrabold text-surface-800">AI Training Hub</h1>
            </div>
            <p className="text-surface-500 text-sm max-w-lg">Falcon AI ko apna business sikho. Import from chat, use smart templates, aur analytics dekho.</p>
          </div>
          <div className="flex gap-3">
            <div className="bg-white px-5 py-3 rounded-2xl border border-surface-200 shadow-sm">
              <div className="flex items-center gap-2 text-surface-500 mb-1"><Target className="w-3.5 h-3.5" /><span className="text-xs">Memories</span></div>
              <div className="text-2xl font-black text-surface-800">{loading ? "..." : stats?.total_learned || data.length}</div>
            </div>
            <div className="bg-white px-5 py-3 rounded-2xl border border-surface-200 shadow-sm">
              <div className="flex items-center gap-2 text-emerald-500 mb-1"><TrendingUp className="w-3.5 h-3.5" /><span className="text-xs">Accuracy</span></div>
              <div className="text-2xl font-black text-emerald-500">{loading ? "..." : `${stats?.accuracy || 100}%`}</div>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 bg-white p-1.5 rounded-2xl border border-surface-200 shadow-sm w-fit flex-wrap">
          {[
            { id: "train" as const, label: "Train AI", icon: Plus },
            { id: "templates" as const, label: "Smart Templates", icon: BookOpen },
            { id: "knowledge" as const, label: "Knowledge Base", icon: FileText },
            { id: "analytics" as const, label: "Analytics", icon: BarChart3 },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                activeTab === tab.id ? "bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-md shadow-amber-500/25" : "text-surface-500 hover:text-surface-800 hover:bg-surface-100"
              }`}>
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </div>

        {/* Train Tab */}
        {activeTab === "train" && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="xl:col-span-1 space-y-6">
              {/* Import from Chat */}
              <div className="bg-white rounded-2xl p-6 border border-surface-200 shadow-sm">
                <div className="flex items-center gap-2 mb-4"><RefreshCw className="w-5 h-5 text-amber-500" /><h3 className="text-sm font-bold text-surface-800">Import from Chat History</h3></div>
                <p className="text-xs text-surface-500 mb-3">Past WhatsApp conversations se AI automatically seekhega.</p>
                <div className="flex gap-2 items-center mb-3">
                  <label className="text-xs text-surface-500">Messages:</label>
                  <input type="number" value={importLimit} onChange={e => setImportLimit(Number(e.target.value))} min={10} max={200}
                    className="w-20 px-2 py-1.5 rounded-lg border border-surface-200 text-xs text-center" />
                  <button onClick={handleImportChat} disabled={importing}
                    className="flex-1 py-2 rounded-xl bg-amber-50 text-amber-700 text-xs font-semibold hover:bg-amber-100 transition-colors disabled:opacity-50">
                    {importing ? "Importing..." : "Import & Learn"}
                  </button>
                </div>
                {importResult && <p className="text-xs text-emerald-600 bg-emerald-50 p-2 rounded-lg">{importResult}</p>}
              </div>

              {/* Form */}
              <div className="bg-white rounded-2xl p-6 border border-surface-200 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2"><Sparkles className="w-5 h-5 text-amber-500" /><h2 className="text-lg font-bold text-surface-800">Inject Knowledge</h2></div>
                  <div className="flex gap-2">
                    <button onClick={() => setShowBulkUpload(true)} className="p-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-surface-500" title="Bulk Upload"><Upload className="w-4 h-4" /></button>
                    <button onClick={handleExport} className="p-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-surface-500" title="Export CSV"><Download className="w-4 h-4" /></button>
                  </div>
                </div>
                <form onSubmit={handleManualTrain} className="space-y-4">
                  <div className="relative">
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="flex items-center gap-2 text-xs font-semibold text-surface-500"><MessageSquareText className="w-3.5 h-3.5" />Customer Query</label>
                      <button type="button" onClick={handleAiSuggest} className="text-xs text-violet-600 font-semibold hover:text-violet-700 flex items-center gap-1"><Wand2 className="w-3 h-3" /> AI Suggest</button>
                    </div>
                    <input value={query} onChange={e => setQuery(e.target.value)} required placeholder="e.g. Aaj dukan khuli hai?"
                      className="w-full bg-surface-50 border border-surface-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 transition-all" />
                    {/* AI Suggestions */}
                    <AnimatePresence>
                      {showSuggestions && suggestions.length > 0 && (
                        <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }}
                          className="absolute left-0 right-0 top-full mt-1 bg-white border border-amber-200 rounded-xl shadow-lg z-10 overflow-hidden">
                          <div className="px-3 py-2 bg-amber-50 border-b border-amber-100 flex items-center gap-1"><Wand2 className="w-3 h-3 text-amber-500" /><span className="text-xs font-semibold text-amber-700">AI Suggestions</span></div>
                          {suggestions.map((s, i) => (
                            <button key={i} type="button" onClick={() => { setResponse(s); setShowSuggestions(false); }}
                              className="w-full text-left px-3 py-2 text-xs text-surface-600 hover:bg-amber-50 border-b border-surface-100 last:border-0">{s}</button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  <div className="relative">
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="flex items-center gap-2 text-xs font-semibold text-surface-500"><BrainCircuit className="w-3.5 h-3.5" />AI Response</label>
                      <button type="button" onClick={() => setShowVarPicker(!showVarPicker)} className="text-xs text-amber-600 font-semibold hover:text-amber-700">+ Variables</button>
                    </div>
                    <textarea value={response} onChange={e => setResponse(e.target.value)} required rows={3} placeholder="e.g. Haan ji! {{product_name}} available hai."
                      className="w-full bg-surface-50 border border-surface-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 transition-all resize-none" />
                    <AnimatePresence>
                      {showVarPicker && (
                        <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }}
                          className="absolute left-0 right-0 top-full mt-1 bg-white border border-amber-200 rounded-xl shadow-lg z-10 p-3">
                          <p className="text-xs text-surface-500 mb-2">Variable click karo to response me add hoga:</p>
                          <div className="flex flex-wrap gap-1.5">
                            {templateVariables.map(v => (
                              <button key={v} type="button" onClick={() => insertVariable(v)}
                                className="px-2 py-1 rounded-lg bg-amber-50 text-amber-700 text-xs font-mono hover:bg-amber-100 transition-colors">{`{{${v}}}`}</button>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="flex items-center gap-2 text-xs font-semibold text-surface-500 mb-1.5"><Languages className="w-3.5 h-3.5" />Language</label>
                      <select value={language} onChange={e => setLanguage(e.target.value)} className="w-full bg-surface-50 border border-surface-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/50">
                        {languageOptions.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="flex items-center gap-2 text-xs font-semibold text-surface-500 mb-1.5"><Tag className="w-3.5 h-3.5" />Intent</label>
                      <select value={intent} onChange={e => setIntent(e.target.value)} className="w-full bg-surface-50 border border-surface-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/50">
                        {intentOptions.map(i => <option key={i} value={i}>{i.replace("_", " ")}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="flex items-center gap-2 text-xs font-semibold text-surface-500 mb-1.5"><Zap className="w-3.5 h-3.5" />Weight: {weight}</label>
                    <input type="range" min="1" max="10" value={weight} onChange={e => setWeight(Number(e.target.value))} className="w-full accent-amber-500" />
                  </div>
                  <button type="submit" className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold text-sm shadow-lg shadow-amber-500/25 hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2">
                    <Plus className="w-4 h-4" /> Train AI
                  </button>
                </form>
              </div>

              {/* Test Mode */}
              <div className="bg-white rounded-2xl p-6 border border-surface-200 shadow-sm">
                <div className="flex items-center gap-2 mb-4"><Play className="w-5 h-5 text-emerald-500" /><h3 className="text-sm font-bold text-surface-800">Test Mode</h3></div>
                <div className="flex gap-2">
                  <input value={testQuery} onChange={e => setTestQuery(e.target.value)} placeholder="Test query likho..." className="flex-1 bg-surface-50 border border-surface-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400/50" />
                  <button onClick={handleTest} className="px-4 py-2 rounded-xl bg-emerald-50 text-emerald-600 text-sm font-semibold hover:bg-emerald-100 transition-colors">Test</button>
                </div>
                {testResult && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-3 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-700">{testResult}</motion.div>
                )}
              </div>
            </motion.div>

            {/* Right: Memory Bank */}
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="xl:col-span-2">
              <div className="bg-white rounded-2xl border border-surface-200 shadow-sm overflow-hidden" style={{ height: "700px" }}>
                <div className="p-5 border-b border-surface-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-bold text-surface-800">Memory Bank</h2>
                    <span className="px-2.5 py-0.5 bg-surface-100 rounded-full text-xs font-semibold text-surface-500">{filteredData.length}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-surface-400" />
                      <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search..." className="w-44 bg-surface-50 border border-surface-200 rounded-full pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-amber-400/50" />
                    </div>
                    <button onClick={() => setShowFilters(!showFilters)} className={`p-2 rounded-lg transition-colors ${showFilters ? "bg-amber-100 text-amber-600" : "bg-surface-100 text-surface-400"}`}><Filter className="w-3.5 h-3.5" /></button>
                    <button onClick={handleTranslate} disabled={translating || data.length === 0} className="p-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-surface-500" title="Translate to other language"><Globe className="w-3.5 h-3.5" /></button>
                  </div>
                </div>
                <AnimatePresence>
                  {showFilters && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                      className="px-5 py-3 border-b border-surface-200 bg-surface-50 flex gap-2 flex-wrap overflow-hidden">
                      <button onClick={() => setFilterIntent("all")} className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${filterIntent === "all" ? "bg-amber-100 text-amber-700" : "bg-surface-100 text-surface-500"}`}>All</button>
                      {intentOptions.map(i => (<button key={i} onClick={() => setFilterIntent(i)} className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-colors ${filterIntent === i ? "bg-amber-100 text-amber-700" : "bg-surface-100 text-surface-500"}`}>{i.replace("_", " ")}</button>))}
                    </motion.div>
                  )}
                </AnimatePresence>
                <div className="flex-1 overflow-y-auto p-3 space-y-2" style={{ height: "calc(100% - 80px)" }}>
                  {errorMsg ? (<div className="h-full flex flex-col items-center justify-center text-red-500 space-y-3"><AlertCircle className="w-10 h-10" /><p className="text-sm font-medium">{errorMsg}</p></div>) :
                   loading ? (<div className="h-full flex items-center justify-center"><div className="w-8 h-8 border-4 border-amber-200 border-t-amber-500 rounded-full animate-spin" /></div>) :
                   filteredData.length === 0 ? (<div className="h-full flex flex-col items-center justify-center text-surface-400 space-y-3"><BrainCircuit className="w-12 h-12 opacity-20" /><p className="text-sm">No memories yet — start training!</p></div>) :
                   (<AnimatePresence>{filteredData.map(entry => (
                     <motion.div key={entry.query_hash} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
                       className="group p-4 bg-surface-50 hover:bg-amber-50/50 border border-surface-200 hover:border-amber-200 rounded-xl transition-all">
                       <div className="flex justify-between items-start gap-3 mb-2">
                         <div className="flex items-center gap-2 flex-wrap">
                           <span className="px-2 py-0.5 bg-amber-100 text-amber-700 border border-amber-200 rounded text-[10px] font-bold uppercase">{entry.language}</span>
                           <span className="px-2 py-0.5 bg-surface-100 text-surface-500 border border-surface-200 rounded text-[10px] font-bold capitalize">{entry.intent.replace("_", " ")}</span>
                           <span className="text-[10px] text-surface-400 flex items-center gap-1"><Target className="w-3 h-3" />{entry.use_count}</span>
                           <span className="text-[10px] text-surface-400 flex items-center gap-1"><Zap className="w-3 h-3" />W:{entry.weight}</span>
                         </div>
                         <button onClick={() => handleDelete(entry.query_hash)} className="text-surface-400 hover:text-red-500 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all"><Trash2 className="w-3.5 h-3.5" /></button>
                       </div>
                       <div className="space-y-2">
                         <div className="flex gap-2"><span className="font-bold text-surface-400 text-xs">Q:</span><p className="text-sm text-surface-700">{entry.query}</p></div>
                         <div className="flex gap-2"><span className="font-bold text-amber-500 text-xs">A:</span><p className="text-sm text-surface-600 bg-amber-50 p-2 rounded-lg border border-amber-100">{entry.response}</p></div>
                       </div>
                     </motion.div>
                   ))}</AnimatePresence>)}
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* Templates Tab */}
        {activeTab === "templates" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6 flex items-start gap-3">
              <Wand2 className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div><p className="text-sm font-semibold text-amber-800">Dynamic Templates</p><p className="text-xs text-amber-600">Templates me <code className="bg-amber-100 px-1 rounded">{"{{variable}}"}</code> use karo — AI automatically fill karega actual values se.</p></div>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {quickTemplates.map((t, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="p-5 bg-white rounded-2xl border border-surface-200 hover:border-amber-200 hover:shadow-lg transition-all group">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-[10px] font-bold capitalize">{t.intent.replace("_", " ")}</span>
                    <span className="text-[10px] text-surface-400">{t.language}</span>
                  </div>
                  <p className="text-sm font-medium text-surface-700 mb-1">Q: {t.query}</p>
                  <p className="text-xs text-surface-500 mb-4 font-mono bg-surface-50 p-2 rounded-lg">{t.response}</p>
                  <button onClick={() => handleTemplateUse(t)} className="w-full py-2 rounded-xl bg-amber-50 text-amber-700 text-xs font-semibold hover:bg-amber-100 transition-colors flex items-center justify-center gap-1">
                    <Plus className="w-3 h-3" /> Use Template
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Knowledge Base Tab */}
        {activeTab === "knowledge" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-surface-200 shadow-sm">
              <div className="flex items-center gap-2 mb-4"><FileText className="w-5 h-5 text-violet-500" /><h3 className="text-lg font-bold text-surface-800">Knowledge Base (RAG)</h3></div>
              <p className="text-sm text-surface-500 mb-4">Apne business documents upload karo — AI unhe padh kar customers ko jawab dega.</p>

              {/* Upload */}
              <div className="border-2 border-dashed border-surface-300 rounded-xl p-6 text-center mb-6 hover:border-violet-400 transition-colors">
                <Upload className="w-10 h-10 text-surface-400 mx-auto mb-3" />
                <p className="text-sm text-surface-600 mb-2">Document upload karo (PDF, DOCX, TXT)</p>
                <input type="file" accept=".pdf,.docx,.txt" className="block mx-auto text-sm" onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const formData = new FormData();
                  formData.append("file", file);
                  formData.append("title", file.name);
                  try {
                    const token = localStorage.getItem("token");
                    const res = await fetch("/api/v1/knowledge/upload", {
                      method: "POST",
                      headers: token ? { Authorization: `Bearer ${token}` } : {},
                      body: formData,
                    });
                    const data = await res.json();
                    alert(data?.message || "Upload complete!");
                  } catch {
                    alert("Upload failed");
                  }
                }} />
              </div>

              {/* Query */}
              <div className="flex gap-2 mb-4">
                <input value={kbQuery} onChange={e => setKbQuery(e.target.value)} placeholder="Knowledge base me search karo..."
                  className="flex-1 bg-surface-50 border border-surface-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400/50" />
                <button onClick={handleKbQuery} disabled={kbLoading} className="px-5 py-2.5 rounded-xl bg-violet-500 text-white text-sm font-semibold hover:bg-violet-600 transition-colors disabled:opacity-50">
                  {kbLoading ? "Searching..." : "Query"}
                </button>
              </div>

              {kbResult && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 rounded-xl bg-violet-50 border border-violet-200 text-sm text-violet-700">{kbResult}</motion.div>
              )}
            </div>

            {/* Translate Section */}
            <div className="bg-white rounded-2xl p-6 border border-surface-200 shadow-sm">
              <div className="flex items-center gap-2 mb-4"><Globe className="w-5 h-5 text-amber-500" /><h3 className="text-lg font-bold text-surface-800">Auto-Translate Training</h3></div>
              <p className="text-sm text-surface-500 mb-4">Apni training data ko automatically doosri bhasha me translate karo.</p>
              <div className="flex gap-2 items-center">
                <select value={translateLang} onChange={e => setTranslateLang(e.target.value)} className="px-3 py-2 rounded-xl border border-surface-200 text-sm">
                  <option value="en">English</option>
                  <option value="mr">Marathi</option>
                  <option value="gu">Gujarati</option>
                  <option value="ta">Tamil</option>
                </select>
                <button onClick={handleTranslate} disabled={translating || data.length === 0} className="px-5 py-2 rounded-xl bg-amber-50 text-amber-700 text-sm font-semibold hover:bg-amber-100 transition-colors disabled:opacity-50">
                  {translating ? "Translating..." : `Translate to ${translateLang.toUpperCase()}`}
                </button>
              </div>
              {translateResult && <p className="text-sm text-emerald-600 mt-3 bg-emerald-50 p-2 rounded-lg">{translateResult}</p>}
            </div>
          </motion.div>
        )}

        {/* Analytics Tab */}
        {activeTab === "analytics" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <div className="grid md:grid-cols-4 gap-6">
              <div className="p-6 bg-white rounded-2xl border border-surface-200 shadow-sm text-center">
                <BrainCircuit className="w-10 h-10 text-amber-500 mx-auto mb-3" />
                <div className="text-3xl font-black text-surface-800">{stats?.total_learned || data.length}</div>
                <div className="text-sm text-surface-500">Total Memories</div>
              </div>
              <div className="p-6 bg-white rounded-2xl border border-surface-200 shadow-sm text-center">
                <TrendingUp className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
                <div className="text-3xl font-black text-emerald-500">{stats?.accuracy || 100}%</div>
                <div className="text-sm text-surface-500">AI Accuracy</div>
              </div>
              <div className="p-6 bg-white rounded-2xl border border-surface-200 shadow-sm text-center">
                <Zap className="w-10 h-10 text-blue-500 mx-auto mb-3" />
                <div className="text-3xl font-black text-surface-800">{stats?.total_use_count || 0}</div>
                <div className="text-sm text-surface-500">Total Uses</div>
              </div>
              <div className="p-6 bg-white rounded-2xl border border-surface-200 shadow-sm text-center">
                <Clock className="w-10 h-10 text-violet-500 mx-auto mb-3" />
                <div className="text-3xl font-black text-surface-800">{Object.keys(stats?.intent_distribution || {}).length}</div>
                <div className="text-sm text-surface-500">Categories</div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Intent Distribution */}
              <div className="p-6 bg-white rounded-2xl border border-surface-200 shadow-sm">
                <h3 className="text-lg font-bold text-surface-800 mb-4">Intent Distribution</h3>
                <div className="space-y-3">
                  {Object.entries(stats?.intent_distribution || {}).map(([intent, count]) => {
                    const maxVal = Math.max(...Object.values(stats?.intent_distribution || {}), 1);
                    const pct = (count / maxVal) * 100;
                    return (
                      <div key={intent} className="flex items-center gap-3">
                        <span className="text-xs text-surface-500 w-28 capitalize">{intent.replace("_", " ")}</span>
                        <div className="flex-1 h-3 bg-surface-100 rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} className="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full" />
                        </div>
                        <span className="text-xs text-surface-500 w-8 text-right font-bold">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Language Distribution */}
              <div className="p-6 bg-white rounded-2xl border border-surface-200 shadow-sm">
                <h3 className="text-lg font-bold text-surface-800 mb-4">Language Distribution</h3>
                <div className="space-y-3">
                  {Object.entries(stats?.language_distribution || {}).map(([lang, count]) => {
                    const maxVal = Math.max(...Object.values(stats?.language_distribution || {}), 1);
                    const pct = (count / maxVal) * 100;
                    return (
                      <div key={lang} className="flex items-center gap-3">
                        <span className="text-xs text-surface-500 w-28 uppercase font-bold">{lang}</span>
                        <div className="flex-1 h-3 bg-surface-100 rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} className="h-full bg-gradient-to-r from-blue-400 to-cyan-500 rounded-full" />
                        </div>
                        <span className="text-xs text-surface-500 w-8 text-right font-bold">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Top Queries */}
            <div className="p-6 bg-white rounded-2xl border border-surface-200 shadow-sm">
              <h3 className="text-lg font-bold text-surface-800 mb-4">Top Used Queries</h3>
              <div className="space-y-2">
                {(stats?.top_queries || []).slice(0, 5).map((q, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-surface-50 rounded-xl">
                    <span className="w-8 h-8 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center text-sm font-bold">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-surface-700 truncate">{q.query}</p>
                      <p className="text-xs text-surface-400">{q.use_count} uses • {q.intent}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Bulk Upload Modal */}
        <AnimatePresence>
          {showBulkUpload && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={() => setShowBulkUpload(false)}>
              <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }}
                className="bg-white rounded-2xl p-6 w-full max-w-lg border border-surface-200 shadow-2xl" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-surface-800">Bulk Upload</h3>
                  <button onClick={() => setShowBulkUpload(false)} className="p-1 rounded-lg hover:bg-surface-100 text-surface-400"><X className="w-5 h-5" /></button>
                </div>
                <p className="text-xs text-surface-500 mb-3">Format: query|response|intent|language (one per line)</p>
                <textarea value={bulkText} onChange={e => setBulkText(e.target.value)} rows={8}
                  placeholder={"Dukan kab khulti hai?|Subah 9 baje|custom|hi\nPrice kitni hai?|₹500|price_inquiry|hi"}
                  className="w-full bg-surface-50 border border-surface-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/50 resize-none font-mono" />
                <button onClick={handleBulkUpload} className="w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold text-sm">Upload & Train</button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      </div>
    </div>
  );
}
