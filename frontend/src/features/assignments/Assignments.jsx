import { useCallback, useEffect, useMemo, useState } from "react";

import PageShell from "../../components/layout/PageShell";
import { EmptyState, ErrorState, InlineAlert, PageHeader, SkeletonList } from "../../components/ui/StateViews";
import useUrlFilters from "../../hooks/useUrlFilters";
import ActivityCard from "../student/ActivityCard";
import { isActiveActivity, loadStudentActivities } from "../student/studentData";

const FILTERS = [
  { label: "All", value: "all" },
  { label: "Open", value: "open" },
  { label: "Submitted", value: "submitted" },
  { label: "Past due", value: "past_due" },
];

// ?filter=open&q=loops — kept in the URL for reloads and shared links.
const URL_DEFAULTS = { filter: "all", q: "" };
const URL_ALLOWED = { filter: FILTERS.map((option) => option.value) };

function matchesFilter(activity, filter) {
  if (filter === "open") return isActiveActivity(activity);
  if (filter === "submitted") return activity.isSubmitted;
  if (filter === "past_due") return activity.status === "past_due";
  return true;
}

export default function Assignments() {
  const [activities, setActivities] = useState([]);
  const [hasClasses, setHasClasses] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [urlFilters, setUrlFilters] = useUrlFilters(URL_DEFAULTS, URL_ALLOWED);
  const filter = urlFilters.filter;
  const searchQuery = urlFilters.q;
  const setFilter = (value) => setUrlFilters({ filter: value });
  const setSearchQuery = (value) => setUrlFilters({ q: value });

  const fetchActivities = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await loadStudentActivities();
      setActivities(data.activities);
      setHasClasses(data.classrooms.length > 0);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  const openCount = activities.filter(isActiveActivity).length;
  const submittedCount = activities.filter((a) => a.isSubmitted).length;

  const visibleActivities = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return activities.filter(
      (activity) =>
        matchesFilter(activity, filter) &&
        (!query ||
          activity.title.toLowerCase().includes(query) ||
          activity.classLabel.toLowerCase().includes(query)),
    );
  }, [activities, filter, searchQuery]);

  return (
    <PageShell assignmentCount={openCount}>
      <PageHeader
        eyebrow="Coursework"
        title="Assignments"
        description={isLoading || error ? "Activities from all of your classes." : `${openCount} open · ${submittedCount} submitted`}
      />

      {error ? (
        <ErrorState error={error} resource="your assignments" onRetry={fetchActivities} />
      ) : (
        <>
          <InlineAlert tone="info" className="mb-5">
            You may submit an activity more than once while submissions remain open. Your latest accepted
            submission becomes the official version for instructor review.
          </InlineAlert>

          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div
              className="flex w-full gap-1 overflow-x-auto rounded-lg border border-border-subtle bg-bg-panel p-1 sm:w-fit"
              role="tablist"
              aria-label="Filter activities"
            >
              {FILTERS.map((option) => {
                const selected = filter === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    role="tab"
                    aria-selected={selected}
                    onClick={() => setFilter(option.value)}
                    className={`whitespace-nowrap rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors ${
                      selected ? "bg-psu-maroon text-white shadow-sm" : "text-text-muted hover:bg-bg-alt hover:text-text-main"
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
            <div className="w-full sm:w-72">
              <label htmlFor="assignment-search" className="sr-only">
                Search assignments
              </label>
              <input
                id="assignment-search"
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title or class…"
                className="input-field"
              />
            </div>
          </div>

          <section aria-label="Activity list">
            {isLoading ? (
              <SkeletonList rows={4} />
            ) : !hasClasses ? (
              <EmptyState
                title="No classes yet"
                message="Join a class from your dashboard using the code from your instructor to receive assignments."
              />
            ) : activities.length === 0 ? (
              <EmptyState
                title="No assignments yet"
                message="Your instructors haven't published any activities. New work will appear here."
              />
            ) : visibleActivities.length === 0 ? (
              <EmptyState
                icon="search"
                title="No matching activities"
                message="No activities match the current filter or search."
                action={
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => {
                      setUrlFilters({ filter: "all", q: "" });
                    }}
                  >
                    Clear filters
                  </button>
                }
              />
            ) : (
              <div className="space-y-3">
                {visibleActivities.map((activity) => (
                  <ActivityCard key={activity.id} activity={activity} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </PageShell>
  );
}
