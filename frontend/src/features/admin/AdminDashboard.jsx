import { useState, useEffect } from "react";
import { useAuth } from "../auth/AuthContext";
import api from "../../services/api";

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const [instructors, setInstructors] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password: "",
  });

  useEffect(() => {
    fetchInstructors();
  }, []);

  const fetchInstructors = async () => {
    try {
      const response = await api.get("/admin/users");
      const users = response.data || response;
      setInstructors(users.filter((u) => u.role === "instructor"));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await api.post("/admin/instructors", form);
      setForm({ email: "", first_name: "", last_name: "", password: "" });
      fetchInstructors();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create instructor");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-base text-text-main p-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black text-psu-maroon dark:text-psu-gold">MIS Dashboard</h1>
          <p className="text-text-muted mt-1">Super Admin Account Provisioning</p>
        </div>
        <button onClick={logout} className="px-4 py-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 font-bold transition-colors">
          Sign Out
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm lg:col-span-1 h-fit">
          <h2 className="text-xl font-bold mb-4">Provision Faculty</h2>
          {error && <div className="mb-4 p-3 bg-red-500/10 text-red-500 rounded-lg text-sm">{error}</div>}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1 block">Email</label>
              <input required type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="w-full px-3 py-2 bg-bg-base border border-border-strong rounded-lg outline-none focus:border-psu-maroon" placeholder="faculty@pampangastateu.edu.ph" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1 block">First Name</label>
                <input required type="text" value={form.first_name} onChange={(e) => setForm({...form, first_name: e.target.value})} className="w-full px-3 py-2 bg-bg-base border border-border-strong rounded-lg outline-none focus:border-psu-maroon" />
              </div>
              <div>
                <label className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1 block">Last Name</label>
                <input required type="text" value={form.last_name} onChange={(e) => setForm({...form, last_name: e.target.value})} className="w-full px-3 py-2 bg-bg-base border border-border-strong rounded-lg outline-none focus:border-psu-maroon" />
              </div>
            </div>
            <div>
              <label className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1 block">Default Password</label>
              <input required type="text" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="w-full px-3 py-2 bg-bg-base border border-border-strong rounded-lg outline-none focus:border-psu-maroon" />
            </div>
            <button disabled={isLoading} type="submit" className="w-full mt-4 bg-psu-maroon text-white font-bold py-2.5 rounded-lg hover:bg-psu-red transition-colors disabled:opacity-50">
              Create Instructor Account
            </button>
          </form>
        </div>

        <div className="bg-bg-glass border border-border-subtle p-6 rounded-2xl shadow-sm lg:col-span-2">
          <h2 className="text-xl font-bold mb-4">Active Faculty Accounts</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-text-muted uppercase bg-bg-base">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3 rounded-tr-lg">Role</th>
                </tr>
              </thead>
              <tbody>
                {instructors.map((inst) => (
                  <tr key={inst.user_id} className="border-b border-border-subtle hover:bg-bg-base/50 transition-colors">
                    <td className="px-4 py-3 font-medium">{inst.first_name} {inst.last_name}</td>
                    <td className="px-4 py-3 text-text-muted">{inst.email}</td>
                    <td className="px-4 py-3"><span className="px-2.5 py-1 bg-psu-maroon/10 text-psu-maroon dark:text-psu-gold text-xs font-bold rounded-full">Instructor</span></td>
                  </tr>
                ))}
                {instructors.length === 0 && (
                  <tr>
                    <td colSpan="3" className="px-4 py-8 text-center text-text-muted">No instructors provisioned yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
