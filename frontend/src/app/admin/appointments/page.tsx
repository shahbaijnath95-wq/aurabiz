"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import Sidebar from "@/components/Sidebar";
import { request } from "@/lib/api";

interface Booking {
  id: string;
  service_name: string;
  customer_name: string;
  customer_phone: string;
  booking_date: string;
  booking_time: string;
  duration_minutes: number;
  price: number;
  status: string;
  notes: string;
  created_at: string;
}

export default function AppointmentsPage() {
  const { business, isAuthenticated, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!business?.id) return;
    fetchBookings();
  }, [business?.id]);

  const fetchBookings = async () => {
    try {
      const data = await request<Booking[]>(`/bookings/${business?.id}`);
      setBookings(Array.isArray(data) ? data : (data as unknown as { bookings?: Booking[] })?.bookings || []);
    } catch (e) {
      console.error("Bookings fetch error:", e);
      toast("Bookings load nahi ho payi", "error");
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (bookingId: string, status: string) => {
    try {
      await request(`/bookings/${bookingId}/status`, {
        method: "PUT",
        body: JSON.stringify({ status }),
      });
      fetchBookings();
    } catch (e) {
      console.error("Update error:", e);
      toast("Status update nahi ho paya", "error");
    }
  };

  const filtered = filter === "all" ? bookings : bookings.filter((b) => b.status === filter);

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    confirmed: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    cancelled: "bg-red-100 text-red-700",
  };

  const today = new Date().toISOString().split("T")[0];
  const todayCount = bookings.filter((b) => b.booking_date === today).length;
  const pendingCount = bookings.filter((b) => b.status === "pending").length;

  return (
    <div className="flex min-h-screen bg-[#faf9f7]">
      <Sidebar />
      <main className="flex-1 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
              <p className="text-sm text-gray-500">Service bookings and schedule</p>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-2xl border border-gray-100 p-4">
              <p className="text-xs text-gray-400 font-medium">Today&apos;s Bookings</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{todayCount}</p>
            </div>
            <div className="bg-white rounded-2xl border border-gray-100 p-4">
              <p className="text-xs text-gray-400 font-medium">Pending Confirmation</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">{pendingCount}</p>
            </div>
            <div className="bg-white rounded-2xl border border-gray-100 p-4">
              <p className="text-xs text-gray-400 font-medium">Total Bookings</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{bookings.length}</p>
            </div>
          </div>

          {/* Filters */}
          <div className="flex gap-2 mb-4">
            {["all", "pending", "confirmed", "completed", "cancelled"].map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  filter === s
                    ? "bg-amber-500 text-white"
                    : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
                }`}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="text-center py-20 text-gray-400">Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-4xl mb-3">📅</p>
              <p className="text-gray-500 font-medium">No appointments found</p>
              <p className="text-sm text-gray-400 mt-1">Bookings from WhatsApp will appear here</p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Service</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Customer</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Date</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Time</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Duration</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Price</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Status</th>
                    <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-5 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((b) => (
                    <tr key={b.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="px-5 py-3">
                        <p className="text-sm font-medium text-gray-900">{b.service_name}</p>
                        {b.notes && <p className="text-xs text-gray-400">{b.notes}</p>}
                      </td>
                      <td className="px-5 py-3">
                        <p className="text-sm text-gray-700">{b.customer_name}</p>
                        <p className="text-xs text-gray-400">{b.customer_phone}</p>
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-700">{b.booking_date}</td>
                      <td className="px-5 py-3 text-sm text-gray-700">{b.booking_time}</td>
                      <td className="px-5 py-3 text-sm text-gray-500">{b.duration_minutes} min</td>
                      <td className="px-5 py-3 text-sm font-semibold text-gray-900">₹{b.price}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[b.status] || "bg-gray-100 text-gray-600"}`}>
                          {b.status}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <select
                          value={b.status}
                          onChange={(e) => updateStatus(b.id, e.target.value)}
                          className="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white"
                        >
                          <option value="pending">Pending</option>
                          <option value="confirmed">Confirmed</option>
                          <option value="completed">Completed</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
