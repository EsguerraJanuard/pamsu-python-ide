import Icon from "./Icon";

/**
 * Footer for a paged list: "Showing 16–30 of 134 events" with previous and
 * next buttons. Renders nothing when everything fits on one page. Without
 * `totalItems` (older servers) only "Page 2 of 9" is shown.
 */
export default function Pagination({ page, totalPages, totalItems, pageSize, onPageChange, disabled = false, noun = "results", className = "" }) {
  if (totalPages <= 1) return null;
  const hasTotal = typeof totalItems === "number" && totalItems > 0;
  const first = (page - 1) * pageSize + 1;
  const last = hasTotal ? Math.min(page * pageSize, totalItems) : page * pageSize;

  return (
    <nav aria-label="Pagination" className={`flex flex-wrap items-center justify-between gap-3 border-t border-border-subtle px-4 py-3 ${className}`}>
      <p className="text-xs text-text-muted" aria-live="polite">
        {hasTotal ? (
          <>
            Showing{" "}
            <span className="font-semibold tabular-nums text-text-main">
              {first.toLocaleString()}–{last.toLocaleString()}
            </span>{" "}
            of <span className="font-semibold tabular-nums text-text-main">{totalItems.toLocaleString()}</span> {noun}
          </>
        ) : (
          <>
            Page {page} of {totalPages}
          </>
        )}
      </p>
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          className="btn-secondary btn-sm px-2"
          onClick={() => onPageChange(page - 1)}
          disabled={disabled || page <= 1}
          aria-label="Previous page"
        >
          <Icon name="chevronLeft" className="h-4 w-4" />
        </button>
        {hasTotal && (
          <span className="min-w-[5.5rem] text-center text-xs tabular-nums text-text-muted">
            Page {page} of {totalPages}
          </span>
        )}
        <button
          type="button"
          className="btn-secondary btn-sm px-2"
          onClick={() => onPageChange(page + 1)}
          disabled={disabled || page >= totalPages}
          aria-label="Next page"
        >
          <Icon name="chevronRight" className="h-4 w-4" />
        </button>
      </div>
    </nav>
  );
}
