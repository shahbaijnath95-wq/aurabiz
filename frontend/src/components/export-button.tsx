"use client";

import { useState } from "react";

// ============================================================
// EXPORT BUTTON — Export data to CSV/JSON/Excel
// ============================================================

interface ExportButtonProps {
  data: Record<string, unknown>[];
  filename: string;
  columns?: { key: string; label: string }[];
  formats?: ("csv" | "json")[];
  className?: string;
}

export function ExportButton({
  data,
  filename,
  columns,
  formats = ["csv", "json"],
  className = "",
}: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const exportCSV = () => {
    if (!data.length) return;

    const cols = columns || Object.keys(data[0]).map((key) => ({ key, label: key }));
    const headers = cols.map((c) => c.label).join(",");
    const rows = data.map((row) =>
      cols.map((c) => {
        const val = row[c.key];
        const str = String(val ?? "");
        return str.includes(",") || str.includes('"') || str.includes("\n")
          ? `"${str.replace(/"/g, '""')}"`
          : str;
      }).join(",")
    );

    const csv = [headers, ...rows].join("\n");
    downloadFile(csv, `${filename}.csv`, "text/csv");
  };

  const exportJSON = () => {
    if (!data.length) return;
    const json = JSON.stringify(data, null, 2);
    downloadFile(json, `${filename}.json`, "application/json");
  };

  const downloadFile = (content: string, name: string, type: string) => {
    setExporting(true);
    try {
      const blob = new Blob([content], { type });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
      setIsOpen(false);
    }
  };

  if (!data.length) return null;

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={exporting}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
      >
        <span>{exporting ? "⏳" : "📤"}</span>
        {exporting ? "Export ho raha hai..." : "Export"}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-2 z-50 bg-white border border-gray-200 rounded-xl shadow-lg py-1 min-w-[160px]">
            {formats.includes("csv") && (
              <button
                onClick={exportCSV}
                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              >
                <span>📊</span>
                CSV file
              </button>
            )}
            {formats.includes("json") && (
              <button
                onClick={exportJSON}
                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              >
                <span>📋</span>
                JSON file
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ============================================================
// QUICK EXPORT — Simple button for common exports
// ============================================================

interface QuickExportProps {
  data: Record<string, unknown>[];
  filename: string;
  label?: string;
  className?: string;
}

export function QuickExport({ data, filename, label = "Export CSV", className = "" }: QuickExportProps) {
  const [exporting, setExporting] = useState(false);

  const handleExport = () => {
    if (!data.length) return;
    setExporting(true);

    try {
      const headers = Object.keys(data[0]).join(",");
      const rows = data.map((row) =>
        Object.values(row).map((val) => {
          const str = String(val ?? "");
          return str.includes(",") ? `"${str}"` : str;
        }).join(",")
      );

      const csv = [headers, ...rows].join("\n");
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${filename}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={exporting || !data.length}
      className={`flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50 ${className}`}
    >
      <span>{exporting ? "⏳" : "📥"}</span>
      {exporting ? "Exporting..." : label}
    </button>
  );
}
