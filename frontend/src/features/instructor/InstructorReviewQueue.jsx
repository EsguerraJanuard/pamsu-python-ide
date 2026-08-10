import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import InstructorSidebar from "../../components/layout/InstructorSidebar";

const InstructorReviewQueue = () => {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchReviewQueue = async () => {
      try {
        const response = await api.get('/instructors/review-queue');
        // api.js returns the parsed JSON body directly
        const data = response?.items || [];
        setSubmissions(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Error fetching review queue:', err);
        setError('Failed to load review queue.');
      } finally {
        setLoading(false);
      }
    };

    fetchReviewQueue();
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f1117] text-white select-none">
      <InstructorSidebar />
      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                        
            <div className="mx-auto max-w-6xl ">

      <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="mb-1 font-mono text-xs text-emerald-400">MONITORING & GRADING</p>
          <h1 className="text-2xl font-bold">Grading Bench</h1>
          <p className="mt-1 text-sm text-white/40">
            Review and grade pending student submissions.
          </p>
        </div>
      </header>

      {error && (
        <div className="mb-4 p-4 bg-red-900/50 border border-red-500 rounded text-red-200">
          {error}
        </div>
      )}

      <div className="bg-[#1a1d27] border border-white/[0.06] rounded-lg overflow-hidden">
        {loading ? (
          <div className="divide-y divide-white/[0.06] w-full text-left text-xs font-mono">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="flex px-4 py-4 animate-pulse items-center">
                <div className="w-1/4 h-3 rounded bg-white/[0.06] mr-4"></div>
                <div className="w-1/4 h-3 rounded bg-white/[0.06] mr-4"></div>
                <div className="w-1/6 h-3 rounded bg-white/[0.06] mr-4"></div>
                <div className="w-1/12 h-3 rounded bg-white/[0.06] mr-4"></div>
                <div className="w-1/6 h-3 rounded bg-white/[0.06] mr-4"></div>
                <div className="w-1/12 h-6 rounded bg-white/[0.06] ml-auto"></div>
              </div>
            ))}
          </div>
        ) : submissions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 ring-4 ring-emerald-500/5">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-white/90">All Caught Up!</h3>
            <p className="text-sm text-slate-400 max-w-sm">
              There are no pending submissions to review. You can check back later.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-800/50 border-b border-white/[0.06]">
                  <th className="p-4 text-sm font-semibold text-white/80">Student Name</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Task Title</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Status</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Similarity</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Submitted At</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Actions</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((sub) => {
                  // Assume similarity_score is 0-1 or 0-100; adjusting for typical case where it might be a decimal
                  // Just treating it as a raw number and applying condition based on if it's already % or ratio
                  let rawScore = sub.similarity_score;
                  let similarityScore = null;
                  let isHighSimilarity = false;
                  
                  if (rawScore !== undefined && rawScore !== null) {
                    if (rawScore <= 1.0) {
                      similarityScore = (rawScore * 100).toFixed(1);
                    } else {
                      similarityScore = parseFloat(rawScore).toFixed(1);
                    }
                    isHighSimilarity = parseFloat(similarityScore) > 70;
                  }

                  return (
                    <tr key={sub.sub_id || sub.id} className="border-b border-white/[0.06] hover:bg-slate-800/20 transition-colors">
                      <td className="p-4 text-sm text-white">
                        {sub.student?.name || sub.user?.full_name || 'Unknown Student'}
                      </td>
                      <td className="p-4 text-sm text-emerald-400">
                        {sub.activity?.title || sub.task?.title || 'Unknown Task'}
                      </td>
                      <td className="p-4 text-sm">
                        <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded text-xs capitalize">
                          {sub.status || 'pending'}
                        </span>
                      </td>
                      <td className="p-4 text-sm">
                        {similarityScore !== null ? (
                          <span className={`${isHighSimilarity ? 'text-red-400 font-bold' : 'text-white/80'}`}>
                            {similarityScore}%
                          </span>
                        ) : (
                          <span className="text-white/40">N/A</span>
                        )}
                      </td>
                      <td className="p-4 text-sm text-white/60">
                        {formatDate(sub.submitted_at)}
                      </td>
                      <td className="p-4 text-sm">
                        <button
                          onClick={() => navigate(`/instructor/submissions/${sub.sub_id || sub.id}`)}
                          className="px-3 py-1 bg-emerald-600/10 text-emerald-400 border border-emerald-500/20 rounded hover:bg-emerald-600 hover:text-white transition-colors"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 20h9"></path>
                            <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"></path>
                          </svg>
                          Review
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
                </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default InstructorReviewQueue;