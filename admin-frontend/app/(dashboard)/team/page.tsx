"use client";
import { useEffect, useState } from "react";
import { masterAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { UserCog, Plus, Trash2 } from "lucide-react";

export default function TeamPage() {
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", name: "", role: "admin", password: "" });

  const load = async () => {
    setLoading(true);
    try {
      const data = await masterAPI.getTeamMembers();
      setMembers(data.members || data.items || []);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await masterAPI.createTeamMember(form);
      toast.success("Team member added");
      setShowForm(false);
      setForm({ email: "", name: "", role: "admin", password: "" });
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await masterAPI.deleteTeamMember(id);
      toast.success("Member deleted");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const toggleActive = async (m: any) => {
    try {
      await masterAPI.updateTeamMember(m.id, { is_active: !m.is_active });
      toast.success(m.is_active ? "Deactivated" : "Activated");
      load();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <UserCog size={24} /> Team Members ({members.length})
        </h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm inline-flex items-center gap-1 hover:bg-blue-700"
        >
          <Plus size={14} /> Add Member
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-xl shadow p-4 mb-4 grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            type="text"
            placeholder="Full Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
            required
          />
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="viewer">Viewer</option>
            <option value="admin">Admin</option>
            <option value="super_admin">Super Admin</option>
          </select>
          <button type="submit" className="bg-green-600 text-white px-3 py-2 rounded-lg text-sm col-span-full">
            Create Member
          </button>
        </form>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading...</div>
      ) : members.length === 0 ? (
        <div className="text-gray-400 text-sm">No team members found</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Role</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Last Login</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{m.name}</td>
                  <td className="px-4 py-3 text-gray-500">{m.email}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      m.role === "super_admin" ? "bg-purple-100 text-purple-700" :
                      m.role === "admin" ? "bg-blue-100 text-blue-700" :
                      "bg-gray-100 text-gray-700"
                    }`}>
                      {m.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleActive(m)}
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        m.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      }`}
                    >
                      {m.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {m.last_login_at ? new Date(m.last_login_at).toLocaleString() : "Never"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(m.id, m.name)}
                      className="text-red-600 hover:underline text-xs inline-flex items-center gap-1"
                    >
                      <Trash2 size={12} /> Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
