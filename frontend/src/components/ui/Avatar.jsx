function initials(name) {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return `${parts[0][0]}${last}`.toUpperCase();
}

/** Initials in a tinted circle. Decorative: the name is always shown next to it. */
export default function Avatar({ name, size = "md" }) {
  const sizes = { sm: "h-8 w-8 text-[11px]", md: "h-9 w-9 text-xs" };
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-psu-maroon/[0.08] font-semibold text-text-brand ring-1 ring-psu-maroon/15 ${sizes[size]}`}
    >
      {initials(name)}
    </span>
  );
}
