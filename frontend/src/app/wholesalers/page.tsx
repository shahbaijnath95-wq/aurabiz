"use client";
import Sidebar from "@/components/Sidebar";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { customers, request, API_BASE } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function WholesalersPage() {
  const [custList, setCustList] = useState<{id: string; name: string; phone_number: string; total_orders: number; total_spent: number; is_wholesaler: boolean}[]>([]);
  const [loading, setLoading] = useState(true);
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchPhone, setSearchPhone] = useState("");
  const [searchResults, setSearchResults] = useState<{id: string; name: string; phone: string}[]>([]);
  const [newWholesalerMode, setNewWholesalerMode] = useState(false);
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  const fetchWholesalers = () => {
    setLoading(true);
    customers.list(businessId, { limit: 50, is_wholesaler: true } as any)
      .then((data) => {
        const list = Array.isArray(data) ? data : (data as { customers?: typeof data[] })?.customers || [];
        setCustList(list);
      })
      .catch(() => toast("Wholesalers load nahi ho paye", "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!businessId) return;
    fetchWholesalers();
  }, [businessId]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchPhone) return;
    try {
      const results = await customers.search(businessId, searchPhone);
      setSearchResults(results as any);
      setNewWholesalerMode(results.length === 0);
    } catch (err) {
      toast("Search failed", "error");
    }
  };

  const handleAddNew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPhone) {
      toast("Phone number zaroori hai", "error");
      return;
    }
    try {
      await customers.create({
        business_id: businessId,
        name: newName,
        phone_number: newPhone,
        is_wholesaler: true
      });
      toast("Naya wholesaler add ho gaya!", "success");
      setShowAddModal(false);
      fetchWholesalers();
    } catch (err: any) {
      toast(err.message || "Error adding wholesaler", "error");
    }
  };

  const makeWholesaler = async (id: string) => {
    try {
      await customers.update(id, { is_wholesaler: true });
      toast("Customer ko wholesaler bana diya!", "success");
      setShowAddModal(false);
      fetchWholesalers();
    } catch (err) {
      toast("Error marking wholesaler", "error");
    }
  };

  const removeWholesaler = async (id: string) => {
    try {
      await customers.update(id, { is_wholesaler: false });
      toast("Wholesaler hata diya", "success");
      fetchWholesalers();
    } catch (err) {
      toast("Error removing wholesaler", "error");
    }
  };

  return (
    <div className="flex min-h-screen bg-surface-100">
      <Sidebar />
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
              <h1 className="text-2xl font-bold text-gray-900">Wholesalers</h1>
              <p className="text-gray-500">Aapke special pricing wale customers</p>
            </div>
            <button 
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-xl font-medium shadow-lg shadow-amber-500/20 hover:shadow-amber-500/30 transition-all hover:-translate-y-0.5"
            >
              + Add Wholesaler
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left p-4 font-medium text-gray-500">Name</th>
                  <th className="text-left p-4 font-medium text-gray-500">Phone</th>
                  <th className="text-right p-4 font-medium text-gray-500">Total Spend</th>
                  <th className="text-center p-4 font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={4} className="text-center py-8 text-gray-400">Loading...</td></tr>
                ) : custList.length === 0 ? (
                  <tr><td colSpan={4} className="text-center py-8 text-gray-400">Abhi koi wholesaler nahi hai</td></tr>
                ) : (
                  custList.map((c, i) => (
                    <tr key={i} className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 text-white flex items-center justify-center text-xs font-bold">
                            {(c.name || "U").charAt(0)}
                          </div>
                          <span className="font-medium text-gray-900">{c.name || "Unknown"}</span>
                          <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold">Wholesale</span>
                        </div>
                      </td>
                      <td className="p-4 text-gray-500">{c.phone_number || "N/A"}</td>
                      <td className="p-4 text-right text-gray-700">₹{(c.total_spent || 0).toLocaleString()}</td>
                      <td className="p-4 text-center">
                        <button onClick={() => removeWholesaler(c.id)} className="text-red-500 hover:text-red-700 text-xs font-medium transition-colors">Remove</button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Add Wholesaler</h2>
            <form onSubmit={handleSearch} className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Search Customer by Phone or Name</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchPhone}
                  onChange={(e) => setSearchPhone(e.target.value)}
                  className="flex-1 rounded-xl border border-gray-200 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="+91..."
                />
                <button type="submit" className="px-4 py-2 bg-gray-900 text-white rounded-xl text-sm font-medium">Search</button>
              </div>
            </form>
            
            {searchResults.length > 0 && (
              <div className="mt-4 border-t border-gray-100 pt-4 max-h-48 overflow-y-auto">
                <p className="text-sm text-gray-500 mb-2">Search Results:</p>
                {searchResults.map((r, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{r.name}</p>
                      <p className="text-xs text-gray-500">{r.phone}</p>
                    </div>
                    <button onClick={() => makeWholesaler(r.id)} className="text-xs bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-lg font-medium hover:bg-indigo-100">Make Wholesaler</button>
                  </div>
                ))}
              </div>
            )}

            {newWholesalerMode && (
              <form onSubmit={handleAddNew} className="mt-6 border-t border-gray-100 pt-4">
                <p className="text-sm font-semibold text-gray-900 mb-3">Customer nahi mila? Naya add karein:</p>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Name</label>
                    <input type="text" value={newName} onChange={e => setNewName(e.target.value)} className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 outline-none" placeholder="Rahul Kumar" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Phone Number *</label>
                    <input type="text" value={newPhone} onChange={e => setNewPhone(e.target.value)} className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 outline-none" placeholder="+919876543210" />
                  </div>
                  <button type="submit" className="w-full py-2 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-lg text-sm font-medium">Add New Wholesaler</button>
                </div>
              </form>
            )}
            
            <div className="mt-6 flex justify-end">
              <button 
                onClick={() => { setShowAddModal(false); setSearchResults([]); setSearchPhone(""); setNewWholesalerMode(false); setNewName(""); setNewPhone(""); }}
                className="px-4 py-2 text-gray-500 hover:text-gray-700 font-medium text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
