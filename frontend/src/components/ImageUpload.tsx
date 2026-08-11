"use client";

import { useState, useRef } from "react";
import { API_BASE } from "@/lib/api";

interface ImageUploadProps {
  value?: string;
  onChange: (url: string) => void;
  className?: string;
}

export default function ImageUpload({ value, onChange, className = "" }: ImageUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = async (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Sirf image file upload karo");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("File 5MB se chhoti honi chahiye");
      return;
    }

    setError("");
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const headers: Record<string, string> = token ? { "Authorization": `Bearer ${token}` } : {};
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", headers, body: formData });
      if (!res.ok) throw new Error("Upload fail ho gaya");
      const data = await res.json();
      onChange(data.url);
    } catch {
      setError("Upload nahi ho paya — dobara try karo");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) upload(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload(file);
  };

  return (
    <div className={className}>
      {value ? (
        <div className="relative inline-block">
          <img src={value} alt="Preview" className="w-24 h-24 rounded-xl object-cover border border-gray-200" />
          <button onClick={() => onChange("")}
            className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600 shadow-sm">
            ✕
          </button>
        </div>
      ) : (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`w-full border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
            dragOver ? "border-amber-400 bg-amber-50" : "border-gray-200 hover:border-amber-300 hover:bg-gray-50"
          } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
        >
          {uploading ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-sm text-gray-500">Upload ho raha hai...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <p className="text-2xl">📸</p>
              <p className="text-sm text-gray-600 font-medium">Photo upload karo</p>
              <p className="text-xs text-gray-400">Drag & drop ya click karo (JPG, PNG — max 5MB)</p>
            </div>
          )}
          <input ref={inputRef} type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
        </div>
      )}
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}
