"use client";
import Sidebar from "@/components/Sidebar";
import ImageUpload from "@/components/ImageUpload";

import { useState, useEffect } from "react";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { inventory as inventoryApi, API_BASE } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

const API = API_BASE.replace("/api/v1", "");
function imgUrl(url: string) {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return API + (url.startsWith("/") ? url : "/" + url);
}

interface InventoryProduct {
  id: string;
  name: string;
  sku: string;
  price: number;
  wholesale_price?: number;
  cost_price: number;
  stock_quantity: number;
  category: string;
  is_active: boolean;
  min_stock: number;
  item_type: string;
  duration_minutes: number;
  brand: string;
  model: string;
  warranty: string;
  hsn_code: string;
  gst_rate: number;
  tags: string[];
  specs: Record<string, string>;
  image_url: string;
  gallery: string[];
  description: string;
  unit: string;
}

const emptyForm = {
  name: "", sku: "", price: "", wholesale_price: "", cost_price: "", stock_quantity: "", category: "",
  unit: "piece", min_stock: "10", description: "", item_type: "product",
  duration_minutes: "", brand: "", model: "", warranty: "", hsn_code: "",
  gst_rate: "", tags: "", image_url: "",
};

export default function InventoryPage() {
  const [products, setProducts] = useState<InventoryProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editProduct, setEditProduct] = useState<InventoryProduct | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [specs, setSpecs] = useState<{ key: string; value: string }[]>([{ key: "", value: "" }]);
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState("all"); // all, product, service
  const [search, setSearch] = useState("");
  const { businessId, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  const loadProducts = () => {
    if (!businessId) {
      setLoading(false);
      return;
    }
    inventoryApi.list(businessId)
      .then((data) => {
        // API may return { products: [...] } or [...]
        const list = Array.isArray(data) ? data : (data as Record<string, unknown>)?.products;
        setProducts(Array.isArray(list) ? list as unknown as InventoryProduct[] : []);
      })
      .catch(() => toast("Inventory load nahi ho payi", "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadProducts(); }, [businessId]);

  const openAddModal = () => {
    setEditProduct(null);
    setForm(emptyForm);
    setSpecs([{ key: "", value: "" }]);
    setShowModal(true);
  };

  const openEditModal = (p: InventoryProduct) => {
    setEditProduct(p);
    setForm({
      name: p.name || "", sku: p.sku || "", price: String(p.price || ""),
      wholesale_price: p.wholesale_price ? String(p.wholesale_price) : "",
      cost_price: String(p.cost_price || ""), stock_quantity: String(p.stock_quantity || ""),
      category: p.category || "", unit: p.unit || "piece", min_stock: String(p.min_stock || 10),
      description: p.description || "", item_type: p.item_type || "product",
      duration_minutes: String(p.duration_minutes || ""), brand: p.brand || "",
      model: p.model || "", warranty: p.warranty || "", hsn_code: p.hsn_code || "",
      gst_rate: String(p.gst_rate || ""), tags: (p.tags || []).join(", "),
      image_url: p.image_url || "",
    });
    const s = p.specs || {};
    setSpecs(Object.keys(s).length > 0 ? Object.entries(s).map(([k, v]) => ({ key: k, value: String(v) })) : [{ key: "", value: "" }]);
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return toast("Product name daalo", "error");
    if (!form.price || Number(form.price) <= 0) return toast("Sahi price daalo", "error");
    setSaving(true);
    try {
      const specsObj: Record<string, string> = {};
      specs.forEach(s => { if (s.key.trim()) specsObj[s.key.trim()] = s.value.trim(); });

      const payload: any = {
        business_id: businessId,
        name: form.name.trim(),
        sku: form.sku.trim() || undefined,
        price: Number(form.price),
        wholesale_price: form.wholesale_price ? Number(form.wholesale_price) : undefined,
        cost_price: form.cost_price ? Number(form.cost_price) : undefined,
        stock_quantity: form.stock_quantity ? Number(form.stock_quantity) : 0,
        category: form.category.trim() || undefined,
        unit: form.unit,
        min_stock: Number(form.min_stock) || 10,
        description: form.description.trim() || undefined,
        item_type: form.item_type,
        duration_minutes: form.duration_minutes ? Number(form.duration_minutes) : undefined,
        brand: form.brand.trim() || undefined,
        model: form.model.trim() || undefined,
        warranty: form.warranty.trim() || undefined,
        hsn_code: form.hsn_code.trim() || undefined,
        gst_rate: form.gst_rate ? Number(form.gst_rate) : 0,
        tags: form.tags ? form.tags.split(",").map((t: string) => t.trim()).filter(Boolean) : [],
        specs: Object.keys(specsObj).length > 0 ? specsObj : undefined,
        image_url: form.image_url.trim() || undefined,
      };

      if (editProduct) {
        await inventoryApi.update(editProduct.id, payload);
        toast("Product update ho gaya!", "success");
      } else {
        await inventoryApi.add(payload);
        toast("Product add ho gaya!", "success");
      }
      setShowModal(false);
      setForm(emptyForm);
      loadProducts();
    } catch (e: any) {
      toast(e?.message || "Product save nahi ho paya", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Ye product delete karna hai?")) return;
    try {
      await inventoryApi.delete(id);
      toast("Product delete ho gaya", "success");
      loadProducts();
    } catch {
      toast("Delete nahi ho paya", "error");
    }
  };

  const filteredProducts = products.filter(p => {
    if (filter === "product" && p.item_type !== "product") return false;
    if (filter === "service" && p.item_type !== "service") return false;
    if (search) {
      const s = search.toLowerCase();
      return (p.name || "").toLowerCase().includes(s) ||
             (p.brand || "").toLowerCase().includes(s) ||
             (p.category || "").toLowerCase().includes(s) ||
             (p.sku || "").toLowerCase().includes(s);
    }
    return true;
  });

  const inputClass = "w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:border-amber-400 focus:ring-2 focus:ring-amber-100 outline-none transition-all";
  const labelClass = "block text-sm font-medium text-gray-700 mb-1";

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-sm text-gray-400 hover:text-amber-600 flex items-center gap-1 mb-2 transition-colors">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
            <p className="text-gray-500">Products aur services manage karo</p>
          </div>
          <button onClick={openAddModal} className="btn-gold text-sm">+ Product/Service Jodo</button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex bg-white rounded-xl border border-gray-100 p-1">
            {["all", "product", "service"].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${filter === f ? "bg-amber-500 text-white" : "text-gray-500 hover:bg-gray-50"}`}>
                {f === "all" ? "Sab" : f === "product" ? "Products" : "Services"}
              </button>
            ))}
          </div>
          <input type="text" placeholder="Search name, brand, category..." value={search} onChange={e => setSearch(e.target.value)}
            className="flex-1 max-w-xs px-4 py-2 rounded-xl border border-gray-200 text-sm focus:border-amber-400 focus:ring-2 focus:ring-amber-100 outline-none" />
        </div>

        {/* Products Table */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left p-4 font-medium text-gray-500">Product</th>
                <th className="text-left p-4 font-medium text-gray-500">Brand</th>
                <th className="text-center p-4 font-medium text-gray-500">Type</th>
                <th className="text-center p-4 font-medium text-gray-500">Stock</th>
                <th className="text-right p-4 font-medium text-gray-500">Price</th>
                <th className="text-center p-4 font-medium text-gray-500">Status</th>
                <th className="text-center p-4 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className="text-center py-8 text-gray-400">Loading...</td></tr>
              ) : filteredProducts.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-8 text-gray-400">Koi product nahi mila.</td></tr>
              ) : (
                filteredProducts.map((p) => (
                  <tr key={p.id} className="border-t border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        {p.image_url ? (
                          <img src={imgUrl(p.image_url)} alt="" className="w-10 h-10 rounded-lg object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-gray-400 text-lg">
                            {p.item_type === "service" ? "🔧" : "📦"}
                          </div>
                        )}
                        <div>
                          <p className="font-medium text-gray-900">{p.name}</p>
                          <p className="text-xs text-gray-400">{p.sku || p.category || ""}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 text-sm text-gray-600">{p.brand || "-"}</td>
                    <td className="p-4 text-center">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${p.item_type === "service" ? "bg-blue-50 text-blue-600" : "bg-purple-50 text-purple-600"}`}>
                        {p.item_type === "service" ? "Service" : "Product"}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <span className={`font-medium ${p.stock_quantity < p.min_stock ? "text-red-500" : "text-gray-900"}`}>
                        {p.stock_quantity}
                      </span>
                    </td>
                    <td className="p-4 text-right text-gray-700">₹{p.price}</td>
                    <td className="p-4 text-center">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${p.stock_quantity < p.min_stock ? "text-red-600 bg-red-50" : "text-emerald-600 bg-emerald-50"}`}>
                        {p.stock_quantity < p.min_stock ? "Low Stock" : "In Stock"}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button onClick={() => openEditModal(p)} className="text-xs text-amber-500 hover:text-amber-700 transition-colors">Edit</button>
                        <button onClick={() => handleDelete(p.id)} className="text-xs text-red-400 hover:text-red-600 transition-colors">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add/Edit Product Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">{editProduct ? "Product Edit Karo" : "Naya Product/Service Jodo"}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>

            <div className="space-y-5">
              {/* Item Type Toggle */}
              <div>
                <label className={labelClass}>Type *</label>
                <div className="flex gap-2">
                  {[{ v: "product", l: "📦 Product", d: "Physical item with stock" }, { v: "service", l: "🔧 Service", d: "Booking with time duration" }].map(t => (
                    <button key={t.v} onClick={() => setForm({ ...form, item_type: t.v })}
                      className={`flex-1 p-3 rounded-xl border-2 text-left transition-all ${form.item_type === t.v ? "border-amber-400 bg-amber-50" : "border-gray-200 hover:border-gray-300"}`}>
                      <p className="font-medium text-sm">{t.l}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{t.d}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Name */}
              <div>
                <label className={labelClass}>{form.item_type === "service" ? "Service" : "Product"} Name *</label>
                <input type="text" placeholder={form.item_type === "service" ? "Jaise: Hair Cut, Laptop Repair" : "Jaise: Maggi Noodles, Mouse"}
                  value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className={inputClass} />
              </div>

              {/* Brand + Model */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>Brand</label>
                  <input type="text" placeholder="Jaise: Logitech, Dell, Samsung" value={form.brand} onChange={e => setForm({ ...form, brand: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Model</label>
                  <input type="text" placeholder="Jaise: MX Master 3, Inspiron 15" value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} className={inputClass} />
                </div>
              </div>

              {/* Price + Cost */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className={labelClass}>Retail Price (₹) *</label>
                  <input type="number" placeholder="40" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Wholesale Price (₹)</label>
                  <input type="number" placeholder="35" value={form.wholesale_price} onChange={e => setForm({ ...form, wholesale_price: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Cost Price (₹)</label>
                  <input type="number" placeholder="30" value={form.cost_price} onChange={e => setForm({ ...form, cost_price: e.target.value })} className={inputClass} />
                </div>
              </div>

              {/* Stock + Min Stock + Unit */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className={labelClass}>Stock Quantity</label>
                  <input type="number" placeholder="100" value={form.stock_quantity} onChange={e => setForm({ ...form, stock_quantity: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Min Stock Alert</label>
                  <input type="number" placeholder="10" value={form.min_stock} onChange={e => setForm({ ...form, min_stock: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Unit</label>
                  <select value={form.unit} onChange={e => setForm({ ...form, unit: e.target.value })} className={inputClass}>
                    <option value="piece">Piece</option>
                    <option value="kg">Kg</option>
                    <option value="gram">Gram</option>
                    <option value="liter">Liter</option>
                    <option value="box">Box</option>
                    <option value="pack">Pack</option>
                    <option value="set">Set</option>
                    <option value="pair">Pair</option>
                  </select>
                </div>
              </div>

              {/* Service Duration */}
              {form.item_type === "service" && (
                <div>
                  <label className={labelClass}>Duration (minutes)</label>
                  <input type="number" placeholder="30" value={form.duration_minutes} onChange={e => setForm({ ...form, duration_minutes: e.target.value })} className={inputClass} />
                </div>
              )}

              {/* SKU + Category */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>SKU Code</label>
                  <input type="text" placeholder="MOUSE-LOGI-001" value={form.sku} onChange={e => setForm({ ...form, sku: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Category</label>
                  <input type="text" placeholder="Electronics, Grocery..." value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className={inputClass} />
                </div>
              </div>

              {/* Warranty + HSN + GST */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className={labelClass}>Warranty</label>
                  <input type="text" placeholder="1 year, 6 months" value={form.warranty} onChange={e => setForm({ ...form, warranty: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>HSN Code</label>
                  <input type="text" placeholder="8471" value={form.hsn_code} onChange={e => setForm({ ...form, hsn_code: e.target.value })} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>GST Rate (%)</label>
                  <input type="number" placeholder="18" value={form.gst_rate} onChange={e => setForm({ ...form, gst_rate: e.target.value })} className={inputClass} />
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className={labelClass}>Tags (comma separated)</label>
                <input type="text" placeholder="gaming, wireless, bestseller" value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} className={inputClass} />
              </div>

              {/* Photo Upload */}
              <div>
                <label className={labelClass}>Photo</label>
                <ImageUpload value={form.image_url} onChange={(url) => setForm({ ...form, image_url: url })} />
              </div>

              {/* Specs */}
              <div>
                <label className={labelClass}>Specifications</label>
                <div className="space-y-2">
                  {specs.map((s, i) => (
                    <div key={i} className="flex gap-2">
                      <input type="text" placeholder="Key (e.g. Color)" value={s.key}
                        onChange={e => { const n = [...specs]; n[i].key = e.target.value; setSpecs(n); }}
                        className="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm" />
                      <input type="text" placeholder="Value (e.g. Black)" value={s.value}
                        onChange={e => { const n = [...specs]; n[i].value = e.target.value; setSpecs(n); }}
                        className="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm" />
                      <button onClick={() => setSpecs(specs.filter((_, j) => j !== i))}
                        className="text-gray-400 hover:text-red-500 px-2">✕</button>
                    </div>
                  ))}
                  <button onClick={() => setSpecs([...specs, { key: "", value: "" }])}
                    className="text-sm text-amber-600 hover:text-amber-700 font-medium">+ Add Spec</button>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className={labelClass}>Description</label>
                <textarea placeholder="Product ke baare mein kuch likho..." value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })} className={inputClass + " h-20 resize-none"} />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowModal(false)} className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors">Cancel</button>
              <button onClick={handleSave} disabled={saving} className="flex-1 btn-gold text-sm disabled:opacity-50">
                {saving ? "Saving..." : editProduct ? "Update Karo" : "Product Jodo"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div></div>
  );
}
