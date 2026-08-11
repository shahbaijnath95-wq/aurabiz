"use client";
import Sidebar from "@/components/Sidebar";
import { PageLoader } from "@/components/skeleton";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { catalog } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

interface CatalogProduct {
  id: string;
  name: string;
  description?: string;
  price: number;
  category?: string;
  image_url?: string;
  is_available: boolean;
  stock_quantity?: number;
  sku?: string;
}

export default function CatalogPage() {
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [categories, setCategories] = useState<string[]>([]);
  const [whatsappPreview, setWhatsappPreview] = useState("");
  const [showPreview, setShowPreview] = useState(false);
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!businessId) return;
    setLoading(true);
    catalog
      .list(businessId)
      .then((data) => {
        const list = Array.isArray(data) ? data as unknown as CatalogProduct[] : (data as unknown as { products?: CatalogProduct[] })?.products || [];
        setProducts(list);
        return catalog.categories(businessId);
      })
      .then((data) => setCategories(Array.isArray(data) ? data : []))
      .catch(() => toast("Catalog load nahi ho paya", "error"))
      .finally(() => setLoading(false));
  }, [businessId]);

  const handleSearch = async () => {
    if (!businessId || !searchQuery.trim()) return;
    try {
      const data = await catalog.search(businessId, searchQuery);
      setProducts(Array.isArray(data) ? data as unknown as CatalogProduct[] : []);
    } catch {
      toast("Search fail ho gaya", "error");
    }
  };

  const handlePreview = async () => {
    if (!businessId) return;
    try {
      const data = await catalog.whatsapp(businessId) as unknown as { message?: string };
      setWhatsappPreview(data?.message || "No preview available");
      setShowPreview(true);
    } catch {
      toast("Preview load nahi ho paya", "error");
    }
  };

  const filtered = products.filter((p) => {
    if (selectedCategory !== "all" && p.category !== selectedCategory) return false;
    return true;
  });

  return (
    <div className="flex min-h-screen bg-surface-100">
      <Sidebar />
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <Link
                href="/dashboard"
                className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors"
              >
                ← Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">Catalog</h1>
              <p className="text-gray-500">Aapke products ka catalog manage karo</p>
            </div>
            <button onClick={handlePreview} className="btn-gold text-sm">
              WhatsApp Preview
            </button>
          </div>

          {showPreview && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-card mb-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">WhatsApp Catalog Preview</h3>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-gray-400 hover:text-gray-600 text-sm"
                >
                  Close
                </button>
              </div>
              <pre className="bg-green-50 rounded-xl p-4 text-sm text-green-800 whitespace-pre-wrap font-mono border border-green-200">
                {whatsappPreview}
              </pre>
            </motion.div>
          )}

          <div className="flex gap-4 mb-6">
            <div className="flex-1 relative">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Products search karo..."
                className="input-angel w-full pl-10"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="input-angel min-w-[160px]"
            >
              <option value="all">Sab Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {loading ? (
            <PageLoader />
          ) : filtered.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center text-gray-400 border border-gray-100 shadow-card">
              {searchQuery ? "Koi product nahi mila" : "Abhi koi product nahi hai. Pehle inventory mein add karo!"}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filtered.map((product, i) => (
                <motion.div
                  key={product.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden hover:shadow-lg transition-shadow"
                >
                  {product.image_url && (
                    <div className="h-40 bg-gray-100">
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 text-sm leading-tight">{product.name}</h3>
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          product.is_available
                            ? "bg-emerald-50 text-emerald-600"
                            : "bg-gray-100 text-gray-400"
                        }`}
                      >
                        {product.is_available ? "Available" : "N/A"}
                      </span>
                    </div>
                    {product.description && (
                      <p className="text-xs text-gray-400 mb-2 line-clamp-2">{product.description}</p>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-bold text-amber-600">₹{product.price.toLocaleString()}</span>
                      {product.category && (
                        <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">
                          {product.category}
                        </span>
                      )}
                    </div>
                    {product.stock_quantity !== undefined && (
                      <div className="mt-2 text-xs text-gray-400">
                        Stock: {product.stock_quantity}
                        {product.stock_quantity < 5 && product.stock_quantity > 0 && (
                          <span className="text-amber-500 ml-1">(Low!)</span>
                        )}
                        {product.stock_quantity === 0 && (
                          <span className="text-red-500 ml-1">(Out of stock)</span>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
