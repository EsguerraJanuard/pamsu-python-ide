import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../services/api";
import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

export default function SubmissionDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submission, setSubmission] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchSubmissionDetails = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const response = await api.get(`/submissions/${id}`);
        // We only have limited data from the backend
        if (isMounted && response) {
          setSubmission(response);
        }
      } catch (err) {
        if (isMounted) {
          setError("Failed to load submission details.");
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchSubmissionDetails();
    return () => { isMounted = false; };
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-screen w-screen bg-[#0a0c14] text-slate-200">
        <Sidebar />
        <div className="flex flex-1 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error || !submission) {
    return (
      <div className="flex h-screen w-screen bg-[#0a0c14] text-slate-200">
        <Sidebar />
        <div className="flex flex-1 flex-col items-center justify-center">
          <h2 className="text-xl font-bold text-white mb-2">Error</h2>
          <p className="text-slate-400 mb-4">{error || "Submission not found"}</p>
          <button
            onClick={() => navigate("/student/submissions")}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
          >
            Back to Submissions
          </button>
        </div>
      </div>
    );
  }

  const statusColors = {
    awaiting_review: "text-blue-400 border-blue-400/30 bg-blue-400/10",
    graded: "text-violet-400 border-violet-400/30 bg-violet-400/10",
    rejected: "text-rose-400 border-rose-400/30 bg-rose-400/10",
    submitted: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10"
  };

  const statusLabel = submission.status.replace("_", " ").toUpperCase();
  const colorClass = statusColors[submission.status] || "text-slate-400 border-slate-400/30 bg-slate-400/10";

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0a0c14] text-slate-200">
      <Sidebar />

      <div className="animate-page-fade flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-between border-b border-slate-800/80 bg-[#0d101d] px-6">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-slate-300">
              Submission Details
            </span>
          </div>
          <button
            onClick={() => navigate("/student/submissions")}
            className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:border-slate-700 hover:bg-slate-800 hover:text-white transition"
          >
            <span>←</span> Back to Submissions
          </button>
        </header>

        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="rounded-xl border border-slate-800/90 bg-[#111424] p-6 shadow-xl relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-xl font-bold text-white tracking-wide">
                    Task ID: {submission.task_id}
                  </h1>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${colorClass}`}>
                    {statusLabel}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  Submitted at: {new Date(submission.accepted_at).toLocaleString()}
                </p>
                <div className="mt-4 flex gap-4 text-sm font-mono text-slate-300">
                  <div className="bg-slate-900 px-3 py-1.5 rounded border border-slate-800">
                    Attempt Number: <span className="text-blue-400 font-bold">{submission.attempt_number}</span>
                  </div>
                  <div className="bg-slate-900 px-3 py-1.5 rounded border border-slate-800">
                    Is Official: <span className="text-emerald-400 font-bold">{submission.is_official ? "Yes" : "No"}</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2">
                 <div className="text-right">
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1.5">AST Validation</p>
                    {submission.ast_pass_fail === null ? (
                      <span className="text-slate-500 font-medium inline-block mt-1">Pending</span>
                    ) : submission.ast_pass_fail ? (
                      <span className="text-emerald-400 font-bold px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded inline-block mt-1">PASSED</span>
                    ) : (
                      <span className="text-rose-400 font-bold px-3 py-1 bg-rose-500/10 border border-rose-500/20 rounded inline-block mt-1">FAILED</span>
                    )}
                 </div>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/90 bg-[#111424] p-5 shadow-lg space-y-4">
             <h2 className="text-sm font-bold text-white tracking-wide border-b border-slate-800 pb-3">
               Submitted Code
             </h2>
             <pre className="font-mono text-[11px] p-4 bg-slate-950 rounded-lg border border-slate-800/50 overflow-x-auto text-blue-300">
                {submission.raw_code}
             </pre>
          </div>
        </main>

        <Statusbar
          sessionStatus="online"
          role="Student"
        />
      </div>
    </div>
  );
}
