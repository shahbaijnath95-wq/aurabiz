"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { teams } from "@/lib/api";
import type { Team, TeamMember } from "@/lib/types";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function TeamsPage() {
  const router = useRouter();
  const { user, business, loading: authLoading } = useAuth();
  const { toast } = useToast();
  const [teamList, setTeamList] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [memberForm, setMemberForm] = useState({ user_id: "", role: "staff" });

  const businessId = business?.id || "";

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
    if (businessId) loadTeams();
  }, [authLoading, user, businessId]);

  async function loadTeams() {
    try {
      const data = await teams.list(businessId);
      setTeamList(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await teams.create({ ...form, business_id: businessId });
      setForm({ name: "", description: "" });
      setShowCreate(false);
      loadTeams();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Create fail ho gaya", "error"); }
  }

  async function handleAddMember(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTeam) return;
    try {
      await teams.addMember(selectedTeam.id, { ...memberForm, team_id: selectedTeam.id });
      setMemberForm({ user_id: "", role: "staff" });
      loadTeams();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Add member fail ho gaya", "error"); }
  }

  async function handleRemoveMember(teamId: string, memberId: string) {
    if (!confirm("Remove member?")) return;
    try {
      await teams.removeMember(teamId, memberId);
      loadTeams();
    } catch (e: unknown) { toast(e instanceof Error ? e.message : "Remove fail ho gaya", "error"); }
  }

  return (
    <div className="flex min-h-screen bg-surface-100"><Sidebar /><div className="flex-1 overflow-y-auto">
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Teams Management</h1>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600">
          + Create Team
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border p-4 mb-6">
          <h3 className="font-semibold mb-3">New Team</h3>
          <form onSubmit={handleCreate} className="flex gap-3">
            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="Team name" className="flex-1 px-3 py-2 border rounded-lg" required />
            <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
              placeholder="Description" className="flex-1 px-3 py-2 border rounded-lg" />
            <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded-lg">Create</button>
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-200 rounded-lg">Cancel</button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : teamList.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border">
          <p className="text-gray-400">No teams yet. Create your first team!</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {teamList.map((team) => (
            <div key={team.id} className="bg-white rounded-xl border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{team.name}</h3>
                  <p className="text-sm text-gray-500">{team.description || "No description"}</p>
                  <p className="text-xs text-gray-400 mt-1">{team.member_count || 0} members</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setSelectedTeam(selectedTeam?.id === team.id ? null : team)}
                    className="px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100">
                    Members
                  </button>
                  <button onClick={() => { if (confirm("Delete team?")) teams.delete(team.id).then(loadTeams); }}
                    className="px-3 py-1 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100">
                    Delete
                  </button>
                </div>
              </div>

              {selectedTeam?.id === team.id && (
                <div className="mt-4 pt-4 border-t">
                  <h4 className="font-medium mb-2">Add Member</h4>
                  <form onSubmit={handleAddMember} className="flex gap-2 mb-3">
                    <input value={memberForm.user_id} onChange={e => setMemberForm({ ...memberForm, user_id: e.target.value })}
                      placeholder="User ID" className="flex-1 px-3 py-2 border rounded-lg text-sm" required />
                    <select value={memberForm.role} onChange={e => setMemberForm({ ...memberForm, role: e.target.value })}
                      className="px-3 py-2 border rounded-lg text-sm">
                      <option value="staff">Staff</option>
                      <option value="admin">Admin</option>
                      <option value="viewer">Viewer</option>
                    </select>
                    <button type="submit" className="px-3 py-2 bg-green-500 text-white rounded-lg text-sm">Add</button>
                  </form>
                  {(team.members?.length ?? 0) > 0 && (
                    <div className="space-y-1">
                      {team.members?.map((m: TeamMember) => (
                        <div key={m.id} className="flex items-center justify-between text-sm py-1 px-2 bg-gray-50 rounded">
                          <span>{m.user_id} — <span className="text-xs text-gray-500">{m.role}</span></span>
                          <button onClick={() => handleRemoveMember(team.id, m.id)} className="text-red-500 text-xs">Remove</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
    </div></div>
  );
}
