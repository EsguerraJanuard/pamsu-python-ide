import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PageShell from "../../components/layout/PageShell";
import JoinClassModal from "../../components/modals/JoinClassModal";
import { EmptyState, ErrorState, InlineAlert, PageHeader } from "../../components/ui/StateViews";
import api from "../../services/api";
import { formatDate } from "../student/studentData";

const ENROLLMENT_STATUS = {
  active: { label: "Enrolled", badge: "badge-success" },
  disabled: { label: "Access paused", badge: "badge-gold" },
  removed: { label: "Removed", badge: "badge-danger" },
};

export default function MyClasses() {
  const [classrooms, setClassrooms] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isJoinModalOpen, setIsJoinModalOpen] = useState(false);
  const [joinedMessage, setJoinedMessage] = useState("");

  const fetchClasses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get("/classrooms/mine");
      setClassrooms(Array.isArray(response) ? response : []);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  const joinButton = (
    <button type="button" onClick={() => setIsJoinModalOpen(true)} className="btn-primary">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
      Join a class
    </button>
  );

  return (
    <PageShell>
      <PageHeader
        eyebrow="Coursework"
        title="My Classes"
        description="Your enrolled classrooms and their activities."
        actions={joinButton}
      />

      {joinedMessage && (
        <InlineAlert tone="success" onDismiss={() => setJoinedMessage("")} className="mb-5">
          {joinedMessage}
        </InlineAlert>
      )}

      {error ? (
        <ErrorState error={error} resource="your classes" onRetry={fetchClasses} />
      ) : isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3" role="status" aria-label="Loading classes">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card h-44 animate-pulse" />
          ))}
        </div>
      ) : classrooms.length === 0 ? (
        <EmptyState
          title="You haven't joined a class yet"
          message="Use the class code provided by your instructor to join a classroom."
          action={joinButton}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {classrooms.map((enrollment) => {
            const cls = enrollment.classroom;
            const status = ENROLLMENT_STATUS[enrollment.enrollment_status] || ENROLLMENT_STATUS.active;
            const canOpen = enrollment.enrollment_status === "active";
            const body = (
              <>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  {cls.subject_code && <span className="badge badge-brand">{cls.subject_code}</span>}
                  {cls.section && <span className="badge badge-neutral">Section {cls.section}</span>}
                  <span className={`badge ${status.badge}`}>{status.label}</span>
                  {!cls.is_active && <span className="badge badge-neutral">Archived</span>}
                </div>
                <h2 className="line-clamp-2 text-base font-semibold text-text-main">{cls.name}</h2>
                {cls.instructor_name && <p className="mt-1 text-sm text-text-muted">{cls.instructor_name}</p>}
                <p className="mt-4 border-t border-border-subtle pt-3 text-xs text-text-muted">
                  {cls.created_at ? `Class created ${formatDate(cls.created_at)}` : "Classroom"}
                </p>
              </>
            );

            return canOpen ? (
              <Link
                key={enrollment.enrollment_id}
                to={`/student/classes/${cls.class_id}`}
                className="card group block p-5 transition hover:border-psu-maroon/30 hover:shadow-md"
              >
                {body}
              </Link>
            ) : (
              <div key={enrollment.enrollment_id} className="card p-5 opacity-75" aria-disabled="true">
                {body}
              </div>
            );
          })}
        </div>
      )}

      <JoinClassModal
        isOpen={isJoinModalOpen}
        onClose={() => setIsJoinModalOpen(false)}
        onSuccess={() => {
          setJoinedMessage("You joined the class.");
          fetchClasses();
        }}
      />
    </PageShell>
  );
}
